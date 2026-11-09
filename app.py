"""Dashboard narrativo: população, amostra e inferência no Survey 2025."""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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


def histograma_comparativo(populacao, amostra):
    fig = go.Figure()
    for titulo, base, cor in [
        ("População", populacao, POP),
        ("Amostra", amostra, AMOSTRA),
    ]:
        fig.add_trace(go.Histogram(
            x=base["WorkExp"].dropna(),
            name=titulo,
            histnorm="percent",
            xbins=dict(start=0, end=105, size=5),
            marker_color=cor,
            opacity=0.72,
            hovertemplate=f"{titulo}: %{{y:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="overlay",
        xaxis_title="Anos de experiência (intervalos de 5)",
        yaxis_title="% das respostas válidas",
    )
    return estilizar(fig, 320)


IA_LABELS = {
    "Yes, I use AI tools daily": "Diariamente",
    "Yes, I use AI tools weekly": "Semanalmente",
    "Yes, I use AI tools monthly or infrequently": "Ocasionalmente",
    "No, but I plan to soon": "Não utiliza, mas pretende",
    "No, and I don't plan to": "Não utiliza nem pretende",
}
IA_ORDER = [*IA_LABELS.values(), "Sem resposta"]


def barras_comparativas(populacao, amostra, coluna, ordem, ausentes=False):
    fig = go.Figure()
    for titulo, base, cor in [
        ("População", populacao, POP),
        ("Amostra", amostra, AMOSTRA),
    ]:
        serie = base[coluna]
        if ausentes:
            serie = serie.fillna("Sem resposta").replace(IA_LABELS)
        freq = serie.value_counts(normalize=True).reindex(ordem, fill_value=0) * 100
        fig.add_trace(go.Bar(
            x=freq.values, y=ordem, orientation="h",
            name=titulo, marker_color=cor,
            hovertemplate=f"{titulo}: %{{x:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="group",
        xaxis_title="% dos respondentes" if ausentes else "% das respostas válidas",
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(ordem))),
    )
    return estilizar(fig, 345)


def intervalo_visual(ic, parametro, multiplicador, unidade):
    lo, hi = ic["inferior"] * multiplicador, ic["superior"] * multiplicador
    centro, ref = ic["estimativa"] * multiplicador, parametro * multiplicador
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[lo, hi], y=[0, 0], mode="lines",
        line=dict(color=AMOSTRA, width=10),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[centro], y=[0], mode="markers",
        marker=dict(size=15, color="white", line=dict(color=AMOSTRA, width=3)),
        hovertemplate="Estimativa: %{x:.2f}<extra></extra>",
    ))
    fig.add_vline(x=ref, line_color=REAL, line_dash="dash", line_width=2)
    limite_inf, limite_sup = min(lo, ref), max(hi, ref)
    folga = max((limite_sup - limite_inf) * .24, .15)
    fig.update_layout(
        xaxis=dict(range=[limite_inf - folga, limite_sup + folga], title=unidade),
        yaxis=dict(visible=False, range=[-.5, .5]),
    )
    return estilizar(fig, 180, legenda=False)


def bloco_descritivo(titulo, base):
    experiencia = base["WorkExp"].dropna()
    ia = base["AISelect"].dropna()
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        a, b = st.columns(2)
        a.metric("Respondentes", num(len(base)))
        b.metric("Utilizam IA", pct(ia.str.startswith("Yes").mean()))
        a, b = st.columns(2)
        a.metric("Experiência média", f"{num(experiencia.mean(), 2)} anos")
        b.metric("Mediana", f"{num(experiencia.median(), 1)} anos")
        st.caption(
            f"IA: {num(len(ia))} respostas válidas · "
            f"WorkExp: {num(len(experiencia))} válidas · "
            f"Desvio-padrão: {num(experiencia.std(), 2)} anos"
        )


def bloco_ic(titulo, ic, real, tipo, texto):
    proporcao = tipo == "proporcao"
    formato = pct if proporcao else lambda x: f"{num(x, 2)} anos"
    multiplicador = 100 if proporcao else 1
    unidade = "Percentual (%)" if proporcao else "Anos"
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        st.caption(texto)
        st.metric("Estimativa da amostra", formato(ic["estimativa"]))
        st.markdown(
            f"**Intervalo de 95%: {formato(ic['inferior'])} a {formato(ic['superior'])}**"
        )
        st.plotly_chart(
            intervalo_visual(ic, real, multiplicador, unidade),
            width="stretch",
        )
        st.caption(
            f"Parâmetro da população: {formato(real)} · "
            f"{num(ic['n'])} respostas válidas"
        )
        cobre = ic["inferior"] <= real <= ic["superior"]
        st.write(
            "O intervalo **contém** o valor populacional observado."
            if cobre else "O intervalo **não contém** o valor populacional observado."
        )


def bloco_teste(pergunta, metodo, h0, h1, resultado, conclusao_sim, conclusao_nao):
    rejeita = resultado["rejeitar_h0"]
    with st.container(border=True):
        st.caption(f"Teste {metodo} · α = 0,05 · análise exploratória")
        st.markdown(f"#### {pergunta}")
        st.write("**Interpretação:** " + (conclusao_sim if rejeita else conclusao_nao))
        a, b = st.columns(2)
        a.metric("Valor-p", p_texto(resultado["valor_p"]))
        estatistica = resultado["z"] if metodo == "Z" else resultado["t"]
        b.metric(f"Estatística {metodo}", num(estatistica, 3))
        st.caption(f"H₀: {h0} · H₁: {h1}")
        st.caption("Decisão: " + ("rejeitar H₀" if rejeita else "não rejeitar H₀"))


# Dados carregados uma vez e amostra reproduzível (seed fixa).
df = carregar_dados()
plano = dimensionar_amostra(df)
amostra = selecionar_amostra(df, plano["n_ajustado"], seed=42)

ia_pop, ia_amostra = df["AISelect"].dropna(), amostra["AISelect"].dropna()
exp_pop, exp_amostra = df["WorkExp"].dropna(), amostra["WorkExp"].dropna()

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
st.caption("Percurso: 01 Amostragem  ·  02 População × amostra  ·  03 Inferência")
st.divider()

# CAPÍTULO 1 — Dimensionamento e sorteio.
st.header("01 / Como selecionamos a amostra?")
st.write(
    "Cada linha representa um respondente único da pesquisa de 2025. "
    "Selecionamos uma amostra aleatória simples sem reposição, com semente 42."
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("População (N)", num(plano["N"]), border=True)
c2.metric("Cálculo inicial (n₀)", num(plano["n0"], 2), border=True)
c3.metric("Correção finita", num(plano["n_final"]), border=True)
c4.metric("Amostra ajustada", num(plano["n_ajustado"]), border=True)

with st.container(border=True):
    st.markdown("**Do planejamento ao sorteio**")
    st.write(
        "**95% de confiança**, **5 pontos percentuais de erro** e "
        "**proporção esperada de 50%** (cenário conservador) produziram "
        f"n₀ = {num(plano['n0'], 2)}. Após a correção para população finita, "
        f"n = {num(plano['n_corrigido'], 2)}, arredondado para "
        f"{num(plano['n_final'])}."
    )
    st.write(
        f"Como {pct(plano['taxa_validas'])} preencheram AISelect, "
        f"ajustamos o sorteio para {num(plano['n_ajustado'])} respondentes, "
        "esperando cerca de 382 respostas válidas para o indicador de IA."
    )
a, b, c = st.columns(3)
a.metric("Sorteados", num(len(amostra)))
b.metric("Respostas válidas de IA", num(len(ia_amostra)))
c.metric("Respostas ausentes de IA", num(amostra["AISelect"].isna().sum()))
st.caption(
    "O ajuste aumenta a quantidade esperada de respostas válidas, "
    "mas não garante o preenchimento nem elimina viés de não resposta."
)
st.divider()

# CAPÍTULO 2 — Painéis 1 e 2 do trabalho.
st.header("02 / O que encontramos na população e na amostra?")
st.write(
    "Os mesmos indicadores são exibidos lado a lado. "
    "Nos gráficos, usamos percentuais para comparar grupos de tamanhos diferentes."
)
col1, col2 = st.columns(2)
with col1:
    bloco_descritivo("Painel 1 · População", df)
with col2:
    bloco_descritivo("Painel 2 · Amostra", amostra)

with st.container(border=True):
    st.markdown("#### Experiência profissional")
    st.plotly_chart(histograma_comparativo(df, amostra), width="stretch")
    st.caption("Frequência relativa entre respostas válidas de WorkExp em cada grupo.")

with st.container(border=True):
    st.markdown("#### Frequência de utilização de IA")
    st.plotly_chart(
        barras_comparativas(df, amostra, "AISelect", IA_ORDER, ausentes=True),
        width="stretch",
    )
    st.caption(
        "Neste gráfico, o denominador é o total de pessoas em cada grupo. "
        "Na proporção de usuários de IA acima, o denominador inclui apenas "
        "quem respondeu a pergunta."
    )

with st.expander("Detalhes complementares: idade e países"):
    col1, col2 = st.columns(2)
    idade = [
        "Under 18 years old", "18-24 years old", "25-34 years old",
        "35-44 years old", "45-54 years old", "55-64 years old",
        "65 years or older", "Prefer not to say",
    ]
    with col1:
        st.markdown("**Faixas etárias**")
        st.plotly_chart(barras_comparativas(df, amostra, "Age", idade), width="stretch")
    with col2:
        st.markdown("**Principais países**")
        paises = df["Country"].value_counts().head(7).index.tolist()
        st.plotly_chart(barras_comparativas(df, amostra, "Country", paises), width="stretch")
        st.caption("Principais países definidos pela frequência na população.")
st.divider()

# CAPÍTULO 3 — Inferência estatística e comparação com os parâmetros.
st.header("03 / O que podemos inferir usando apenas a amostra?")
st.write(
    "Estimamos os parâmetros por intervalos de confiança de 95%. "
    "Os dados completos da população entram apenas como referência visual."
)
col1, col2 = st.columns(2)
with col1:
    bloco_ic(
        "Proporção que utiliza IA", ic_ia, p_pop, "proporcao",
        "Entre as pessoas com resposta válida em AISelect.",
    )
with col2:
    bloco_ic(
        "Média de experiência profissional", ic_exp, exp_pop.mean(), "media",
        "Entre as pessoas com resposta válida em WorkExp.",
    )
st.caption(
    "Legenda: verde = intervalo de confiança; ponto branco = estimativa amostral; "
    "linha amarela tracejada = parâmetro populacional. "
    "Em repetições do procedimento, cerca de 95% dos intervalos cobririam "
    "o parâmetro, sob as condições estatísticas do método."
)

st.subheader("Testes de hipóteses: quais afirmações têm evidência?")
st.caption(
    "Quatro testes exploratórios com significância de 5%, "
    "aplicados às respostas válidas da amostra."
)
p1 = teste_proporcao(
    int(ia_amostra.str.startswith("Yes").sum()), len(ia_amostra), len(ia_pop), p0=.75
)
p2 = teste_proporcao(
    int((ia_amostra == "Yes, I use AI tools daily").sum()),
    len(ia_amostra), len(ia_pop), p0=.40
)
m1 = teste_media(amostra["WorkExp"], len(exp_pop), mu0=10, alternativa="maior")
m2 = teste_media(amostra["WorkExp"], len(exp_pop), mu0=15, alternativa="diferente")

col1, col2 = st.columns(2)
with col1:
    bloco_teste(
        "Mais de 75% utilizam IA?", "Z", "p ≤ 75%", "p > 75%", p1,
        "Há evidência de proporção superior a 75%.",
        "Não há evidência suficiente de proporção superior a 75%.",
    )
with col2:
    bloco_teste(
        "Mais de 40% usam IA diariamente?", "Z", "p ≤ 40%", "p > 40%", p2,
        "Há evidência de uso diário superior a 40%.",
        "Não há evidência suficiente de uso diário superior a 40%.",
    )
col1, col2 = st.columns(2)
with col1:
    bloco_teste(
        "A experiência média supera 10 anos?", "t", "μ ≤ 10", "μ > 10", m1,
        "Há evidência de média superior a 10 anos.",
        "Não há evidência suficiente de média superior a 10 anos.",
    )
with col2:
    bloco_teste(
        "A experiência média é diferente de 15 anos?", "t", "μ = 15", "μ ≠ 15", m2,
        "Há evidência de média diferente de 15 anos.",
        "Não há evidência suficiente de média diferente de 15 anos.",
    )

with st.expander("Pressupostos e limitações"):
    st.write(
        "Os dois testes Z atendem à regra usual de pelo menos dez "
        "sucessos e dez fracassos esperados sob H₀: "
        f"para 75%, {num(.75 * len(ia_amostra), 1)} e "
        f"{num(.25 * len(ia_amostra), 1)}; para 40%, "
        f"{num(.40 * len(ia_amostra), 1)} e "
        f"{num(.60 * len(ia_amostra), 1)}."
    )
    st.write(
        f"O teste t utiliza {num(len(exp_amostra))} respostas válidas. "
        "A distribuição de experiência é assimétrica e contém valores extremos; "
        "os procedimentos com correção finita são aproximações."
    )
    st.write(
        "A base original não é uma amostra probabilística de todos os "
        "desenvolvedores do mundo. As conclusões se restringem aos respondentes "
        "válidos de cada variável. Os limites das hipóteses foram definidos após "
        "explorar os dados; os testes são exploratórios, sem correção para "
        "múltiplas comparações. Não rejeitar H₀ não comprova H₀."
    )

st.divider()
st.caption(
    "Fonte: [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/) "
    f"· [CSV da análise]({URL_DADOS}) · sorteio reproduzível (seed=42)."
)
