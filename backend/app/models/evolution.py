"""
Modelo: Evoluções Semanais
Registra as notas técnicas de cada sessão e a mensagem traduzida pelo TEO para os pais.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Evolution(Base):
    __tablename__ = "evolucoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Chaves estrangeiras
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    profissional_id = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)

    # Dados da sessão
    data_sessao = Column(Date, nullable=False, default=date.today)
    tipo_sessao = Column(String(100), nullable=True)  # ex: "Terapia Ocupacional", "Fonoaudiologia"
    duracao_minutos = Column(String(10), nullable=True)

    # Notas técnicas (linguagem clínica — preenchidas pelo terapeuta)
    notas_tecnicas = Column(Text, nullable=False)

    # Mensagem traduzida pelo TEO para os pais (gerada pelo LLM)
    mensagem_pais = Column(Text, nullable=True)

    # Controle de envio WhatsApp
    whatsapp_enviado = Column(Boolean, default=False)
    whatsapp_enviado_em = Column(DateTime, nullable=True)
    whatsapp_sid = Column(String(100), nullable=True)  # SID da mensagem Twilio

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos ORM
    paciente = relationship("Patient", back_populates="evolucoes")
    profissional = relationship("Professional", back_populates="evolucoes_registradas")

    def __repr__(self):
        return f"<Evolution id={self.id} paciente={self.paciente_id} data={self.data_sessao}>"
