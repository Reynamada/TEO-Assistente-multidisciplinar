"""
TEO — Página: Neuropediatra
Módulo 3: Dashboard de progresso, pareceres e geração de relatório PDF semestral.
"""
import os
import httpx
import streamlit as st
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from components.auth import get_auth_headers  # noqa
from components.charts import (  # noqa
    grafico_evolucoes_por_mes, grafico_tipos_sessao,
    gauge_laudo_status, timeline_sessoes
)

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

st.markdown("## 👨‍⚕️ Painel do Neuropediatra")
st.caption("Visualize o progresso dos pacientes e gere relatórios semestrais consolidados.")

# Busca pacientes
pacientes = get_api("/patients/")
pacientes_map = {f"{p['nome']}": p for p in pacientes} if pacientes else {}

if not pacientes_map:
    st.warning("Nenhum paciente cadastrado.")
    st.stop()

# Seletor de paciente na sidebar da página
paciente_nome = st.selectbox("👶 Selecionar paciente", list(pacientes_map.keys()))
paciente = pacientes_map.get(paciente_nome, {})
pac_id = paciente.get("id")

if not pac_id:
    st.stop()

# ── Dados do paciente ──────────────────────────────────────
col_info, col_gauge = st.columns([3, 2])

with col_info:
    st.markdown(f"### {paciente.get('nome')}")
    ci1, ci2, ci3 = st.columns(3)
    with ci1:
        nasc = paciente.get("data_nascimento", "")
        try:
            from datetime import date as d
            idade = (d.today() - d.fromisoformat(nasc)).days // 365
            st.metric("Idade", f"{idade} anos")
        except Exception:
            st.metric("Nascimento", nasc)
    with ci2:
        st.metric("Diagnóstico", paciente.get("diagnostico_principal", "TEA"))
    with ci3:
        st.metric("Responsável", paciente.get("nome_responsavel", "—"))

    st.caption(f"📱 WhatsApp: {paciente.get('whatsapp_responsavel', '—')}")

with col_gauge:
    ultimo_laudo = paciente.get("data_ultimo_laudo")
    if ultimo_laudo:
        try:
            dias = (date.today() - date.fromisoformat(ultimo_laudo)).days
            gauge_laudo_status(dias)
        except Exception:
            st.info("Laudo registrado")
    else:
        st.warning("📋 Nenhum laudo registrado para este paciente.")

st.divider()

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Progresso e Gráficos", "📝 Pareceres", "📄 Relatório Semestral"])

# ── Tab 1: Progresso ──────────────────────────────────────
with tab1:
    evolucoes = get_api(f"/evolutions/patient/{pac_id}?limit=48")

    if not evolucoes:
        st.info("Nenhuma evolução registrada para este paciente ainda.")
    else:
        st.caption(f"**{len(evolucoes)} sessões** analisadas")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            grafico_evolucoes_por_mes(evolucoes)
        with col_g2:
            grafico_tipos_sessao(evolucoes)

        st.markdown("#### 📅 Timeline de Sessões")
        timeline_sessoes(evolucoes)

        # Últimas sessões em tabela
        st.markdown("#### 📋 Últimas Sessões")
        import pandas as pd
        df = pd.DataFrame([{
            "Data": e.get("data_sessao"),
            "Tipo": e.get("tipo_sessao", "—"),
            "WhatsApp": "✅" if e.get("whatsapp_enviado") else "⏳",
            "Resumo Clínico": e.get("notas_tecnicas", "")[:100] + "..."
        } for e in evolucoes[:10]])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Tab 2: Pareceres ──────────────────────────────────────
with tab2:
    st.subheader("📝 Pareceres por Área Terapêutica")
    st.caption("Preencha os pareceres de cada área antes de gerar o relatório semestral.")

    if "pareceres" not in st.session_state:
        st.session_state["pareceres"] = {}

    areas = [
        "Neuropediatria",
        "Terapia Ocupacional",
        "Fonoaudiologia",
        "Psicologia",
        "Psicopedagogia",
        "Fisioterapia",
    ]

    for area in areas:
        key = f"parecer_{area}_{pac_id}"
        valor = st.text_area(
            f"**{area}**",
            value=st.session_state["pareceres"].get(area, ""),
            height=100,
            placeholder=f"Parecer da equipe de {area} sobre o período...",
            key=key
        )
        st.session_state["pareceres"][area] = valor

    if st.button("💾 Salvar Pareceres", type="secondary"):
        st.success("✅ Pareceres salvos! Agora gere o relatório na aba 'Relatório Semestral'.")


# ── Tab 3: Relatório Semestral ─────────────────────────────
with tab3:
    st.subheader("📄 Geração de Relatório Semestral")
    st.caption("O TEO analisa as últimas 48 sessões, gera uma síntese com IA e exporta o PDF profissional.")

    # Período
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        periodo_inicio = st.date_input(
            "Início do período",
            value=date.today() - timedelta(days=180),
            key="rel_inicio"
        )
    with col_p2:
        periodo_fim = st.date_input(
            "Fim do período",
            value=date.today(),
            key="rel_fim"
        )

    # Histórico de relatórios
    relatorios = get_api(f"/reports/patient/{pac_id}")
    if relatorios:
        st.markdown("#### 📚 Relatórios Anteriores")
        for rel in relatorios:
            status = "✅ PDF Gerado" if rel.get("pdf_path") else "⏳ Em processamento..."
            with st.expander(f"{status} — {rel.get('periodo_inicio')} a {rel.get('periodo_fim')} ({rel.get('num_evolucoes_analisadas')} sessões)"):
                if rel.get("sintese_global"):
                    st.markdown("**Síntese gerada pelo TEO:**")
                    st.info(rel["sintese_global"][:500] + "...")

                if rel.get("pdf_path"):
                    rel_id = rel["id"]
                    if st.button(f"⬇️ Baixar PDF", key=f"dl_{rel_id}"):
                        try:
                            r = httpx.get(
                                f"{BACKEND_URL}/api/v1/reports/{rel_id}/download",
                                headers=get_auth_headers(),
                                timeout=30
                            )
                            if r.status_code == 200:
                                st.download_button(
                                    label="📄 Clique para baixar o PDF",
                                    data=r.content,
                                    file_name=f"relatorio_{paciente_nome.replace(' ', '_').lower()}.pdf",
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(str(e))

    st.divider()

    # Botão de geração
    col_gen1, col_gen2 = st.columns([3, 1])
    with col_gen1:
        st.markdown("""
        **O TEO irá:**
        1. 📝 Ler todas as evoluções do período selecionado (até 48 sessões)
        2. 🤖 Gerar uma síntese global com IA (Groq/Llama)
        3. 📊 Incluir os pareceres por área preenchidos acima
        4. 📄 Renderizar o PDF com capa, gráficos e assinatura
        """)

    with col_gen2:
        gerar = st.button(
            "🚀 Gerar Relatório\nSemestral",
            type="primary",
            use_container_width=True,
            key="btn_gerar_relatorio"
        )

    if gerar:
        with st.spinner("TEO está analisando e gerando o relatório... ⏳ Isso pode levar alguns segundos."):
            try:
                r = httpx.post(
                    f"{BACKEND_URL}/api/v1/reports/generate/{pac_id}",
                    headers=get_auth_headers(),
                    params={
                        "periodo_inicio": str(periodo_inicio),
                        "periodo_fim": str(periodo_fim),
                    },
                    timeout=120
                )
                if r.status_code == 201:
                    st.success(
                        "✅ Relatório iniciado! O PDF será gerado em background. "
                        "Atualize a página em alguns segundos para visualizar."
                    )
                    st.balloons()
                elif r.status_code == 400:
                    st.error(f"❌ {r.json().get('detail', 'Erro desconhecido')}")
                else:
                    st.error(f"Erro {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
