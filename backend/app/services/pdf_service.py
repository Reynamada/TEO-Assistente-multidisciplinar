"""
TEO — PDF Service (WeasyPrint)
Gera o Relatório Semestral consolidado em PDF a partir de template HTML/Jinja2.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

from app.config import get_settings

settings = get_settings()


def _get_template_env():
    """Retorna ambiente Jinja2 configurado para os templates HTML."""
    from jinja2 import Environment, FileSystemLoader
    templates_path = Path(settings.templates_dir)
    if not templates_path.exists():
        templates_path = Path(__file__).parent.parent.parent.parent / "templates"
    return Environment(loader=FileSystemLoader(str(templates_path)))


def gerar_relatorio_semestral(
    paciente_data: dict,
    profissional_data: dict,
    evolucoes: list[dict],
    sintese_global: str,
    pareceres: Optional[dict] = None,
    periodo_inicio: str = "",
    periodo_fim: str = "",
    report_id: str = ""
) -> str:
    """
    Gera o PDF do relatório semestral.

    Args:
        paciente_data: Dict com dados do paciente
        profissional_data: Dict com dados do neuropediatra
        evolucoes: Lista de evoluções do período
        sintese_global: Texto gerado pelo LLM
        pareceres: Dict com pareceres por área terapêutica
        periodo_inicio: Data início formatada
        periodo_fim: Data fim formatada
        report_id: UUID do relatório para nomear o arquivo

    Returns:
        Caminho absoluto do PDF gerado
    """
    try:
        from weasyprint import HTML, CSS

        # Prepara diretório de saída
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo
        nome_limpo = paciente_data.get("nome", "paciente").replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"relatorio_semestral_{nome_limpo}_{timestamp}.pdf"
        pdf_path = reports_dir / pdf_filename

        # Renderiza template HTML
        env = _get_template_env()
        template = env.get_template("relatorio_semestral.html")

        html_content = template.render(
            paciente=paciente_data,
            profissional=profissional_data,
            evolucoes=evolucoes,
            sintese_global=sintese_global,
            pareceres=pareceres or {},
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            data_geracao=datetime.now().strftime("%d/%m/%Y às %H:%M"),
            clinic_name=settings.clinic_name,
            num_sessoes=len(evolucoes)
        )

        # Converte HTML para PDF
        logger.info(f"Gerando PDF para {paciente_data.get('nome')}...")
        HTML(string=html_content).write_pdf(str(pdf_path))

        logger.info(f"PDF gerado: {pdf_path}")
        return str(pdf_path)

    except ImportError:
        logger.error("WeasyPrint não instalado. Use: pip install weasyprint")
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        raise


def pdf_para_bytes(pdf_path: str) -> bytes:
    """Lê um PDF gerado e retorna como bytes (para streaming HTTP)."""
    with open(pdf_path, "rb") as f:
        return f.read()
