# 🧩 TEO — Tu Enlace Organizador

> **Sistema de IA para Clínicas Multidisciplinares de Neurodesenvolvimento (TEA)**  
> Desenvolvido com FastAPI + PostgreSQL + Streamlit + Groq (LLM gratuito) + Twilio WhatsApp

---

## 📋 Visão Geral

O TEO automatiza 3 fluxos críticos de uma clínica de autismo:

| Módulo | Descrição |
|--------|-----------|
| 📝 **Módulo 1** | Tradução de evoluções clínicas → mensagens WhatsApp empáticas para os pais |
| 📅 **Módulo 2** | CRON job da Regra dos 5 Meses — alerta e agendamento automático de laudos |
| 📄 **Módulo 3** | Síntese semestral via IA + PDF consolidado profissional para o neuropediatra |

---

## 🏗️ Arquitetura

```
TEO/
├── backend/          # FastAPI + APScheduler + SQLAlchemy
│   ├── app/
│   │   ├── models/   # PostgreSQL (Pacientes, Profissionais, Evoluções, Citas, Relatórios)
│   │   ├── routers/  # REST API endpoints
│   │   ├── services/ # LLM (Groq), WhatsApp (Twilio), PDF (WeasyPrint), Auth (JWT)
│   │   └── jobs/     # CRON jobs (Regra dos 5 meses)
│   └── sql/          # Scripts de inicialização do banco
├── frontend/         # Streamlit Dashboard (3 níveis de acesso)
│   ├── pages/        # Recepção / Terapeutas / Neuropediatra
│   └── components/   # Auth, Gráficos, Formulários
├── templates/        # Template HTML do relatório PDF (Jinja2)
├── nginx/
│   └── nginx.conf    # Reverse proxy HTTPS + WebSocket + segurança
├── docker-compose.yml          # Desenvolvimento local
├── docker-compose.prod.yml     # Produção (NGINX + SSL + sem hot-reload)
└── .env.prod.example           # Variáveis de produção
```

---

## 🚀 Setup Rápido

### Pré-requisitos
- Streamlit Cloud + Render + Neon (Docker opcional)
- Python 3.12+ (para desenvolvimento local)
- Conta Groq (gratuita): https://console.groq.com/
- Conta Twilio (opcional para WhatsApp real): https://console.twilio.com/

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

**Variáveis obrigatórias:**
```env
GROQ_API_KEY=gsk_...         # API Groq (gratuita)
TWILIO_ACCOUNT_SID=AC...     # Twilio (opcional — simula em dev)
TWILIO_AUTH_TOKEN=...
SECRET_KEY=...               # Chave JWT (gerar com: openssl rand -hex 32)
```

### 2. Iniciar com Docker

```bash
docker-compose up -d
```

Serviços disponíveis:
| Serviço | URL |
|---------|-----|
| **Dashboard** (Streamlit) | http://localhost:8501 |
| **API** (FastAPI) | http://localhost:8000 |
| **Documentação API** | http://localhost:8000/docs |
| **pgAdmin** (banco) | http://localhost:5050 |

### 3. Desenvolvimento Local (sem Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env  # configure o .env
uvicorn app.main:app --reload

# Frontend (outro terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---
## ☁️ Deploy Gratuito (Streamlit Cloud + Render + Neon)

**Passo a passo fácil e gratuito**
1. **GitHub** – suba o código para um repositório.
2. **Neon.tech** – crie a base de dados PostgreSQL, copie a *Connection String*.
3. **Render** – crie o serviço backend usando o `render.yaml` já presente no projeto. Na seção **Environment** adicione as variáveis:
   - `DATABASE_URL` – a URL do Neon.
   - `GROQ_API_KEY` – sua chave Groq.
   - `SECRET_KEY` – senha segura (ex.: `openssl rand -hex 32`).
   - (Opcional) `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`.
   Copie a URL pública gerada (ex.: `https://teo-backend-xxx.onrender.com`).
4. **Streamlit Cloud** – crie uma nova app apontando para `frontend/app.py`. Em **Advanced Settings → Secrets** adicione:
```toml
BACKEND_URL = "https://teo-backend-xxx.onrender.com"
```
   (substitua pelo link obtido no passo 3).
5. Clique em **Deploy**. Em poucos minutos o app estará acessível via URL do Streamlit e consumirá o backend hospedado no Render.

Para mais detalhes veja o passo‑a‑passo completo no [Walkthrough](../walkthrough.md).

## 👥 Níveis de Acesso

| Perfil | Funcionalidades |
|--------|----------------|
| **Recepção** | Cadastro de pacientes, visualização de agendamentos, laudos vencendo |
| **Terapeuta** | Tudo da Recepção + formulário de evolução + envio WhatsApp |
| **Neuropediatra** | Tudo + dashboard de progresso + geração de relatório PDF |
| **Admin** | Acesso total + cadastro de profissionais |

---

## 🤖 LLM (Modelos Gratuitos)

O TEO usa **Groq API** como provedor primário (gratuito, sem limite de uso razoável):

```env
GROQ_MODEL=llama-3.1-70b-versatile  # Recomendado
# Alternativas gratuitas:
# GROQ_MODEL=mixtral-8x7b-32768
# GROQ_MODEL=gemma2-9b-it
```

Se o Groq falhar, o sistema faz fallback para **Ollama local**:
```bash
# Instalar Ollama: https://ollama.ai/
ollama pull llama3:8b
```

---

## 📱 WhatsApp (Twilio Sandbox)

Para testar sem aprovação Meta:

1. Acesse: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Conecte seu WhatsApp ao sandbox (`whatsapp:+14155238886`)
3. Configure o webhook: `POST https://seu-ngrok.ngrok.io/api/v1/whatsapp/webhook`

**Para expor o backend localmente:**
```bash
ngrok http 8000
# Use a URL https://xxx.ngrok.io no Twilio Console
```

---

## 📅 CRON Jobs

| Job | Frequência | Descrição |
|-----|-----------|-----------|
| `verificar_laudos_vencendo` | Diário às 08:00 | Regra dos 5 meses — alerta automático WhatsApp |
| `resetar_alertas_mensalmente` | 1º dia do mês 07:00 | Reseta flags para reenvio mensal |

**Disparo manual (teste):**
```bash
curl -X POST http://localhost:8000/api/v1/cron/trigger-manual \
  -H "Authorization: Bearer <token>"
```

---

## 📄 Geração de PDF

O PDF semestral usa **WeasyPrint** com template HTML Jinja2 em `templates/relatorio_semestral.html`.

Inclui:
- Capa com dados do paciente e período
- Síntese global narrativa (gerada pelo LLM)
- Pareceres por área terapêutica
- Tabela completa de sessões
- Campo de assinatura do neuropediatra

---

## 🧩 Skills Antigravity IDE

3 Skills especializadas instaladas em `~/.gemini/config/skills/`:

| Skill | Arquivo | Uso |
|-------|---------|-----|
| Tradução de Evoluções | `teo_evolucao.md` | Converter notas clínicas em mensagens WhatsApp |
| Agendamento (5 meses) | `teo_agendamento.md` | CRON, webhook Twilio, NLU de respostas |
| Relatório Semestral | `teo_relatorio.md` | Síntese LLM, WeasyPrint, template PDF |

---

## 🛠️ Stack Técnica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | Python 3.12 + FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Banco de Dados | PostgreSQL 16 |
| Scheduler | APScheduler 3.10 |
| LLM | Groq API (Llama 3.1 70B) + Ollama fallback |
| WhatsApp | Twilio Python SDK |
| PDF | WeasyPrint 62 + Jinja2 |
| Frontend | Streamlit 1.38 + Plotly |
| Auth | JWT (python-jose) + bcrypt |
| Containers | Docker + Docker Compose |

---

## 📄 Licença

Desenvolvido pela equipe **Antigravity** para uso clínico interno.  
Todos os dados de pacientes são confidenciais — use HTTPS em produção.

---

## 🌐 Deploy em Produção (VPS + HTTPS)

O TEO suporta acesso **híbrido: LAN interna + remoto** usando um único servidor VPS com HTTPS.

### Arquitetura de Produção

```
Internet (terapeutas home office)
        │
        ▼ HTTPS :443
  [NGINX + Let's Encrypt]
        │
   ┌────┴────────────────┐
   │        VPS          │  DigitalOcean / Contabo / Hetzner
   │  teo_nginx_prod     │  (~$12-20/mês)
   │  teo_backend_prod   │
   │  teo_frontend_prod  │
   │  teo_postgres_prod  │  ← Não exposto à internet
   └─────────────────────┘
        │
   LAN da clínica acessa pelo mesmo domínio HTTPS
```

### Passo a Passo de Deploy

#### 1. Provisionar o VPS

Requisitos mínimos:
- **2 vCPU, 4GB RAM, 40GB SSD** (ex: DigitalOcean Droplet $24/mês)
- Ubuntu 22.04 LTS
- Docker + Docker Compose instalados

```bash
# No VPS, instalar Docker
curl -fsSL https://get.docker.com | bash
apt install docker-compose-plugin -y
```

#### 2. Fazer upload do projeto

```bash
# No seu computador
git clone ou zipar o projeto, depois:
scp -r "TEO-Assistente/" root@IP_DO_VPS:/opt/teo/
```

#### 3. Configurar variáveis de produção

```bash
cd /opt/teo
cp .env.prod.example .env
nano .env  # Preencha: GROQ_API_KEY, TWILIO_*, SECRET_KEY, DOMAIN
```

Gerar `SECRET_KEY` segura:
```bash
openssl rand -hex 32
```

#### 4. Obter certificado SSL (Let's Encrypt)

```bash
# Primeiro, aponte seu domínio para o IP do VPS no seu DNS
# Depois, obtenha o certificado inicial:
docker run --rm -v /opt/teo/nginx/certbot_conf:/etc/letsencrypt \
  -v /opt/teo/nginx/certbot_www:/var/www/certbot \
  -p 80:80 certbot/certbot certonly \
  --standalone -d teo.suaclinica.com.br \
  --email admin@suaclinica.com.br --agree-tos
```

#### 5. Iniciar em produção

```bash
cd /opt/teo
docker compose -f docker-compose.prod.yml up -d

# Verificar logs
docker compose -f docker-compose.prod.yml logs -f backend
```

#### 6. Configurar webhook Twilio

No Twilio Console, atualize o webhook para:
```
https://teo.suaclinica.com.br/api/v1/whatsapp/webhook
```

### Acesso ao pgAdmin em Produção

O pgAdmin fica em `127.0.0.1:5050` — **nunca exposto à internet**.
Acesse via SSH tunnel:

```bash
# Do seu computador local:
ssh -L 5050:localhost:5050 root@IP_DO_VPS
# Abra: http://localhost:5050
```

### Backup do Banco de Dados

```bash
# Backup manual
docker exec teo_postgres_prod pg_dump -U teo_user teo_db > backup_$(date +%Y%m%d).sql

# Cron de backup automático (no VPS)
0 3 * * * docker exec teo_postgres_prod pg_dump -U teo_user teo_db > /opt/teo/backups/backup_$(date +%Y%m%d).sql
```

### Provedores VPS Recomendados

| Provedor | Plano | Preço | Região BR |
|---|---|---|---|
| [DigitalOcean](https://digitalocean.com) | 2vCPU 4GB | ~$24/mês | São Paulo |
| [Contabo](https://contabo.com) | 4vCPU 8GB | ~€8/mês | — |
| [Hetzner](https://hetzner.com) | 2vCPU 4GB | ~€7/mês | — |
| [Hostinger](https://hostinger.com.br) | VPS 4GB | ~R$65/mês | Brasil |

