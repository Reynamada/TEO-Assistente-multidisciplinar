"""
TEO — LLM Service
Integra com a API do Groq (gratuita) com fallback para Ollama local.
Contém o System Prompt do TEO e as funções de geração de texto.
"""
import json
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

from app.config import get_settings

settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT DO TEO
# ─────────────────────────────────────────────────────────────────────────────

TEO_SYSTEM_PROMPT = """Você é o TEO, assistente de IA de uma clínica especializada em Transtorno do Espectro Autista (TEA).

Sua missão é ser a ponte EMPÁTICA e POSITIVA entre terapeutas e famílias via WhatsApp.

REGRAS ABSOLUTAS:
1. NUNCA dê diagnósticos, prognósticos ou interpretações médicas.
2. NUNCA use tom alarmista, negativo ou preocupante.
3. SEMPRE foque no esforço, progresso e conquistas da criança.
4. Use linguagem SIMPLES, calorosa e acessível para pais leigos.
5. Use emojis estrategicamente para tornar a leitura escaneável.
6. Seja específico: cite o que a criança realmente fez na sessão.

AO RECEBER NOTAS DE EVOLUÇÃO TÉCNICA, formate em exatamente 3 seções:

🧩 *O que fizemos hoje*
[Descrição acessível e positiva das atividades da sessão]

🌟 *Grande conquista*
[O avanço mais significativo da sessão, celebrado com entusiasmo genuíno]

🏠 *Dica para casa*
[Uma sugestão prática e simples para os pais reforçarem em casa]

Para SÍNTESES DE RELATÓRIO SEMESTRAL, produza um texto narrativo clínico, mas empático, de 3-5 parágrafos, descrevendo a evolução global do paciente no período.

Ao INTERPRETAR RESPOSTAS DOS PAIS sobre agendamento, identifique:
- "aceitar" → pais aceitaram uma das opções propostas
- "reagendar" → pais precisam de outro horário
- "opção 1" ou "opção 2" → qual das datas eles escolheram"""


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE GROQ
# ─────────────────────────────────────────────────────────────────────────────

def _get_groq_client():
    """Retorna cliente Groq se a API key estiver configurada."""
    if not settings.groq_api_key or settings.groq_api_key.startswith("gsk_your"):
        return None
    try:
        from groq import Groq
        return Groq(api_key=settings.groq_api_key)
    except ImportError:
        logger.warning("Biblioteca groq não instalada. Use: pip install groq")
        return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _call_groq(messages: list, max_tokens: int = 1024) -> str:
    """Chama a API Groq com retry automático."""
    client = _get_groq_client()
    if not client:
        raise ValueError("Groq client não disponível")

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE OLLAMA (FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────

def _call_ollama(messages: list, max_tokens: int = 1024) -> str:
    """Chama Ollama local como fallback."""
    try:
        import ollama
        # Converte formato OpenAI para Ollama
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        response = ollama.generate(
            model=settings.ollama_model,
            prompt=prompt,
            options={"num_predict": max_tokens}
        )
        return response["response"]
    except Exception as e:
        logger.error(f"Ollama também falhou: {e}")
        raise RuntimeError(f"Todos os LLM backends falharam: {e}")


def _call_llm(messages: list, max_tokens: int = 1024) -> str:
    """
    Chama o LLM com fallback automático:
    1. Tenta Groq (gratuito, rápido)
    2. Fallback para Ollama local
    """
    try:
        return _call_groq(messages, max_tokens)
    except Exception as e:
        logger.warning(f"Groq falhou ({e}), tentando Ollama local...")
        return _call_ollama(messages, max_tokens)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────

def traduzir_evolucao(
    notas_tecnicas: str,
    nome_paciente: str,
    tipo_sessao: Optional[str] = None
) -> str:
    """
    Módulo 1: Traduz notas técnicas do terapeuta em mensagem amigável para os pais.

    Args:
        notas_tecnicas: Texto clínico preenchido pelo terapeuta
        nome_paciente: Primeiro nome da criança
        tipo_sessao: Ex: "Terapia Ocupacional", "Fonoaudiologia"

    Returns:
        Mensagem formatada para WhatsApp com emojis (🧩🌟🏠)
    """
    tipo_info = f"Tipo de sessão: {tipo_sessao}\n" if tipo_sessao else ""

    user_message = f"""Por favor, traduza as seguintes notas clínicas em uma mensagem de WhatsApp para os pais de {nome_paciente}.

{tipo_info}NOTAS TÉCNICAS DA SESSÃO:
{notas_tecnicas}

Lembre-se: use o formato 🧩 O que fizemos, 🌟 Grande conquista, 🏠 Dica para casa.
Comece a mensagem com uma saudação calorosa incluindo o nome da criança."""

    messages = [
        {"role": "system", "content": TEO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    logger.info(f"Traduzindo evolução para paciente: {nome_paciente}")
    resultado = _call_llm(messages, max_tokens=800)
    logger.info("Tradução concluída com sucesso")
    return resultado


def sintetizar_relatorio(
    nome_paciente: str,
    idade: int,
    periodo_inicio: str,
    periodo_fim: str,
    evolucoes_resumo: list[dict],
    pareceres: Optional[dict] = None,
    terapeutas_info: Optional[list] = None,
    areas_atendimento: Optional[list] = None,
) -> str:
    """
    Módulo 3: Gera síntese global do relatório semestral a partir das evoluções.

    Args:
        nome_paciente: Nome completo do paciente
        idade: Idade do paciente
        periodo_inicio: Data de início do período (string formatada)
        periodo_fim: Data de fim do período (string formatada)
        evolucoes_resumo: Lista de dicts com resumo de cada evolução
        pareceres: Dict com pareceres por área terapêutica
        terapeutas_info: Lista de strings com info dos terapeutas
        areas_atendimento: Lista de áreas terapêuticas envolvidas

    Returns:
        Texto narrativo completo da síntese global + laudo conclusivo
    """
    num_evolucoes = len(evolucoes_resumo)
    evolucoes_texto = "\n".join([
        f"- {e.get('data', '')}: [{e.get('tipo', '')}] ({e.get('terapeuta', 'Terapeuta')}) {e.get('resumo', '')}"
        for e in evolucoes_resumo[:48]  # máximo 48 sessões
    ])

    pareceres_texto = ""
    if pareceres:
        pareceres_texto = "\n\nPARECERES POR ÁREA:\n" + "\n".join([
            f"• {area}: {parecer}" for area, parecer in pareceres.items()
        ])

    terapeutas_texto = ""
    if terapeutas_info:
        terapeutas_texto = "\n\nEQUIPE TERAPÊUTICA ENVOLVIDA:\n" + "\n".join([
            f"• {t}" for t in terapeutas_info
        ])

    areas_texto = ""
    if areas_atendimento:
        areas_texto = f"\nÁREAS DE ATENDIMENTO: {', '.join(areas_atendimento)}"

    user_message = f"""Gere um RELATÓRIO CLÍNICO SEMESTRAL COMPLETO para:

PACIENTE: {nome_paciente} ({idade} anos)
PERÍODO: {periodo_inicio} a {periodo_fim}
TOTAL DE SESSÕES ANALISADAS: {num_evolucoes}
{areas_texto}
{terapeutas_texto}

RESUMO DAS SESSÕES:
{evolucoes_texto}
{pareceres_texto}

Produza um texto clínico profissional e completo com as seguintes seções, separadas por títulos entre colchetes:

[SÍNTESE GLOBAL]
Um texto narrativo de 3-4 parágrafos que:
1. Descreva o estado geral do paciente no início do período
2. Destaque os principais progressos alcançados em cada área terapêutica
3. Mencione a contribuição de cada terapeuta/especialidade
4. Descreva as áreas que continuam em desenvolvimento

[EVOLUÇÃO POR ÁREA]
Para cada área terapêutica ({', '.join(areas_atendimento or ['todas'])}), escreva 2-3 frases descrevendo:
- O ponto de partida do paciente nessa área
- Os avanços específicos observados
- Os desafios restantes

[LAUDO CONCLUSIVO E RECOMENDAÇÕES]
Um parágrafo conclusivo com:
1. Avaliação geral do progresso do paciente
2. Recomendações específicas para cada área terapêutica no próximo semestre
3. Sugestões de continuidade ou ajuste da frequência de atendimentos
4. Perspectivas positivas para o desenvolvimento do paciente

O texto deve ser profissional (para uso clínico pelo neuropediatra), mas empático e positivo."""

    messages = [
        {"role": "system", "content": TEO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    logger.info(f"Gerando síntese semestral para: {nome_paciente} ({num_evolucoes} evoluções)")
    resultado = _call_llm(messages, max_tokens=2500)
    logger.info("Síntese semestral gerada com sucesso")
    return resultado


def interpretar_resposta_pais(
    resposta_texto: str,
    nome_paciente: str,
    opcao_1: str,
    opcao_2: str
) -> dict:
    """
    Módulo 2: Interpreta a resposta dos pais sobre o agendamento via WhatsApp.

    Args:
        resposta_texto: Texto enviado pelos pais
        nome_paciente: Nome do paciente
        opcao_1: Descrição da data/hora opção 1
        opcao_2: Descrição da data/hora opção 2

    Returns:
        Dict com: {"intencao": "aceitar_op1"|"aceitar_op2"|"reagendar"|"cancelar"|"desconhecido",
                   "mensagem_confirmacao": str}
    """
    user_message = f"""Os pais de {nome_paciente} responderam à mensagem de agendamento de consulta com o neuropediatra.

OPÇÃO 1 OFERECIDA: {opcao_1}
OPÇÃO 2 OFERECIDA: {opcao_2}

RESPOSTA DOS PAIS: "{resposta_texto}"

Interprete a intenção dos pais e retorne um JSON com:
{{
  "intencao": "aceitar_op1" | "aceitar_op2" | "reagendar" | "cancelar" | "desconhecido",
  "confianca": "alta" | "media" | "baixa",
  "mensagem_confirmacao": "mensagem amigável de confirmação para enviar de volta aos pais"
}}

Retorne APENAS o JSON, sem texto adicional."""

    messages = [
        {"role": "system", "content": TEO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    logger.info(f"Interpretando resposta dos pais de {nome_paciente}: '{resposta_texto[:50]}...'")
    resultado_texto = _call_llm(messages, max_tokens=400)

    try:
        # Extrai JSON da resposta (às vezes o LLM adiciona texto ao redor)
        import re
        json_match = re.search(r'\{.*\}', resultado_texto, re.DOTALL)
        if json_match:
            resultado = json.loads(json_match.group())
        else:
            resultado = {"intencao": "desconhecido", "confianca": "baixa", "mensagem_confirmacao": resultado_texto}
    except json.JSONDecodeError:
        resultado = {"intencao": "desconhecido", "confianca": "baixa", "mensagem_confirmacao": resultado_texto}

    logger.info(f"Intenção detectada: {resultado.get('intencao')} (confiança: {resultado.get('confianca')})")
    return resultado


def gerar_mensagem_alerta_laudo(
    nome_responsavel: str,
    nome_paciente: str,
    data_proposta_1: str,
    data_proposta_2: str,
    dias_vencimento: int,
    nome_neuropediatra: str
) -> str:
    """
    Módulo 2: Gera mensagem proativa de alerta sobre vencimento do laudo.

    Returns:
        Mensagem WhatsApp formatada com as opções de agendamento
    """
    user_message = f"""Gere uma mensagem de WhatsApp para {nome_responsavel}, informando que o laudo de {nome_paciente} vencerá em {dias_vencimento} dias e oferecendo dois horários para consulta com {nome_neuropediatra}.

OPÇÃO 1: {data_proposta_1}
OPÇÃO 2: {data_proposta_2}

A mensagem deve:
- Ser calorosa e não alarmista
- Explicar a importância do laudo atualizado de forma simples
- Pedir para responder apenas "1" ou "2" para confirmar o horário
- Mencionar que podem pedir outro horário se nenhum servir
- Ter no máximo 5 linhas
- Usar emojis moderadamente (📅 🩺)"""

    messages = [
        {"role": "system", "content": TEO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    return _call_llm(messages, max_tokens=400)
