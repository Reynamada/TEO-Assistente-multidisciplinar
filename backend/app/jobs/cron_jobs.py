"""
TEO — CRON Jobs (APScheduler)
Implementa a REGRA DOS 5 MESES e outras automações agendadas.
"""
from datetime import datetime, date, timedelta
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.patient import Patient
from app.models.professional import Professional, ProfessionalRole
from app.models.appointment import Appointment, AppointmentStatus
from app.services import whatsapp_service, llm_service

settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# TAREFA PRINCIPAL: REGRA DOS 5 MESES (150 dias)
# ─────────────────────────────────────────────────────────────────────────────

def verificar_laudos_vencendo():
    """
    Varre todos os pacientes ativos e dispara alertas de WhatsApp
    para aqueles cujo laudo vencerá nos próximos {LAUDO_ALERT_DAYS} dias.

    Regra: data_atual - data_ultimo_laudo >= 150 dias (5 meses)
    """
    logger.info("🔍 CRON: Iniciando verificação de laudos vencendo...")
    db: Session = SessionLocal()

    try:
        hoje = date.today()
        limite_dias = settings.laudo_alert_days

        # Busca pacientes ativos com laudo registrado e alerta não enviado
        pacientes = db.query(Patient).filter(
            Patient.ativo == True,
            Patient.data_ultimo_laudo.isnot(None),
            Patient.alerta_laudo_enviado == False,
        ).all()

        alertas_enviados = 0

        for paciente in pacientes:
            dias_desde_laudo = (hoje - paciente.data_ultimo_laudo).days

            if dias_desde_laudo >= limite_dias:
                dias_restantes = max(0, 180 - dias_desde_laudo)  # regra dos 6 meses
                logger.info(
                    f"⚠️  Paciente {paciente.nome}: {dias_desde_laudo} dias desde último laudo "
                    f"({dias_restantes} dias para vencer)"
                )

                # Busca neuropediatra do paciente (ou qualquer neuropediatra disponível)
                neuropediatra = None
                if paciente.neuropediatra_id:
                    neuropediatra = db.query(Professional).filter(
                        Professional.id == paciente.neuropediatra_id,
                        Professional.ativo == True
                    ).first()

                if not neuropediatra:
                    neuropediatra = db.query(Professional).filter(
                        Professional.role == ProfessionalRole.NEUROPEDIATRA,
                        Professional.ativo == True
                    ).first()

                if not neuropediatra:
                    logger.warning(f"Sem neuropediatra disponível para {paciente.nome}. Pulando.")
                    continue

                # Gera 2 opções de horário (próximas semanas)
                data_op1 = datetime.combine(
                    hoje + timedelta(days=7), datetime.min.time().replace(hour=9, minute=0)
                )
                data_op2 = datetime.combine(
                    hoje + timedelta(days=14), datetime.min.time().replace(hour=14, minute=30)
                )

                opcao_1_fmt = data_op1.strftime("%A, %d/%m/%Y às %H:%M")
                opcao_2_fmt = data_op2.strftime("%A, %d/%m/%Y às %H:%M")

                # Registra a cita na tabela antes de enviar
                cita = Appointment(
                    paciente_id=paciente.id,
                    neuropediatra_id=neuropediatra.id,
                    data_proposta_1=data_op1,
                    data_proposta_2=data_op2,
                    status=AppointmentStatus.PENDENTE,
                    alerta_enviado_em=datetime.utcnow(),
                )
                db.add(cita)
                db.flush()  # Obtém o ID sem commitar

                # Envia WhatsApp
                try:
                    sid = whatsapp_service.enviar_opcoes_agendamento(
                        para_numero=paciente.whatsapp_responsavel,
                        nome_responsavel=paciente.nome_responsavel,
                        nome_paciente=paciente.nome.split()[0],
                        opcao_1_fmt=opcao_1_fmt,
                        opcao_2_fmt=opcao_2_fmt,
                        nome_neuropediatra=f"Dr(a). {neuropediatra.nome.split()[-1]}",
                        dias_restantes=dias_restantes
                    )
                    cita.alerta_whatsapp_sid = sid
                    paciente.alerta_laudo_enviado = True
                    alertas_enviados += 1
                    logger.info(f"✅ Alerta enviado para {paciente.nome_responsavel} ({paciente.whatsapp_responsavel})")
                except Exception as e:
                    logger.error(f"❌ Falha ao enviar WhatsApp para {paciente.nome}: {e}")
                    db.rollback()
                    continue

        db.commit()
        logger.info(f"✅ CRON finalizado: {alertas_enviados} alertas enviados de {len(pacientes)} verificados")

    except Exception as e:
        logger.error(f"❌ Erro crítico no CRON de laudos: {e}")
        db.rollback()
    finally:
        db.close()


def resetar_alertas_mensalmente():
    """
    Reseta o flag alerta_laudo_enviado mensalmente para reenvio
    caso o responsável não tenha respondido.
    """
    logger.info("🔄 CRON: Resetando flags de alerta mensalmente...")
    db: Session = SessionLocal()
    try:
        db.query(Patient).filter(
            Patient.alerta_laudo_enviado == True
        ).update({"alerta_laudo_enviado": False})
        db.commit()
        logger.info("✅ Flags resetados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao resetar flags: {e}")
        db.rollback()
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DO SCHEDULER
# ─────────────────────────────────────────────────────────────────────────────

def create_scheduler() -> BackgroundScheduler:
    """
    Cria e configura o APScheduler com todos os jobs do TEO.

    Jobs configurados:
    - verificar_laudos_vencendo: Diariamente às 08:00
    - resetar_alertas_mensalmente: No 1º dia de cada mês às 07:00
    """
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

    # Extrai hora e minuto do config
    try:
        hora_str, minuto_str = settings.cron_run_time.split(":")
        hora = int(hora_str)
        minuto = int(minuto_str)
    except (ValueError, AttributeError):
        hora, minuto = 8, 0

    # Job 1: Verificação diária de laudos
    scheduler.add_job(
        verificar_laudos_vencendo,
        trigger=CronTrigger(hour=hora, minute=minuto),
        id="verificar_laudos_diario",
        name="Verificação Diária de Laudos (Regra 5 Meses)",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Job 2: Reset mensal dos alertas (1º dia do mês às 07:00)
    scheduler.add_job(
        resetar_alertas_mensalmente,
        trigger=CronTrigger(day=1, hour=7, minute=0),
        id="resetar_alertas_mensal",
        name="Reset Mensal de Alertas de Laudo",
        replace_existing=True,
    )

    logger.info(f"📅 Scheduler configurado: verificação diária às {settings.cron_run_time}")
    return scheduler
