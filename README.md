# TEO – Assistente Multidisciplinar

![Demo Screenshot](https://raw.githubusercontent.com/your-repo/TEO-Assistente-multidisciplinar/main/assets/demo.png)

## 📖 Overview

**TEO** (pronounced *te‑o*) is a modern, **multidisciplinary health‑assistant platform** built with **FastAPI** (backend) and **Streamlit** (frontend). It provides a seamless experience for clinicians, receptionists, therapists, and patients to manage appointments, view medical records, and interact via a clean, premium UI.

The project is designed to be **easily deployable** on Docker‑Compose locally, **Render** in the cloud, and **Neon.tech** for the PostgreSQL database. It includes:
- Role‑based authentication with JWT tokens.
- Automated email/SMS notifications via Twilio.
- PDF report generation with WeasyPrint.
- Scheduling of background jobs (e.g., backups) via APScheduler.
- A polished UI featuring glass‑morphism, smooth micro‑animations, and a dark‑mode theme.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI 0.115, Pydantic 2.9, SQLAlchemy 2.0, PostgreSQL 16, Uvicorn 0.30 |
| **Frontend** | Streamlit 1.38, Plotly 5.24, extra‑streamlit‑components |
| **Containerization** | Docker, Docker‑Compose (production) |
| **Cloud Deployment** | Render (Docker service), Neon.tech (managed PostgreSQL) |
| **Auxiliary** | Twilio, WeasyPrint, APScheduler, Groq, Ollama |

---

## 🚀 Getting Started (Local Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/TEO-Assistente-multidisciplinar.git
   cd TEO-Assistente-multidisciplinar
   ```

2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # PowerShell
   pip install -r requirements.txt
   ```

3. **Configure environment variables** – copy the template and fill in your values:
   ```bash
   cp .env.example .env
   ```
   Required keys (excerpt):
   ```dotenv
   DATABASE_URL=postgresql://user:password@localhost:5432/teo
   SECRET_KEY=super‑secret-key
   GROQ_API_KEY=...
   TWILIO_ACCOUNT_SID=...
   TWILIO_AUTH_TOKEN=...
   ENVIRONMENT=development
   DEBUG=true
   ```

4. **Run the services**
   - **Backend** (FastAPI):
     ```bash
     uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
     ```
   - **Frontend** (Streamlit):
     ```bash
     streamlit run frontend/app.py
     ```

5. **Seed the database (optional)**
   ```bash
   python backend/scripts/seed.py
   ```
   This creates demo users for each role (see **Credentials** below).

---

## 📦 Docker Production Build

The repository now ships with a **Docker‑Compose production file** that builds the backend using the repository root as the build context (so `requirements.txt` is found). To build and run locally:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
The services will be exposed on:
- **FastAPI** – `http://localhost:8000`
- **Streamlit UI** – `http://localhost:8501`
- **Nginx reverse proxy** – `http://localhost` (port 80)

A **`.dockerignore`** file is included to keep the image lightweight (excludes virtualenv, frontend assets, git history, etc.).

---

## ☁️ Render Deployment

`render.yaml` has been updated to use the repository root as the Docker context and points to `./backend/Dockerfile`. Deploy by linking your GitHub repository in the Render dashboard and selecting the **Web Service** configuration. All required environment variables (Database URL, API keys, etc.) should be defined in Render’s **Environment** section.

---

## 🔐 Default Credentials (Demo)

| Role | Email | Password |
|------|-------|----------|
| **Neuropediatra** | neuropediatra@clinica.com | `123456` |
| **Recepção** | recepcao@clinica.com | `123456` |
| **Terapeuta** | terapeuta@clinica.com | `123456` |
| **Administrador** | adminReyna@clinica.com | `123456` |
| **Psicólogo** | psicologia@clinica.com | `123456` |
| **Psicopedagogo** | sandra@clinica.com | `123456` |
| **Fisioterapeuta** | fabio@clinica.com | `123456` |

These users are created by `backend/scripts/seed.py`.

---

## 📚 Documentation

- **API Docs** – Open `http://localhost:8000/docs` after the backend starts.
- **Project Wiki** – See the `docs/` folder for architecture diagrams, database schema, and contribution guidelines.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑feature`).
3. Write tests and ensure they pass: `pytest`
4. Submit a Pull Request.

Please adhere to the existing coding style (black, isort) and include comprehensive commit messages.

---

## 📄 License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## 🙌 Acknowledgments

Thanks to the open‑source community for the fantastic libraries that make this project possible: FastAPI, Streamlit, SQLAlchemy, Pydantic, Twilio, WeasyPrint, and many more.
