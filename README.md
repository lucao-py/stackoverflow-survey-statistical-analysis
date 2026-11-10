# Amostragem e inferência estatística

Projeto final de Estatística Aplicada com o **Stack Overflow Developer Survey 2025**. Compara parâmetros da base completa com estimativas de uma amostra aleatória simples (AAS), por análise descritiva, intervalos de confiança e testes de hipóteses.

O Streamlit mantém três etapas: **dimensionamento**, **população × amostra lado a lado** e **inferência estatística**.

## Base, população e variáveis

A pesquisa investiga perfil, experiência e uso de tecnologias por desenvolvedores. A participação é voluntária, com divulgação principalmente pelos canais do Stack Overflow.

- **Fontes:** [relatório de 2025](https://survey.stackoverflow.co/2025/), [metodologia oficial](https://survey.stackoverflow.co/2025/methodology) e [CSV utilizado](https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/2025/results.csv), no [repositório oficial](https://github.com/StackExchange/Survey).
- **População:** os **49.191 registros e 172 variáveis** do CSV carregado; os identificadores dos respondentes são únicos.
- **Unidade amostral:** respondente individual.

| Variável | Tipo e significado | Válidas na população | Válidas na amostra |
| --- | --- | ---: | ---: |
| `AISelect` | Qualitativa: frequência de uso de IA | 33.720 | 374 |
| `WorkExp` | Quantitativa: anos de experiência profissional | 42.893 | 474 |

“Utilizam IA” reúne uso diário, semanal e mensal/ocasional, identificado por `Yes`; intenção de começar a usar IA não é uso atual.

**CSV e divulgação oficial são universos distintos.** O portal informa 49.009 respostas, enquanto este CSV contém 49.191 registros; a origem específica da divergência não foi reconciliada. O destaque de 84% no [relatório sobre IA](https://survey.stackoverflow.co/2025/ai) também inclui intenção de uso. Os denominadores deste projeto são calculados do arquivo.

Os números do README foram conferidos em **09/11/2026**. No dashboard, dimensões, contagens e resultados são dinâmicos.

## Dimensionamento e seleção

O dimensionamento da **proporção** adota confiança de 95%, `Z = 1,96`, margem de **5 pontos percentuais** (`E = 0,05`) e `p = 0,50`, escolha conservadora por maximizar `p(1−p)`.

1. `n₀ = Z²p(1−p)/E² = 384,16`.
2. Correção finita: `n = Nn₀/(N+n₀−1) = 381,1908`; arredondamento para **382**.
3. Taxa válida de IA: `rIA = 33.720/49.191 ≈ 68,55%`.
4. Ajuste: `n_aj = ceil(382/rIA) = 558`.

A seleção usa `DataFrame.sample(n=558, replace=False, random_state=42)`: AAS sem reposição, igual probabilidade de inclusão para cada registro e semente fixa. O sorteio abrange toda a base, incluindo registros com respostas ausentes.

**558 registros não garantem exatamente 382 respostas válidas.** O ajuste usa a taxa global como expectativa; a amostra atual tem **374 respostas válidas de IA**. O sorteio não é repetido para atingir o alvo. A margem estimada do IC obtido é 3,89 p.p., sem garantir a precisão conservadora planejada para todo sorteio possível.

## Métodos e denominadores

- **Descrição de experiência:** média, mediana e desvio-padrão, excluindo ausentes. O desvio populacional usa `ddof=0`; o amostral, `ddof=1`: **10,80** e **12,36 anos**, respectivamente.
- **Frequências de IA:** os gráficos incluem “Sem resposta” e usam o total de registros de cada painel. O indicador de uso atual e a inferência usam apenas respostas válidas.
- **Proporção:** IC bilateral de Wald a 95% e testes Z unilaterais à direita, com correção `sqrt((N−n)/(N−1))`. O erro-padrão do teste usa `p₀`; o do IC usa a estimativa amostral.
- **Média:** IC bilateral e testes t de Student, com `n−1` graus de liberdade e `SE = s/sqrt(n) × sqrt((N−n)/N)`.

Em cada análise, `N` e `n` contam respostas válidas da variável. A inferência usa valores e variabilidade da amostra; os parâmetros populacionais são referências de comparação.

A aproximação normal da proporção tem **306 sucessos e 68 insucessos** no IC. Sob H₀, as contagens esperadas são **280,5/93,5** para 75% e **149,6/224,4** para 40%, todas maiores que 10. A média tem 474 observações e 473 graus de liberdade; a aproximação por amostra grande não demonstra normalidade de `WorkExp`.

## Resultados e interpretação

| Indicador | População | Amostra | IC 95% | Diferença amostra − população |
| --- | ---: | ---: | --- | ---: |
| Uso atual de IA | 78,50% | 81,82% | 77,93% a 85,71% | +3,32 p.p. |
| Experiência média | 13,37 anos | 14,31 anos | 13,20 a 15,42 anos | +0,94 ano |

Ambos os ICs contêm o parâmetro populacional. Isso descreve esta amostra; confiança de 95% não garante cobertura em todo sorteio.

| Hipótese nula | Hipótese alternativa | Estatística | Valor-p | Decisão a 5% |
| --- | --- | ---: | ---: | --- |
| Uso de IA: `p ≤ 0,75` | `p > 0,75` | Z = 3,06 | 0,0011 | Rejeitar H₀ |
| Uso diário: `p ≤ 0,40` | `p > 0,40` | Z = 3,33 | 0,0004 | Rejeitar H₀ |
| Experiência: `μ ≤ 10` | `μ > 10` | t = 7,63 | < 0,0001 | Rejeitar H₀ |
| Experiência: `μ = 15` | `μ ≠ 15` | t = −1,22 | 0,2224 | Não rejeitar H₀ |

Os limiares são **referências exploratórias**, não oficiais: 75% e 40% contrastam adoção ampla e uso cotidiano; 10 e 15 anos situam a experiência média. Há evidência para as três primeiras alternativas. Não rejeitar a hipótese de média igual a 15 anos não demonstra igualdade.

## Limitações e revisão matemática

- A AAS representa o CSV, não todos os desenvolvedores. Recrutamento voluntário e não resposta limitam a generalização; excluir ausentes não elimina possíveis vieses.
- As quatro análises são exploratórias, sem ajuste por comparações múltiplas: 5% é a significância por teste, não um controle conjunto.
- Assimetria e extremos de experiência limitam a aproximação t. A faixa inicial dos gráficos vai de 0 a 50 anos, mas os cálculos e a normalização incluem todos os valores válidos, inclusive os acima de 50.
- Reprodutibilidade exige a mesma versão e ordem do CSV. O endereço acompanha a branch `main` e pode ser atualizado; a semente isoladamente não congela os dados.

**Correção identificada:** o IC e os testes da média combinavam `s²` com divisor `n−1` e correção finita com denominador `N−1`. Sob AAS, a expressão coerente é `Var̂(média) = (1−n/N)s²/n` ([Penn State](https://online.stat.psu.edu/stat506/Lesson01)). O erro-padrão e a fórmula exibida foram corrigidos. Os limites do IC mudaram aproximadamente **0,000013 ano**; valores arredondados e decisões permaneceram iguais. Dimensionamento e proporções foram preservados.

## Executar e validar

Na raiz do repositório:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

A primeira carga requer internet para baixar o CSV, mantido em cache pelo Streamlit durante a execução.

Testes leves:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

O notebook `notebook/estudos.ipynb` é auxiliar e não precisa ser executado para abrir o dashboard.
