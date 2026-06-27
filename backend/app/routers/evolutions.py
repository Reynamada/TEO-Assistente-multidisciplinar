"""
TEO — Router: Evoluções Semanais
Módulo 1 do sistema: registro de sessões + tradução LLM + disparo WhatsApp.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.evolution import Evolution
from app.models.patient import Patient
from app.models.professional import Professional, ProfessionalRole
from app.schemas.schemas import EvolutionCreate, EvolutionResponse, TranslateEvolutionRequest
from app.services.auth_service import get_current_user, require_role
from app.services import llm_service, whatsapp_service

router = APIRouter(prefix="/evolutions", tags=["Evoluções"])


@router.get("/patient/{patient_id}", response_model=List[EvolutionResponse])
def list_evolutions(
    patient_id: UUID,
    limit: int = 48,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista evoluções de um paciente (padrão: últimas 48 sessões)."""
    return db.query(Evolution).filter(
        Evolution.paciente_id == patient_id
    ).order_by(Evolution.data_sessao.desc()).limit(limit).all()


@router.post("/", response_model=EvolutionResponse, status_code=201)
def create_evolution(
    data: EvolutionCreate,
    background_tasks: BackgroundTasks,
    auto_translate: bool = True,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.TERAPEUTA, ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN
    ))
):
    """
    Cria nova evolução de sessão.
    Se auto_translate=True, chama o LLM em background para traduzir as notas.
    """
    # Verifica se paciente existe
    patient = db.query(Patient).filter(Patient.id == data.paciente_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    evolution = Evolution(
        paciente_id=data.paciente_id,
        profissional_id=current_user.id,
        data_sessao=data.data_sessao,
        tipo_sessao=data.tipo_sessao,
        duracao_minutos=data.duracao_minutos,
        notas_tecnicas=data.notas_tecnicas,
    )
    db.add(evolution)
    db.commit()
    db.refresh(evolution)

    # Tradução automática em background
    if auto_translate:
        background_tasks.add_task(
            _traduzir_e_salvar,
            evolution_id=evolution.id,
            notas=data.notas_tecnicas,
            nome_paciente=patient.nome.split()[0],
            tipo_sessao=data.tipo_sessao
        )

    return evolution


def _traduzir_e_salvar(evolution_id: UUID, notas: str, nome_paciente: str, tipo_sessao: str):
    """Background task: traduz notas e salva mensagem_pais no banco."""
    db = SessionLocal()
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        mensagem = llm_service.traduzir_evolucao(notas, nome_paciente, tipo_sessao)
        db.query(Evolution).filter(Evolution.id == evolution_id).update(
            {"mensagem_pais": mensagem}
        )
        db.commit()
    except Exception as e:
        from loguru import logger
        logger.error(f"Erro na tradução background: {e}")
    finally:
        db.close()


@router.post("/translate-preview", response_model=dict)
def translate_preview(
    data: TranslateEvolutionRequest,
    current_user: Professional = Depends(get_current_user)
):
    """
    Pré-visualiza a tradução LLM sem salvar no banco.
    Usado no dashboard do terapeuta antes de enviar.
    """
    mensagem = llm_service.traduzir_evolucao(
        data.notas_tecnicas,
        data.nome_paciente,
        data.tipo_sessao
    )
    return {"mensagem_traduzida": mensagem}


@router.post("/{evolution_id}/send-whatsapp", response_model=dict)
def send_evolution_whatsapp(
    evolution_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.TERAPEUTA, ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN
    ))
):
    """
    Envia a mensagem de evolução traduzida pelo WhatsApp para os pais.
    Requer que a tradução já tenha sido gerada (mensagem_pais não nula).
    """
    evolution = db.query(Evolution).filter(Evolution.id == evolution_id).first()
    if not evolution:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    if not evolution.mensagem_pais:
        raise HTTPException(status_code=400, detail="Tradução ainda não gerada. Aguarde ou use /translate-preview")

    if evolution.whatsapp_enviado:
        raise HTTPException(status_code=400, detail="WhatsApp já foi enviado para esta evolução")

    patient = db.query(Patient).filter(Patient.id == evolution.paciente_id).first()

    sid = whatsapp_service.enviar_resultado_evolucao(
        para_numero=patient.whatsapp_responsavel,
        mensagem_traduzida=evolution.mensagem_pais
    )

    evolution.whatsapp_enviado = True
    evolution.whatsapp_enviado_em = datetime.utcnow()
    evolution.whatsapp_sid = sid
    db.commit()

    return {"success": True, "sid": sid, "enviado_para": patient.whatsapp_responsavel}
