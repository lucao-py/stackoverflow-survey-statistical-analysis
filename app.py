"""Dashboard narrativo: população, amostra e inferência no Survey 2025."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import gaussian_kde

from src.dados import carregar_dados, URL_DADOS
from src.visualizacoes import (
    AMOSTRA, POPULACAO, CONFIG_GRAFICOS, estilizar,
    grafico_ic_barras, grafico_decisao_testes,
)
from src.amostragem import dimensionar_amostra, selecionar_amostra
from src.estatisticas import (
    intervalo_proporcao, intervalo_media, teste_proporcao, teste_media
)

st.set_page_config(
    page_title="Stack Overflow | Análise Estatística",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

POP = POPULACAO

st.html("""
<style>
.st-key-painel_populacao, .st-key-painel_amostra,
.st-key-painel_ic_proporcao, .st-key-painel_ic_media,
.st-key-dimensionamento {
    background: #151C25;
    border-color: #293442;
    border-radius: 12px;
}
.st-key-painel_populacao [data-testid="stMetricValue"],
.st-key-painel_amostra [data-testid="stMetricValue"] {
    font-size: clamp(1.25rem, 2.5vw, 2rem);
    font-variant-numeric: tabular-nums;
    line-height: 1.3;
}
</style>
""")


def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor * 100, 2)}%"


def p_texto(valor):
    return "< 0,0001" if valor < 0.0001 else num(valor, 4)


IA_LABELS = {
    "Yes, I use AI tools daily": "Diariamente",
    "Yes, I use AI tools weekly": "Semanalmente",
    "Yes, I use AI tools monthly or infrequently": "Ocasionalmente",
    "No, but I plan to soon": "Pretende utilizar",
    "No, and I don't plan to": "Não pretende",
}



@st.cache_data(show_spinner=False)
def curva_distribuicao(serie):
    """Curva KDE na escala percentual de um histograma de classes de 4 anos."""
    valores = serie.dropna().astype(float).to_numpy()
    eixo = np.linspace(0, 100, 400)
    densidade = gaussian_kde(valores)(eixo)
    return eixo, densidade * 400


def painel_descritivo(base, titulo, cor):
    experiencia = base["WorkExp"].dropna()
    ia = base["AISelect"].dropna()

    chave = "populacao" if titulo == "População" else "amostra"
    with st.container(border=True, key=f"painel_{chave}"):
        st.subheader(titulo)
        c1, c2 = st.columns(2)
        c1.metric("Respondentes", num(len(base)))
        c2.metric("Utilizam IA", pct(ia.str.startswith("Yes").mean()))
        c3, c4 = st.columns(2)
        c3.metric("Experiência média", f"{num(experiencia.mean(), 2)} anos")
        c4.metric("Mediana", f"{num(experiencia.median(), 1)} anos")

        st.markdown("**Distribuição da experiência profissional**")
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=experiencia,
            xbins=dict(start=0, end=104, size=4),
            histnorm="percent", marker_color=cor,
            opacity=0.28, name="Histograma",
            hovertemplate="%{y:.2f}% no intervalo<extra></extra>",
        ))
        eixo, curva = curva_distribuicao(experiencia)
        fig.add_trace(go.Scatter(
            x=eixo, y=curva, mode="lines",
            name="Curva KDE",
            line=dict(color=cor, width=3),
            hovertemplate=(
                "<b>Curva de distribuição (KDE)</b><br>"
                "%{x:.0f} anos: %{y:.2f}%<extra></extra>"
            ),
        ))
        fig.update_layout(
            xaxis_title="Anos de experiência",
            yaxis_title="% por intervalo de 4 anos",
            xaxis_range=[0, 50],
            legend=dict(orientation="h", x=0, y=1.12),
        )
        st.plotly_chart(
            estilizar(fig, 340, legenda=True), width="stretch",
            theme=None, config=CONFIG_GRAFICOS,
        )

        st.markdown("**Frequência de utilização de IA**")
        frequencias = (
            base["AISelect"]
            .fillna("Sem resposta")
            .replace(IA_LABELS)
            .value_counts(normalize=True)
            .mul(100)
        )
        ordem = [*IA_LABELS.values(), "Sem resposta"]
        porcentagens = frequencias.reindex(ordem, fill_value=0)
        fig = go.Figure(go.Bar(
            x=porcentagens.values,
            y=ordem, orientation="h", marker_color=cor,
            text=[f"\u2002{num(valor, 1)}%" for valor in porcentagens.values],
            textposition="outside",
            textfont=dict(color="#E5E7EB", size=12),
            cliponaxis=False,
            hovertemplate="%{x:.1f}%<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="% do total de respondentes",
            xaxis_range=[0, max(10, float(porcentagens.max()) * 1.28)],
            yaxis=dict(categoryorder="array", categoryarray=list(reversed(ordem))),
        )
        st.plotly_chart(
            estilizar(fig, 280, legenda=False), width="stretch",
            theme=None, config=CONFIG_GRAFICOS,
        )


def mostrar_ic(titulo, ic, populacao, percentual, formula):
    """Exibe as barras horizontais no formato da referência, sem cards de KPIs."""
    chave = "proporcao" if percentual else "media"
    with st.container(border=True, key=f"painel_ic_{chave}"):
        st.markdown(f"#### {titulo}")
        st.plotly_chart(
            grafico_ic_barras(ic, populacao, percentual=percentual),
            width="stretch", theme=None, config=CONFIG_GRAFICOS,
            key=f"grafico_ic_{chave}",
            alt=f"Comparação populacional e IC de {titulo}",
        )
        escala = 100 if percentual else 1
        unidade = "%" if percentual else " anos"
        st.caption(
            f"IC 95%: {num(ic['inferior'] * escala, 2)} a "
            f"{num(ic['superior'] * escala, 2)}{unidade}"
            f" · Amplitude: {num((ic['superior'] - ic['inferior']) * escala, 2)}"
            f"{' p.p.' if percentual else ' anos'}"
        )
        st.latex(formula)


# Dados e seleção amostral.
df = carregar_dados()
plano = dimensionar_amostra(df)
amostra = selecionar_amostra(df, plano["n_ajustado"], seed=42)

ia_pop, ia_amostra = df["AISelect"].dropna(), amostra["AISelect"].dropna()
exp_pop = df["WorkExp"].dropna()

p_pop = ia_pop.str.startswith("Yes").mean()
ic_ia = intervalo_proporcao(
    int(ia_amostra.str.startswith("Yes").sum()),
    len(ia_amostra), len(ia_pop),
)
ic_exp = intervalo_media(amostra["WorkExp"], len(exp_pop))

# Introdução e identificação do estudo.
st.caption("STACK OVERFLOW DEVELOPER SURVEY · 2025 / ESTATÍSTICA APLICADA")
st.title("Amostragem e inferência estatística")
st.write(
    "Análise descritiva da população e de uma amostra aleatória simples, "
    "com intervalos de confiança e testes de hipóteses."
)
st.caption("01 Dimensionamento  ·  02 População × amostra  ·  03 Inferência")
st.divider()


# CAPÍTULO 1 — somente cálculo da amostra.
st.header("01 / Dimensionamento da amostra")
a, b, c, d = st.columns(4)
a.metric("População (N)", num(plano["N"]), border=True)
b.metric("Amostra inicial (n₀)", num(plano["n0"], 2), border=True)
c.metric("Amostra calculada", num(plano["n_final"]), border=True)
d.metric("Amostra ajustada", num(plano["n_ajustado"]), border=True)

with st.container(border=True, key="dimensionamento"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Fórmula inicial**")
        st.latex(r"n_0=\frac{Z^2p(1-p)}{E^2}")
        st.caption("Z = 1,96 · p = 0,50 · E = 0,05")
    with c2:
        st.markdown("**2. Correção finita**")
        st.latex(r"n=\frac{N n_0}{N+n_0-1}")
        st.caption(f"n = {num(plano['n_corrigido'], 2)} → {num(plano['n_final'])}")
    with c3:
        st.markdown("**3. Ajuste por respostas válidas**")
        st.latex(r"n_{\mathrm{aj}}=\left\lceil\frac{n}{r_{IA}}\right\rceil")
        st.caption(
            f"rIA = {pct(plano['taxa_validas'])} · "
            f"n ajustado = {num(plano['n_ajustado'])}"
        )

st.divider()



# CAPÍTULO 2 — estrutura comparativa original: dois painéis completos.
st.header("02 / População × amostra")
col_pop, col_amostra = st.columns(2)
with col_pop:
    painel_descritivo(df, "População", POP)
with col_amostra:
    painel_descritivo(amostra, "Amostra", AMOSTRA)
st.divider()



# CAPÍTULO 3 — destaque visual e fórmulas dos intervalos.
st.header("03 / Inferência estatística")
st.subheader("Intervalos de confiança · 95%")

mostrar_ic(
    "Proporção que utiliza IA", ic_ia, p_pop, True,
    r"IC_p=\hat p\ \pm\ z_{0{,}975}"
    r"\sqrt{\frac{\hat p(1-\hat p)}{n}\cdot\frac{N-n}{N-1}}",
)
mostrar_ic(
    "Média de experiência profissional", ic_exp, exp_pop.mean(), False,
    r"IC_\mu=\bar x\ \pm\ t_{0{,}975;\,n-1}"
    r"\frac{s}{\sqrt n}\sqrt{\frac{N-n}{N-1}}",
)

st.divider()
st.subheader("Testes de hipóteses")
st.caption("Significância de 5% · duas proporções e duas médias")

p1 = teste_proporcao(
    int(ia_amostra.str.startswith("Yes").sum()), len(ia_amostra), len(ia_pop), p0=.75
)
p2 = teste_proporcao(
    int((ia_amostra == "Yes, I use AI tools daily").sum()),
    len(ia_amostra), len(ia_pop), p0=.40
)
m1 = teste_media(amostra["WorkExp"], len(exp_pop), mu0=10, alternativa="maior")
m2 = teste_media(amostra["WorkExp"], len(exp_pop), mu0=15, alternativa="diferente")


testes = [
    {
        "nome": "Uso de IA acima de 75%",
        "h0": "p ≤ 0,75", "h1": "p > 0,75",
        "metodo": "Z", "estatistica": p1["z"],
        "valor_p": p1["valor_p"], "rejeitar": p1["rejeitar_h0"],
    },
    {
        "nome": "Uso diário acima de 40%",
        "h0": "p ≤ 0,40", "h1": "p > 0,40",
        "metodo": "Z", "estatistica": p2["z"],
        "valor_p": p2["valor_p"], "rejeitar": p2["rejeitar_h0"],
    },
    {
        "nome": "Experiência média acima de 10",
        "h0": "μ ≤ 10", "h1": "μ > 10",
        "metodo": "t", "estatistica": m1["t"],
        "valor_p": m1["valor_p"], "rejeitar": m1["rejeitar_h0"],
    },
    {
        "nome": "Experiência média diferente de 15",
        "h0": "μ = 15", "h1": "μ ≠ 15",
        "metodo": "t", "estatistica": m2["t"],
        "valor_p": m2["valor_p"], "rejeitar": m2["rejeitar_h0"],
    },
]

st.plotly_chart(
    grafico_decisao_testes(testes), width="stretch", theme=None,
    config=CONFIG_GRAFICOS, key="grafico_decisao_testes",
    alt="Quatro testes de hipóteses, valores-p e decisões",
)

st.divider()
st.caption(
    "Fonte: [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/) "
    f"· [Dados utilizados]({URL_DADOS})"
)
