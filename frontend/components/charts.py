"""
TEO — Frontend Streamlit | Componentes de Gráficos
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st


def grafico_evolucoes_por_mes(evolucoes: list) -> None:
    """Exibe gráfico de barras de sessões por mês."""
    if not evolucoes:
        st.info("Nenhuma sessão registrada ainda.")
        return

    df = pd.DataFrame(evolucoes)
    df["data_sessao"] = pd.to_datetime(df["data_sessao"])
    df["mes"] = df["data_sessao"].dt.to_period("M").astype(str)
    contagem = df.groupby("mes").size().reset_index(name="sessoes")

    fig = px.bar(
        contagem,
        x="mes",
        y="sessoes",
        title="📊 Sessões por Mês",
        color="sessoes",
        color_continuous_scale=["#BEE3F8", "#4A90B8", "#2C6E9C"],
        labels={"mes": "Mês", "sessoes": "Nº de Sessões"}
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)


def grafico_tipos_sessao(evolucoes: list) -> None:
    """Pizza com distribuição por tipo de sessão."""
    if not evolucoes:
        return

    df = pd.DataFrame(evolucoes)
    tipos = df["tipo_sessao"].fillna("Não informado")
    contagem = tipos.value_counts().reset_index()
    contagem.columns = ["tipo", "quantidade"]

    colors = ["#4A90B8", "#6CBF8A", "#F6AD55", "#FC8181", "#9F7AEA", "#76E4F7"]
    fig = px.pie(
        contagem,
        names="tipo",
        values="quantidade",
        title="🏥 Distribuição por Tipo de Terapia",
        color_discrete_sequence=colors
    )
    fig.update_layout(
        font_family="Inter",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def gauge_laudo_status(dias_desde_laudo: int, limite: int = 150) -> None:
    """Gauge mostrando status do laudo (urgência)."""
    percentual = min(100, (dias_desde_laudo / 180) * 100)

    if dias_desde_laudo < 120:
        cor = "#6CBF8A"
        status = "✅ Em dia"
    elif dias_desde_laudo < 150:
        cor = "#F6AD55"
        status = "⚠️ Atenção"
    else:
        cor = "#FC8181"
        status = "🚨 Vencendo"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=dias_desde_laudo,
        delta={"reference": limite, "valueformat": ".0f"},
        number={"suffix": " dias", "font": {"size": 24}},
        title={"text": f"Status do Laudo<br><span style='font-size:14px'>{status}</span>"},
        gauge={
            "axis": {"range": [0, 180], "ticksuffix": "d"},
            "bar": {"color": cor},
            "steps": [
                {"range": [0, 120], "color": "#F0FFF4"},
                {"range": [120, 150], "color": "#FFFBEB"},
                {"range": [150, 180], "color": "#FFF5F5"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 3},
                "thickness": 0.75,
                "value": limite
            }
        }
    ))
    fig.update_layout(
        height=220,
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter"
    )
    st.plotly_chart(fig, use_container_width=True)


def timeline_sessoes(evolucoes: list) -> None:
    """Timeline horizontal das sessões."""
    if not evolucoes:
        return

    df = pd.DataFrame(evolucoes)
    df["data_sessao"] = pd.to_datetime(df["data_sessao"])
    df["tipo_sessao"] = df["tipo_sessao"].fillna("Não informado")

    fig = px.scatter(
        df,
        x="data_sessao",
        y="tipo_sessao",
        color="tipo_sessao",
        title="📅 Timeline de Sessões",
        labels={"data_sessao": "Data", "tipo_sessao": "Tipo"},
        size_max=10,
    )
    fig.update_traces(marker=dict(size=12, symbol="circle"))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        showlegend=False,
        xaxis={"showgrid": True, "gridcolor": "#E2E8F0"},
        yaxis={"showgrid": False}
    )
    st.plotly_chart(fig, use_container_width=True)
