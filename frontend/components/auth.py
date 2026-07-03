"""
TEO — Frontend Streamlit | Componente de Autenticação
"""
import os
import httpx
import streamlit as st

BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))


def login_page():
    """Renderiza a página de login do TEO."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 4rem;
    }

    .teo-logo {
        font-size: 4rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .teo-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4A90B8, #6CBF8A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.25rem;
    }

    .teo-subtitle {
        color: #718096;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Logo e título
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="teo-logo">🧩</div>', unsafe_allow_html=True)
        st.markdown('<div class="teo-title">TEO</div>', unsafe_allow_html=True)
        st.markdown('<div class="teo-subtitle">Tu Enlace Organizador<br>Sistema de IA para Clínicas de Neurodesenvolvimento</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("📧 E-mail", placeholder="seu@email.com")
            password = st.text_input("🔑 Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Preencha e-mail e senha.")
                return

            with st.spinner("Autenticando..."):
                try:
                    resp = httpx.post(
                        f"{BACKEND_URL}/api/v1/auth/token",
                        data={"username": email, "password": password},
                        timeout=60
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state["authenticated"] = True
                        st.session_state["token"] = data["access_token"]
                        st.session_state["role"] = data["role"]
                        st.session_state["user_name"] = data["nome"]
                        st.rerun()
                    else:
                        st.error("❌ E-mail ou senha incorretos.")
                except httpx.ConnectError:
                    st.error("⚠️ Backend indisponível. Verifique se o servidor está rodando.")
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.markdown("---")
        st.caption("🔒 Acesso restrito à equipe clínica autorizada.")


def logout():
    """Remove dados de autenticação da sessão."""
    for key in ["authenticated", "token", "role", "user_name"]:
        st.session_state.pop(key, None)
    st.rerun()


def get_auth_headers() -> dict:
    """Retorna headers de autorização para chamadas à API."""
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"}


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_role() -> str:
    return st.session_state.get("role", "")


def get_user_name() -> str:
    return st.session_state.get("user_name", "")
