"""Dashboard narrativo: população, amostra e inferência no Survey 2025."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import gaussian_kde

from src.dados import carregar_dados, URL_DADOS
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

POP, AMOSTRA, REAL = "#94A3B8", "#2DD4BF", "#FBBF24"


def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor * 100, 2)}%"


def p_texto(valor):
    return "< 0,0001" if valor < 0.0001 else num(valor, 4)


def estilizar(fig, altura=300, legenda=True):
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        margin=dict(l=5, r=12, t=22, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legenda,
        legend=dict(orientation="h", y=1.16),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)")
    fig.update_yaxes(showgrid=False)
    return fig



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

    with st.container(border=True):
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
            name="Curva de distribuição (KDE)",
            line=dict(color=cor, width=3),
            hovertemplate="%{x:.0f} anos: %{y:.2f}%<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="Anos de experiência",
            yaxis_title="% por intervalo de 4 anos",
            xaxis_range=[0, 50],
            legend=dict(orientation="h", x=0, y=1.12),
        )
        st.plotly_chart(estilizar(fig, 320, legenda=True), width="stretch")
        st.caption("Curva suavizada · recorte visual até 50 anos; métricas usam todos os valores.")

        st.markdown("**Frequência de utilização de IA**")
        frequencias = (
            base["AISelect"]
            .fillna("Sem resposta")
            .replace(IA_LABELS)
            .value_counts(normalize=True)
            .mul(100)
        )
        ordem = [*IA_LABELS.values(), "Sem resposta"]
        fig = go.Figure(go.Bar(
            x=frequencias.reindex(ordem, fill_value=0).values,
            y=ordem, orientation="h", marker_color=cor,
            hovertemplate="%{x:.1f}%<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="% do total de respondentes",
            yaxis=dict(categoryorder="array", categoryarray=list(reversed(ordem))),
        )
        st.plotly_chart(estilizar(fig, 280, legenda=False), width="stretch")
        st.caption(
            f"IA: {num(len(ia))} respostas válidas · "
            f"Experiência: {num(len(experiencia))} válidas · "
            f"Desvio-padrão: {num(experiencia.std(), 2)} anos"
        )

        with st.expander("Explorar idade e países"):
            idades = [
                "Under 18 years old", "18-24 years old", "25-34 years old",
                "35-44 years old", "45-54 years old", "55-64 years old",
                "65 years or older", "Prefer not to say",
            ]
            idade = base["Age"].value_counts(normalize=True).mul(100)
            fig = go.Figure(go.Bar(
                x=idade.reindex(idades, fill_value=0).values,
                y=idades, orientation="h", marker_color=cor,
            ))
            fig.update_layout(
                xaxis_title="% das respostas válidas",
                yaxis=dict(categoryorder="array", categoryarray=list(reversed(idades))),
            )
            st.plotly_chart(estilizar(fig, 315, legenda=False), width="stretch")

            paises = base["Country"].value_counts().head(8)
            fig = go.Figure(go.Bar(
                x=paises.values, y=paises.index, orientation="h", marker_color=cor,
            ))
            fig.update_layout(
                xaxis_title="Respondentes",
                yaxis=dict(categoryorder="total ascending"),
            )
            st.plotly_chart(estilizar(fig, 280, legenda=False), width="stretch")



def grafico_intervalo(ic, populacao, escala):
    """Barra horizontal flutuante: o preenchimento é exatamente o IC."""
    li = ic["inferior"] * escala
    ponto = ic["estimativa"] * escala
    ls = ic["superior"] * escala
    referencia = populacao * escala
    amplitude = ls - li

    # Escala aproximada para distinguir claramente os dois extremos.
    folga = max(amplitude * 0.5, 1 if escala == 100 else 0.3)
    x_min, x_max = min(li, referencia) - folga, max(ls, referencia) + folga
    unidade = "%" if escala == 100 else " anos"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[amplitude], base=[li], y=[0], orientation="h", width=0.36,
        marker=dict(color=AMOSTRA, line=dict(color=AMOSTRA, width=2)),
        name="Intervalo de 95%",
        customdata=[[li, ponto, ls]],
        hovertemplate=(
            "IC 95%: %{customdata[0]:.2f} a %{customdata[2]:.2f}"
            "<br>Estimativa: %{customdata[1]:.2f}<extra></extra>"
        ),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[ponto], y=[0], mode="markers",
        marker=dict(symbol="diamond", size=17, color="white",
                    line=dict(color="#0E1117", width=2)),
        hovertemplate="Estimativa: %{x:.2f}<extra></extra>",
        showlegend=False,
    ))
    fig.add_vline(x=referencia, line_color=REAL, line_dash="dash", line_width=3)

    # Extremidades com marcas e valores explícitos, sem depender do hover.
    for extremo, ancora in [(li, "right"), (ls, "left")]:
        fig.add_trace(go.Scatter(
            x=[extremo, extremo], y=[-0.23, 0.23],
            mode="lines", line=dict(color="#E5E7EB", width=3),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_annotation(
            x=extremo, y=0.44,
            text=f"<b>{num(extremo, 2)}{unidade}</b>",
            xanchor=ancora, showarrow=False,
            font=dict(size=15, color="#E5E7EB"),
        )
    fig.add_annotation(
        x=ponto, y=-0.47, text=f"Estimativa: {num(ponto, 2)}{unidade}",
        showarrow=False, font=dict(size=13, color="#E5E7EB"),
    )
    fig.update_layout(
        xaxis=dict(
            title="Proporção (%)" if escala == 100 else "Experiência (anos)",
            range=[x_min, x_max],
            ticksuffix="%" if escala == 100 else "",
            tickfont=dict(size=13), zeroline=False,
        ),
        yaxis=dict(
            range=[-0.85, 0.85], tickvals=[0], ticktext=["IC 95%"],
            showgrid=False,
        ),
        margin=dict(l=38, r=30, t=12, b=22),
    )
    return estilizar(fig, 310, legenda=False)


def painel_intervalo(titulo, ic, parametro, escala, formula):
    fmt = pct if escala == 100 else lambda v: f"{num(v, 2)} anos"
    largura = ic["superior"] - ic["inferior"]
    margem = largura / 2
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        st.plotly_chart(
            grafico_intervalo(ic, parametro, escala), width="stretch"
        )

        a, b, c = st.columns(3)
        a.metric("Limite inferior", fmt(ic["inferior"]))
        b.metric("Estimativa amostral", fmt(ic["estimativa"]))
        c.metric("Limite superior", fmt(ic["superior"]))
        if escala == 100:
            st.caption(
                f"Amplitude do IC: {num(largura * 100, 2)} p.p. "
                f"· margem de erro: ±{num(margem * 100, 2)} p.p."
            )
        else:
            st.caption(
                f"Amplitude do IC: {num(largura, 2)} anos "
                f"· margem de erro: ±{num(margem, 2)} anos"
            )
        st.caption(
            f"Barra verde = IC 95% · losango branco = estimativa · "
            f"linha amarela = população ({fmt(parametro)}) · "
            f"n válido = {num(ic['n'])}"
        )
        st.latex(formula)


def painel_teste(numero, titulo, metodo, h0, h1, referencia, estimativa, resultado, conclusao):
    valor_p = resultado["valor_p"]
    rejeita = resultado["rejeitar_h0"]
    estat = resultado["z"] if metodo == "Z" else resultado["t"]
    with st.container(border=True):
        st.caption(f"TESTE {numero} · {metodo}")
        st.markdown(f"#### {titulo}")
        a, b, c = st.columns(3)
        a.metric("Estimativa", estimativa)
        b.metric("Referência", referencia)
        c.metric("Valor-p", p_texto(valor_p))
        st.markdown(f"**H₀:** {h0}　　**H₁:** {h1}")
        st.caption(
            f"Estatística {metodo} = {num(estat, 3)} · α = 0,05"
        )
        st.markdown(
            f"**{'Rejeitamos' if rejeita else 'Não rejeitamos'} H₀.** {conclusao}"
        )


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

# Introdução: pergunta que organiza a narrativa do vídeo.
st.caption("STACK OVERFLOW DEVELOPER SURVEY · 2025 / ESTATÍSTICA APLICADA")
st.title(
    f"O que {num(len(amostra))} respondentes revelam sobre uma população de "
    f"{num(len(df))}?"
)
st.write(
    "Um estudo de amostragem aleatória, análise descritiva, "
    "intervalos de confiança e testes de hipóteses."
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

with st.container(border=True):
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

painel_intervalo(
    "Proporção que utiliza IA", ic_ia, p_pop, 100,
    r"IC_p=\hat p\ \pm\ z_{0{,}975}"
    r"\sqrt{\frac{\hat p(1-\hat p)}{n}\cdot\frac{N-n}{N-1}}",
)
painel_intervalo(
    "Média de experiência profissional", ic_exp, exp_pop.mean(), 1,
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

a, b = st.columns(2)
with a:
    painel_teste(
        "01", "Uso de IA > 75%?", "Z", "p ≤ 75%", "p > 75%",
        "75%", pct(p1["proporcao"]), p1,
        ("Há evidência de uso superior a 75%." if p1["rejeitar_h0"]
         else "Evidência insuficiente de uso superior a 75%."),
    )
with b:
    painel_teste(
        "02", "Uso diário de IA > 40%?", "Z", "p ≤ 40%", "p > 40%",
        "40%", pct(p2["proporcao"]), p2,
        ("Há evidência de uso diário superior a 40%." if p2["rejeitar_h0"]
         else "Evidência insuficiente de uso diário superior a 40%."),
    )

a, b = st.columns(2)
with a:
    painel_teste(
        "03", "Experiência média > 10 anos?", "t", "μ ≤ 10", "μ > 10",
        "10 anos", f"{num(m1['estimativa'], 2)} anos", m1,
        ("Há evidência de média superior a 10 anos." if m1["rejeitar_h0"]
         else "Evidência insuficiente de média superior a 10 anos."),
    )
with b:
    painel_teste(
        "04", "Experiência média ≠ 15 anos?", "t", "μ = 15", "μ ≠ 15",
        "15 anos", f"{num(m2['estimativa'], 2)} anos", m2,
        ("Há evidência de média diferente de 15 anos." if m2["rejeitar_h0"]
         else "Evidência insuficiente de média diferente de 15 anos."),
    )

st.divider()
st.caption(
    "Fonte: [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/) "
    f"· [Dados utilizados]({URL_DADOS})"
)
