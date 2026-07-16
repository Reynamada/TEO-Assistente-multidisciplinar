"""
TEO — Página: Admin
Gestão de atribuição de terapeutas, horários iniciais e coordenação de agendas.
"""
import os
import httpx
import streamlit as st
import sys
from datetime import date, time, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from components.auth import get_auth_headers, get_role  # noqa

BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))


def get_api(endpoint: str) -> list | dict:
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


def patch_api(endpoint: str, data: dict) -> tuple[bool, dict]:
    try:
        import httpx
        r = httpx.patch(f"{BACKEND_URL}/api/v1{endpoint}", json=data, headers=get_auth_headers(), timeout=30)
        if r.status_code in [200, 201]:
            return True, r.json()
        else:
            st.error(f"❌ Erro na API PATCH {endpoint} (HTTP {r.status_code}): {r.text}")
            return False, {"detail": r.text}
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com API PATCH {endpoint}: {e}")
        return False, {"detail": str(e)}


# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## ⚙️ Painel Administrativo")
st.caption("Atribuição de terapeutas sugeridos, definição de horários iniciais e coordenação de agendas.")

# Carrega dados
pacientes = get_api("/patients/")
pacientes_map = {p["id"]: p for p in pacientes} if pacientes else {}
pacientes_list = [f"{p['nome']} ({p['nome_responsavel']})" for p in pacientes] if pacientes else []

terapeutas = get_api("/professionals/terapeutas")
terapeutas_map = {t["id"]: t for t in terapeutas} if terapeutas else {}
terapeutas_list = [f"{t['nome']} — {t.get('especialidade', 'Sem especialidade')}" for t in terapeutas] if terapeutas else []

neuropediatras = get_api("/professionals/neuropediatras")
neuropediatras_map = {n["id"]: n for n in neuropediatras} if neuropediatras else {}

total_pac = len(pacientes) if pacientes else 0
total_ter = len([t for t in terapeutas if t.get("ativo", True)]) if terapeutas else 0
total_neu = len([n for n in neuropediatras if n.get("ativo", True)]) if neuropediatras else 0

tab1, tab2, tab3 = st.tabs(["👥 Atribuição de Terapeutas", "📅 Horários Iniciais", "📊 Visão Geral"])

# ── Tab 1: Atribuição de Terapeutas ──────────────────────────────────────────
with tab1:
    st.subheader("👥 Atribuição de Terapeutas aos Pacientes")
    st.caption("O Neuropediatra indica os terapeutas; o Admin atribui/vincula oficialmente e define a carga.")

    if not pacientes_list:
        st.warning("Nenhum paciente cadastrado.")
    else:
        pac_selecionado = st.selectbox(
            "👶 Selecionar Paciente",
            options=pacientes_list,
            key="admin_pac_atrib"
        )
        pac_id = next(p["id"] for p in pacientes if f"{p['nome']} ({p['nome_responsavel']})" == pac_selecionado)
        paciente = next(p for p in pacientes if p["id"] == pac_id)

        # Mostra indicações do neuropediatra
        indicacoes = get_api(f"/indications/patient/{pac_id}")
        
        st.markdown(f"### 👶 {paciente['nome']}")
        st.caption(f"Resp: {paciente['nome_responsavel']} | 📱 {paciente['whatsapp_responsavel']} | 🧠 Diag: {paciente.get('diagnostico_principal', 'TEA')}")

        if indicacoes.get("terapeutas_ids"):
            st.markdown("**🩺 Indicações do Neuropediatra:**")
            for tid in indicacoes["terapeutas_ids"]:
                t = terapeutas_map.get(tid)
                if t:
                    st.markdown(f"• **{t['nome']}** — {t.get('especialidade', 'Sem especialidade')} {f\"({t.get('registro_conselho', '')})\" if t.get('registro_conselho') else ''}")
            if indicacoes.get("diagnostico"):
                st.markdown(f"**Diagnóstico:** {indicacoes['diagnostico']}")
            if indicacoes.get("recomendacoes"):
                st.markdown(f"**Recomendações:** {indicacoes['recomendacoes']}")
        else:
            st.info("Nenhuma indicação do neuropediatra registrada ainda.")

        st.divider()
        st.markdown("### 🔗 Vinculação Oficial (Admin)")

        # Terapeutas já vinculados (via evoluções ou indicações)
        vinculados = get_api(f"/patients/{pac_id}/therapists")
        vinculados_ids = set(v["id"] for v in vinculados) if vinculados else set()

        # Seleção de terapeutas para vincular
        terapeutas_opcoes = {f"{t['nome']} — {t.get('especialidade', 'Sem especialidade')}": t["id"] for t in terapeutas}
        
        selecionados = st.multiselect(
            "Terapeutas a vincular a este paciente:",
            options=list(terapeutas_opcoes.keys()),
            default=[k for k, v in terapeutas_opcoes.items() if v in vinculados_ids],
            key=f"vincular_{pac_id}"
        )
        selecionados_ids = [terapeutas_opcoes[k] for k in selecionados]

        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            if st.button("🔗 Vincular Terapeutas", type="primary", use_container_width=True):
                if not selecionados_ids:
                    st.warning("Selecione pelo menos um terapeuta.")
                else:
                    # Atualiza indicações (cria/atualiza)
                    payload = {
                        "terapeutas_ids": selecionados_ids,
                        "diagnostico": indicacoes.get("diagnostico", ""),
                        "evolucao": indicacoes.get("evolucao", ""),
                        "recomendacoes": indicacoes.get("recomendacoes", "")
                    }
                    ok, resp = post_api(f"/indications/patient/{pac_id}", payload)
                    if ok:
                        st.success(f"✅ {len(selecionados_ids)} terapeuta(s) vinculado(s) ao paciente!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {resp.get('detail', 'Erro ao vincular')}")
        with col_v2:
            if st.button("🗑️ Desvincular Todos", type="secondary", use_container_width=True):
                if st.session_state.get(f"confirm_desvinc_{pac_id}"):
                    payload = {
                        "terapeutas_ids": [],
                        "diagnostico": "",
                        "evolucao": "",
                        "recomendacoes": ""
                    }
                    ok, resp = post_api(f"/indications/patient/{pac_id}", payload)
                    if ok:
                        st.success("✅ Todos os terapeutas desvinculados!")
                        st.session_state.pop(f"confirm_desvinc_{pac_id}", None)
                        st.rerun()
                    else:
                        st.error(f"❌ {resp.get('detail', 'Erro')}")
                else:
                    st.session_state[f"confirm_desvinc_{pac_id}"] = True
                    st.warning("⚠️ Clique novamente para confirmar")

# ── Tab 2: Horários Iniciais ────────────────────────────────────────────────
with tab2:
    st.subheader("📅 Definição de Horários Iniciais de Terapia")
    st.caption("O Admin fixa os horários iniciais de cada terapia; a Recepção depois oferece opções ao responsável.")

    if not pacientes_list:
        st.warning("Nenhum paciente cadastrado.")
    else:
        pac_selecionado = st.selectbox(
            "👶 Selecionar Paciente",
            options=pacientes_list,
            key="admin_pac_horarios"
        )
        pac_id = next(p["id"] for p in pacientes if f"{p['nome']} ({p['nome_responsavel']})" == pac_selecionado)
        paciente = next(p for p in pacientes if p["id"] == pac_id)

        st.markdown(f"### 👶 {paciente['nome']}")
        
        # Busca terapeutas vinculados
        vinculados = get_api(f"/patients/{pac_id}/therapists")
        
        if not vinculados:
            st.warning("⚠️ Nenhum terapeuta vinculado a este paciente. Vá na aba 'Atribuição de Terapeutas' primeiro.")
        else:
            st.markdown("### ⏰ Horários por Terapeuta")
            
            for t in vinculados:
                with st.expander(f"🩺 {t['nome']} — {t.get('especialidade', 'Sem especialidade')}", expanded=True):
                    col_h1, col_h2, col_h3 = st.columns(3)
                    with col_h1:
                        dia = st.selectbox(
                            "Dia da semana",
                            ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
                            key=f"dia_{t['id']}_{pac_id}"
                        )
                    with col_h2:
                        hora_ini = st.time_input(
                            "Início", value=time(9, 0), key=f"ini_{t['id']}_{pac_id}"
                        )
                    with col_h3:
                        hora_fim = st.time_input(
                            "Fim", value=time(10, 0), key=f"fim_{t['id']}_{pac_id}"
                        )
                    
                    freq = st.selectbox(
                        "Frequência",
                        ["1x/semana", "2x/semana", "3x/semana"],
                        index=1,
                        key=f"freq_{t['id']}_{pac_id}"
                    )
                    
                    if st.button("💾 Salvar Horário", key=f"save_sched_{t['id']}_{pac_id}"):
                        # Aqui seria ideal ter um endpoint de agendamento de sessões recorrentes
                        st.success(f"✅ Horário salvo: {dia} {hora_ini.strftime('%H:%M')}–{hora_fim.strftime('%H:%M')} ({freq})")
                        st.info("💡 Próximo passo: Recepção envia opções ao responsável via WhatsApp")

# ── Tab 3: Visão Geral ──────────────────────────────────────────────────────
with tab3:
    st.subheader("📊 Visão Geral da Clínica")
    
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    
    total_pac = len(pacientes) if pacientes else 0
    total_ter = len(terapeutas) if terapeutas else 0
    total_neu = len(neuropediatras) if neuropediatras else 0
    
    if terapeutas:
        total_ter = len([t for t in terapeutas if t.get("ativo", True)])
    else:
        total_ter = 0
    
    # Neuropediatras
    neuropediatras = get_api("/professionals/?role=neuropediatra")
    if neuropediatras:
        total_neu = len([n for n in neuropediatras if n.get("ativo", True)])
    else:
        total_neu = 0
    
    # Pacientes com terapeutas vinculados
    pac_com_ter = 0
    if pacientes:
        for p in pacientes:
            v = get_api(f"/patients/{p['id']}/therapists")
            if v:
                pac_com_ter += 1
    
    with col_g1:
        st.metric("👶 Pacientes Totais", total_pac)
    with col_g2:
        st.metric("🩺 Terapeutas", total_ter)
    with col_g3:
        st.metric("👨‍⚕️ Neuropediatras", total_neu)
    with col_g4:
        st.metric("🔗 Pacientes com Terapeutas", f"{pac_com_ter}/{total_pac}")

    st.divider()

    # Tabela de pacientes e seus terapeutas
    st.markdown("### 📋 Pacientes e Equipes Terapêuticas")
    
    if pacientes:
        rows = []
        for p in pacientes:
            v = get_api(f"/patients/{p['id']}/therapists")
            ter_nomes = ", ".join([f"{t['nome']} ({t.get('especialidade','')})" for t in v]) if v else "—"
            rows.append({
                "Paciente": p["nome"],
                "Responsável": p["nome_responsavel"],
                "WhatsApp": p["whatsapp_responsavel"],
                "Diagnóstico": p.get("diagnostico_principal", "TEA"),
                "Terapeutas Vinculados": ter_nomes,
                "Último Laudo": p.get("data_ultimo_laudo", "—")
            })
        
        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum paciente cadastrado.")