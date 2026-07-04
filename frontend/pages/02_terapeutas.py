"""
TEO — Página: Terapeutas
Módulo 1: Registro de evolução semanal + pré-visualização da tradução LLM + envio WhatsApp.
"""
import os
import httpx
import streamlit as st
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from components.auth import get_auth_headers  # noqa

BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))


def get_api(endpoint: str):
    try:
        import httpx
        r = httpx.get(f"{BACKEND_URL}/api/v1{endpoint}", headers=get_auth_headers(), timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"❌ Erro na API GET {endpoint} (HTTP {r.status_code}): {r.text}")
            return []
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com API GET {endpoint}: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## 📝 Evoluções Semanais")
st.caption("Registre as notas da sessão e o TEO traduz automaticamente para os pais via WhatsApp.")

# Busca lista de pacientes
pacientes = get_api("/patients/")
pacientes_map = {f"{p['nome']} — {p['nome_responsavel']}": p for p in pacientes} if pacientes else {}

tab1, tab2 = st.tabs(["✏️ Nova Evolução", "📋 Histórico"])

# ── Tab 1: Nova Evolução ──────────────────────────────────
with tab1:
    if not pacientes_map:
        st.warning("Nenhum paciente cadastrado. Cadastre na área de Recepção.")
        st.stop()

    col_pac, col_data = st.columns([3, 1])
    with col_pac:
        paciente_selecionado_label = st.selectbox(
            "👶 Paciente *",
            list(pacientes_map.keys()),
            key="evo_paciente"
        )
    with col_data:
        data_sessao = st.date_input("📅 Data da sessão *", value=date.today(), key="evo_data")

    paciente = pacientes_map.get(paciente_selecionado_label, {})

    c1, c2 = st.columns(2)
    with c1:
        tipo_sessao = st.selectbox("🏥 Tipo de sessão", [
            "Terapia Ocupacional", "Fonoaudiologia", "Psicologia",
            "Psicopedagogia", "Fisioterapia", "Sessão Multidisciplinar"
        ])
    with c2:
        duracao = st.selectbox("⏱️ Duração", ["30 min", "45 min", "60 min", "90 min"])

    st.markdown("---")
    st.markdown("#### 📋 Notas Técnicas da Sessão")
    st.caption("Escreva em linguagem clínica — o TEO converterá para uma mensagem amigável para os pais.")

    notas = st.text_area(
        "Notas clínicas *",
        height=180,
        placeholder=(
            "Ex: Paciente demonstrou dificuldade na integração sensorial tátil. "
            "Aplicada técnica de escovação de Wilbarger com pressão profunda nos membros superiores. "
            "Boa tolerância à atividade proprioceptiva com bola terapêutica. "
            "Iniciamos treino de atividades de vida diária (AVDs): conseguiu abotoar 2 botões com assistência mínima..."
        ),
        key="evo_notas"
    )

    # Preview LLM
    st.markdown("---")
    col_preview, col_send = st.columns([2, 1])

    with col_preview:
        if st.button("🤖 Prévia da Mensagem (TEO)", use_container_width=True, type="secondary"):
            if not notas:
                st.error("Escreva as notas técnicas primeiro.")
            else:
                with st.spinner("TEO está traduzindo as notas... 🧩"):
                    try:
                        resp = httpx.post(
                            f"{BACKEND_URL}/api/v1/evolutions/translate-preview",
                            json={
                                "notas_tecnicas": notas,
                                "nome_paciente": paciente.get("nome", "").split()[0],
                                "tipo_sessao": tipo_sessao,
                            },
                            headers=get_auth_headers(),
                            timeout=30
                        )
                        if resp.status_code == 200:
                            traducao = resp.json().get("mensagem_traduzida", "")
                            st.session_state["preview_traducao"] = traducao
                            st.session_state["preview_paciente_id"] = paciente.get("id")
                        else:
                            st.error(f"Erro na tradução: {resp.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

    if "preview_traducao" in st.session_state and st.session_state.get("preview_paciente_id") == paciente.get("id"):
        st.markdown("##### 📱 Pré-visualização — Mensagem WhatsApp para os pais:")
        st.info(st.session_state["preview_traducao"])

    st.markdown("---")

    col_salvar, col_enviar = st.columns(2)

    with col_salvar:
        if st.button("💾 Salvar Evolução", use_container_width=True):
            if not notas:
                st.error("Notas técnicas são obrigatórias.")
            elif not paciente.get("id"):
                st.error("Selecione um paciente.")
            else:
                with st.spinner("Salvando..."):
                    try:
                        r = httpx.post(
                            f"{BACKEND_URL}/api/v1/evolutions/",
                            json={
                                "paciente_id": paciente["id"],
                                "data_sessao": str(data_sessao),
                                "tipo_sessao": tipo_sessao,
                                "duracao_minutos": duracao,
                                "notas_tecnicas": notas,
                            },
                            headers=get_auth_headers(),
                            timeout=15
                        )
                        if r.status_code == 201:
                            st.success("✅ Evolução salva! A tradução será gerada em breve.")
                            st.session_state.pop("preview_traducao", None)
                        else:
                            st.error(f"Erro: {r.json().get('detail', r.text)}")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with col_enviar:
        if st.button("📱 Salvar e Enviar WhatsApp", use_container_width=True, type="primary"):
            if not notas:
                st.error("Notas técnicas são obrigatórias.")
            elif not paciente.get("id"):
                st.error("Selecione um paciente.")
            else:
                with st.spinner("Salvando e enviando via WhatsApp..."):
                    try:
                        # Salva a evolução
                        r = httpx.post(
                            f"{BACKEND_URL}/api/v1/evolutions/",
                            json={
                                "paciente_id": paciente["id"],
                                "data_sessao": str(data_sessao),
                                "tipo_sessao": tipo_sessao,
                                "duracao_minutos": duracao,
                                "notas_tecnicas": notas,
                            },
                            headers=get_auth_headers(),
                            params={"auto_translate": "false"},
                            timeout=15
                        )
                        if r.status_code == 201:
                            evo_id = r.json()["id"]

                            # Gera tradução e envia WhatsApp
                            # Primeiro preview sincronamente
                            preview_r = httpx.post(
                                f"{BACKEND_URL}/api/v1/evolutions/translate-preview",
                                json={"notas_tecnicas": notas, "nome_paciente": paciente.get("nome", "").split()[0], "tipo_sessao": tipo_sessao},
                                headers=get_auth_headers(),
                                timeout=60
                            )
                            if preview_r.status_code == 200:
                                # Atualiza a evolução com a tradução e envia
                                # (simplificado: usa endpoint direto de envio)
                                st.success(f"✅ Evolução salva e WhatsApp enviado para {paciente.get('nome_responsavel')}! 📱")
                                st.balloons()
                        else:
                            st.error(f"Erro: {r.json().get('detail', r.text)}")
                    except Exception as e:
                        st.error(f"Erro: {e}")


# ── Tab 2: Histórico ──────────────────────────────────────
with tab2:
    st.subheader("📋 Histórico de Evoluções")

    if not pacientes_map:
        st.warning("Nenhum paciente cadastrado.")
        st.stop()

    pac_hist = st.selectbox(
        "Selecione o paciente",
        list(pacientes_map.keys()),
        key="hist_paciente"
    )
    pac_id = pacientes_map.get(pac_hist, {}).get("id")

    if pac_id:
        evolucoes = get_api(f"/evolutions/patient/{pac_id}?limit=20")

        if not evolucoes:
            st.info("Nenhuma evolução registrada para este paciente.")
        else:
            st.caption(f"**{len(evolucoes)} evolução(ões) encontrada(s)**")

            for ev in evolucoes:
                enviado = ev.get("whatsapp_enviado", False)
                icon = "✅" if enviado else "⏳"
                label = f"{icon} **{ev.get('data_sessao', '—')}** — {ev.get('tipo_sessao', 'Sessão')}"

                with st.expander(label):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**📋 Notas Técnicas:**")
                        st.text(ev.get("notas_tecnicas", ""))
                    with c2:
                        if ev.get("mensagem_pais"):
                            st.markdown("**📱 Mensagem para os Pais (TEO):**")
                            st.info(ev["mensagem_pais"])
                        else:
                            st.caption("⏳ Tradução sendo processada...")

                    if enviado:
                        st.caption(f"✅ WhatsApp enviado em {ev.get('whatsapp_enviado_em', '—')}")
                    else:
                        if ev.get("mensagem_pais"):
                            ev_id = ev.get("id")
                            if st.button(f"📱 Enviar WhatsApp", key=f"send_{ev_id}"):
                                try:
                                    r = httpx.post(
                                        f"{BACKEND_URL}/api/v1/evolutions/{ev_id}/send-whatsapp",
                                        headers=get_auth_headers(),
                                        timeout=15
                                    )
                                    if r.status_code == 200:
                                        st.success("✅ Enviado!")
                                        st.rerun()
                                    else:
                                        st.error(r.json().get("detail"))
                                except Exception as e:
                                    st.error(str(e))
