"""
TEO — Router: Relatórios Semestrais
Módulo 3: geração de síntese via LLM e PDF via WeasyPrint.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
import os

from app.database import get_db
from app.models.report import Report
from app.models.evolution import Evolution
from app.models.patient import Patient
from app.models.professional import Professional, ProfessionalRole
from app.schemas.schemas import ReportCreate, ReportUpdate, ReportResponse, ReportGenerateRequest
from app.services.auth_service import get_current_user, require_role
from app.services import llm_service, pdf_service

router = APIRouter(prefix="/reports", tags=["Relatórios Semestrais"])


@router.get("/patient/{patient_id}", response_model=List[ReportResponse])
def list_reports(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(get_current_user)
):
    """Lista histórico de relatórios de um paciente."""
    return db.query(Report).filter(
        Report.paciente_id == patient_id
    ).order_by(Report.created_at.desc()).all()


@router.post("/generate/{patient_id}", response_model=ReportResponse, status_code=201)
def generate_report(
    patient_id: UUID,
    payload: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN
    ))
):
    """
    Módulo 3: Inicia geração do relatório semestral.
    1. Busca as evoluções do período
    2. Chama LLM para síntese global (background)
    3. Gera o PDF (background)
    """
    import json
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    # Busca evoluções do período (max 48)
    evolucoes = db.query(Evolution).filter(
        Evolution.paciente_id == patient_id,
        Evolution.data_sessao >= payload.periodo_inicio,
        Evolution.data_sessao <= payload.periodo_fim
    ).order_by(Evolution.data_sessao.asc()).limit(48).all()

    if not evolucoes:
        raise HTTPException(status_code=400, detail="Nenhuma evolução encontrada no período informado")

    # Cria registro do relatório
    report = Report(
        paciente_id=patient_id,
        periodo_inicio=payload.periodo_inicio,
        periodo_fim=payload.periodo_fim,
        num_evolucoes_analisadas=str(len(evolucoes)),
        pareceres_json=json.dumps(payload.pareceres) if payload.pareceres else None
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Dispara geração em background
    background_tasks.add_task(
        _gerar_relatorio_completo,
        report_id=report.id,
        patient_id=patient_id,
        evolucoes_ids=[e.id for e in evolucoes],
        assinado_por_id=current_user.id,
        periodo_inicio=payload.periodo_inicio.strftime("%d/%m/%Y"),
        periodo_fim=payload.periodo_fim.strftime("%d/%m/%Y"),
    )

    return report


def _gerar_relatorio_completo(
    report_id: UUID,
    patient_id: UUID,
    evolucoes_ids: list,
    assinado_por_id: UUID,
    periodo_inicio: str,
    periodo_fim: str
):
    """Background task: gera síntese LLM + PDF."""
    from app.database import SessionLocal
    from loguru import logger

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        profissional = db.query(Professional).filter(Professional.id == assinado_por_id).first()
        report = db.query(Report).filter(Report.id == report_id).first()
        evolucoes = db.query(Evolution).filter(Evolution.id.in_(evolucoes_ids)).all()

        # Prepara resumo das evoluções para o LLM
        evolucoes_resumo = [
            {
                "data": e.data_sessao.strftime("%d/%m/%Y"),
                "tipo": e.tipo_sessao or "Sessão",
                "resumo": e.notas_tecnicas[:200]
            }
            for e in evolucoes
        ]

        # Gera síntese via LLM
        sintese = llm_service.sintetizar_relatorio(
            nome_paciente=patient.nome,
            idade=patient.idade,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            evolucoes_resumo=evolucoes_resumo,
        )

        # Prepara dados para o template PDF
        patient_data = {
            "nome": patient.nome,
            "data_nascimento": patient.data_nascimento.strftime("%d/%m/%Y"),
            "idade": patient.idade,
            "diagnostico": patient.diagnostico_principal,
            "responsavel": patient.nome_responsavel,
        }
        profissional_data = {
            "nome": profissional.nome if profissional else "Neuropediatra",
            "registro": profissional.registro_conselho or "",
            "especialidade": profissional.especialidade.value if profissional and profissional.especialidade else "",
        }
        evolucoes_para_pdf = [
            {
                "data": e.data_sessao.strftime("%d/%m/%Y"),
                "tipo": e.tipo_sessao or "",
                "notas": e.notas_tecnicas,
                "mensagem_pais": e.mensagem_pais or "",
            }
            for e in evolucoes
        ]

        import json
        pareceres_dict = json.loads(report.pareceres_json) if report.pareceres_json else None

        # Gera PDF
        pdf_path = pdf_service.gerar_relatorio_semestral(
            paciente_data=patient_data,
            profissional_data=profissional_data,
            evolucoes=evolucoes_para_pdf,
            sintese_global=sintese,
            pareceres=pareceres_dict,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            report_id=str(report_id)
        )

        # Atualiza relatório no banco
        report.sintese_global = sintese
        report.pdf_path = pdf_path
        report.pdf_gerado_em = datetime.utcnow()
        report.assinado_por = assinado_por_id
        db.commit()

        logger.info(f"✅ Relatório {report_id} gerado com sucesso: {pdf_path}")

    except Exception as e:
        from loguru import logger
        logger.error(f"❌ Erro ao gerar relatório {report_id}: {e}")
    finally:
        db.close()


@router.get("/{report_id}/download")
def download_report_pdf(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(
        ProfessionalRole.NEUROPEDIATRA, ProfessionalRole.ADMIN, ProfessionalRole.RECEPCAO
    ))
):
    """Download do PDF do relatório semestral. Gera/regenera o PDF se necessário."""
    from loguru import logger
    import json

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    patient = db.query(Patient).filter(Patient.id == report.paciente_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente associado não encontrado")

    # Se o arquivo não existir fisicamente, gera/regenera
    if not report.pdf_path or not os.path.exists(report.pdf_path):
        logger.info(f"PDF não encontrado para relatório {report_id}. Gerando agora...")
        try:
            from app.models.professional import Professional
            profissional = db.query(Professional).filter(Professional.id == report.assinado_por).first()

            patient_data = {
                "nome": patient.nome,
                "data_nascimento": patient.data_nascimento.strftime("%d/%m/%Y"),
                "idade": patient.idade,
                "diagnostico": patient.diagnostico_principal,
                "responsavel": patient.nome_responsavel,
            }

            profissional_data = {
                "nome": profissional.nome if profissional else "Neuropediatra",
                "registro": profissional.registro_conselho or "",
                "especialidade": profissional.especialidade.value if profissional and profissional.especialidade else "",
            }

            pareceres_dict = json.loads(report.pareceres_json) if report.pareceres_json else None

            pdf_path = pdf_service.gerar_relatorio_semestral(
                paciente_data=patient_data,
                profissional_data=profissional_data,
                evolucoes=[],
                sintese_global=report.sintese_global or "Síntese global não disponível.",
                pareceres=pareceres_dict,
                periodo_inicio=report.periodo_inicio.strftime("%d/%m/%Y"),
                periodo_fim=report.periodo_fim.strftime("%d/%m/%Y"),
                report_id=str(report.id)
            )
            report.pdf_path = pdf_path
            db.commit()
            logger.info(f"PDF regenerado com sucesso: {pdf_path}")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF para relatório {report_id}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Não foi possível gerar o PDF: {str(e)}"
            )

    filename = f"relatorio_{patient.nome.replace(' ', '_').lower()}_{report.periodo_fim}.pdf"

    return FileResponse(
        path=report.pdf_path,
        filename=filename,
        media_type="application/pdf"
    )
