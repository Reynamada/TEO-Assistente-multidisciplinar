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

st.markdown("## 📝 Evoluções Clínicas — Terapia")
user_name = st.session_state.get("user_name", "Terapeuta")
user_role = st.session_state.get("user_role", "terapeuta")
st.info(f"👨‍⚕️ **Terapeuta:** {user_name} | **Especialidade / Perfil:** {user_role.title()}")

# Busca lista de pacientes (O backend agora garante que Terapeutas só recebam seus pacientes vinculados)
pacientes = get_api("/patients/")
pacientes_map = {f"{p['nome']} — {p['nome_responsavel']}": p for p in pacientes} if pacientes else {}

tab1, tab2, tab3 = st.tabs(["✏️ Nova Evolução", "📋 Histórico de Evoluções", "📄 Laudo do Neuropediatra"])

# ── Tab 1: Nova Evolução ──────────────────────────────────
with tab1:
    if not pacientes_map:
        st.warning("⚠️ Nenhum paciente vinculado a você foi encontrado no momento.")
        st.stop()

    col_pac, col_num = st.columns([3, 1])
    with col_pac:
        paciente_selecionado_label = st.selectbox(
            "👶 Paciente *",
            list(pacientes_map.keys()),
            key="evo_paciente"
        )
    with col_num:
        num_sessao = st.number_input("🔢 Nº da Sessão *", min_value=1, max_value=500, value=1, step=1, key="evo_num")

    col_data, col_tempo = st.columns(2)
    with col_data:
        data_sessao = st.date_input("📅 Data da sessão *", value=date.today(), key="evo_data")
    with col_tempo:
        duracao = st.selectbox("⏱️ Tempo de cada sessão *", ["30 min", "45 min", "50 min", "60 min", "90 min"], index=2, key="evo_duracao")

    paciente = pacientes_map.get(paciente_selecionado_label, {})
    tipo_sessao = f"Sessão #{num_sessao} — {user_role.title()}"

    st.markdown("---")
    st.markdown("#### 📋 Registro Clínico Estruturado da Sessão")
    st.caption("Preencha as atividades, avanços e recomendações abaixo. O TEO traduzirá essas informações para uma mensagem empática para os pais via WhatsApp.")

    col_a, col_b = st.columns(2)
    with col_a:
        atividades = st.text_area(
            "🧩 Atividades Feitas na Sessão *",
            height=140,
            placeholder="Ex: Exercícios de integração sensorial com texturas, circuito motor na rampa e treino de preensão...",
            key="evo_atividades"
        )
    with col_b:
        avancos = st.text_area(
            "🌟 Avanços e Conquistas da Sessão *",
            height=140,
            placeholder="Ex: Tolerou bem a atividade sensorial sem desregulação, expressou verbalmente suas vontades, conseguiu focar por 15 min...",
            key="evo_avancos"
        )

    recomendacoes = st.text_area(
        "🏠 Recomendações e Dicas para Casa *",
        height=100,
        placeholder="Ex: Orientamos a família a continuar estimulando o uso de potes de grãos em casa para manter a autorregulação...",
        key="evo_recomendacoes"
    )

    notas_completas = f"Número da Sessão: #{num_sessao} | Tempo: {duracao}\n\n🧩 Atividades Realizadas na Sessão:\n{atividades}\n\n🌟 Avanços / Conquistas:\n{avancos}\n\n🏠 Recomendações:\n{recomendacoes}"

    # Preview LLM
    st.markdown("---")
    col_preview, col_send = st.columns([2, 1])

    with col_preview:
        if st.button("🤖 Prévia da Mensagem (TEO)", use_container_width=True, type="secondary"):
            if not atividades or not avancos or not recomendacoes:
                st.error("⚠️ Preencha os campos de Atividades, Avanços e Recomendações antes de gerar a prévia.")
            else:
                with st.spinner("TEO está traduzindo o registro clínico para os pais... 🧩"):
                    try:
                        resp = httpx.post(
                            f"{BACKEND_URL}/api/v1/evolutions/translate-preview",
                            json={
                                "notas_tecnicas": notas_completas,
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
            if not atividades or not avancos or not recomendacoes:
                st.error("⚠️ Preencha os campos de Atividades, Avanços e Recomendações.")
            elif not paciente.get("id"):
                st.error("Selecione um paciente.")
            else:
                with st.spinner("Salvando evolução..."):
                    try:
                        r = httpx.post(
                            f"{BACKEND_URL}/api/v1/evolutions/",
                            json={
                                "paciente_id": paciente["id"],
                                "data_sessao": str(data_sessao),
                                "tipo_sessao": tipo_sessao,
                                "duracao_minutos": duracao,
                                "notas_tecnicas": notas_completas,
                            },
                            headers=get_auth_headers(),
                            timeout=15
                        )
                        if r.status_code == 201:
                            st.success("✅ Evolução salva com sucesso! A tradução será processada.")
                            st.session_state.pop("preview_traducao", None)
                        else:
                            st.error(f"Erro: {r.json().get('detail', r.text)}")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with col_enviar:
        if st.button("📱 Salvar e Enviar WhatsApp", use_container_width=True, type="primary"):
            if not atividades or not avancos or not recomendacoes:
                st.error("⚠️ Preencha os campos de Atividades, Avanços e Recomendações.")
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
                                "notas_tecnicas": notas_completas,
                            },
                            headers=get_auth_headers(),
                            params={"auto_translate": "false"},
                            timeout=15
                        )
                        if r.status_code == 201:
                            evo_id = r.json()["id"]

                            # Gera tradução e envia WhatsApp
                            preview_r = httpx.post(
                                f"{BACKEND_URL}/api/v1/evolutions/translate-preview",
                                json={"notas_tecnicas": notas_completas, "nome_paciente": paciente.get("nome", "").split()[0], "tipo_sessao": tipo_sessao},
                                headers=get_auth_headers(),
                                timeout=60
                            )
                            if preview_r.status_code == 200:
                                st.success(f"✅ Evolução salva e WhatsApp enviado para {paciente.get('nome_responsavel')}! 📱")
                                st.balloons()
                        else:
                            st.error(f"Erro: {r.json().get('detail', r.text)}")
                    except Exception as e:
                        st.error(f"Erro: {e}")


# ── Tab 2: Histórico de Evoluções ─────────────────────────
with tab2:
    st.subheader("📋 Histórico das Suas Evoluções")
    st.caption("Acesso estrito apenas aos seus registros clínicos realizados com os seus pacientes vinculados.")

    if not pacientes_map:
        st.warning("⚠️ Nenhum paciente vinculado encontrado.")
        st.stop()

    pac_hist = st.selectbox(
        "Selecione o paciente para ver seu histórico de sessões",
        list(pacientes_map.keys()),
        key="hist_paciente"
    )
    pac_id = pacientes_map.get(pac_hist, {}).get("id")

    if pac_id:
        evolucoes = get_api(f"/evolutions/patient/{pac_id}?limit=20")

        if not evolucoes:
            st.info("Nenhuma evolução registrada por você para este paciente.")
        else:
            st.caption(f"**{len(evolucoes)} evolução(ões) encontrada(s)**")

            for ev in evolucoes:
                enviado = ev.get("whatsapp_enviado", False)
                icon = "✅" if enviado else "⏳"
                dur = ev.get('duracao_minutos', '—')
                label = f"{icon} **{ev.get('data_sessao', '—')}** — {ev.get('tipo_sessao', 'Sessão')} ({dur})"

                with st.expander(label):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**📋 Registro Técnico Estruturado:**")
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


# ── Tab 3: Laudo do Neuropediatra ─────────────────────────
with tab3:
    st.subheader("📄 Leitura do Laudo do Neuropediatra")
    st.caption("Consulta aos laudos e diretrizes semestrais emitidas pelo Neuropediatra para seus pacientes vinculados.")

    if not pacientes_map:
        st.warning("⚠️ Nenhum paciente vinculado encontrado.")
        st.stop()

    pac_laudo_label = st.selectbox(
        "Selecione o paciente para visualizar o laudo",
        list(pacientes_map.keys()),
        key="laudo_paciente"
    )
    pac_laudo_id = pacientes_map.get(pac_laudo_label, {}).get("id")

    if pac_laudo_id:
        relatorios = get_api(f"/reports/patient/{pac_laudo_id}")

        if not relatorios:
            st.info("Nenhum laudo ou relatório semestral emitido pelo Neuropediatra para este paciente até o momento.")
        else:
            st.caption(f"**{len(relatorios)} laudo(s) encontrado(s)**")

            for rel in relatorios:
                periodo = f"{rel.get('periodo_inicio', '—')} a {rel.get('periodo_fim', '—')}"
                with st.expander(f"📄 Laudo Semestral — Período: {periodo}", expanded=True):
                    if rel.get("sintese_global"):
                        st.markdown("**🧠 Síntese Global / Avaliação e Conduta:**")
                        st.write(rel["sintese_global"])
                    else:
                        st.info("Síntese em processamento.")

                    if rel.get("num_evolucoes_analisadas"):
                        st.caption(f"📊 Evoluções analisadas no período do laudo: {rel.get('num_evolucoes_analisadas')}")

                    rel_id = rel.get("id")
                    st.markdown("---")
                    col_dl, _ = st.columns([2, 2])
                    with col_dl:
                        key_bytes_ter = f"pdf_ter_{rel_id}"
                        if key_bytes_ter in st.session_state:
                            st.download_button(
                                label="💾 Baixar Arquivo PDF agora",
                                data=st.session_state[key_bytes_ter],
                                file_name=f"Laudo_Neuropediatra_{pac_laudo_label.split('—')[0].strip()}_{periodo.replace('/', '-')}.pdf",
                                mime="application/pdf",
                                key=f"save_pdf_{rel_id}"
                            )
                        else:
                            if st.button("📥 Obter / Gerar PDF do Laudo", key=f"dl_laudo_{rel_id}", use_container_width=True):
                                with st.spinner("⏳ Gerando laudo em PDF com WeasyPrint (aguarde uns segundos)..."):
                                    try:
                                        r_pdf = httpx.get(
                                            f"{BACKEND_URL}/api/v1/reports/{rel_id}/download",
                                            headers=get_auth_headers(),
                                            timeout=120
                                        )
                                        if r_pdf.status_code == 200:
                                            st.session_state[key_bytes_ter] = r_pdf.content
                                            st.success("✅ Laudo PDF carregado!")
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao obter PDF: HTTP {r_pdf.status_code}")
                                    except Exception as e_pdf:
                                        st.error(f"⚠️ Erro ao carregar PDF: {e_pdf}")
