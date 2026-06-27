"""
Modelo: Relatórios Semestrais
Armazena a síntese gerada pela IA e o caminho do PDF gerado pelo WeasyPrint.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Report(Base):
    __tablename__ = "relatorios_semestrais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Chaves estrangeiras
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    assinado_por = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=True)
    cita_id = Column(UUID(as_uuid=True), ForeignKey("citas_neurologia.id"), nullable=True)

    # Período coberto pelo relatório
    periodo_inicio = Column(Date, nullable=False)
    periodo_fim = Column(Date, nullable=False)

    # Conteúdo gerado pela IA
    sintese_global = Column(Text, nullable=True)  # Síntese narrativa gerada pelo LLM
    num_evolucoes_analisadas = Column(String(10), nullable=True)

    # Arquivo PDF gerado
    pdf_path = Column(String(500), nullable=True)
    pdf_gerado_em = Column(DateTime, nullable=True)

    # Pareceres individuais por área (JSON serializado)
    pareceres_json = Column(Text, nullable=True)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos ORM
    paciente = relationship("Patient", back_populates="relatorios")
    assinado_por_profissional = relationship("Professional", back_populates="relatorios_assinados")

    def __repr__(self):
        return f"<Report id={self.id} paciente={self.paciente_id} periodo={self.periodo_inicio}/{self.periodo_fim}>"
