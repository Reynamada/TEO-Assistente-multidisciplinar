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
    # Placeholder PDF generation (no weasyprint)
    try:
        # Prepare output directory
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy PDF file path
        nome_limpo = paciente_data.get("nome", "paciente").replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"relatorio_semestral_{nome_limpo}_{timestamp}.pdf"
        pdf_path = reports_dir / pdf_filename

        # Write minimal PDF header to create a valid (though empty) PDF file
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%âãÏÓ\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")

        logger.info(f"Generated placeholder PDF for {paciente_data.get('nome')} at {pdf_path}")
        return str(pdf_path)
    except Exception as e:
        logger.error(f"Erro ao gerar PDF placeholder: {e}")
        raise


def pdf_para_bytes(pdf_path: str) -> bytes:
    """Lê um PDF gerado e retorna como bytes (para streaming HTTP)."""
    with open(pdf_path, "rb") as f:
        return f.read()
