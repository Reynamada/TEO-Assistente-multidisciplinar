# Base de Conhecimento
---
## ☁️ Deploy Gratuito (Streamlit Cloud + Render + Neon)

**Passo a passo fácil e gratuito**
1. **GitHub** – suba o código para um repositório.
2. **Neon.tech** – crie a base de dados PostgreSQL e copie a *Connection String*.
3. **Render** – crie o serviço backend usando o `render.yaml`. Na seção **Environment** defina as variáveis:
   - `DATABASE_URL` – URL do Neon.
   - `GROQ_API_KEY` – sua chave Groq.
   - `SECRET_KEY` – senha segura (ex.: `openssl rand -hex 32`).
   - (Opcional) `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`.
   Copie a URL pública gerada (ex.: `https://teo-backend-xxx.onrender.com`).
4. **Streamlit Cloud** – crie uma app apontando para `frontend/app.py`. Em **Advanced Settings → Secrets** adicione:
```toml
BACKEND_URL = "https://teo-backend-xxx.onrender.com"
```
(Substitua pelo link obtido no passo 3).
5. Clique em **Deploy**. Em poucos minutos o app estará acessível via URL do Streamlit e consumirá o backend hospedado no Render.

Para detalhes completos veja o [Walkout](../walkthrough.md).
---

## Dados Utilizados

| Fonte | Formato | Para que serve no TEO |
|---------|---------|---------------------|
| Banco de Dados (Tabela `pacientes`) | PostgreSQL / UUID | Armazena dados clínicos, contato do responsável e data do último laudo para a regra dos 5 meses. |
| Banco de Dados (Tabela `profissionais`) | PostgreSQL | Armazena terapeutas e neuropediatras com seus roles e hashed passwords para controle de acesso. |
| Banco de Dados (Tabela `evolucoes`) | PostgreSQL | Notas técnicas de cada sessão + mensagem traduzida pelo LLM + controle de envio WhatsApp. |
| Banco de Dados (Tabela `citas_neurologia`) | PostgreSQL | Agendamentos disparados pelo CRON com FSM de status (pendente → confirmado → realizado). |
| Banco de Dados (Tabela `relatorios_semestrais`) | PostgreSQL | Síntese gerada pela IA + caminho do PDF gerado pelo WeasyPrint. |
| System Prompt TEO | Python (constante) | Contexto permanente injetado em todas as chamadas ao LLM — define a persona, regras e formato de output. |

> [!TIP]
> O `TEO_SYSTEM_PROMPT` em `backend/app/services/llm_service.py` é a única fonte de conhecimento **estática e local**. Todo o restante (pacientes, evoluções, agendamentos) vive no banco PostgreSQL e é consultado dinamicamente a cada requisição.

---

## Adaptações nos Dados

```
- Todos os dados clínicos vivem em um Banco de Dados Relacional (PostgreSQL) via SQLAlchemy, 
  garantindo integridade referencial entre Pacientes, Evoluções, Profissionais e Relatórios.
- O System Prompt do TEO foi mantido como constante Python por ser altamente especializado
  e estável — qualquer mudança de persona ou regra é uma decisão clínica deliberada.
- O histórico de evoluções é consultado dinamicamente para gerar a síntese semestral,
  limitado às últimas 48 sessões para otimizar tokens e relevância clínica.
- A interpretação de respostas dos pais (NLU) usa um prompt de classificação fechado em
  5 intenções: aceitar_op1, aceitar_op2, reagendar, cancelar, desconhecido.
```

---

## Estratégia de Integração

### Como os dados são carregados?

## 1. Injeção dinâmica no prompt (via API)
As notas clínicas do terapeuta são enviadas via `POST /api/v1/evolutions/translate-preview` e
injetadas no prompt do LLM em tempo real. O contexto do paciente (nome, tipo de sessão) enriquece
o prompt para personalizar a mensagem.

## 2. Carregamento via SQLAlchemy (ORM)
O backend usa SQLAlchemy para consultar dinamicamente o banco PostgreSQL. Veja o padrão de 
carregamento das evoluções para a síntese semestral:

```python
from app.database import SessionLocal
from app.models.evolution import Evolution

def carregar_evolucoes_periodo(paciente_id: str, inicio: date, fim: date, limite: int = 48):
    db = SessionLocal()
    try:
        evolucoes = db.query(Evolution).filter(
            Evolution.paciente_id == paciente_id,
            Evolution.data_sessao >= inicio,
            Evolution.data_sessao <= fim
        ).order_by(Evolution.data_sessao.asc()).limit(limite).all()

        return [
            {
                "data": e.data_sessao.strftime("%d/%m/%Y"),
                "tipo": e.tipo_sessao or "Sessão",
                "resumo": e.notas_tecnicas[:200]
            }
            for e in evolucoes
        ]
    finally:
        db.close()
```

### 3. CRON Job — Carregamento Automático (Regra dos 5 Meses)
O `APScheduler` executa `verificar_laudos_vencendo()` diariamente às 08:00 (horário de Brasília).
A função consulta automaticamente todos os pacientes com laudos vencidos e dispara o fluxo:

```python
# Lógica central da regra dos 5 meses
pacientes = db.query(Patient).filter(
    Patient.ativo == True,
    Patient.data_ultimo_laudo.isnot(None),
    Patient.alerta_laudo_enviado == False,
).all()

for paciente in pacientes:
    dias_desde_laudo = (hoje - paciente.data_ultimo_laudo).days
    if dias_desde_laudo >= 150:  # 5 meses
        # → gera opções de horário
        # → cria registro em citas_neurologia
        # → envia WhatsApp via Twilio
        # → marca alerta_laudo_enviado = True
```

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

Os dados clínicos NÃO estão fixos no system prompt.
Eles são carregados via código e injetados dinamicamente conforme o tipo de operação.
O TEO_SYSTEM_PROMPT define a PERSONA e as REGRAS — os dados do paciente enriquecem o USER_MESSAGE.

Exemplo de como os dados são montados para tradução de evolução:

```python
user_message = f"""Por favor, traduza as seguintes notas clínicas em uma mensagem 
de WhatsApp para os pais de {nome_paciente}.

Tipo de sessão: {tipo_sessao}

NOTAS TÉCNICAS DA SESSÃO:
{notas_tecnicas}

Use o formato 🧩 O que fizemos, 🌟 Grande conquista, 🏠 Dica para casa.
Comece com uma saudação calorosa incluindo o nome da criança."""

messages = [
    {"role": "system", "content": TEO_SYSTEM_PROMPT},  # Persona + Regras
    {"role": "user", "content": user_message}           # Dados reais
]
```

## Exemplo de Contexto Montado — Síntese Semestral

> Como os dados são formatados para o relatório semestral:

```
PACIENTE: Mateo García (6 anos)
PERÍODO: 01/01/2026 a 30/06/2026
TOTAL DE SESSÕES ANALISADAS: 36

RESUMO DAS SESSÕES:
- 05/01/2026: [Terapia Ocupacional] Sessão focada em integração sensorial tátil...
- 12/01/2026: [Fonoaudiologia] Trabalho de imitação de sons e vocalizações...
- 19/01/2026: [Psicologia] Atividades de regulação emocional com cartões visuais...
...

PARECERES POR ÁREA:
• Terapia Ocupacional: Evoluiu significativamente na tolerância sensorial...
• Fonoaudiologia: Ampliou vocabulário funcional de 12 para 34 palavras...
• Psicologia: Demonstra maior regulação em situações de frustração...

→ LLM gera síntese narrativa de 3-4 parágrafos para o relatório médico
→ WeasyPrint renderiza o PDF profissional com capa, gráficos e assinatura
```

## Exemplo de Contexto Montado — Interpretação de Resposta dos Pais (NLU)

```
OPÇÃO 1 OFERECIDA: Terça-feira, 14/07/2026 às 09:00
OPÇÃO 2 OFERECIDA: Sexta-feira, 17/07/2026 às 14:30

RESPOSTA DOS PAIS: "pode ser na sexta mesmo, a gente tá livres de tarde"

→ NLU classifica: {"intencao": "aceitar_op2", "confianca": "alta"}
→ Sistema atualiza: cita.status = CONFIRMADO_OP2
→ Envia confirmação: "Perfeito! Consulta confirmada para sexta, 17/07 às 14:30 ✅"
```
