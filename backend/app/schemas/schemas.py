"""
TEO — Schemas Pydantic para validação de dados.
Cobre Pacientes, Profissionais, Evoluções, Agendamentos e Relatórios.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
from app.models.professional import ProfessionalRole, ProfessionalEspecialidade
from app.models.appointment import AppointmentStatus


# ─────────────────────────────────────────────
# PACIENTES
# ─────────────────────────────────────────────

class PatientBase(BaseModel):
    nome: str
    data_nascimento: date
    diagnostico_principal: str = "TEA"
    nome_responsavel: str
    parentesco_responsavel: str = "Mãe/Pai"
    whatsapp_responsavel: str
    email_responsavel: Optional[str] = None
    observacoes: Optional[str] = None

class PatientCreate(PatientBase):
    neuropediatra_id: Optional[UUID] = None

class PatientUpdate(BaseModel):
    nome: Optional[str] = None
    data_nascimento: Optional[date] = None
    nome_responsavel: Optional[str] = None
    whatsapp_responsavel: Optional[str] = None
    email_responsavel: Optional[str] = None
    neuropediatra_id: Optional[UUID] = None
    data_ultimo_laudo: Optional[date] = None
    ativo: Optional[bool] = None
    observacoes: Optional[str] = None

class PatientResponse(PatientBase):
    id: UUID
    data_ultimo_laudo: Optional[date] = None
    alerta_laudo_enviado: bool
    neuropediatra_id: Optional[UUID] = None
    ativo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# PROFISSIONAIS
# ─────────────────────────────────────────────

class ProfessionalBase(BaseModel):
    nome: str
    email: EmailStr
    role: ProfessionalRole
    especialidade: Optional[ProfessionalEspecialidade] = None
    registro_conselho: Optional[str] = None
    telefone: Optional[str] = None

class ProfessionalCreate(ProfessionalBase):
    password: str

class ProfessionalUpdate(BaseModel):
    nome: Optional[str] = None
    especialidade: Optional[ProfessionalEspecialidade] = None
    registro_conselho: Optional[str] = None
    telefone: Optional[str] = None
    ativo: Optional[bool] = None

class ProfessionalResponse(ProfessionalBase):
    id: UUID
    ativo: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str
    role: ProfessionalRole
    nome: str

class TokenData(BaseModel):
    email: Optional[str] = None


# ─────────────────────────────────────────────
# EVOLUÇÕES
# ─────────────────────────────────────────────

class EvolutionBase(BaseModel):
    paciente_id: UUID
    data_sessao: date
    tipo_sessao: Optional[str] = None
    duracao_minutos: Optional[str] = None
    notas_tecnicas: str

class EvolutionCreate(EvolutionBase):
    pass

class EvolutionUpdate(BaseModel):
    notas_tecnicas: Optional[str] = None
    tipo_sessao: Optional[str] = None

class EvolutionResponse(EvolutionBase):
    id: UUID
    profissional_id: UUID
    mensagem_pais: Optional[str] = None
    whatsapp_enviado: bool
    whatsapp_enviado_em: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TranslateEvolutionRequest(BaseModel):
    """Request para traduzir notas técnicas via LLM sem salvar."""
    notas_tecnicas: str
    nome_paciente: str
    tipo_sessao: Optional[str] = None


# ─────────────────────────────────────────────
# AGENDAMENTOS
# ─────────────────────────────────────────────

class AppointmentBase(BaseModel):
    paciente_id: UUID
    neuropediatra_id: UUID
    data_proposta_1: Optional[datetime] = None
    data_proposta_2: Optional[datetime] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    data_confirmada: Optional[datetime] = None
    resposta_pais: Optional[str] = None
    observacoes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: UUID
    status: AppointmentStatus
    data_confirmada: Optional[datetime] = None
    resposta_pais: Optional[str] = None
    alerta_enviado_em: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# RELATÓRIOS
# ─────────────────────────────────────────────

class ReportCreate(BaseModel):
    paciente_id: UUID
    periodo_inicio: date
    periodo_fim: date
    cita_id: Optional[UUID] = None

class ReportUpdate(BaseModel):
    sintese_global: Optional[str] = None
    pareceres_json: Optional[str] = None
    assinado_por: Optional[UUID] = None

class ReportResponse(BaseModel):
    id: UUID
    paciente_id: UUID
    periodo_inicio: date
    periodo_fim: date
    sintese_global: Optional[str] = None
    num_evolucoes_analisadas: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_gerado_em: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
