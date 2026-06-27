"""
Modelo: Citas (Consultas) de Neurologia
Gerencia o agendamento de consultas com o neuropediatra, disparado pela regra dos 5 meses.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AppointmentStatus(str, PyEnum):
    PENDENTE = "pendente"           # Mensagem enviada, aguardando resposta dos pais
    CONFIRMADO_OP1 = "confirmado_op1"  # Pais confirmaram opção 1
    CONFIRMADO_OP2 = "confirmado_op2"  # Pais confirmaram opção 2
    REAGENDAMENTO = "reagendamento"    # Pais pediram outro horário
    CANCELADO = "cancelado"
    REALIZADO = "realizado"


class Appointment(Base):
    __tablename__ = "citas_neurologia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Chaves estrangeiras
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    neuropediatra_id = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)

    # Opções de horário oferecidas ao responsável
    data_proposta_1 = Column(DateTime, nullable=True)
    data_proposta_2 = Column(DateTime, nullable=True)

    # Resultado
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDENTE)
    data_confirmada = Column(DateTime, nullable=True)
    resposta_pais = Column(Text, nullable=True)   # Texto original da resposta via WhatsApp

    # Controle de mensagens
    alerta_whatsapp_sid = Column(String(100), nullable=True)
    alerta_enviado_em = Column(DateTime, nullable=True)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observacoes = Column(Text, nullable=True)

    # Relacionamentos ORM
    paciente = relationship("Patient", back_populates="citas_neurologia")
    neuropediatra = relationship(
        "Professional",
        back_populates="citas_como_neuropediatra",
        foreign_keys=[neuropediatra_id]
    )

    def __repr__(self):
        return f"<Appointment id={self.id} status={self.status} paciente={self.paciente_id}>"
