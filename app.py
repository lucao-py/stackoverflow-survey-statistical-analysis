"""Dashboard narrativo: população, amostra e inferência no Survey 2025."""

from html import escape

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import gaussian_kde, norm, t

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
.legenda-formula {
    color: #7C8592;
    font-size: 0.78rem;
    line-height: 1.6;
    margin: 0.2rem 0 0.5rem;
}
.legenda-formula span {
    display: block;
    margin-top: 0.3rem;
}
</style>
""")


def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor * 100, 2)}%"


def p_texto(valor):
    return "< 0,0001" if valor < 0.0001 else num(valor, 4)


def legenda_formula(explicacao, variaveis):
    st.html(
        f'<p class="legenda-formula">{escape(explicacao)}'
        f'<span>{escape(variaveis)}</span></p>'
    )


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
        desvio = experiencia.std(ddof=0 if chave == "populacao" else 1)
        st.caption(f"Desvio-padrão da experiência: **{num(desvio, 2)} anos**")

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


def mostrar_ic(titulo, ic, populacao, percentual, formula, explicacao, variaveis):
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
        diferenca = round((ic["estimativa"] - populacao) * escala, 2)
        sinal = "+" if diferenca > 0 else ""
        contem = ic["inferior"] <= populacao <= ic["superior"]
        st.caption(
            f"Diferença amostra − população: {sinal}{num(diferenca, 2)}"
            f"{' p.p.' if percentual else ' anos'}; valor populacional "
            f"{'dentro' if contem else 'fora'} do IC."
        )
        st.latex(formula)
        legenda_formula(explicacao, variaveis)


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
with st.expander("Sobre a base de dados", expanded=False):
    st.caption(
        "Fonte: [Stack Overflow Developer Survey 2025]"
        "(https://survey.stackoverflow.co/2025/) · "
        f"[CSV utilizado]({URL_DADOS}) · "
        f"{num(df.shape[0])} observações · {num(df.shape[1])} variáveis."
    )
    st.caption(
        "População: registros da pesquisa presentes no CSV utilizado. "
        "Unidade amostral: respondente individual. "
        "Variáveis centrais: `AISelect` (qualitativa, frequência de uso de IA) "
        "e `WorkExp` (quantitativa, anos de experiência profissional)."
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
        legenda_formula(
            "Calcula o tamanho inicial da amostra para estimar uma proporção "
            "com 95% de confiança e margem de erro de 5 pontos percentuais.",
            f"Z = 1,96 (valor crítico) · p = 0,50 (proporção conservadora) · "
            f"E = 0,05 (erro tolerado) · n₀ = {num(plano['n0'], 2)}.",
        )
    with c2:
        st.markdown("**2. Correção finita**")
        st.latex(r"n=\frac{N n_0}{N+n_0-1}")
        legenda_formula(
            "Reduz o tamanho inicial para considerar que a população é finita; "
            "o resultado é arredondado para cima.",
            f"N = {num(plano['N'])} (população) · "
            f"n₀ = {num(plano['n0'], 2)} (tamanho inicial) · "
            f"n = {num(plano['n_corrigido'], 2)} → {num(plano['n_final'])} respondentes.",
        )
    with c3:
        st.markdown("**3. Ajuste por respostas válidas**")
        st.latex(r"n_{\mathrm{aj}}=\left\lceil\frac{n}{r_{IA}}\right\rceil")
        legenda_formula(
            "Amplia a seleção para compensar respostas ausentes sobre IA. "
            "A quantidade de respostas válidas é esperada, não garantida.",
            f"n = {num(plano['n_final'])} (meta de respostas válidas) · "
            f"rIA = {pct(plano['taxa_validas'])} (taxa de respostas válidas na base) · "
            f"n ajustado = {num(plano['n_ajustado'])}. O símbolo ⌈ ⌉ arredonda para cima.",
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
    "Estima uma faixa de confiança de 95% para a proporção que utiliza IA: "
    "a proporção da amostra mais ou menos uma margem de erro, com correção finita.",
    f"p̂ = {pct(ic_ia['estimativa'])} (proporção amostral) · "
    f"z₀,₉₇₅ = {num(norm.ppf(0.975), 2)} (valor crítico) · "
    f"n = {num(ic_ia['n'])} (respostas válidas na amostra) · "
    f"N = {num(len(ia_pop))} (respostas válidas na população).",
)
mostrar_ic(
    "Média de experiência profissional", ic_exp, exp_pop.mean(), False,
    r"IC_\mu=\bar x\ \pm\ t_{0{,}975;\,n-1}"
    r"\frac{s}{\sqrt n}\sqrt{\frac{N-n}{N}}",
    "Estima uma faixa de confiança de 95% para a experiência média: "
    "a média da amostra mais ou menos uma margem de erro, usando t de Student "
    "e correção finita.",
    f"x̄ = {num(ic_exp['estimativa'], 2)} anos (média amostral) · "
    f"s = {num(amostra['WorkExp'].std(ddof=1), 2)} anos (desvio-padrão amostral) · "
    f"n = {num(ic_exp['n'])} (respostas válidas na amostra) · "
    f"N = {num(len(exp_pop))} (respostas válidas na população) · "
    f"t₀,₉₇₅ = {num(t.ppf(0.975, df=ic_exp['n'] - 1), 3)} "
    f"(valor crítico, {num(ic_exp['n'] - 1)} graus de liberdade).",
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

with st.expander("Notas metodológicas", expanded=False):
    st.markdown(
        "- **Referências exploratórias:** 75% para uso de IA e 40% para uso "
        "diário contrastam adoção ampla e rotina; 10 e 15 anos situam a "
        "experiência média. São valores redondos de comparação, não limites oficiais.\n"
        "- **Condições:** seleção aleatória sem reposição, com correção finita. "
        "O teste Z exige contagens esperadas de sucessos e insucessos "
        "suficientemente grandes sob H₀; o IC da proporção usa as contagens "
        "observadas. Para a média, usa-se t com n−1 graus de liberdade e "
        "aproximação pelo teorema central do limite em amostras grandes.\n"
        "- **Ausentes e denominadores:** exclusão por variável, sem imputação. "
        f"IA: {num(ic_ia['n'])} respostas válidas na amostra e "
        f"{num(len(ia_pop))} na população; experiência: {num(ic_exp['n'])} e "
        f"{num(len(exp_pop))}, respectivamente. As barras de frequência de IA "
        "incluem ‘Sem resposta’ e usam o total de registros de cada painel.\n"
        "- **Variabilidade:** outra amostra pode produzir estimativas, ICs e "
        "decisões diferentes. Os ICs e testes usam apenas os valores da amostra; "
        "os parâmetros populacionais servem à comparação. As quatro hipóteses "
        "são exploratórias, sem ajuste para comparações múltiplas.\n"
        "- **Alcance e fonte:** a pesquisa é voluntária; a AAS deste projeto "
        "representa o CSV, não todos os desenvolvedores. O "
        "[relatório oficial](https://survey.stackoverflow.co/2025/methodology) "
        "possui uma base de divulgação distinta; os números deste painel "
        "são calculados diretamente do arquivo utilizado."
    )

st.divider()
st.caption(
    "Fonte: [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/) "
    f"· [Dados utilizados]({URL_DADOS})"
)
