"""
TEO — Router: Profissionais
Listagem de profissionais por role/especialidade.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.professional import Professional, ProfessionalRole, ProfessionalEspecialidade
from app.schemas.schemas import ProfessionalSimpleResponse
from app.services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/professionals", tags=["Profissionais"])


@router.get("", response_model=List[ProfessionalSimpleResponse])
def list_professionals(
    role: Optional[ProfessionalRole] = Query(None, description="Filtrar por role"),
    especialidade: Optional[ProfessionalEspecialidade] = Query(None, description="Filtrar por especialidade"),
    ativo: bool = True,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista profissionais (Terapeutas veem apenas vinculados)."""
    query = db.query(Professional).filter(Professional.ativo == ativo)

    if role:
        query = query.filter(Professional.role == role)
    if especialidade:
        query = query.filter(Professional.especialidade == especialidade)

    # Terapeutas veem apenas profissionais com quem compartilham pacientes
    if current_user.role == ProfessionalRole.TERAPEUTA:
        from app.routers.patients import _get_allowed_patient_ids_for_terapeuta
        allowed_patient_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        # Busca profissionais que atendem esses pacientes
        from app.models.evolution import Evolution
        prof_ids = db.query(Evolution.profissional_id).filter(
            Evolution.paciente_id.in_(allowed_patient_ids)
        ).distinct().all()
        prof_ids = [p[0] for p in prof_ids]
        if prof_ids:
            query = query.filter(Professional.id.in_(prof_ids))
        else:
            query = query.filter(Professional.id == current_user.id)

    return query.order_by(Professional.nome).all()


@router.get("/terapeutas", response_model=List[ProfessionalSimpleResponse])
def list_terapeutas(
    especialidade: Optional[ProfessionalEspecialidade] = Query(None),
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista apenas terapeutas (para seleção em indicações)."""
    query = db.query(Professional).filter(
        Professional.role == ProfessionalRole.TERAPEUTA,
        Professional.ativo == True
    )
    if especialidade:
        query = query.filter(Professional.especialidade == especialidade)
    return query.order_by(Professional.nome).all()


@router.get("/neuropediatras", response_model=List[ProfessionalSimpleResponse])
def list_neuropediatras(
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista apenas neuropediatras."""
    return db.query(Professional).filter(
        Professional.role == ProfessionalRole.NEUROPEDIATRA,
        Professional.ativo == True
    ).order_by(Professional.nome).all()


@router.get("/{prof_id}", response_model=ProfessionalSimpleResponse)
def get_professional(
    prof_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna detalhes de um profissional específico."""
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return prof