"""
Modelo: Pacientes
Armazena todos os dados clínicos e de contato dos pacientes atendidos pela clínica.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Patient(Base):
    __tablename__ = "pacientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    diagnostico_principal = Column(String(100), default="TEA")

    # Responsável
    nome_responsavel = Column(String(200), nullable=False)
    parentesco_responsavel = Column(String(50), default="Mãe/Pai")
    whatsapp_responsavel = Column(String(20), nullable=False, unique=True)
    email_responsavel = Column(String(150), nullable=True)

    # Controle de laudo (regra dos 5 meses)
    data_ultimo_laudo = Column(Date, nullable=True)
    alerta_laudo_enviado = Column(Boolean, default=False)

    # Relacionamentos
    neuropediatra_id = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=True)
    ativo = Column(Boolean, default=True)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observacoes = Column(Text, nullable=True)

    # Relacionamentos ORM
    neuropediatra = relationship("Professional", back_populates="pacientes_atendidos", foreign_keys=[neuropediatra_id])
    evolucoes = relationship("Evolution", back_populates="paciente", cascade="all, delete-orphan")
    citas_neurologia = relationship("Appointment", back_populates="paciente", cascade="all, delete-orphan")
    relatorios = relationship("Report", back_populates="paciente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient id={self.id} nome={self.nome}>"

    @property
    def idade(self) -> int:
        """Calcula a idade do paciente em anos."""
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
