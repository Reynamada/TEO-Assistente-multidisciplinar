# 🛠️ Plataformas, APIs e Bibliotecas do TEO
> Resumo detalhado de cada tecnologia usada, seu papel e por que foi escolhida.

## ☁️ Deploy Gratuito

Para publicar o TEO no **Streamlit Cloud** (plano gratuito):

1️⃣ Crie uma conta no [Streamlit Cloud](https://share.streamlit.io/).
2️⃣ Conecte seu repositório GitHub contendo o projeto.
3️⃣ No arquivo `streamlit.toml` (ou diretamente nas Secrets), adicione as variáveis de ambiente necessárias:
   - `BACKEND_URL` – URL do backend hospedado no Render ou outro serviço.
   - `GROQ_API_KEY` – chave da API Groq.
   - `TWILIO_ACCOUNT_SID` e `TWILIO_AUTH_TOKEN` – para o sandbox (opcional).
4️⃣ Configure o **branch** (`main`) e clique em **Deploy**.
5️⃣ Após o deploy, verifique se a URL do frontend está funcionando e se comunica com o backend.

> **Dica:** O plano gratuito permite até 3 apps simultâneos e até 1 GB de armazenamento – suficiente para o TEO em ambiente de demonstração.

---

## 🔒 Segurança e Ocultação de Chaves/APIs

> [!WARNING]
> **NUNCA exponha credenciais reais ou chaves de API no repositório Git ou na documentação pública.**
>
> Todas as chaves secretas (como `GROQ_API_KEY`, `TWILIO_AUTH_TOKEN`, senhas de banco de dados e chaves SMTP) devem ser tratadas de forma estritamente confidencial e segura.
>
> ### 🛡️ Diretrizes de Proteção:
> 1. **Variáveis de Ambiente (`.env`):** No ambiente local, todas as chaves e segredos devem ser configurados no arquivo `.env`. Este arquivo está adicionado ao `.gitignore` e **nunca** deve ser commitado ou compartilhado no repositório Git.
> 2. **Provedores Cloud (Streamlit Cloud, Render, etc.):** Utilize a área de configurações de **Secrets** ou **Environment Variables** de cada plataforma para injetar as credenciais dinamicamente em produção/homologação.
> 3. **Exemplos e Placeholders:** Ao documentar exemplos ou criar templates de configuração (ex: `.env.example`), use placeholders genéricos e fictícios (ex: `SUA_CHAVE_AQUI`).
> 4. **Tratamento no Código:** O backend (`config.py`) lê os segredos de forma segura via variáveis de ambiente usando `pydantic-settings`.

---

## 🎯 Visão Geral da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│  TERAPEUTA/MÉDICO  →  Streamlit (UI)  →  FastAPI (Backend)       │
│                              ↓                    ↓               │
│                    PostgreSQL (DB)        Groq API (LLM)          │
│                                                   ↓               │
│                              ←── Tradução / Síntese / NLU ───    │
│                                                   ↓               │
│                    Twilio WhatsApp Business API                   │
│                    WeasyPrint + Jinja2 (PDF)                      │
│                    APScheduler (CRON — Regra 5 meses)            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ CAMADA DE INTERFACE

### 1. Streamlit
| | |
|---|---|
| **Site** | [streamlit.io](https://streamlit.io) |
| **Tipo** | Framework web Python |
| **Custo** | Gratuito (open source) |
| **Deploy** | Docker (auto-hospedado) + NGINX + Let's Encrypt |

**Por que foi escolhido:**
- Permite construir um dashboard clínico completo **100% em Python**, sem HTML/CSS/JavaScript
- `st.session_state` mantém o estado de autenticação JWT e dados entre interações
- Componentes nativos (tabs, expanders, progress bars) encaixam perfeitamente no fluxo clínico
- Plotly nativo para os gráficos de progresso do paciente (barras, pizza, gauge, timeline)
- Permite o deploy em servidor privado da clínica (LGPD compliance)

**Usado em:** `frontend/app.py`, `frontend/pages/`, `frontend/components/`

---

## 🧠 CAMADA DE INTELIGÊNCIA ARTIFICIAL

### 2. Groq API (Primária)
| | |
|---|---|
| **Site** | [console.groq.com](https://console.groq.com) |
| **Tipo** | Inferência LLM ultra-rápida (GroqChip) |
| **Autenticação** | Bearer Token (`GROQ_API_KEY`) |
| **Protocolo** | Compatível com API OpenAI (`/openai/v1/chat/completions`) |
| **Custo** | **Gratuito** (plano Developer sem custo) |

**Por que foi escolhido:**
- **Velocidade excepcional:** ~2s de latência para chamadas ao Llama 3.1 70B — viável para uso em tempo real no Dashboard
- **Totalmente gratuito** no plano Developer (limite de tokens por minuto, adequado para clínicas)
- Compatível com a interface OpenAI — mesma estrutura de mensagens que outros modelos
- Llama 3.1 70B tem excelente capacidade de seguir System Prompts complexos e manter o tom empático

**Modelo em uso:**
| Modelo | Papel |
|---|---|
| `llama-3.1-70b-versatile` | Tradução de evoluções, síntese semestral e NLU de agendamento |

**Usado em:** `backend/app/services/llm_service.py`

### 3. Ollama (Fallback Local)
| | |
|---|---|
| **Site** | [ollama.ai](https://ollama.ai) |
| **Tipo** | Servidor LLM local open source |
| **Custo** | Gratuito (roda na máquina do servidor) |
| **Protocolo** | REST API local (`http://localhost:11434`) |

**Por que foi escolhido:**
- Fallback automático quando o Groq está indisponível ou sem quota
- Permite desenvolvimento e testes **offline** sem custos
- Garante **continuidade do serviço** mesmo em falhas externas
- `llama3:8b` é suficiente para tradução de evoluções com qualidade aceitável

**Estratégia de Fallback:**
```
Groq (primário) → 3 retries com backoff exponencial (tenacity)
     ↓ (se falhar)
Ollama local (llama3:8b)
     ↓ (se falhar também)
HTTP 503 com mensagem descritiva ao usuário
```

**Usado em:** `backend/app/services/llm_service.py` → `_call_ollama_fallback()`

---

## 🗄️ CAMADA DE PERSISTÊNCIA

### 4. PostgreSQL 16
| | |
|---|---|
| **Tipo** | Banco de dados relacional |
| **Custo** | Gratuito (open source, auto-hospedado via Docker) |
| **Protocolo** | `postgresql://` via psycopg2 |
| **Imagem Docker** | `postgres:16-alpine` |

**Por que foi escolhido:**
- Armazena todas as entidades clínicas com integridade referencial (FK entre Pacientes, Evoluções, Relatórios)
- UUIDs como primary keys para segurança e escalabilidade
- ACID compliant — seguro para dados médicos sensíveis
- Auto-hospedado via Docker — **nenhum dado clínico vai para cloud de terceiros** (LGPD)

**Tabelas principais:**
| Tabela | Conteúdo |
|---|---|
| `pacientes` | Dados clínicos, contato do responsável, data do último laudo |
| `profissionais` | Equipe da clínica com roles e hashed passwords |
| `evolucoes` | Notas técnicas + mensagem traduzida pelo LLM + status WhatsApp |
| `citas_neurologia` | Agendamentos com FSM de status (pendente → confirmado → realizado) |
| `relatorios_semestrais` | Síntese da IA + caminho do PDF gerado |

**Usado em:** `backend/app/models/`, `backend/app/database.py`

### 5. SQLAlchemy 2.0
| | |
|---|---|
| **Tipo** | ORM (Object-Relational Mapper) Python |
| **Custo** | Gratuito (open source) |

**Por que foi escolhido:**
- **Abstrai o banco de dados**: código Python trabalha com objetos, não SQL bruto — mais seguro e legível
- `create_all()` com `checkfirst=True` — migrations idempotentes sem quebrar dados existentes
- `AsyncSession` para compatibilidade com FastAPI assíncrono
- Permite trocar o banco facilmente (ex: SQLite para testes, PostgreSQL para produção)

**Usado em:** `backend/app/database.py`, todos os routers e services

---

## 📡 CAMADA DE COMUNICAÇÃO

### 6. Twilio — WhatsApp Business API
| | |
|---|---|
| **Site** | [twilio.com](https://console.twilio.com) |
| **Tipo** | API de mensagens WhatsApp |
| **Autenticação** | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` |
| **Custo** | Pago (Sandbox gratuito para desenvolvimento) |
| **Sandbox** | `whatsapp:+14155238886` |

**Por que foi escolhido:**
- API oficial e aprovada pela Meta para envio programático de WhatsApp
- SDK Python maduro (`twilio` library) com abstrações simples
- Sandbox de desenvolvimento gratuito — permite testar sem aprovação Meta
- Suporte a webhook para receber respostas dos pais em tempo real

**Modo Simulação (desenvolvimento):**
```python
# Se TWILIO_ACCOUNT_SID não está configurado, o sistema opera em modo debug:
# As mensagens são impressas no log do container em vez de enviadas.
# Não há erro — o fluxo continua normalmente para testes.
```

**Usado em:** `backend/app/services/whatsapp_service.py`, `backend/app/routers/whatsapp.py`

---

## 📄 CAMADA DE EXPORTAÇÃO

### 7. WeasyPrint + Playwright + Jinja2
| | |
|---|---|
| **Tipo** | Renderização HTML→PDF + Template Engine |
| **Custo** | Gratuito (open source) |
| **Dependências OS** | Pango, Cairo, GTK (WeasyPrint) / Chromium Headless (Playwright) |

**Por que foram escolhidos:**
- **Jinja2**: Permite mapear variáveis dinâmicas de forma ágil no template HTML (dados do paciente, pareceres por área, métricas e sessões).
- **WeasyPrint**: Utilizado primariamente em ambientes Linux/Produção para gerar os PDFs seguindo especificações CSS de mídia impressa.
- **Playwright (Chromium)**: Utilizado como motor principal em ambiente Windows (onde o WeasyPrint possui dependências complexas de biblioteca Gtk/Pango) e como mecanismo robusto de fallback em produção caso o WeasyPrint encontre algum problema de renderização.
- **Gerado em memória**: O PDF é disponibilizado diretamente para download ou gravação, otimizando os recursos do servidor.

**Template:** `templates/relatorio_semestral.html`

**Seções do PDF gerado:**
1. Capa (logo, dados do paciente, período, confidencialidade)
2. Métricas do período (4 cards: sessões, especialidades, duração, idade)
3. Síntese Global (narrativa gerada pelo LLM com badge de IA)
4. Pareceres por Área (grid de cards por especialidade)
5. Registro de Sessões (tabela completa com data, tipo e notas)
6. Assinatura do Neuropediatra (campo em branco para assinar)

**Usado em:** `backend/app/services/pdf_service.py` → `gerar_relatorio_semestral()`

---

## ⏱️ CAMADA DE AUTOMAÇÃO

### 8. APScheduler 3.10
| | |
|---|---|
| **Tipo** | Scheduler de tarefas Python em processo |
| **Custo** | Gratuito (open source) |

**Por que foi escolhido:**
- Roda **dentro do processo FastAPI** — sem precisar de um serviço externo (Celery, Redis)
- `CronTrigger` com timezone permite disparar exatamente às 08:00 horário de Brasília
- Persiste o estado das tasks em memória (suficiente para clínica com volume moderado)
- `lifespan` do FastAPI inicia e para o scheduler automaticamente com a aplicação

**Jobs configurados:**
| Job | Frequência | Função |
|---|---|---|
| `verificar_laudos_vencendo` | Diário 08:00 BRT | Regra dos 5 meses — alerta automático WhatsApp |
| `resetar_alertas_mensalmente` | 1º dia do mês 07:00 | Reseta `alerta_laudo_enviado` para permitir reenvio mensal |

**Usado em:** `backend/app/jobs/cron_jobs.py`, `backend/app/main.py`

---

## 🔐 CAMADA DE SEGURANÇA

### 9. python-jose + bcrypt (JWT)
| | |
|---|---|
| **Tipo** | Autenticação via JSON Web Tokens |
| **Custo** | Gratuito (open source) |

**Por que foi escolhido:**
- **JWT stateless**: sem necessidade de banco de sessões — o token carrega o role do usuário
- `require_role()` como decorator reutilizável protege endpoints por perfil de acesso
- `bcrypt` com cost factor padrão para hashing seguro de senhas
- Token de 8h (configurável) — adequado para jornadas de trabalho

**Usado em:** `backend/app/services/auth_service.py`, todos os routers

---

## 🌐 CAMADA DE INFRAESTRUTURA

### 10. Docker + Docker Compose
| | |
|---|---|
| **Tipo** | Containerização e orquestração |
| **Custo** | Gratuito (open source) |

**Por que foi escolhido:**
- Isola cada serviço em containers independentes
- `docker-compose.yml` para desenvolvimento local (hot-reload)
- `docker-compose.prod.yml` para produção (NGINX + Certbot + sem debug)
- Volumes nomeados garantem persistência do PostgreSQL entre reinicializações

### 11. NGINX (Produção)
| | |
|---|---|
| **Tipo** | Reverse Proxy + Load Balancer |
| **Custo** | Gratuito (open source) |

**Por que foi escolhido:**
- HTTPS via Let's Encrypt (certbot auto-renovação a cada 12h)
- WebSocket para o Streamlit funcionar via HTTPS (necessário para funcionar corretamente)
- Headers de segurança (HSTS, X-Frame-Options, X-Content-Type)
- PostgreSQL e pgAdmin jamais expostos diretamente à internet

---

## 📊 Resumo Comparativo

| Tecnologia | Tipo | Custo | Autenticação | Papel no TEO |
|---|---|---|---|---|
| **Streamlit** | Framework UI | Gratuito | — | Dashboard clínico com 3 perfis |
| **Groq API** | LLM Gateway | **Gratuito** | Bearer Token | Tradução, síntese, NLU |
| **Ollama** | LLM Local | Gratuito | — | Fallback offline |
| **PostgreSQL** | Banco relacional | Gratuito | URL + senha | Todos os dados clínicos |
| **SQLAlchemy** | ORM Python | Gratuito | — | Abstração do banco |
| **WhatsApp Web (wa.me)** | Link Direto | **Gratuito** | — | Envio imediato e gratuito via navegador (sem Twilio) |
| **Twilio** | WhatsApp API | Pago/Sandbox | SID + Token | Envio em segundo plano automatizado via API |
| **SMTP Email** | Protocolo de Envio | Gratuito / Hospedado | Usuário + Senha SMTP | Envio automático dos PDFs aos pais e neuropediatras |
| **WeasyPrint** | PDF Engine | Gratuito | — | Relatório semestral (Linux/Produção) |
| **Playwright** | PDF Engine / Fallback | Gratuito | — | Motor primário em Windows e Fallback seguro de PDF |
| **Jinja2** | Template Engine | Gratuito | — | Template HTML do PDF |
| **APScheduler** | Task Scheduler | Gratuito | — | CRON da regra dos 5 meses |
| **FastAPI** | Web Framework | Gratuito | — | Backend REST + Webhook |
| **python-jose** | JWT | Gratuito | — | Autenticação + roles |
| **NGINX** | Reverse Proxy | Gratuito | — | HTTPS + WebSocket (produção) |

> [!NOTE]
> Das 14 tecnologias principais, **13 são completamente gratuitas**. O único custo real opcional é o Twilio WhatsApp Business — e mesmo esse tem o WhatsApp Web gratuito integrado como alternativa.

---

## 🔄 Fluxo Completo — Tradução de Evolução

```
Terapeuta digita notas técnicas no Dashboard
          ↓
POST /api/v1/evolutions/translate-preview
          ↓
  llm_service.traduzir_evolucao(notas, paciente, tipo)
          ↓
  ┌─ Groq API (llama-3.1-70b) ─ ✅ retorna mensagem ~2s
  │         [se falhar — 3 retries]
  └─ Ollama local (llama3:8b) ─ fallback
          ↓
  Mensagem formatada: 🧩 O que fizemos / 🌟 Conquista / 🏠 Dica
          ↓
Dashboard exibe pré-visualização para o terapeuta revisar
          ↓
Terapeuta clica "Salvar e Enviar WhatsApp"
          ↓
  POST /api/v1/evolutions/ → Background Task
          ↓
  whatsapp_service.enviar_mensagem(numero, mensagem)
          ↓
  Twilio API → WhatsApp do responsável ✅
          ↓
evolucao.whatsapp_enviado = True | banco de dados atualizado
```
