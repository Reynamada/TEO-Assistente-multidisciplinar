"""
TEO — Configurações centralizadas via pydantic-settings.
Lê automaticamente do arquivo .env na raiz do projeto.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- Banco de Dados ---
    database_url: str = "postgresql://teo_user:teo_secure_password_change_me@localhost:5432/teo_db"

    # --- Segurança JWT ---
    secret_key: str = "mude_esta_chave_secreta"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # --- Groq LLM ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    # --- Ollama (Fallback) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"

    # --- OpenAI (optional) ---
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    # --- Twilio WhatsApp ---
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    twilio_webhook_url: str = ""

    # --- SMTP Email ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@clinicateo.com"

    # --- Clínica ---
    clinic_name: str = "Clínica TEO Neurodesenvolvimento"
    clinic_phone: str = ""
    clinic_email: str = ""

    # --- Diretórios ---
    reports_dir: str = "./reports"
    templates_dir: str = "./templates"

    # --- Scheduler ---
    laudo_alert_days: int = 150
    cron_run_time: str = "08:00"

    # --- Ambiente ---
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""
    return Settings()
