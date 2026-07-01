# 🧩 TEO — Tu Enlace Organizador

> **Sistema de IA para Clínicas Multidisciplinares de Neurodesenvolvimento (TEA)**  
> Desenvolvido com FastAPI + PostgreSQL + Streamlit + Groq (LLM gratuito) + WhatsApp Web / Twilio + Email SMTP Automático

---

## 📋 Visão Geral

O TEO automatiza 3 fluxos críticos de uma clínica de autismo e neurodesenvolvimento:

| Módulo | Descrição |
|--------|-----------|
| 📝 **Módulo 1: Evoluções Semanais** | Registro de sessões clínicas por terapeutas. Tradução automática de notas técnicas em mensagens empáticas para os pais via IA. Envio instantâneo via **WhatsApp Web (Gratuito)** ou **Twilio API (Segundo plano)**. |
| 📅 **Módulo 2: Alertas dos 5 Meses** | Monitoramento automático de laudos perto do vencimiento. Geração de alertas e busca automática de consultas livres com a neuropediatra do paciente. Envio via WhatsApp Web (gratuito) ou Twilio API. Permite à recepção **editar dados básicos** dos pacientes direto no painel. |
| 📄 **Módulo 3: Relatório Semestral** | Consolidação de até 48 sessões de evoluções. Geração de laudo estruturado via IA destacando **Evolução Clínica**, **Deficiências a Tratar** e **Recomendações**. Renderização de PDF profissional (WeasyPrint) com **envio automático por Email** aos pais e à neuropediatra acompanhante. |

---

## 🏗️ Arquitetura

```
TEO/
├── backend/          # FastAPI + APScheduler + SQLAlchemy
│   ├── app/
│   │   ├── models/   # PostgreSQL (Pacientes, Profissionais, Evoluções, Citas, Relatórios)
│   │   ├── routers/  # REST API endpoints (Autenticação, Clientes, Evoluções, Relatórios)
│   │   ├── services/ # LLM (Groq), WhatsApp (Twilio), Email (SMTP), PDF (WeasyPrint), Auth (JWT)
│   │   └── jobs/     # CRON jobs (Regra dos 5 meses, reset de alertas)
│   └── scripts/      # Scripts de desenvolvimento (seed de banco de dados)
├── frontend/         # Streamlit Dashboard (Interface clínica responsiva)
│   ├── pages/        # Recepção / Terapeutas / Neuropediatra
│   └── components/   # Componentes de UI (Autenticação, Gráficos Plotly)
├── templates/        # Template HTML/CSS do laudo PDF (Jinja2)
├── nginx/            # Servidor proxy reverso (Nginx com suporte a SSL Let's Encrypt)
├── docker-compose.yml          # Setup local de desenvolvimento
├── docker-compose.prod.yml     # Setup de produção com Nginx HTTPS
└── render.yaml                 # Configuração para deploy direto no Render
```

---

## 🚀 Setup Rápido

### Pré-requisitos
- Python 3.12+ (para execução local)
- PostgreSQL (ou Neon.tech na nuvem)
- Conta Groq (Gratuito e Ultra-rápido): https://console.groq.com/
- Conta Twilio (Opcional — o sistema possui envio grátis via WhatsApp Web)
- Servidor de Email SMTP (Opcional — possui modo simulação em tela)

### 1. Configurar variáveis de ambiente
Copie o arquivo de exemplo e edite as variáveis no arquivo `.env`:
```bash
cp .env.example .env
```

**Principais variáveis do `.env`:**
```env
DATABASE_URL=postgresql://teo_user:teo_secure_password_change_me@localhost:5432/teo_db
SECRET_KEY=f60b86a01490219c629fbbe95079a4de5bf85e33dbe4faad2db3f6e1f0e40ffc # JWT Secret Key segura
GROQ_API_KEY=gsk_... # Sua chave de API do Groq

# Opcional - SMTP Email (Se vazio, rodará em Modo Simulação no console)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
SMTP_FROM=noreply@clinicateo.com

# Opcional - Twilio WhatsApp (Se vazio, rodará em Modo Simulação no console)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 2. Executar Seed de Desenvolvimento (Histórico de 5 meses)
Para testar a inteligência do TEO e os gráficos, o projeto inclui um script que cria profissionais das 5 áreas da clínica e gera **20 semanas consecutivas (5 meses) de sessões completas** para o paciente Mateo García.
```bash
# Executar a partir do diretório raiz
cmd /C "set PYTHONPATH=%cd%\backend && .venv\Scripts\python.exe backend\scripts\seed.py"
```

### 3. Execução Local (sem Docker)

```bash
# Terminal 1: Servidor Backend (FastAPI)
cmd /C "set PYTHONPATH=%cd%\backend && .venv\Scripts\uvicorn.exe backend.main:app --reload --host 0.0.0.0 --port 8000"

# Terminal 2: Servidor Frontend (Streamlit)
.venv\Scripts\streamlit.exe run frontend/app.py
```

---

## 👥 Níveis de Acesso e Perfis Clínicos

O TEO possui autenticação JWT com controle de acesso baseado em papéis de usuários (RBAC):

| Perfil | Ações Permitidas |
|--------|------------------|
| 🏥 **Recepção** | Cadastro de novos pacientes, visualização da lista de cadastrados, **edição rápida de dados** (nome, nascimento, responsável, telefone), visualização de laudos vencendo e disparo manual de alertas. |
| 🧩 **Terapeuta** | Permissões de Recepção + formulário de registro de sessões, geração de prévia de WhatsApp traduzida por IA, e envio de alertas via **WhatsApp Web direto (gratuito)** ou Twilio. Permissão estendida para **gerar laudos semestrais**. |
| 👨‍⚕️ **Neuropediatra** | Permissões completas + visualização do dashboard de progresso do paciente (gráficos Plotly por especialidade), preenchimento de pareceres médicos e **geração de relatório semestral consolidador**. |
| 🔑 **Admin** | Acesso irrestrito a todos os painéis, além do gerenciamento e cadastro de novos profissionais da clínica. |

---

## 🤖 Módulos de Inteligência Artificial (Groq Llama 3.1)

O TEO se integra com a API do Groq usando o modelo `llama-3.1-70b-versatile`. As tarefas inteligentes incluem:

* **Tradução Empática**: Converte jargão técnico médico em linguagem afetiva estruturada em: *🧩 O que fizemos*, *🌟 Grande conquista*, e *🏠 Dica para casa*.
* **Laudo Semestral Clínico**: Analisa o histórico de até 48 sessões de evoluções multidisciplinares (Terapia Ocupacional, Fonoaudiologia, Psicologia, Psicopedagogia e Fisioterapia) e gera um laudo estruturado sob três seções:
  1. `### 📈 Evolução Clínica`
  2. `### ⚠️ Deficiências e Desafios a serem Tratados`
  3. `### 💡 Recomendações Terapêuticas`
* **NLU de Agendamento (WhatsApp)**: Classifica as respostas dos pais (ex: *"quero a primeira opção"*) para atualizar automaticamente o status da consulta no banco de dados.

---

## 📧 Disparo de Emails Automático (Laudos)

Quando um profissional (Médico ou Terapeuta) finaliza a geração do relatório semestral na aba **Relatório Semestral**:
1. O backend gera o PDF consolidado com o WeasyPrint.
2. O sistema dispara em segundo plano o envio de e-mails:
   * **Para os Pais**: Envia o laudo em PDF em anexo com uma mensagem calorosa comemorando a evolução da criança.
   * **Para a Neuropediatra do Caso**: Envia o PDF para que o médico acompanhante tenha o compilado das 5 especialidades na mesa no momento da consulta.
3. Se não houver configuração de e-mail SMTP ativa, o sistema registrará as informações no log do console em **Modo Simulação** para auditoria de testes.

---

## ☁️ Deploy na Nuvem (Gratuito)

Você pode hospedar o ecossistema TEO de forma 100% gratuita utilizando a seguinte arquitetura:

1. **Base de Dados**: Hospedar no **Neon.tech** (PostgreSQL Serverless gratuito).
2. **Backend (FastAPI)**: Hospedar no **Render.com** (Web Service gratuito rodando em container Docker). Configurar o diretório raiz como `backend` e as variáveis de ambiente necessárias.
3. **Frontend (Streamlit)**: Hospedar no **Streamlit Community Cloud** (Conectado ao repositório do GitHub com ponto de entrada em `frontend/app.py` e configurando a variável `BACKEND_URL` em Advanced Settings).

---

## 🛠️ Stack Técnica

* **Backend**: Python 3.12, FastAPI 0.115, SQLAlchemy 2.0, APScheduler 3.10
* **Banco de Dados**: PostgreSQL 16 (Neon.tech / Local)
* **Frontend**: Streamlit 1.38, Plotly (Gráficos), Pandas
* **Geração de PDF**: WeasyPrint 62, Jinja2 Templates
* **Segurança**: Criptografia de senhas com `bcrypt` (passlib) e tokens JWT (`python-jose`)
* **AI Engine**: Groq API (Llama 3.1 70B) com fallback local para Ollama (Llama 3 8B)
