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


def _get_allowed_patient_ids_for_terapeuta(db: Session, current_user: Professional):
    """Calcula os IDs de pacientes vinculados a um determinado terapeuta."""
    from app.models.evolution import Evolution
    from app.models.report import Report
    # 1. IDs de pacientes com evoluções/sessões realizadas por este terapeuta
    evo_p_ids = [r[0] for r in db.query(Evolution.paciente_id).filter(Evolution.profissional_id == current_user.id).distinct().all()]
    
    # 2. IDs de pacientes onde o laudo ou observações indicam a especialidade ou nome do terapeuta
    spec_str = current_user.especialidade.value if current_user.especialidade else ""
    spec_p_ids = []
    if spec_str:
        spec_reports = db.query(Report.paciente_id).filter(Report.pareceres_json.ilike(f"%{spec_str}%")).distinct().all()
        spec_p_ids = [r[0] for r in spec_reports]
        
        spec_patients = db.query(Patient.id).filter(
            Patient.observacoes.ilike(f"%{spec_str}%") | Patient.observacoes.ilike(f"%{current_user.nome}%")
        ).all()
        spec_p_ids.extend([p[0] for p in spec_patients])
        
    return set(evo_p_ids + spec_p_ids)


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    ativo: Optional[bool] = True,
    search: Optional[str] = Query(None, description="Busca por nome ou WhatsApp"),
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista pacientes com filtro e busca (Terapeutas visualizam APENAS seus pacientes vinculados)."""
    query = db.query(Patient).filter(Patient.ativo == ativo)
    
    if current_user.role == ProfessionalRole.TERAPEUTA:
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        query = query.filter(Patient.id.in_(allowed_ids))
        
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

    patient = Patient(**data.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


# ── IMPORTANTE: rotas específicas ANTES do wildcard /{patient_id} ──────────

@router.get("/laudos/vencendo", response_model=List[PatientResponse])
def laudos_vencendo(
    dias: int = Query(150, description="Dias desde o último laudo"),
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista pacientes com laudos vencendo (regra dos 5 meses)."""
    from datetime import date, timedelta
    limite = date.today() - timedelta(days=dias)
    query = db.query(Patient).filter(
        Patient.ativo == True,
        Patient.data_ultimo_laudo <= limite
    )
    if current_user.role == ProfessionalRole.TERAPEUTA:
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        query = query.filter(Patient.id.in_(allowed_ids))
    return query.all()


@router.get("/{patient_id}/therapists", response_model=List[dict])
def get_patient_therapists(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna lista de profissionais/especialistas vinculados ou com evoluções de um paciente."""
    from app.models.evolution import Evolution
    from app.models.appointment import Appointment

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if current_user.role == ProfessionalRole.TERAPEUTA:
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        if patient_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Acesso proibido.")

    # 1. Profissionais das evoluções
    evo_profs = (
        db.query(Professional)
        .join(Evolution, Evolution.profissional_id == Professional.id)
        .filter(Evolution.paciente_id == patient_id)
        .all()
    )
    # 2. Profissionais de agendamentos (neuropediatra)
    appt_profs = (
        db.query(Professional)
        .join(Appointment, Appointment.neuropediatra_id == Professional.id)
        .filter(Appointment.paciente_id == patient_id)
        .all()
    )
    # 3. Neuropediatra vinculado diretamente ao paciente
    pat_profs = [patient.neuropediatra] if patient.neuropediatra else []

    seen_ids = set()
    result = []
    for p in evo_profs + appt_profs + pat_profs:
        if p and str(p.id) not in seen_ids:
            seen_ids.add(str(p.id))
            # Se tiver especialidade cadastrada, usa ela; senão usa o label do role
            if p.especialidade:
                spec = p.especialidade.value
            else:
                role_labels = {
                    "terapeuta": "Terapeuta",
                    "neuropediatra": "Neuropediatria",
                    "recepcao": "Recepção",
                    "admin": "Administrativo",
                }
                spec = role_labels.get(p.role.value if p.role else "", "Terapeuta")
            result.append({
                "id": str(p.id),
                "nome": p.nome,
                "especialidade": spec,
                "role": p.role.value if p.role else "terapeuta",
                "registro_conselho": p.registro_conselho or ""
            })
    return result


# ── Wildcard /{patient_id} DEPOIS das rotas específicas ────────────────────

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Retorna dados de um paciente específico (com verificação de vínculo para Terapeutas)."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
        
    if current_user.role == ProfessionalRole.TERAPEUTA:
        allowed_ids = _get_allowed_patient_ids_for_terapeuta(db, current_user)
        if patient_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Acesso proibido: este paciente não está vinculado a você.")
            
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

    update_data = data.dict(exclude_unset=True)
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
