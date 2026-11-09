
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.dados import carregar_dados
from src.amostragem import dimensionar_amostra, selecionar_amostra
from src.estatisticas import (intervalo_proporcao,intervalo_media,teste_proporcao, teste_media)

st.set_page_config(
    page_title="Stack Overflow | Statistical Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

df = carregar_dados()
parametros = dimensionar_amostra(df)
amostra = selecionar_amostra(df, parametros["n_ajustado"])


# --------------------------------------------------
# Funções de visualização
# --------------------------------------------------

def configurar_grafico(fig, altura=280):
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        margin=dict(l=5, r=5, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    return fig


def painel_descritivo(base, titulo, cor):
    with st.container(border=True):
        st.subheader(titulo)

        exp = base["WorkExp"].dropna()
        ia = base["AISelect"].dropna()

        c1, c2 = st.columns(2)
        c1.metric("Respondentes", f"{len(base):,}")
        c2.metric("Utilizam IA", f"{ia.str.startswith('Yes').mean():.2%}")

        c3, c4 = st.columns(2)
        c3.metric("Experiência média", f"{exp.mean():.2f} anos")
        c4.metric("Mediana", f"{exp.median():.1f} anos")

        st.markdown("**Experiência profissional**")

        fig = px.histogram(
            base,
            x="WorkExp",
            nbins=25,
            range_x=[0, 100],
            histnorm="percent",
            labels={"WorkExp": "Anos de experiência"},
        )
        fig.update_traces(marker_color=cor)
        fig.update_layout(yaxis_title="% das respostas válidas")
        st.plotly_chart(configurar_grafico(fig), width="stretch")

        st.markdown("**Frequência de utilização de IA**")

        categorias = {
            "Yes, I use AI tools daily": "Diariamente",
            "Yes, I use AI tools weekly": "Semanalmente",
            "Yes, I use AI tools monthly or infrequently": "Ocasionalmente",
            "No, but I plan to soon": "Pretende utilizar",
            "No, and I don't plan to": "Não pretende"
        }

        dados_ia = (
            base["AISelect"]
            .fillna("Sem resposta")
            .replace(categorias)
            .value_counts(normalize=True)
            .mul(100)
            .rename_axis("Resposta")
            .reset_index(name="Percentual")
        )

        fig = px.bar(
            dados_ia,
            x="Percentual",
            y="Resposta",
            orientation="h",
            labels={"Percentual": "% dos respondentes"},
        )
        fig.update_traces(marker_color=cor)
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(configurar_grafico(fig), width="stretch")

        st.caption(
            f"IA: {len(ia)} respostas válidas · "
            f"Experiência: {len(exp)} respostas válidas · "
            f"Desvio-padrão: {exp.std():.2f} anos"
        )

        with st.expander("Explorar idade e países"):
            idade = (
                base["Age"]
                .value_counts(normalize=True)
                .mul(100)
                .rename_axis("Faixa")
                .reset_index(name="Percentual")
            )

            fig = px.bar(
                idade,
                x="Percentual",
                y="Faixa",
                orientation="h",
            )
            fig.update_traces(marker_color=cor)
            st.plotly_chart(configurar_grafico(fig, 330), width="stretch")

            paises = (
                base["Country"]
                .value_counts()
                .head(8)
                .rename_axis("País")
                .reset_index(name="Respondentes")
            )

            fig = px.bar(
                paises,
                x="Respondentes",
                y="País",
                orientation="h",
            )
            fig.update_traces(marker_color=cor)
            st.plotly_chart(configurar_grafico(fig, 300), width="stretch")


def grafico_intervalo(estimativa, inferior, superior, populacao):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[inferior, superior],
        y=[0, 0],
        mode="lines",
        line=dict(color="#2DD4BF", width=10),
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=[estimativa],
        y=[0],
        mode="markers",
        marker=dict(
            color="#F8FAFC",
            size=15,
            line=dict(color="#2DD4BF", width=3)
        ),
        hovertemplate="Estimativa: %{x:.2f}<extra></extra>"
    ))

    fig.add_vline(
        x=populacao,
        line_dash="dash",
        line_color="#FBBF24",
        line_width=2
    )

    minimo = min(inferior, populacao)
    maximo = max(superior, populacao)
    margem_visual = max((maximo - minimo) * 0.2, 0.1)

    fig.update_layout(
        height=165,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[
            minimo - margem_visual,
            maximo + margem_visual
        ]),
        yaxis=dict(visible=False, range=[-0.5, 0.5]),
    )

    return configurar_grafico(fig, 165)


# --------------------------------------------------
# Cabeçalho
# --------------------------------------------------

st.caption("STACK OVERFLOW DEVELOPER SURVEY · 2025")
st.title("Análise Estatística dos Desenvolvedores")
st.write(
    "População, amostragem aleatória simples e inferência "
    "sobre experiência profissional e utilização de IA."
)

c1, c2, c3 = st.columns(3)
c1.metric("População", f"{len(df):,}", border=True)
c2.metric("Amostra AAS", f"{len(amostra):,}", border=True)
c3.metric("Nível de confiança", "95%", border=True)

st.divider()


# --------------------------------------------------
# Painéis 1 e 2 — Análise descritiva
# --------------------------------------------------

st.header("Análise descritiva")
st.caption("População completa e amostra aleatória, lado a lado.")

col_pop, col_amostra = st.columns(2)

with col_pop:
    painel_descritivo(df, "01 / População", "#64748B")

with col_amostra:
    painel_descritivo(amostra, "02 / Amostra", "#2DD4BF")

st.divider()


# --------------------------------------------------
# Painel 3 — Inferência estatística
# --------------------------------------------------

st.header("03 / Inferência estatística")
st.caption(
    "Intervalos de confiança de 95%, calculados com "
    "as respostas válidas da amostra."
)

ia_pop = df["AISelect"].dropna()
ia_amostra = amostra["AISelect"].dropna()

p_pop = ia_pop.str.startswith("Yes").mean()

ic_ia = intervalo_proporcao(
    sucessos=ia_amostra.str.startswith("Yes").sum(),
    n=len(ia_amostra),
    N=len(ia_pop)
)

exp_pop = df["WorkExp"].dropna()

ic_exp = intervalo_media(
    valores=amostra["WorkExp"],
    N=len(exp_pop)
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### Proporção de usuários de IA")
        st.metric(
            "Estimativa amostral",
            f"{ic_ia['estimativa']:.2%}"
        )
        st.plotly_chart(
            grafico_intervalo(
                ic_ia["estimativa"] * 100,
                ic_ia["inferior"] * 100,
                ic_ia["superior"] * 100,
                p_pop * 100
            ),
            width="stretch"
        )
        st.write(
            f"**IC 95%:** {ic_ia['inferior']:.2%} "
            f"a {ic_ia['superior']:.2%}"
        )
        st.caption(
            f"Parâmetro populacional: {p_pop:.2%} "
            f"· n válido: {ic_ia['n']}"
        )

with col2:
    with st.container(border=True):
        st.markdown("#### Média de experiência profissional")
        st.metric(
            "Estimativa amostral",
            f"{ic_exp['estimativa']:.2f} anos"
        )
        st.plotly_chart(
            grafico_intervalo(
                ic_exp["estimativa"],
                ic_exp["inferior"],
                ic_exp["superior"],
                exp_pop.mean()
            ),
            width="stretch"
        )
        st.write(
            f"**IC 95%:** {ic_exp['inferior']:.2f} "
            f"a {ic_exp['superior']:.2f} anos"
        )
        st.caption(
            f"Parâmetro populacional: {exp_pop.mean():.2f} anos "
            f"· n válido: {ic_exp['n']}"
        )

st.caption(
    "Legenda: verde = intervalo de confiança · "
    "ponto branco = estimativa amostral · "
    "linha amarela = parâmetro populacional."
)

st.info(
    "Próxima etapa: testes de hipóteses para "
    "duas proporções e duas médias."
)

st.caption(
    "Fonte: Stack Overflow Developer Survey 2025. "
    "A inferência é condicionada às respostas válidas "
    "de cada variável."
)

# --------------------------------------------------
# Testes de hipóteses
# --------------------------------------------------

st.subheader("Testes de hipóteses")
st.caption("Nível de significância: 5% | Análises exploratórias")

# 1. Proporção de usuários de IA > 75%
teste_p1 = teste_proporcao(
    sucessos=ia_amostra.str.startswith("Yes").sum(),
    n=len(ia_amostra),
    N=len(ia_pop),
    p0=0.75
)

# 2. Proporção de usuários diários > 40%
teste_p2 = teste_proporcao(
    sucessos=(ia_amostra == "Yes, I use AI tools daily").sum(),
    n=len(ia_amostra),
    N=len(ia_pop),
    p0=0.40
)

# 3. Experiência média > 10 anos
teste_m1 = teste_media(
    valores=amostra["WorkExp"],
    N=len(exp_pop),
    mu0=10,
    alternativa="maior"
)

# 4. Experiência média diferente de 15 anos
teste_m2 = teste_media(
    valores=amostra["WorkExp"],
    N=len(exp_pop),
    mu0=15,
    alternativa="diferente"
)

testes = [
    {
        "Teste": "Uso de IA",
        "H₀": "p ≤ 75%",
        "H₁": "p > 75%",
        "Estatística": teste_p1["z"],
        "Valor-p": teste_p1["valor_p"],
        "Rejeitar": teste_p1["rejeitar_h0"],
        "Método": "Z"
    },
    {
        "Teste": "Uso diário de IA",
        "H₀": "p ≤ 40%",
        "H₁": "p > 40%",
        "Estatística": teste_p2["z"],
        "Valor-p": teste_p2["valor_p"],
        "Rejeitar": teste_p2["rejeitar_h0"],
        "Método": "Z"
    },
    {
        "Teste": "Experiência > 10",
        "H₀": "μ ≤ 10",
        "H₁": "μ > 10",
        "Estatística": teste_m1["t"],
        "Valor-p": teste_m1["valor_p"],
        "Rejeitar": teste_m1["rejeitar_h0"],
        "Método": "t"
    },
    {
        "Teste": "Experiência ≠ 15",
        "H₀": "μ = 15",
        "H₁": "μ ≠ 15",
        "Estatística": teste_m2["t"],
        "Valor-p": teste_m2["valor_p"],
        "Rejeitar": teste_m2["rejeitar_h0"],
        "Método": "t"
    }
]

import pandas as pd

resultado_testes = pd.DataFrame(testes)

resultado_testes["Conclusão"] = resultado_testes["Rejeitar"].map(
    {True: "Rejeita H₀", False: "Não rejeita H₀"}
)

resultado_testes["Estatística"] = resultado_testes[
    "Estatística"
].map(lambda x: f"{x:.3f}")

resultado_testes["Valor-p"] = resultado_testes[
    "Valor-p"
].map(lambda x: f"{x:.4g}")

st.dataframe(
    resultado_testes[
        ["Teste", "Método", "H₀", "H₁",
         "Estatística", "Valor-p", "Conclusão"]
    ],
    hide_index=True,
    width="stretch"
)

st.caption(
    "As decisões consideram α = 0,05 individualmente. "
    "Não rejeitar H₀ não significa comprovar que ela é verdadeira."
)
