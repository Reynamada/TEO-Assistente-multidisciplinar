"""
TEO — Router: Indicações Terapêuticas
Formulário do Neuropediatra para indicar terapeutas + diagnóstico/evolução/recomendações.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.professional import Professional, ProfessionalRole
from app.schemas.schemas import IndicationCreate, IndicationUpdate, IndicationResponse
from app.services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/indications", tags=["Indicações Terapêuticas"])


@router.get("/patient/{patient_id}", response_model=IndicationResponse)
def get_indication(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna as indicações terapêuticas e laudo do neuropediatra para um paciente."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    # Terapeutas só veem indicações dos seus pacientes vinculados
    if current_user.role == ProfessionalRole.TERAPEUTA:
        from app.routers.patients import _get_allowed_patient_ids_for_terapeuta
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        if patient_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Acesso proibido: paciente não vinculado a você.")

    # Retorna dados do paciente (onde estão as indicações)
    return IndicationResponse(
        terapeutas_ids=[str(t.id) for t in patient.terapeutas_sugeridos] if patient.terapeutas_sugeridos else [],
        diagnostico=patient.diagnostico_consulta or patient.diagnostico_principal,
        evolucao=patient.evolucao_consulta or patient.observacoes,
        recomendacoes=patient.recomendacoes_consulta or patient.recomendacoes_terapeuta,
        atualizado_em=patient.updated_at
    )


@router.post("/patient/{patient_id}", response_model=IndicationResponse, status_code=201)
def create_indication(
    patient_id: UUID,
    payload: IndicationCreate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN))
):
    """
    Neuropediatra registra/atualiza indicações terapêuticas:
    - Lista de terapeutas sugeridos (IDs)
    - Diagnóstico
    - Evolução observada
    - Recomendações para próximo período
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    # Valida terapeutas
    terapeutas = []
    if payload.terapeutas_ids:
        terapeutas = db.query(Professional).filter(
            Professional.id.in_(payload.terapeutas_ids),
            Professional.role == ProfessionalRole.TERAPEUTA
        ).all()
        if len(terapeutas) != len(payload.terapeutas_ids):
            raise HTTPException(status_code=400, detail="Um ou mais IDs de terapeuta inválidos")

    patient.terapeutas_sugeridos = terapeutas
    patient.diagnostico_consulta = payload.diagnostico or patient.diagnostico_consulta
    patient.evolucao_consulta = payload.evolucao or patient.evolucao_consulta
    patient.recomendacoes_consulta = payload.recomendacoes or patient.recomendacoes_consulta
    db.commit()
    db.refresh(patient)

    return IndicationResponse(
        terapeutas_ids=[str(t.id) for t in terapeutas],
        diagnostico=patient.diagnostico_consulta,
        evolucao=patient.evolucao_consulta,
        recomendacoes=patient.recomendacoes_consulta,
        atualizado_em=patient.updated_at
    )


@router.patch("/patient/{patient_id}", response_model=IndicationResponse)
def update_indication(
    patient_id: UUID,
    payload: IndicationUpdate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN))
):
    """Atualiza campos específicos da indicação."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if payload.terapeutas_ids is not None:
        terapeutas = db.query(Professional).filter(
            Professional.id.in_(payload.terapeutas_ids),
            Professional.role == ProfessionalRole.TERAPEUTA
        ).all()
        if len(terapeutas) != len(payload.terapeutas_ids):
            raise HTTPException(status_code=400, detail="Um ou mais IDs de terapeuta inválidos")
        patient.terapeutas_sugeridos = terapeutas

    if payload.diagnostico is not None:
        patient.diagnostico_consulta = payload.diagnostico
    if payload.evolucao is not None:
        patient.evolucao_consulta = payload.evolucao
    if payload.recomendacoes is not None:
        patient.recomendacoes_consulta = payload.recomendacoes

    db.commit()
    db.refresh(patient)

    return IndicationResponse(
        terapeutas_ids=[str(t.id) for t in patient.terapeutas_sugeridos] if patient.terapeutas_sugeridos else [],
        diagnostico=patient.diagnostico_consulta,
        evolucao=patient.evolucao_consulta,
        recomendacoes=patient.recomendacoes_consulta,
        atualizado_em=patient.updated_at
    )