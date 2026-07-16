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


def post_api(endpoint: str, data: dict) -> tuple[bool, dict]:
    try:
        import httpx
        r = httpx.post(f"{BACKEND_URL}/api/v1{endpoint}", json=data, headers=get_auth_headers(), timeout=30)
        if r.status_code in [200, 201]:
            return True, r.json()
        else:
            st.error(f"❌ Erro na API POST {endpoint} (HTTP {r.status_code}): {r.text}")
            return False, {"detail": r.text}
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com API POST {endpoint}: {e}")
        return False, {"detail": str(e)}


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

    # Exibir especialistas/terapeutas vinculados
    linked_profs = get_api(f"/patients/{pac_id}/therapists")
    if linked_profs:
        from collections import defaultdict
        t_map = defaultdict(set)
        for lp in linked_profs:
            name = lp.get("nome")
            spec = lp.get("especialidade") or ""
            role = lp.get("role", "")
            # Mostra todos os profissionais clínicos (ignora apenas admin/recepcao)
            if name and role not in {"recepcao", "admin"}:
                t_map[spec or "Especialidade não informada"].add(name)
        if t_map:
            t_str = " | ".join([f"**{k}:** {', '.join(sorted(list(v)))}" for k, v in sorted(t_map.items())])
            st.markdown(f"🩺 {t_str}")


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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Progresso e Gráficos", "📝 Pareceres", "🏥 Indicações Terapêuticas", "📄 Relatório Semestral"])

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
                    key_np = f"pdf_np_{rel_id}"
                    if key_np in st.session_state:
                        st.download_button(
                            label="💾 Baixar Arquivo PDF agora",
                            data=st.session_state[key_np],
                            file_name=f"relatorio_{paciente_nome.replace(' ', '_').lower()}_{rel_id[:8]}.pdf",
                            mime="application/pdf",
                            key=f"dl_{rel_id}",
                            use_container_width=True,
                            type="primary"
                        )
                        import base64
                        b64_pdf = base64.b64encode(st.session_state[key_np]).decode("utf-8")
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="550px" style="border: 1px solid #ccc; border-radius: 6px; margin-top: 8px;"></iframe>'
                        st.markdown("**Visualização do Relatório (PDF):**")
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        if st.button("📄 Carregar & Visualizar PDF do Relatório", key=f"btn_np_{rel_id}", use_container_width=True):
                            with st.spinner("⏳ Gerando relatório em PDF com WeasyPrint (aguarde alguns segundos)..."):
                                try:
                                    pdf_url = f"{BACKEND_URL}/api/v1/reports/{rel_id}/download"
                                    r_pdf = httpx.get(pdf_url, headers=get_auth_headers(), timeout=120)
                                    if r_pdf.status_code == 200:
                                        st.session_state[key_np] = r_pdf.content
                                        st.success("✅ PDF pronto para visualização e download!")
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Arquivo PDF indisponível no servidor no momento.")
                                except Exception as e:
                                    st.error(f"Erro ao obter bytes do PDF: {e}")

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
                payload = {
                    "periodo_inicio": str(periodo_inicio),
                    "periodo_fim": str(periodo_fim),
                    "pareceres": st.session_state.get("pareceres", {})
                }
                r = httpx.post(
                    f"{BACKEND_URL}/api/v1/reports/generate/{pac_id}",
                    json=payload,
                    headers=get_auth_headers(),
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


# ── Tab 4: Indicações Terapêuticas ───────────────────────────
with tab4:
    st.subheader("🏥 Indicações Terapêuticas e Laudo da Consulta")
    st.caption("Preencha as indicações de terapeutas, diagnóstico, evolução observada e recomendações para o próximo período. Ao salvar, o responsável é notificado por WhatsApp.")

    # Busca terapeutas disponíveis
    terapeutas = get_api("/professionals/terapeutas")
    terapeutas_map = {f"{t['nome']} — {t['especialidade']}": t['id'] for t in terapeutas} if terapeutas else {}

    if not terapeutas_map:
        st.warning("⚠️ Nenhum terapeuta cadastrado no sistema. Cadastre terapeutas antes de indicar.")
    else:
        # Indicações atuais
        indicacoes_atual = get_api(f"/indications/patient/{pac_id}")
        
        st.markdown("### 📋 Indicações Atuais")
        if indicacoes_atual.get("terapeutas_ids"):
            terapeutas_atual = get_api("/professionals/terapeutas")
            nomes_atuais = []
            for tid in indicacoes_atual["terapeutas_ids"]:
                for t in terapeutas_atual:
                    if t['id'] == tid:
                        nomes_atuais.append(f"• {t['nome']} ({t['especialidade']})")
                        break
            st.markdown("**Terapeutas indicados:**\n" + "\n".join(nomes_atuais))
        else:
            st.info("Nenhum terapeuta indicado ainda.")

        if indicacoes_atual.get("diagnostico"):
            st.markdown(f"**Diagnóstico:** {indicacoes_atual['diagnostico']}")
        if indicacoes_atual.get("evolucao"):
            st.markdown(f"**Evolução observada:** {indicacoes_atual['evolucao']}")
        if indicacoes_atual.get("recomendacoes"):
            st.markdown(f"**Recomendações:** {indicacoes_atual['recomendacoes']}")

        st.divider()
        st.markdown("### ✏️ Atualizar Indicações")

        # Seleção de terapeutas
        terapeutas_selecionados = st.multiselect(
            "👥 Terapeutas a indicar *",
            options=list(terapeutas_map.keys()),
            default=[k for k, v in terapeutas_map.items() if v in indicacoes_atual.get("terapeutas_ids", [])],
            placeholder="Selecione um ou mais terapeutas"
        )

        # Diagnóstico
        diagnostico = st.text_area(
            "🩺 Diagnóstico da consulta *",
            value=indicacoes_atual.get("diagnostico", ""),
            height=100,
            placeholder="Ex: TEA (nível 1) — melhora na interação social, mantém estereotipias motoras..."
        )

        # Evolução observada
        evolucao = st.text_area(
            "📈 Evolução observada na consulta",
            value=indicacoes_atual.get("evolucao", ""),
            height=100,
            placeholder="Descreva a evolução do paciente desde a última consulta..."
        )

        # Recomendações
        recomendacoes = st.text_area(
            "💡 Recomendações para o próximo período *",
            value=indicacoes_atual.get("recomendacoes", ""),
            height=100,
            placeholder="Ex: Manter TO 2x/semana, iniciar Fono 1x/semana, encaminhar para avaliação psicológica..."
        )

        if st.button("💾 Salvar Indicações e Notificar Responsável", type="primary", use_container_width=True):
            if not terapeutas_selecionados:
                st.error("⚠️ Selecione pelo menos um terapeuta.")
            elif not diagnostico.strip():
                st.error("⚠️ Preencha o diagnóstico.")
            elif not recomendacoes.strip():
                st.error("⚠️ Preencha as recomendações.")
            else:
                payload = {
                    "terapeutas_ids": [terapeutas_map[t] for t in terapeutas_selecionados],
                    "diagnostico": diagnostico.strip(),
                    "evolucao": evolucao.strip() if evolucao else "",
                    "recomendacoes": recomendacoes.strip()
                }
                ok, resp = post_api(f"/indications/patient/{pac_id}", payload)
                if ok:
                    st.success("✅ Indicações salvas! O responsável foi notificado por WhatsApp.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {resp.get('detail', 'Erro ao salvar')}")


# ── Tab 4: Indicações Terapêuticas ───────────────────────────
with tab4:
    st.subheader("🏥 Indicações Terapêuticas — Consulta do Neuropediatra")
    st.caption("Selecione os terapeutas recomendados, registre diagnóstico, evolução e recomendações. O TEO enviará ao responsável via WhatsApp.")

    # Carrega indicações atuais
    indicacoes = get_api(f"/indications/patient/{pac_id}")

    # Busca terapeutas disponíveis para seleção
    terapeutas_disponiveis = get_api("/professionals/") if "professionals" not in st.session_state else st.session_state["professionals"]
    if not terapeutas_disponiveis:
        try:
            terapeutas_disponiveis = get_api("/professionals/")
            st.session_state["professionals"] = terapeutas_disponiveis
        except Exception:
            terapeutas_disponiveis = []

    # Filtra apenas terapeutas
    terapeutas_list = [t for t in terapeutas_disponiveis if t.get("role") == "terapeuta"]
    terapeutas_opcoes = {f"{t['nome']} ({t.get('especialidade', 'Sem especialidade')})": t['id'] for t in terapeutas_list}

    # Terapeutas já indicados
    atuais_ids = set(indicacoes.get("terapeutas_ids", [])) if indicacoes else set()

    st.markdown("#### 👥 Equipe Terapêutica Recomendada")
    selecionados = st.multiselect(
        "Selecione os terapeutas recomendados para este paciente:",
        options=list(terapeutas_opcoes.keys()),
        default=[k for k, v in terapeutas_opcoes.items() if v in atuais_ids],
        help="Mantenha pressionado Ctrl/Cmd para selecionar múltiplos"
    )
    selecionados_ids = [terapeutas_opcoes[k] for k in selecionados]

    st.markdown("#### 🩺 Diagnóstico da Consulta")
    diagnostico_atual = indicacoes.get("diagnostico", "") if indicacoes else ""
    diagnostico = st.text_area(
        "Diagnóstico formal (ex: TEA Nível 2 + TDAH):",
        value=diagnostico_atual,
        height=100,
        placeholder="Registre o diagnóstico formal da consulta..."
    )

    st.markdown("#### 📈 Evolução Observada na Consulta")
    evolucao_atual = indicacoes.get("evolucao", "") if indicacoes else ""
    evolucao = st.text_area(
        "Evolução observada (progressos, regressões, marcos):",
        value=evolucao_atual,
        height=120,
        placeholder="Descreva a evolução do paciente desde a última consulta..."
    )

    st.markdown("#### 💡 Recomendações para o Próximo Período")
    recomendacoes_atual = indicacoes.get("recomendacoes", "") if indicacoes else ""
    recomendacoes = st.text_area(
        "Recomendações (ajuste de frequência, novas metas, encaminhamentos):",
        value=recomendacoes_atual,
        height=120,
        placeholder="Ex: Aumentar TO para 2x/semana, iniciar Psicologia, reavaliação em 4 meses..."
    )

    col_salvar, col_limpar = st.columns([1, 1])
    with col_salvar:
        if st.button("💾 Salvar Indicações e Enviar WhatsApp", type="primary", use_container_width=True):
            if not selecionados_ids:
                st.warning("⚠️ Selecione pelo menos um terapeuta.")
            else:
                payload = {
                    "terapeutas_ids": selecionados_ids,
                    "diagnostico": diagnostico,
                    "evolucao": evolucao,
                    "recomendacoes": recomendacoes
                }
                ok, resp = post_api(f"/indications/patient/{pac_id}", payload)
                if ok:
                    st.success("✅ Indicações salvas! WhatsApp enviado ao responsável.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {resp.get('detail', 'Erro ao salvar')}")

    with col_limpar:
        if st.button("🗑️ Limpar Indicações", type="secondary", use_container_width=True):
            if st.session_state.get("confirmar_limpar_indicacoes"):
                payload = {
                    "terapeutas_ids": [],
                    "diagnostico": "",
                    "evolucao": "",
                    "recomendacoes": ""
                }
                ok, resp = post_api(f"/indications/patient/{pac_id}", payload)
                if ok:
                    st.success("✅ Indicações limpas!")
                    st.session_state.pop("confirmar_limpar_indicacoes", None)
                    st.rerun()
                else:
                    st.error(f"❌ {resp.get('detail', 'Erro')}")
            else:
                st.session_state["confirmar_limpar_indicacoes"] = True
                st.warning("⚠️ Clique novamente para confirmar limpeza")

    st.divider()

    # Exibe indicações atuais
    if indicacoes:
        st.markdown("### 📋 Indicações Atuais Registradas")
        if indicacoes.get("terapeutas_ids"):
            terapeutas_nomes = []
            for tid in indicacoes["terapeutas_ids"]:
                t = next((t for t in terapeutas_list if t['id'] == tid), None)
                if t:
                    terapeutas_nomes.append(f"{t['nome']} ({t.get('especialidade', '')})")
            st.markdown(f"**Terapeutas:** {', '.join(terapeutas_nomes) if terapeutas_nomes else '—'}")
        if indicacoes.get("diagnostico"):
            st.markdown(f"**Diagnóstico:** {indicacoes['diagnostico']}")
        if indicacoes.get("evolucao"):
            st.markdown(f"**Evolução:** {indicacoes['evolucao']}")
        if indicacoes.get("recomendacoes"):
            st.markdown(f"**Recomendações:** {indicacoes['recomendacoes']}")
        if indicacoes.get("atualizado_em"):
            st.caption(f"Atualizado em: {indicacoes['atualizado_em']}")
    else:
        st.info("Nenhuma indicação registrada ainda.")
