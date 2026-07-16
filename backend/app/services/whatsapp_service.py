"""
TEO — WhatsApp Service (Twilio)
Gerencia envio e recebimento de mensagens WhatsApp bidirecional.
"""
from datetime import datetime
from typing import Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


def _get_twilio_client():
    """Retorna cliente Twilio se as credenciais estiverem configuradas."""
    if not settings.twilio_account_sid or settings.twilio_account_sid.startswith("AC"):
        if len(settings.twilio_account_sid) < 20:
            logger.warning("Twilio não configurado — simulando envio em modo DEBUG")
            return None
    try:
        from twilio.rest import Client
        return Client(settings.twilio_account_sid, settings.twilio_auth_token)
    except ImportError:
        logger.error("twilio não instalado. Use: pip install twilio")
        return None


def enviar_mensagem(
    para_numero: str,
    mensagem: str
) -> Optional[str]:
    """
    Envia mensagem WhatsApp via Twilio.

    Args:
        para_numero: Número no formato internacional (ex: +5511999999999)
        mensagem: Texto da mensagem

    Returns:
        SID da mensagem Twilio ou None em modo debug
    """
    # Garante formato whatsapp:+XXXXXXXXXXX
    if not para_numero.startswith("whatsapp:"):
        to_whatsapp = f"whatsapp:{para_numero}"
    else:
        to_whatsapp = para_numero

    client = _get_twilio_client()

    if client is None:
        # Modo simulação (sem Twilio configurado)
        logger.info(f"[SIMULAÇÃO] Mensagem para {para_numero}:\n{mensagem}")
        return f"SIMULATED_SID_{datetime.utcnow().timestamp()}"

    try:
        message = client.messages.create(
            body=mensagem,
            from_=settings.twilio_whatsapp_from,
            to=to_whatsapp
        )
        logger.info(f"Mensagem enviada para {para_numero} | SID: {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp para {para_numero}: {e}")
        raise


def processar_webhook(form_data: dict) -> dict:
    """
    Processa incoming message do webhook Twilio.

    Args:
        form_data: Dados do webhook (x-www-form-urlencoded)

    Returns:
        Dict com: {
            "de": str (número do remetente),
            "mensagem": str (texto recebido),
            "media_url": str|None (URL de mídia se houver)
        }
    """
    return {
        "de": form_data.get("From", "").replace("whatsapp:", ""),
        "mensagem": form_data.get("Body", "").strip(),
        "media_url": form_data.get("MediaUrl0", None),
        "num_media": int(form_data.get("NumMedia", 0)),
        "timestamp": datetime.utcnow().isoformat(),
    }


def enviar_opcoes_agendamento(
    para_numero: str,
    nome_responsavel: str,
    nome_paciente: str,
    opcao_1_fmt: str,
    opcao_2_fmt: str,
    nome_neuropediatra: str,
    dias_restantes: int
) -> Optional[str]:
    """
    Envia mensagem estruturada com opções de agendamento para o responsável.
    Usado pelo CRON job da regra dos 5 meses.
    """
    mensagem = (
        f"Olá, {nome_responsavel}! 😊\n\n"
        f"Sou o TEO, assistente da Clínica. O laudo de *{nome_paciente}* "
        f"vencerá em *{dias_restantes} dias* e precisamos agendar a consulta de renovação "
        f"com a {nome_neuropediatra}. 🩺\n\n"
        f"Tenho estas opções disponíveis:\n\n"
        f"📅 *Opção 1:* {opcao_1_fmt}\n"
        f"📅 *Opção 2:* {opcao_2_fmt}\n\n"
        f"Responda *1* ou *2* para confirmar, ou escreva *outro horário* se precisar de outra data. "
        f"Estamos aqui para ajudar! 💙"
    )
    return enviar_mensagem(para_numero, mensagem)


def enviar_confirmacao_agendamento(
    para_numero: str,
    nome_responsavel: str,
    nome_paciente: str,
    data_confirmada_fmt: str,
    nome_neuropediatra: str
) -> Optional[str]:
    """Confirma o agendamento para os pais após confirmação."""
    mensagem = (
        f"Perfeito, {nome_responsavel}! ✅\n\n"
        f"A consulta de *{nome_paciente}* com a {nome_neuropediatra} está confirmada para:\n\n"
        f"📅 *{data_confirmada_fmt}*\n\n"
        f"Lembrarei você 24h antes. Qualquer dúvida, é só escrever aqui! 💙"
    )
    return enviar_mensagem(para_numero, mensagem)


def enviar_resultado_evolucao(
    para_numero: str,
    mensagem_traduzida: str
) -> Optional[str]:
    """
    Módulo 1: Envia a mensagem de evolução traduzida pelo TEO para os pais.
    """
    return enviar_mensagem(para_numero, mensagem_traduzida)


def enviar_laudo_pronto(
    para_numero: str,
    nome_responsavel: str,
    nome_paciente: str,
    periodo_inicio: str,
    periodo_fim: str,
    nome_neuropediatra: str
) -> Optional[str]:
    """
    Notifica os responsáveis que o laudo semestral foi gerado e está disponível.
    """
    mensagem = (
        f"Olá, {nome_responsavel}! 😊\n\n"
        f"O laudo semestral de *{nome_paciente}* referente ao período "
        f"{periodo_inicio} a {periodo_fim} foi finalizado pela {nome_neuropediatra}. 📋\n\n"
        f"O documento está disponível no sistema para consulta. "
        f"Se preferir, podemos enviar o PDF por aqui — é só responder *sim*.\n\n"
        f"Continuamos acompanhando de perto o desenvolvimento do {nome_paciente}! 💙"
    )
    return enviar_mensagem(para_numero, mensagem)


def enviar_indicacoes_terapeuticas(
    para_numero: str,
    nome_responsavel: str,
    nome_paciente: str,
    terapeutas_nomes: list[str],
    diagnostico: str,
    recomendacoes: str,
    nome_neuropediatra: str
) -> Optional[str]:
    """
    Notifica os responsáveis sobre as indicações terapêuticas do neuropediatra.
    """
    terapeutas_lista = "\n".join([f"• {nome}" for nome in terapeutas_nomes]) if terapeutas_nomes else "—"
    
    mensagem = (
        f"Olá, {nome_responsavel}! 😊\n\n"
        f"A {nome_neuropediatra} finalizou a consulta de *{nome_paciente}* e definiu o plano terapêutico:\n\n"
        f"🩺 *Diagnóstico:* {diagnostico or 'Não informado'}\n\n"
        f"👥 *Equipe terapêutica recomendada:*\n{terapeutas_lista}\n\n"
        f"💡 *Recomendações para o próximo período:*\n{recomendacoes or '—'}\n\n"
        f"Os horários iniciais serão definidos em breve e a Recepção entrará em contato para agendamento. "
        f"Qualquer dúvida, é só escrever aqui! 💙"
    )
    return enviar_mensagem(para_numero, mensagem)
