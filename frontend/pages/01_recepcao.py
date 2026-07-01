"""
TEO — Página: Recepção
Cadastro de pacientes, visualização de agendamentos e status de mensagens WhatsApp.
"""
import os
import httpx
import streamlit as st
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from components.auth import get_auth_headers  # noqa

BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))


def get_api(endpoint: str) -> list | dict:
    try:
        r = httpx.get(f"{BACKEND_URL}/api/v1{endpoint}", headers=get_auth_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def post_api(endpoint: str, data: dict) -> tuple[bool, dict]:
    try:
        r = httpx.post(f"{BACKEND_URL}/api/v1{endpoint}", json=data, headers=get_auth_headers(), timeout=10)
        return r.status_code in [200, 201], r.json()
    except Exception as e:
        return False, {"detail": str(e)}


# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## 👶 Gestão de Pacientes")
st.caption("Cadastro, edição e visualização de pacientes e laudos.")

tab1, tab2, tab3 = st.tabs(["📋 Lista de Pacientes", "➕ Novo Paciente", "🚨 Laudos Vencendo"])

# ── Tab 1: Lista ──────────────────────────────────────────
with tab1:
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search = st.text_input("🔍 Buscar por nome ou WhatsApp", placeholder="Digite para filtrar...")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    search_param = f"?search={search}" if search else ""
    pacientes = get_api(f"/patients/{search_param}")

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        st.caption(f"**{len(pacientes)} paciente(s) encontrado(s)**")
        for p in pacientes:
            with st.expander(f"👶 **{p['nome']}** — Resp: {p['nome_responsavel']} | 📱 {p['whatsapp_responsavel']}"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"**Nascimento:** {p.get('data_nascimento', '—')}")
                    st.markdown(f"**Diagnóstico:** {p.get('diagnostico_principal', 'TEA')}")
                with c2:
                    st.markdown(f"**Responsável:** {p.get('nome_responsavel', '—')}")
                    st.markdown(f"**Parentesco:** {p.get('parentesco_responsavel', '—')}")
                with c3:
                    st.markdown(f"**WhatsApp:** {p.get('whatsapp_responsavel', '—')}")
                    st.markdown(f"**E-mail:** {p.get('email_responsavel', '—') or '—'}")
                with c4:
                    ultimo_laudo = p.get('data_ultimo_laudo')
                    if ultimo_laudo:
                        from datetime import date
                        try:
                            data_laudo = date.fromisoformat(ultimo_laudo)
                            dias = (date.today() - data_laudo).days
                            if dias >= 150:
                                st.error(f"🚨 Laudo: **{dias} dias** (VENCIDO)")
                            elif dias >= 120:
                                st.warning(f"⚠️ Laudo: **{dias} dias** (atenção)")
                            else:
                                st.success(f"✅ Laudo: **{dias} dias** (ok)")
                        except Exception:
                            st.info(f"Último laudo: {ultimo_laudo}")
                    else:
                        st.warning("📋 Sem laudo registrado")

                    alerta = p.get("alerta_laudo_enviado", False)
                    if alerta:
                        st.caption("📱 Alerta WhatsApp enviado")


# ── Tab 2: Novo Paciente ──────────────────────────────────
with tab2:
    st.subheader("Cadastrar Novo Paciente")

    with st.form("form_novo_paciente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome completo *", placeholder="Nome da criança")
            data_nasc = st.date_input("Data de nascimento *")
            diagnostico = st.selectbox("Diagnóstico principal", ["TEA", "TEA + TDAH", "TDAH", "Outro"])
        with c2:
            nome_resp = st.text_input("Nome do responsável *", placeholder="Mãe, Pai, etc.")
            parentesco = st.selectbox("Parentesco", ["Mãe", "Pai", "Avô/Avó", "Outro"])
            whatsapp = st.text_input("WhatsApp do responsável *", placeholder="+55 11 99999-9999")

        email_resp = st.text_input("E-mail do responsável (opcional)")
        observacoes = st.text_area("Observações", placeholder="Informações adicionais...")

        # Busca neuropediatras disponíveis
        profissionais = get_api("/patients/")  # Workaround: buscaremos por role

        submit = st.form_submit_button("✅ Cadastrar Paciente", type="primary", use_container_width=True)

        if submit:
            if not nome or not nome_resp or not whatsapp:
                st.error("Preencha os campos obrigatórios (*)")
            else:
                payload = {
                    "nome": nome,
                    "data_nascimento": str(data_nasc),
                    "diagnostico_principal": diagnostico,
                    "nome_responsavel": nome_resp,
                    "parentesco_responsavel": parentesco,
                    "whatsapp_responsavel": whatsapp,
                    "email_responsavel": email_resp or None,
                    "observacoes": observacoes or None,
                }
                ok, resp = post_api("/patients/", payload)
                if ok:
                    st.success(f"✅ Paciente **{nome}** cadastrado com sucesso!")
                    st.balloons()
                else:
                    st.error(f"Erro: {resp.get('detail', 'Erro desconhecido')}")


# ── Tab 3: Laudos Vencendo ────────────────────────────────
with tab3:
    st.subheader("🚨 Pacientes com Laudos Vencendo (Regra dos 5 Meses)")
    st.caption("Pacientes com mais de 150 dias desde o último laudo de neurodesenvolvimento.")

    laudos = get_api("/patients/laudos/vencendo?dias=150")

    if not laudos:
        st.success("✅ Todos os laudos estão dentro do prazo!")
    else:
        st.error(f"**{len(laudos)} paciente(s)** com laudo vencendo ou vencido.")

        from datetime import date
        for p in laudos:
            ultimo_laudo = p.get("data_ultimo_laudo", "")
            try:
                dias = (date.today() - date.fromisoformat(ultimo_laudo)).days if ultimo_laudo else "—"
            except Exception:
                dias = "—"

            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"**{p['nome']}**")
                st.caption(f"Resp: {p['nome_responsavel']} | {p['whatsapp_responsavel']}")
            with col2:
                st.markdown(f"📋 Último laudo: **{ultimo_laudo or 'Não registrado'}**")
                if isinstance(dias, int):
                    st.error(f"⏱️ **{dias} dias** atrás") if dias >= 150 else st.warning(f"⏱️ **{dias} dias** atrás")
            with col3:
                alerta_enviado = p.get("alerta_laudo_enviado", False)
                if alerta_enviado:
                    st.success("📱 Alerta enviado")
                else:
                    st.warning("📱 Aguardando CRON")
            st.divider()

        if st.button("🤖 Disparar CRON Manualmente (Teste)", type="secondary"):
            try:
                r = httpx.post(f"{BACKEND_URL}/api/v1/cron/trigger-manual", headers=get_auth_headers())
                if r.status_code == 200:
                    st.success("✅ CRON executado! Alertas enviados via WhatsApp.")
                    st.rerun()
                else:
                    st.error(f"Erro: {r.text}")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
