"""
Modelo: Profissionais
Terapeutas, neuropediatras e equipe de recepção da clínica.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ProfessionalRole(str, PyEnum):
    RECEPCAO = "recepcao"
    TERAPEUTA = "terapeuta"
    NEUROPEDIATRA = "neuropediatra"
    ADMIN = "admin"


class ProfessionalEspecialidade(str, PyEnum):
    FONOAUDIOLOGIA = "Fonoaudiologia"
    TERAPIA_OCUPACIONAL = "Terapia Ocupacional"
    PSICOLOGIA = "Psicologia"
    PSICOPEDAGOGIA = "Psicopedagogia"
    FISIOTERAPIA = "Fisioterapia"
    NEUROPEDIATRIA = "Neuropediatria"
    RECEPCAO_ADM = "Recepção/Administrativo"


class Professional(Base):
    __tablename__ = "profissionais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)

    role = Column(Enum(ProfessionalRole), nullable=False, default=ProfessionalRole.TERAPEUTA)
    especialidade = Column(Enum(ProfessionalEspecialidade), nullable=True)
    registro_conselho = Column(String(50), nullable=True)  # CRM, CRP, CREFONO etc.

    telefone = Column(String(20), nullable=True)
    ativo = Column(Boolean, default=True)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos ORM
    pacientes_atendidos = relationship(
        "Patient",
        back_populates="neuropediatra",
        foreign_keys="Patient.neuropediatra_id"
    )
    evolucoes_registradas = relationship("Evolution", back_populates="profissional")
    citas_como_neuropediatra = relationship(
        "Appointment",
        back_populates="neuropediatra",
        foreign_keys="Appointment.neuropediatra_id"
    )
    relatorios_assinados = relationship("Report", back_populates="assinado_por_profissional")

    def __repr__(self):
        return f"<Professional id={self.id} nome={self.nome} role={self.role}>"
