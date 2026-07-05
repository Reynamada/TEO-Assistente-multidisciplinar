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
        # Prepare output directory
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Create a unique PDF file path
        nome_limpo = paciente_data.get("nome", "paciente").replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"relatorio_semestral_{nome_limpo}_{timestamp}.pdf"
        pdf_path = reports_dir / pdf_filename

        # Render HTML template via Jinja2
        env = _get_template_env()
        template = env.get_template("relatorio_semestral.html")

        # Prepare context data
        data_geracao = datetime.now().strftime("%d/%m/%Y")
        num_sessoes = len(evolucoes)

        context = {
            "clinic_name": settings.clinic_name,
            "paciente": paciente_data,
            "profissional": profissional_data,
            "evolucoes": evolucoes,
            "sintese_global": sintese_global,
            "pareceres": pareceres,
            "periodo_inicio": periodo_inicio,
            "periodo_fim": periodo_fim,
            "data_geracao": data_geracao,
            "num_sessoes": num_sessoes,
            "report_id": report_id,
        }

        html_content = template.render(**context)

        # Try generating using WeasyPrint
        try:
            logger.info("Attempting PDF generation using WeasyPrint...")
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(target=str(pdf_path))
            logger.info(f"Successfully generated PDF using WeasyPrint at {pdf_path}")
            return str(pdf_path)
        except Exception as wp_error:
            logger.warning(
                f"WeasyPrint generation failed or not configured (GTK error?): {wp_error}. "
                "Falling back to Playwright..."
            )
            
            # Fallback to Playwright
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    # Launch chromium in headless mode
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.set_content(html_content)
                    page.emulate_media(media="print")
                    # Wait for network idle/fonts to load (10s timeout max)
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass  # Continue even if timeout; fonts may be unavailable in server
                    page.pdf(
                        path=str(pdf_path),
                        format="A4",
                        print_background=True,
                        margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
                    )
                    browser.close()
                logger.info(f"Successfully generated PDF using Playwright fallback at {pdf_path}")
                return str(pdf_path)
            except Exception as pw_error:
                logger.error(f"Playwright PDF generation failed: {pw_error}")
                # Re-raise the original WeasyPrint error or a custom error combining both
                raise RuntimeError(
                    f"Failed to generate PDF. WeasyPrint error: {wp_error}. Playwright error: {pw_error}"
                )
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        raise


def pdf_para_bytes(pdf_path: str) -> bytes:
    """Lê um PDF gerado e retorna como bytes (para streaming HTTP)."""
    with open(pdf_path, "rb") as f:
        return f.read()

