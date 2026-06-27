"""
TEO — Router: WhatsApp Webhook
Recebe e processa mensagens entrantes via Twilio webhook.
NLU: interpreta respostas dos pais sobre agendamentos.
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.services import whatsapp_service, llm_service

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook Twilio para mensagens WhatsApp recebidas.
    Interpreta respostas dos pais sobre agendamentos de consulta.

    Configure este endpoint no Twilio Console como:
    POST https://seu-dominio/api/v1/whatsapp/webhook
    """
    form_data = await request.form()
    dados = whatsapp_service.processar_webhook(dict(form_data))

    numero_remetente = dados["de"]
    mensagem_recebida = dados["mensagem"]

    logger.info(f"📱 WhatsApp recebido de {numero_remetente}: '{mensagem_recebida}'")

    # Busca paciente pelo WhatsApp do responsável
    patient = db.query(Patient).filter(
        Patient.whatsapp_responsavel == numero_remetente
    ).first()

    if not patient:
        logger.warning(f"Número {numero_remetente} não encontrado no sistema")
        # Responde que não reconhece o número
        _responder_twilio(numero_remetente, (
            "Olá! 😊 Não encontrei seu cadastro em nosso sistema.\n"
            "Por favor, entre em contato diretamente com a clínica. Obrigado!"
        ))
        return Response(content="", media_type="text/xml")

    # Busca agendamento pendente para este paciente
    cita_pendente = db.query(Appointment).filter(
        Appointment.paciente_id == patient.id,
        Appointment.status == AppointmentStatus.PENDENTE
    ).order_by(Appointment.created_at.desc()).first()

    if not cita_pendente:
        logger.info(f"Sem agendamento pendente para {patient.nome}. Mensagem livre.")
        return Response(content="", media_type="text/xml")

    # Interpreta resposta via LLM NLU
    opcao_1_fmt = cita_pendente.data_proposta_1.strftime("%A, %d/%m/%Y às %H:%M") if cita_pendente.data_proposta_1 else "Opção 1"
    opcao_2_fmt = cita_pendente.data_proposta_2.strftime("%A, %d/%m/%Y às %H:%M") if cita_pendente.data_proposta_2 else "Opção 2"

    # Verificação rápida para "1" ou "2" sem precisar de LLM
    msg_lower = mensagem_recebida.strip().lower()
    if msg_lower in ["1", "opção 1", "opcao 1", "op1", "primeira"]:
        intencao = "aceitar_op1"
    elif msg_lower in ["2", "opção 2", "opcao 2", "op2", "segunda"]:
        intencao = "aceitar_op2"
    else:
        # Usa NLU do LLM para casos ambíguos
        resultado = llm_service.interpretar_resposta_pais(
            mensagem_recebida, patient.nome.split()[0], opcao_1_fmt, opcao_2_fmt
        )
        intencao = resultado.get("intencao", "desconhecido")

    # Atualiza o agendamento com base na intenção
    cita_pendente.resposta_pais = mensagem_recebida

    if intencao == "aceitar_op1":
        cita_pendente.status = AppointmentStatus.CONFIRMADO_OP1
        cita_pendente.data_confirmada = cita_pendente.data_proposta_1
        msg_confirmacao = (
            f"Perfeito, {patient.nome_responsavel}! ✅\n\n"
            f"Consulta de *{patient.nome.split()[0]}* confirmada para:\n"
            f"📅 *{opcao_1_fmt}*\n\n"
            f"Lembrarei você 24h antes. Até lá! 💙"
        )
    elif intencao == "aceitar_op2":
        cita_pendente.status = AppointmentStatus.CONFIRMADO_OP2
        cita_pendente.data_confirmada = cita_pendente.data_proposta_2
        msg_confirmacao = (
            f"Perfeito, {patient.nome_responsavel}! ✅\n\n"
            f"Consulta de *{patient.nome.split()[0]}* confirmada para:\n"
            f"📅 *{opcao_2_fmt}*\n\n"
            f"Lembrarei você 24h antes. Até lá! 💙"
        )
    elif intencao == "reagendar":
        cita_pendente.status = AppointmentStatus.REAGENDAMENTO
        msg_confirmacao = (
            f"Sem problema, {patient.nome_responsavel}! 😊\n\n"
            f"Nossa equipe entrará em contato em breve para encontrar um horário melhor para vocês. "
            f"Obrigado pela compreensão! 💙"
        )
    elif intencao == "cancelar":
        cita_pendente.status = AppointmentStatus.CANCELADO
        msg_confirmacao = (
            f"Entendido, {patient.nome_responsavel}. Se precisar reagendar no futuro, "
            f"é só nos avisar aqui. Cuide-se! 💙"
        )
    else:
        msg_confirmacao = (
            f"Olá, {patient.nome_responsavel}! 😊\n"
            f"Não entendi bem sua resposta. Você pode responder *1* ou *2* para confirmar o horário, "
            f"ou escrever *outro horário* se precisar de outra data."
        )

    db.commit()

    # Envia confirmação
    whatsapp_service.enviar_mensagem(numero_remetente, msg_confirmacao)

    return Response(content="", media_type="text/xml")


def _responder_twilio(para: str, mensagem: str):
    """Helper para enviar resposta via Twilio."""
    try:
        whatsapp_service.enviar_mensagem(para, mensagem)
    except Exception as e:
        logger.error(f"Erro ao responder via Twilio: {e}")
