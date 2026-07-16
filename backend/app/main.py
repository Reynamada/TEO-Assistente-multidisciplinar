"""
TEO — FastAPI Application Entry Point
Sistema de IA para Clínicas de Neurodesenvolvimento (TEA)
"""
import os
from contextlib import asynccontextmanager
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import create_tables
from .jobs.cron_jobs import create_scheduler

# Importa todos os routers
from .routers import auth, patients, evolutions, appointments, whatsapp, reports, indications

settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    global scheduler

    # Startup
    logger.info("🚀 TEO Backend iniciando...")

    # Cria tabelas no banco (caso não existam)
    try:
        create_tables()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")

    # Inicia o scheduler de CRON jobs
    try:
        scheduler = create_scheduler()
        scheduler.start()
        logger.info(f"📅 Scheduler iniciado — verificação diária às {settings.cron_run_time}")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {e}")

    # Cria diretório de relatórios
    os.makedirs(settings.reports_dir, exist_ok=True)

    logger.info(f"🧩 TEO Backend pronto | Ambiente: {settings.environment}")
    yield

    # Shutdown
    logger.info("🛑 TEO Backend encerrando...")
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("📅 Scheduler encerrado")


# ─────────────────────────────────────────────────────────────────────────────
# APP FASTAPI
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TEO — Tu Enlace Organizador",
    description=(
        "Sistema de IA para Clínicas Multidisciplinares de Neurodesenvolvimento (TEA). "
        "Módulos: Tradução de Evoluções via LLM, Agendamentos (Regra dos 5 Meses), "
        "e Relatórios Semestrais consolidados em PDF."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# ─────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (e.g., Streamlit Cloud)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(patients.router, prefix=API_PREFIX)
app.include_router(evolutions.router, prefix=API_PREFIX)
app.include_router(appointments.router, prefix=API_PREFIX)
app.include_router(whatsapp.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(indications.router, prefix=API_PREFIX)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS BASE
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "sistema": "TEO — Tu Enlace Organizador",
        "versao": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check para monitoramento e Docker."""
    return JSONResponse(
        content={"status": "healthy", "ambiente": settings.environment},
        status_code=200
    )


@app.post("/api/v1/cron/trigger-manual", tags=["Admin"])
def trigger_cron_manual():
    """
    Dispara manualmente o CRON de verificação de laudos.
    Útil para testes sem esperar o horário agendado.
    """
    from app.jobs.cron_jobs import verificar_laudos_vencendo
    verificar_laudos_vencendo()
    return {"message": "CRON executado manualmente com sucesso"}
