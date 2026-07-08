"""
TEO — Router: Agendamentos (Citas Neurologia)
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.professional import Professional, ProfessionalRole
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])


@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
    status: Optional[AppointmentStatus] = None,
    patient_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista agendamentos com filtros opcionais por status e paciente (Terapeutas veem apenas de vinculados)."""
    query = db.query(Appointment)
    if current_user.role == ProfessionalRole.TERAPEUTA:
        from app.routers.patients import _get_allowed_patient_ids_for_terapeuta
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        query = query.filter(Appointment.paciente_id.in_(allowed_ids))
    if status:
        query = query.filter(Appointment.status == status)
    if patient_id:
        query = query.filter(Appointment.paciente_id == patient_id)
    return query.order_by(Appointment.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.RECEPCAO, ProfessionalRole.ADMIN
    ))
):
    """Cria novo agendamento manualmente."""
    appointment = Appointment(**data.dict())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Atualiza status de um agendamento."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(appointment, key, value)

    # Se confirmado, atualiza data_ultimo_laudo do paciente
    if data.status in [AppointmentStatus.REALIZADO]:
        from app.models.patient import Patient
        from datetime import date
        patient = db.query(Patient).filter(Patient.id == appointment.paciente_id).first()
        if patient:
            patient.data_ultimo_laudo = date.today()
            patient.alerta_laudo_enviado = False

    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/pending-count", response_model=dict)
def pending_count(
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna contagem de agendamentos por status (para dashboard)."""
    from sqlalchemy import func
    counts = db.query(
        Appointment.status, func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    return {status.value: count for status, count in counts}
