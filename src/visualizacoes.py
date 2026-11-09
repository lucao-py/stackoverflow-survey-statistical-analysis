"""Visualizações da inferência para o painel Streamlit (Matplotlib)."""

from threading import RLock

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

FUNDO = "#161C24"
TEXTO = "#E5E7EB"
SECUNDARIO = "#94A3B8"
GRADE = "#2B3948"
POPULACAO = "#667F9B"
AMOSTRA = "#4E9CDB"
DESTAQUE = "#2DD4BF"
LIMIAR = "#FBBF24"
PLOT_LOCK = RLock()


def _pt(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def _preparar(fig, ax):
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=SECUNDARIO, labelsize=11, length=0)
    ax.grid(axis="x", color=GRADE, alpha=0.75, lw=0.8)
    ax.set_axisbelow(True)


def grafico_ic_barras(ic, valor_populacional, percentual=False):
    """Duas barras a partir de zero; a barra da amostra traz o IC como errorbar.

    A leitura combina a referência visual enviada pelo aluno (barras + hastes)
    com a indicação explícita dos limites numéricos do IC.
    """
    escala = 100 if percentual else 1
    unidade = "%" if percentual else " anos"
    ponto = ic["estimativa"] * escala
    inferior = ic["inferior"] * escala
    superior = ic["superior"] * escala
    populacao = valor_populacional * escala
    erro_esquerda = ponto - inferior
    erro_direita = superior - ponto

    limite_padrao = 100 if percentual else 25
    eixo_max = max(
        limite_padrao,
        np.ceil(max(superior, ponto, populacao) * 1.22 / 5) * 5,
    )

    fig, ax = plt.subplots(figsize=(12.5, 3.3), dpi=130)
    _preparar(fig, ax)

    ax.barh(
        [1, 0], [populacao, ponto], height=0.42,
        color=[POPULACAO, AMOSTRA], zorder=2,
    )
    ax.errorbar(
        [ponto], [0],
        xerr=[[erro_esquerda], [erro_direita]],
        fmt="none", ecolor=TEXTO,
        elinewidth=2.5, capsize=10, capthick=2.5, zorder=6,
    )

    ax.set_xlim(0, eixo_max)
    ax.set_ylim(-0.76, 1.55)
    ax.set_yticks([1, 0], ["População", "Amostra (IC 95%)"])
    ax.tick_params(axis="y", colors=TEXTO)
    marcacoes = np.linspace(0, eixo_max, 6)
    ax.set_xticks(marcacoes)
    ax.set_xticklabels([f"{v:g}{unidade if percentual else ''}" for v in marcacoes])
    ax.set_xlabel("Percentual de usuários de IA" if percentual else "Anos de experiência",
                  color=SECUNDARIO, labelpad=12)

    # O valor pontual é rotulado fora das barras.
    for y, valor in [(1, populacao), (0, ponto)]:
        ax.text(
            min(valor + eixo_max * 0.016, eixo_max * 0.94),
            y, f"{_pt(valor)}{unidade}",
            color=TEXTO, fontsize=14, fontweight="bold", va="center",
        )

    # Os dois extremos e a amplitude permanecem legíveis sem passar o mouse.
    ax.text(
        eixo_max * 0.985, -0.56,
        f"IC 95%: {_pt(inferior)} a {_pt(superior)}{unidade}"
        f"    ·    Amplitude: {_pt(superior - inferior)}"
        f"{' p.p.' if percentual else ' anos'}",
        ha="right", va="center", color=TEXTO, fontsize=11,
    )
    fig.tight_layout(pad=1.5)
    return fig


def grafico_decisao_testes(testes):
    """Matriz de 4 testes: hipóteses, valor-p versus α e decisão.

    Sem cartões repetidos nem transformação -log10 do valor-p.
    """
    n = len(testes)
    if not n:
        raise ValueError("A lista de testes está vazia.")

    valor_max = max(float(item["valor_p"]) for item in testes)
    escala_max = max(0.12, valor_max * 1.2)

    fig = plt.figure(figsize=(13.5, 1.1 * n + 2.0), dpi=130, facecolor=FUNDO)
    gs = GridSpec(
        1, 3, figure=fig, width_ratios=[1.42, 1.05, 0.82],
        left=0.035, right=0.975, bottom=0.16, top=0.84, wspace=0.08,
    )
    esquerda = fig.add_subplot(gs[0, 0])
    centro = fig.add_subplot(gs[0, 1], sharey=esquerda)
    direita = fig.add_subplot(gs[0, 2], sharey=esquerda)

    for ax in (esquerda, centro, direita):
        ax.set_facecolor(FUNDO)
        ax.set_ylim(-0.62, n - 0.48)
        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        for linha in np.arange(0.5, n - 0.1, 1.0):
            ax.axhline(linha, color=GRADE, lw=0.8, zorder=0)

    esquerda.set_xlim(0, 1)
    direita.set_xlim(0, 1)
    centro.set_xlim(-escala_max * 0.012, escala_max)
    centro.set_xticks(
        [x for x in (0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80)
         if x <= escala_max]
    )
    centro.set_xticklabels(
        [_pt(x, 2) if x else "0" for x in centro.get_xticks()],
        color=SECUNDARIO, fontsize=10,
    )
    centro.tick_params(axis="x", bottom=True, colors=SECUNDARIO, length=0)

    for ax, titulo in (
        (esquerda, "HIPÓTESE"),
        (centro, "VALOR-P"),
        (direita, "DECISÃO"),
    ):
        ax.text(
            0.01, 1.07, titulo, transform=ax.transAxes,
            fontsize=11, color=SECUNDARIO, fontweight="bold",
        )

    centro.axvline(0.05, color=LIMIAR, lw=2, ls="--", zorder=1)
    centro.text(
        0.05, n - 0.44, "α = 0,05",
        color=LIMIAR, fontsize=10, ha="center", va="bottom",
    )

    for i, teste in enumerate(testes):
        y = n - 1 - i
        p = float(teste["valor_p"])
        rejeita = bool(teste["rejeitar"])
        ponto_cor = DESTAQUE if rejeita else POPULACAO
        legenda_p = "p < 0,0001" if p < 0.0001 else f"p = {_pt(p, 4)}"

        esquerda.text(
            0.015, y + 0.14, teste["nome"],
            color=TEXTO, fontsize=12, fontweight="bold", va="center",
        )
        esquerda.text(
            0.015, y - 0.17, f"H₀: {teste['h0']}    ·    H₁: {teste['h1']}",
            color=SECUNDARIO, fontsize=10, va="center",
        )

        centro.hlines(y, 0, escala_max * 0.94, color=GRADE, lw=5, zorder=1)
        centro.plot(p, y, marker="o", markersize=12, color=ponto_cor, zorder=4)
        vai_para_esquerda = p > escala_max * 0.72
        centro.text(
            p - escala_max * 0.03 if vai_para_esquerda else p + escala_max * 0.025,
            y + 0.15,
            legenda_p, ha="right" if vai_para_esquerda else "left",
            va="center", color=TEXTO, fontsize=11,
            bbox=dict(facecolor=FUNDO, edgecolor="none", pad=1.5),
        )

        direita.text(
            0.03, y + 0.14,
            "REJEITA H₀" if rejeita else "NÃO REJEITA H₀",
            color=DESTAQUE if rejeita else SECUNDARIO,
            fontsize=12, fontweight="bold", va="center",
        )
        direita.text(
            0.03, y - 0.17,
            f"{teste['metodo']} = {_pt(teste['estatistica'])}",
            color=SECUNDARIO, fontsize=10, va="center",
        )
    return fig
