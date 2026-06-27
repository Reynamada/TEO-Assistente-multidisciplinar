from datetime import date
from sqlalchemy.orm import Session

from app.models.professional import Professional, ProfessionalRole, ProfessionalEspecialidade
from app.models.patient import Patient

def test_create_professional(db_session: Session):
    prof = Professional(
        nome="Dra. Teste",
        email="teste@clinica.com",
        hashed_password="fakehash",
        role=ProfessionalRole.NEUROPEDIATRA,
        especialidade=ProfessionalEspecialidade.NEUROPEDIATRIA
    )
    db_session.add(prof)
    db_session.commit()
    
    saved_prof = db_session.query(Professional).filter_by(email="teste@clinica.com").first()
    assert saved_prof is not None
    assert saved_prof.nome == "Dra. Teste"
    assert saved_prof.role == ProfessionalRole.NEUROPEDIATRA

def test_create_patient_with_neuropediatra(db_session: Session):
    prof = Professional(
        nome="Dr. João",
        email="joao@clinica.com",
        hashed_password="fakehash",
        role=ProfessionalRole.NEUROPEDIATRA
    )
    db_session.add(prof)
    db_session.commit()
    db_session.refresh(prof)
    
    patient = Patient(
        nome="Mateo Teste",
        data_nascimento=date(2020, 5, 10),
        diagnostico_principal="TEA",
        nome_responsavel="Maria Teste",
        whatsapp_responsavel="+5511999999999",
        neuropediatra_id=prof.id
    )
    db_session.add(patient)
    db_session.commit()
    
    saved_patient = db_session.query(Patient).filter_by(whatsapp_responsavel="+5511999999999").first()
    assert saved_patient is not None
    assert saved_patient.idade >= 0
    assert saved_patient.neuropediatra.nome == "Dr. João"
