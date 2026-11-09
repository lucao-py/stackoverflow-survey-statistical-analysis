"""Regressões da conversão dos gráficos de inferência para Plotly."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from src.estatisticas import intervalo_proporcao
from src.visualizacoes import grafico_decisao_testes, grafico_ic_barras


class GraficosInferenciaisTest(unittest.TestCase):
    def test_proporcao_preserva_estimativa_e_extremos_do_intervalo(self):
        ic = intervalo_proporcao(306, 374, 33720)
        fig = grafico_ic_barras(ic, 0.7849644128113878, percentual=True)
        populacao, amostra = fig.data

        self.assertAlmostEqual(populacao.x[0], 78.49644128113879)
        self.assertAlmostEqual(amostra.x[0], ic["estimativa"] * 100)
        self.assertAlmostEqual(
            amostra.x[0] - amostra.error_x.arrayminus[0], ic["inferior"] * 100,
        )
        self.assertAlmostEqual(
            amostra.x[0] + amostra.error_x.array[0], ic["superior"] * 100,
        )
        self.assertIn("Respostas válidas: 374", amostra.hovertemplate)
        self.assertEqual(fig.layout.xaxis.range, (0, 100))

    def test_media_preserva_unidade_e_intervalo_assimetrico(self):
        ic = {"estimativa": 14.31, "inferior": 13.20, "superior": 15.60, "n": 474}
        fig = grafico_ic_barras(ic, 13.37)
        populacao, amostra = fig.data

        self.assertEqual(populacao.x[0], 13.37)
        self.assertEqual(amostra.x[0], 14.31)
        self.assertAlmostEqual(amostra.error_x.arrayminus[0], 1.11)
        self.assertAlmostEqual(amostra.error_x.array[0], 1.29)
        self.assertIn("14,31 anos", amostra.hovertemplate)
        self.assertIn("13,20 anos", amostra.hovertemplate)
        self.assertIn("15,60 anos", amostra.hovertemplate)

    def test_intervalo_proximo_de_100_por_cento_mantem_rotulo_no_eixo(self):
        ic = {"estimativa": 0.99, "inferior": 0.97, "superior": 1, "n": 400}
        fig = grafico_ic_barras(ic, 0.98, percentual=True)

        self.assertLessEqual(fig.layout.annotations[1].x, 100)
        self.assertGreater(fig.layout.annotations[1].y, fig.data[1].y[0])

    def test_testes_preservam_valores_pequenos_ordem_e_decisoes(self):
        valores = [0.0011, 0.0004, 6.395e-14, 0.2224]
        testes = [
            dict(nome=f"Teste {i}", h0="μ = 15", h1="μ ≠ 15", metodo="t",
                 estatistica=-1.22, valor_p=p, rejeitar=p < 0.05)
            for i, p in enumerate(valores)
        ]
        fig = grafico_decisao_testes(testes)
        pontos = [trace for trace in fig.data if trace.mode == "markers"]

        self.assertEqual([trace.x[0] for trace in pontos], valores)
        self.assertEqual([trace.y[0] for trace in pontos], [3, 2, 1, 0])
        self.assertIn("REJEITA H₀", pontos[0].hovertemplate)
        self.assertIn("NÃO REJEITA H₀", pontos[-1].hovertemplate)
        self.assertTrue(any(
            shape.type == "line" and shape.xref == "x2"
            and shape.x0 == shape.x1 == 0.05
            for shape in fig.layout.shapes
        ))
        self.assertEqual(json.loads(fig.to_json())["layout"].get("images", []), [])

    def test_teste_com_valor_p_igual_a_um_fica_visivel(self):
        teste = dict(nome="Teste", h0="p = 0,5", h1="p ≠ 0,5", metodo="Z",
                     estatistica=0, valor_p=1, rejeitar=False)
        fig = grafico_decisao_testes([teste])
        self.assertGreater(fig.layout.xaxis2.range[1], 1)

    def test_lista_vazia_continua_sendo_rejeitada(self):
        with self.assertRaises(ValueError):
            grafico_decisao_testes([])


class EstruturaDashboardTest(unittest.TestCase):
    def test_layout_formulas_e_sete_graficos_nativos(self):
        base = pd.DataFrame({
            "AISelect": np.tile([
                "Yes, I use AI tools daily", "No, and I don't plan to", None,
            ], 400),
            "WorkExp": np.arange(1200, dtype=float) % 45,
        })
        base.loc[::11, "WorkExp"] = np.nan
        app = Path(__file__).resolve().parents[1] / "app.py"
        with patch("src.dados.carregar_dados", return_value=base):
            at = AppTest.from_file(str(app)).run(timeout=30)

        self.assertEqual(len(at.exception), 0)
        self.assertEqual([header.value for header in at.header], [
            "01 / Dimensionamento da amostra",
            "02 / População × amostra",
            "03 / Inferência estatística",
        ])
        self.assertEqual(len(at.metric), 12)
        self.assertEqual(len(at.latex), 5)
        self.assertEqual(len(at.get("plotly_chart")), 7)
        self.assertEqual(len(at.get("imgs")), 0)


if __name__ == "__main__":
    unittest.main()
