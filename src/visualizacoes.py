"""Gráficos Plotly com uma identidade visual comum ao dashboard."""

from html import escape
import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

FUNDO = "#151C25"
TEXTO = "#E5E7EB"
SECUNDARIO = "#94A3B8"
GRADE = "rgba(148,163,184,0.10)"
POPULACAO = "#94A3B8"
AMOSTRA = "#2DD4BF"
LIMIAR = "#FBBF24"
FONTE = "Source Sans Pro, Source Sans 3, sans-serif"

CONFIG_GRAFICOS = {
    "displaylogo": False,
    "scrollZoom": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "toImageButtonOptions": {"scale": 2},
}


def _pt(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _valor_p(valor):
    return "< 0,0001" if valor < 0.0001 else _pt(valor, 4)


def estilizar(fig, altura=300, legenda=True):
    """Integra gráficos descritivos e inferenciais ao tema do Streamlit."""
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        font=dict(family=FONTE, size=13, color=TEXTO),
        separators=",.",
        margin=dict(l=12, r=28, t=64 if legenda else 18, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legenda,
        legend=dict(
            orientation="h", y=1.0, yanchor="bottom", x=0,
            font=dict(size=11, color=SECUNDARIO),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=FUNDO, bordercolor="#334155",
            font=dict(family=FONTE, size=13, color=TEXTO),
            align="left",
        ),
        barcornerradius=4,
        modebar=dict(
            bgcolor="rgba(0,0,0,0)", color=SECUNDARIO, activecolor=AMOSTRA,
        ),
        dragmode="zoom",
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRADE, zeroline=False,
        showline=False, ticks="", tickfont=dict(size=12, color=SECUNDARIO),
        title_font=dict(size=12, color=SECUNDARIO), title_standoff=18,
        ticklabelstandoff=6, automargin=True,
    )
    fig.update_yaxes(
        showgrid=False, zeroline=False, showline=False, ticks="",
        tickfont=dict(size=12, color=SECUNDARIO),
        title_font=dict(size=12, color=SECUNDARIO), title_standoff=18,
        ticklabelstandoff=10, automargin=True,
    )
    return fig


def grafico_ic_barras(ic, valor_populacional, percentual=False):
    """Mantém as duas barras e o IC, com valores e limites no hover."""
    escala = 100 if percentual else 1
    unidade = "%" if percentual else " anos"
    ponto = float(ic["estimativa"]) * escala
    inferior = float(ic["inferior"]) * escala
    superior = float(ic["superior"]) * escala
    populacao = float(valor_populacional) * escala
    amplitude = superior - inferior

    eixo_min = min(0, math.floor(min(inferior, populacao) / 5) * 5)
    eixo_max = 100 if percentual else max(
        25, math.ceil(max(superior, populacao) * 1.22 / 5) * 5,
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="População", x=[populacao], y=[1], orientation="h",
        width=0.34, marker=dict(color=POPULACAO, line_width=0),
        hovertemplate=(
            "<b>População</b><br>"
            f"Valor observado: {_pt(populacao)}{unidade}"
            "<extra></extra>"
        ),
    ))
    fig.add_trace(go.Bar(
        name="Amostra (IC 95%)", x=[ponto], y=[0], orientation="h",
        width=0.34, marker=dict(color=AMOSTRA, line_width=0),
        error_x=dict(
            type="data", symmetric=False,
            array=[superior - ponto], arrayminus=[ponto - inferior],
            color=TEXTO, thickness=2, width=7,
        ),
        hovertemplate=(
            "<b>Amostra · IC 95%</b><br>"
            f"Estimativa: {_pt(ponto)}{unidade}<br>"
            f"Limite inferior: {_pt(inferior)}{unidade}<br>"
            f"Limite superior: {_pt(superior)}{unidade}<br>"
            f"Amplitude: {_pt(amplitude)}{' p.p.' if percentual else ' anos'}<br>"
            f"Respostas válidas: {_pt(ic['n'], 0)}"
            "<extra></extra>"
        ),
    ))

    # O valor fica depois da haste, em vez de colidir com o intervalo.
    # A distância em pixels permanece legível ao redimensionar o painel.
    for y, valor, fim in ((1, populacao, populacao), (0, ponto, superior)):
        proximo_da_borda = fim > eixo_max * 0.87
        fig.add_annotation(
            x=fim, y=y + 0.30 if proximo_da_borda else y,
            text=f"<b>{_pt(valor)}{unidade}</b>", showarrow=False,
            xanchor="right" if proximo_da_borda else "left",
            xshift=0 if proximo_da_borda else 18,
            font=dict(size=15, color=TEXTO),
        )
    estilizar(fig, altura=265, legenda=False)
    fig.update_layout(
        margin=dict(l=148, r=92, t=12, b=52),
        barmode="overlay", bargap=0.6, hovermode="closest",
    )
    fig.update_xaxes(
        range=[eixo_min, eixo_max],
        title_text="Percentual de usuários de IA" if percentual else "Anos de experiência",
        ticksuffix="%" if percentual else "", nticks=6,
        title_standoff=24,
    )
    fig.update_yaxes(
        range=[-0.55, 1.55], tickvals=[1, 0],
        ticktext=["População", "Amostra (IC 95%)"],
        tickfont=dict(size=13, color=TEXTO),
        fixedrange=True, automargin=True,
    )
    return fig


def grafico_decisao_testes(testes):
    """Preserva a matriz hipótese / valor-p / decisão em um gráfico nativo."""
    if not testes:
        raise ValueError("A lista de testes está vazia.")

    n = len(testes)
    alfa = 0.05
    valor_max = max(float(item["valor_p"]) for item in testes)
    escala_max = max(0.12, valor_max * 1.2)
    fig = make_subplots(
        rows=1, cols=3, shared_yaxes=True,
        column_widths=[0.46, 0.32, 0.22], horizontal_spacing=0.04,
    )
    estilizar(fig, altura=96 * n + 100, legenda=False)
    fig.update_layout(
        margin=dict(l=4, r=8, t=72, b=44), hovermode="closest",
    )
    fig.update_yaxes(range=[-0.5, n - 0.5], visible=False, fixedrange=True)
    fig.update_xaxes(visible=False, range=[0, 1], fixedrange=True, col=1)
    fig.update_xaxes(visible=False, range=[0, 1], fixedrange=True, col=3)
    marcacoes = [
        p for p in (0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1)
        if p <= escala_max
        and not (p == 0.10 and escala_max >= 0.20)
        and not (p == alfa and escala_max >= 0.50)
    ]
    fig.update_xaxes(
        range=[-escala_max * 0.045, escala_max], tickvals=marcacoes,
        ticktext=[_pt(p, 2) if p else "0" for p in marcacoes],
        showgrid=False, col=2,
    )

    for coluna, titulo in enumerate(("HIPÓTESE", "VALOR-P", "DECISÃO"), start=1):
        eixo = "x domain" if coluna == 1 else f"x{coluna} domain"
        fig.add_annotation(
            x=0, y=1.12, xref=eixo, yref="paper", text=titulo,
            showarrow=False, xanchor="left",
            font=dict(size=12, color=SECUNDARIO),
        )

    fig.add_vrect(
        x0=0, x1=alfa, fillcolor="rgba(45,212,191,0.035)",
        line_width=0, layer="below", row=1, col=2,
        exclude_empty_subplots=False,
    )
    fig.add_vline(
        x=alfa, line_color=LIMIAR, line_width=1.5,
        line_dash="dash", row=1, col=2, exclude_empty_subplots=False,
    )
    fig.add_annotation(
        x=alfa, y=1.045, xref="x2", yref="paper", text="α = 0,05",
        showarrow=False, font=dict(size=12, color=LIMIAR),
        bgcolor="#0E1117", borderpad=3,
    )

    for i, teste in enumerate(testes):
        y = n - 1 - i
        p = float(teste["valor_p"])
        rejeita = bool(teste["rejeitar"])
        cor = AMOSTRA if rejeita else POPULACAO
        decisao = "REJEITA H₀" if rejeita else "NÃO REJEITA H₀"
        nome, h0, h1 = (escape(teste[campo]) for campo in ("nome", "h0", "h1"))
        estatistica = f"{escape(teste['metodo'])} = {_pt(teste['estatistica'])}"

        if i:
            fig.add_shape(
                type="line", x0=0, x1=1, xref="paper",
                y0=y + 0.5, y1=y + 0.5, yref="y",
                line=dict(color=GRADE, width=1), layer="below",
            )
        for deslocamento, texto, tamanho, cor_texto in (
            (0.12, f"<b>{nome}</b>", 14, TEXTO),
            (-0.18, f"H₀: {h0} &nbsp;·&nbsp; H₁: {h1}", 12, SECUNDARIO),
        ):
            fig.add_annotation(
                x=0, y=y + deslocamento, xref="x", yref="y",
                text=texto, showarrow=False, xanchor="left",
                align="left", font=dict(size=tamanho, color=cor_texto),
            )

        fig.add_trace(go.Scatter(
            x=[0, escala_max * 0.94], y=[y, y], mode="lines",
            line=dict(color="#273341", width=4),
            hoverinfo="skip", showlegend=False,
        ), row=1, col=2)
        fig.add_trace(go.Scatter(
            name=teste["nome"], x=[p], y=[y], mode="markers",
            marker=dict(size=13, color=cor, line=dict(color="#0E1117", width=2)),
            hovertemplate=(
                f"<b>{nome}</b><br>H₀: {h0}<br>H₁: {h1}<br>"
                f"{estatistica}<br>Valor-p: {_valor_p(p)}<br>"
                f"Significância: {_pt(alfa)}<br><b>{decisao}</b>"
                "<extra></extra>"
            ), showlegend=False,
        ), row=1, col=2)
        fig.add_annotation(
            x=p, y=y + 0.28, xref="x2", yref="y2",
            text=f"p {_valor_p(p)}" if p < 0.0001 else f"p = {_valor_p(p)}",
            xanchor="right" if p > escala_max * 0.7 else "left",
            xshift=-8 if p > escala_max * 0.7 else 8,
            showarrow=False, font=dict(size=13, color=TEXTO),
            bgcolor="#0E1117", borderpad=3,
        )
        fig.add_annotation(
            x=0.02, y=y + 0.12, xref="x3", yref="y3",
            text=f"<b>{decisao}</b>", showarrow=False, xanchor="left",
            font=dict(size=12, color=cor), borderpad=6,
            bgcolor="rgba(45,212,191,0.09)" if rejeita else "rgba(148,163,184,0.09)",
        )
        fig.add_annotation(
            x=0.02, y=y - 0.22, xref="x3", yref="y3",
            text=estatistica, showarrow=False, xanchor="left", xshift=6,
            font=dict(size=12, color=SECUNDARIO),
        )
    return fig
