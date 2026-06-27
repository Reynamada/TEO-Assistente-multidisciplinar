"""
TEO — Router: Pacientes
CRUD completo de pacientes com controle de acesso por role.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.professional import Professional, ProfessionalRole
from app.schemas.schemas import PatientCreate, PatientUpdate, PatientResponse
from app.services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    ativo: Optional[bool] = True,
    search: Optional[str] = Query(None, description="Busca por nome ou WhatsApp"),
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista pacientes com filtro e busca."""
    query = db.query(Patient).filter(Patient.ativo == ativo)
    if search:
        query = query.filter(
            Patient.nome.ilike(f"%{search}%") |
            Patient.whatsapp_responsavel.ilike(f"%{search}%") |
            Patient.nome_responsavel.ilike(f"%{search}%")
        )
    return query.order_by(Patient.nome).offset(skip).limit(limit).all()


@router.post("/", response_model=PatientResponse, status_code=201)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.RECEPCAO, ProfessionalRole.ADMIN
    ))
):
    """Cadastra novo paciente. Apenas Recepção e Admin."""
    existing = db.query(Patient).filter(Patient.whatsapp_responsavel == data.whatsapp_responsavel).first()
    if existing:
        raise HTTPException(status_code=400, detail="WhatsApp já cadastrado para outro paciente")

    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna dados de um paciente específico."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Atualiza dados do paciente."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204)
def deactivate_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(ProfessionalRole.ADMIN))
):
    """Desativa um paciente (soft delete). Apenas Admin."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    patient.ativo = False
    db.commit()


@router.get("/laudos/vencendo", response_model=List[PatientResponse])
def laudos_vencendo(
    dias: int = Query(150, description="Dias desde o último laudo"),
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista pacientes com laudos vencendo (regra dos 5 meses)."""
    from datetime import date, timedelta
    limite = date.today() - timedelta(days=dias)
    return db.query(Patient).filter(
        Patient.ativo == True,
        Patient.data_ultimo_laudo <= limite
    ).all()
