"""
TEO — App Principal Streamlit
Ponto de entrada com autenticação e roteamento por role.
"""
import streamlit as st
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.auth import login_page, logout, is_authenticated, get_role, get_user_name

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO GLOBAL DA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TEO — Tu Enlace Organizador",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# ESTILOS GLOBAIS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a2744 0%, #1e3a5f 50%, #1a4a3a 100%);
}

[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: #A0AEC0 !important;
    font-size: 0.8rem;
}

/* Botão primário */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4A90B8, #6CBF8A);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: all 0.2s;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(74, 144, 184, 0.4);
}

/* Cards de métricas */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Esconde elementos padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Cabeçalho personalizado */
.teo-header {
    background: linear-gradient(135deg, #1a2744 0%, #1e3a5f 100%);
    color: white;
    padding: 1rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.teo-header-left { display: flex; align-items: center; gap: 12px; }
.teo-header h1 { font-size: 1.4rem; font-weight: 700; margin: 0; color: white; }
.teo-header .subtitle { font-size: 0.8rem; color: #A0AEC0; }
.teo-header .badge {
    background: rgba(108, 191, 138, 0.2);
    border: 1px solid #6CBF8A;
    color: #6CBF8A;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROTEAMENTO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(role: str, user_name: str):
    """Sidebar com navegação por role."""
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem;">
            <div style="font-size: 1.5rem; margin-bottom: 4px;">🧩</div>
            <div style="font-size: 1rem; font-weight: 700;">TEO</div>
            <div style="font-size: 0.75rem; color: #A0AEC0;">Tu Enlace Organizador</div>
        </div>
        <div style="padding: 0.5rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.7rem; color: #A0AEC0; text-transform: uppercase; letter-spacing: 0.05em;">Usuário</div>
            <div style="font-weight: 600; font-size: 0.9rem;">👤 {user_name}</div>
            <div style="font-size: 0.75rem; color: #6CBF8A;">● {role.capitalize()}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navegação por role
        role_pages = {
            "recepcao": [
                ("🏥 Dashboard", "dashboard"),
                ("👶 Pacientes", "pacientes"),
                ("📅 Agendamentos", "agendamentos"),
            ],
            "terapeuta": [
                ("🏥 Dashboard", "dashboard"),
                ("👶 Pacientes", "pacientes"),
                ("📝 Evoluções", "evolucoes"),
                ("📅 Agendamentos", "agendamentos"),
            ],
            "neuropediatra": [
                ("🏥 Dashboard", "dashboard"),
                ("👶 Pacientes", "pacientes"),
                ("📊 Progresso", "progresso"),
                ("📝 Evoluções", "evolucoes"),
                ("📄 Relatórios", "relatorios"),
                ("📅 Agendamentos", "agendamentos"),
            ],
            "admin": [
                ("🏥 Dashboard", "dashboard"),
                ("👶 Pacientes", "pacientes"),
                ("📝 Evoluções", "evolucoes"),
                ("📅 Agendamentos", "agendamentos"),
                ("📄 Relatórios", "relatorios"),
                ("⚙️ Admin", "admin"),
            ]
        }

        pages = role_pages.get(role, role_pages["recepcao"])

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = pages[0][1]

        for label, page_id in pages:
            is_active = st.session_state.get("current_page") == page_id
            button_style = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_id}", use_container_width=True, type=button_style):
                st.session_state["current_page"] = page_id
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚪 Sair", use_container_width=True):
            logout()


def render_header(title: str, subtitle: str = ""):
    """Cabeçalho padronizado das páginas."""
    role = get_role()
    badge_map = {
        "recepcao": "🏥 Recepção",
        "terapeuta": "🩺 Terapeuta",
        "neuropediatra": "👨‍⚕️ Neuropediatra",
        "admin": "⚙️ Admin"
    }
    st.markdown(f"""
    <div class="teo-header">
        <div class="teo-header-left">
            <span style="font-size: 1.5rem;">🧩</span>
            <div>
                <h1>{title}</h1>
                {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
            </div>
        </div>
        <span class="badge">{badge_map.get(role, role)}</span>
    </div>
    """, unsafe_allow_html=True)


def page_dashboard():
    render_header("Dashboard TEO", "Visão geral da clínica")
    import httpx
    from components.auth import get_auth_headers
    BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))

    col1, col2, col3, col4 = st.columns(4)

    try:
        headers = get_auth_headers()
        # Pacientes ativos
        r = httpx.get(f"{BACKEND_URL}/api/v1/patients/", headers=headers, timeout=30)
        pacientes = r.json() if r.status_code == 200 else []

        # Agendamentos
        r2 = httpx.get(f"{BACKEND_URL}/api/v1/appointments/pending-count", headers=headers, timeout=30)
        counts = r2.json() if r2.status_code == 200 else {}

        # Laudos vencendo
        r3 = httpx.get(f"{BACKEND_URL}/api/v1/patients/laudos/vencendo", headers=headers, timeout=30)
        laudos_vencendo = r3.json() if r3.status_code == 200 else []

        with col1:
            st.metric("👶 Pacientes Ativos", len(pacientes))
        with col2:
            st.metric("📅 Consultas Pendentes", counts.get("pendente", 0))
        with col3:
            st.metric("✅ Confirmados", counts.get("confirmado_op1", 0) + counts.get("confirmado_op2", 0))
        with col4:
            st.metric("🚨 Laudos Vencendo", len(laudos_vencendo), delta_color="inverse")

    except Exception:
        with col1: st.metric("👶 Pacientes", "—")
        with col2: st.metric("📅 Pendentes", "—")
        with col3: st.metric("✅ Confirmados", "—")
        with col4: st.metric("🚨 Laudos", "—")

    st.info("💡 **Navegue pelo menu lateral** para acessar as funcionalidades do TEO de acordo com seu perfil.")


def page_em_construcao(titulo: str):
    render_header(titulo)
    st.warning("🚧 Esta seção está disponível nas páginas dedicadas (menu lateral).")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not is_authenticated():
        login_page()
        return

    role = get_role()
    user_name = get_user_name()

    render_sidebar(role, user_name)

    current_page = st.session_state.get("current_page", "dashboard")

    if current_page == "dashboard":
        page_dashboard()
    elif current_page == "pacientes":
        # Importa a página de recepção (pacientes)
        exec(open(os.path.join(os.path.dirname(__file__), "pages", "01_recepcao.py"), encoding="utf-8").read())
    elif current_page == "evolucoes":
        exec(open(os.path.join(os.path.dirname(__file__), "pages", "02_terapeutas.py"), encoding="utf-8").read())
    elif current_page in ["relatorios", "progresso"]:
        exec(open(os.path.join(os.path.dirname(__file__), "pages", "03_neuropediatra.py"), encoding="utf-8").read())
    elif current_page == "agendamentos":
        page_em_construcao("📅 Agendamentos")
        st.info("Agendamentos são gerenciados automaticamente pelo TEO via WhatsApp. Consulte os registros abaixo.")
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
