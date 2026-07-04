"""
TEO — Página: Agendamentos
Controle de consultas, confirmações automáticas do Neuropediatra e WhatsApp.
"""
import os
import httpx
import streamlit as st
import sys
from datetime import datetime

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


def patch_api(endpoint: str, data: dict) -> tuple[bool, dict]:
    try:
        import httpx
        r = httpx.patch(f"{BACKEND_URL}/api/v1{endpoint}", json=data, headers=get_auth_headers(), timeout=10)
        if r.status_code in [200, 201]:
            return True, r.json()
        else:
            st.error(f"❌ Erro na API PATCH {endpoint} (HTTP {r.status_code}): {r.text}")
            return False, {"detail": r.text}
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com API PATCH {endpoint}: {e}")
        return False, {"detail": str(e)}


st.markdown("## 📅 Agendamentos e Confirmações")
st.caption("Acompanhe o status dos convites de consultas enviados via WhatsApp e gerencie as agendas confirmadas.")

# Carrega pacientes para mapear ids para nomes
pacientes = get_api("/patients/")
pacientes_map = {p["id"]: p for p in pacientes} if pacientes else {}

# Carrega todos os agendamentos
agendamentos = get_api("/appointments/")

if not agendamentos:
    st.info("Nenhum agendamento registrado até o momento.")
else:
    tab1, tab2 = st.tabs(["⏳ Aguardando Resposta (Pendentes)", "✅ Agendas Confirmadas & Concluídas"])

    # Separa os agendamentos por status
    pendentes = [a for a in agendamentos if a["status"] == "pendente"]
    concluidos = [a for a in agendamentos if a["status"] != "pendente"]

    with tab1:
        st.subheader("Mensagens Enviadas (Neuropediatra)")
        st.caption("Consultas sugeridas automaticamente pelo TEO. Aguardando confirmação do responsável.")

        if not pendentes:
            st.success("✅ Nenhuma confirmação pendente no momento!")
        else:
            for a in pendentes:
                pac = pacientes_map.get(a["paciente_id"], {})
                pac_nome = pac.get("nome", "Paciente Desconhecido")
                resp_nome = pac.get("nome_responsavel", "—")
                whatsapp = pac.get("whatsapp_responsavel", "—")

                enviado_em_str = "Aguardando envio..."
                if a.get("alerta_enviado_em"):
                    try:
                        enviado_em_str = datetime.fromisoformat(a["alerta_enviado_em"]).strftime("%d/%m/%Y às %H:%M")
                    except Exception:
                        enviado_em_str = a["alerta_enviado_em"]

                op1_str = "—"
                if a.get("data_proposta_1"):
                    try:
                        op1_str = datetime.fromisoformat(a["data_proposta_1"]).strftime("%d/%m/%Y às %H:%M")
                    except Exception:
                        op1_str = a["data_proposta_1"]

                op2_str = "—"
                if a.get("data_proposta_2"):
                    try:
                        op2_str = datetime.fromisoformat(a["data_proposta_2"]).strftime("%d/%m/%Y às %H:%M")
                    except Exception:
                        op2_str = a["data_proposta_2"]

                with st.container(border=True):
                    col_info, col_opcoes, col_acoes = st.columns([3, 3, 2])
                    with col_info:
                        st.markdown(f"👶 **{pac_nome}**")
                        st.caption(f"Resp: {resp_nome} | 📱 {whatsapp}")
                        st.info(f"💬 **Notificação enviada em:** {enviado_em_str}")
                    with col_opcoes:
                        st.markdown("**Opções sugeridas:**")
                        st.markdown(f"1️⃣ {op1_str}")
                        st.markdown(f"2️⃣ {op2_str}")
                    with col_acoes:
                        # Apenas Recepção e Admin podem forçar confirmação
                        if get_role() in ["admin", "recepcao"]:
                            status_opcao = st.selectbox(
                                "Confirmar manual",
                                ["Manter Pendente", "Opção 1", "Opção 2", "Cancelado"],
                                key=f"sel_pend_{a['id']}"
                            )
                            if status_opcao != "Manter Pendente":
                                status_map = {
                                    "Opção 1": "confirmado_op1",
                                    "Opção 2": "confirmado_op2",
                                    "Cancelado": "cancelado"
                                }
                                data_conf = a["data_proposta_1"] if status_opcao == "Opção 1" else a["data_proposta_2"]
                                if status_opcao == "Cancelado":
                                    data_conf = None
                                
                                payload = {
                                    "status": status_map[status_opcao],
                                    "data_confirmada": data_conf
                                }
                                ok, resp = patch_api(f"/appointments/{a['id']}", payload)
                                if ok:
                                    st.success("Status atualizado!")
                                    st.rerun()

    with tab2:
        st.subheader("Histórico de Agendas Feitas")
        st.caption("Consultas confirmadas, reagendadas, canceladas ou já realizadas.")

        if not concluidos:
            st.info("Nenhum agendamento concluído ou confirmado.")
        else:
            for a in concluidos:
                pac = pacientes_map.get(a["paciente_id"], {})
                pac_nome = pac.get("nome", "Paciente Desconhecido")
                resp_nome = pac.get("nome_responsavel", "—")
                whatsapp = pac.get("whatsapp_responsavel", "—")

                status_colors = {
                    "confirmado_op1": "🟢 Confirmado (Opção 1)",
                    "confirmado_op2": "🟢 Confirmado (Opção 2)",
                    "realizado": "🔵 Realizado",
                    "reagendamento": "🟠 Reagendamento solicitado",
                    "cancelado": "🔴 Cancelado"
                }

                status_label = status_colors.get(a["status"], a["status"].capitalize())

                data_conf_str = "Sem data confirmada"
                if a.get("data_confirmada"):
                    try:
                        data_conf_str = datetime.fromisoformat(a["data_confirmada"]).strftime("%d/%m/%Y às %H:%M")
                    except Exception:
                        data_conf_str = a["data_confirmada"]

                with st.container(border=True):
                    col_info, col_detalhes, col_status = st.columns([3, 3, 2])
                    with col_info:
                        st.markdown(f"👶 **{pac_nome}**")
                        st.caption(f"Resp: {resp_nome} | 📱 {whatsapp}")
                        if a.get("resposta_pais"):
                            st.caption(f"💬 *Resposta dos pais:* \"{a['resposta_pais']}\"")
                    with col_detalhes:
                        st.markdown(f"📅 **Data Confirmada:**")
                        st.markdown(f"`{data_conf_str}`")
                    with col_status:
                        st.markdown(f"**Status:**")
                        if "confirmado" in a["status"]:
                            st.success(status_label)
                        elif a["status"] == "realizado":
                            st.info(status_label)
                        elif a["status"] == "reagendamento":
                            st.warning(status_label)
                        else:
                            st.error(status_label)

                        # Permitir marcar como realizado
                        if get_role() in ["admin", "recepcao"] and a["status"] in ["confirmado_op1", "confirmado_op2"]:
                            if st.button("Marcar como Realizado", key=f"btn_real_{a['id']}", use_container_width=True):
                                ok, resp = patch_api(f"/appointments/{a['id']}", {"status": "realizado"})
                                if ok:
                                    st.success("Consulta realizada!")
                                    st.rerun()
