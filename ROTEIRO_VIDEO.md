# Roteiro de apresentação — 5 minutos

Roteiro-guia com transições naturais, explicações e valores para acompanhar no dashboard. Os tempos são estimados: faça um ensaio para ajustar o ritmo.

Para caber em cinco minutos, **explique o significado dos dados enquanto aponta os números**. Ler cada porcentagem isoladamente deixaria a apresentação corrida.

## 0:00–0:25 — Apresentação e base de dados

*[Mostre o início e abra “Sobre a base de dados”.]*

Comece apresentando o propósito:

> “Neste trabalho, eu apliquei amostragem e inferência estatística aos dados do Stack Overflow Developer Survey de 2025. A ideia foi comparar o que conhecemos da base completa com aquilo que conseguimos estimar usando uma amostra.”

Apresente brevemente:

- **49.191 observações e 172 variáveis** no CSV.
- Cada observação representa **um respondente**.
- `AISelect`: variável qualitativa sobre utilização de IA.
- `WorkExp`: variável quantitativa sobre anos de experiência profissional.

Deixe claro que “população”, neste trabalho, significa **os registros do arquivo utilizado**.

## 0:25–1:15 — Dimensionamento da amostra

*[Feche o expander e acompanhe as três fórmulas com o cursor.]*

Explique a função de cada fórmula, seguindo esta sequência:

1. **Cálculo inicial:** confiança de 95%, `Z = 1,96`, margem de erro de **5 pontos percentuais** e proporção esperada de **50%**. Essa proporção é conservadora porque representa o cenário de maior variabilidade.
2. O resultado inicial é **384,16**. A correção para população finita leva a **381,19**, arredondados para **382**.
3. Como **68,55%** da base possui resposta válida para IA, o ajuste aumenta o tamanho para **558 registros**.

Use uma transição simples:

> “O cálculo define quantos registros selecionar. Depois, eu preciso garantir que essa seleção seja realmente aleatória.”

Explique que utilizou **AAS sem reposição**, com igual chance para cada registro e semente fixa para reproduzir o sorteio.

Finalize com a ressalva:

> “Esse ajuste considera a taxa média de respostas. Ele não garante exatamente 382 respostas válidas: nesta amostra, obtive 374 para IA.”

## 1:15–2:35 — População × amostra

*[Mostre os dois painéis e compare sempre esquerda com direita.]*

Apresente os indicadores como uma comparação:

| Indicador | População | Amostra |
| --- | ---: | ---: |
| Respondentes | 49.191 | 558 |
| Utilizam IA, entre respostas válidas | 78,50% | 81,82% |
| Experiência média | 13,37 anos | 14,31 anos |
| Mediana da experiência | 10 anos | 11 anos |
| Desvio-padrão | 10,80 anos | 12,36 anos |

Explique o significado:

- **Média:** resume o nível médio de experiência.
- **Mediana:** divide as respostas ordenadas ao meio.
- **Desvio-padrão:** mostra a dispersão. A amostra apresenta maior dispersão de experiência.

*[Aponte o histograma e a curva.]*

Cada barra reúne **quatro anos de experiência**. A curva KDE suaviza a distribuição e ajuda a visualizar sua forma. A cauda à direita indica respondentes com experiências mais altas, ajudando a explicar por que a média supera a mediana.

A faixa inicial termina em 50 anos, mas **os cálculos incluem os valores acima dessa faixa**.

*[Desça para as frequências de IA.]*

Explique as categorias e destaque que as distribuições são próximas:

| Categoria | População | Amostra |
| --- | ---: | ---: |
| Uso diário | 32,3% | 32,4% |
| Semanal | 12,1% | 11,6% |
| Ocasional | 9,4% | 10,8% |
| Pretende utilizar | 3,7% | 2,7% |
| Não pretende utilizar | 11,1% | 9,5% |
| Sem resposta | 31,5% | 33,0% |

O ponto essencial para explicar é:

> “Essas barras incluem todos os registros, inclusive os sem resposta. Já o indicador de utilização de IA considera somente quem respondeu à pergunta. Por isso, os denominadores são diferentes.”

Nas análises, há **33.720 e 374 respostas válidas de IA**, respectivamente na população e na amostra; para experiência, **42.893 e 474**.

## 2:35–3:35 — Intervalos de confiança

*[Mostre os dois gráficos e passe o mouse sobre uma barra da amostra.]*

Explique primeiro a lógica das fórmulas: **estimativa mais ou menos uma margem de erro**.

A proporção utiliza a distribuição normal, representada por **Z**. A média utiliza **t de Student**, com a dispersão estimada pela amostra. As fórmulas também consideram o tamanho amostral e a população finita.

Depois interprete:

| Análise | IC de 95% | Amplitude | Diferença amostra − população |
| --- | --- | ---: | ---: |
| Uso de IA | 77,93% a 85,71% | 7,77 p.p. | +3,32 p.p. |
| Experiência média | 13,20 a 15,42 anos | 2,22 anos | +0,94 ano |

Conecte a incerteza ao resultado:

> “A estimativa amostral não precisa coincidir exatamente com o valor populacional. Aqui, os dois intervalos contêm os respectivos parâmetros da população.”

Explique corretamente os 95%: **em repetidos sorteios, esse procedimento produziria intervalos que contêm o parâmetro em aproximadamente 95% das vezes**.

## 3:35–4:35 — Testes de hipóteses

*[Mostre a matriz e percorra suas quatro linhas.]*

Antes dos resultados, esclareça:

- **H₀:** hipótese de referência.
- **H₁:** alternativa investigada.
- **Z e t:** distância entre a estimativa e a referência, medida em erros-padrão.
- **Valor-p:** sob H₀, probabilidade de um resultado tão extremo quanto o observado ou mais.
- A linha amarela marca **0,05**, equivalente à significância de **5%**.

Use a tabela para orientar a explicação:

| Pergunta investigada | Estatística | Valor-p | Interpretação |
| --- | ---: | ---: | --- |
| Uso de IA supera 75%? | Z = 3,06 | 0,0011 | Há evidência de que supera |
| Uso diário supera 40%? | Z = 3,33 | 0,0004 | Há evidência de que supera |
| Experiência média supera 10 anos? | t = 7,63 | < 0,0001 | Há evidência de que supera |
| Experiência média difere de 15 anos? | t = −1,22 | 0,2224 | Evidência insuficiente de diferença |

Dê destaque à última linha:

> “Não rejeitar a hipótese de média igual a quinze anos não significa comprovar essa igualdade. Significa que esta amostra não trouxe evidência suficiente para concluir que existe diferença.”

## 4:35–5:00 — Limitações e conclusão

*[Aponte “Notas metodológicas”; abra somente se houver tempo.]*

Finalize conectando o método às suas limitações:

> “A comparação mostrou estimativas próximas dos parâmetros da base, acompanhadas de uma medida de incerteza. Mas outro sorteio poderia produzir resultados diferentes. Além disso, a pesquisa original é voluntária: a amostra representa o CSV analisado, e não todos os desenvolvedores.”

Mencione que os quatro testes são **exploratórios, sem ajuste conjunto para comparações múltiplas**.

Encerre com a contribuição do projeto:

> “O trabalho permitiu acompanhar o processo completo: dimensionar e selecionar uma amostra, descrever os dados e interpretar estimativas e testes com suas limitações.”

## Orientações para a gravação

Ensaie usando esses blocos como referência. Faça pequenas pausas nas mudanças de etapa e use o cursor para acompanhar a explicação. Se o ensaio ultrapassar cinco minutos, reduza a leitura dos percentuais das categorias e mantenha a explicação sobre seus denominadores.

As indicações entre colchetes são ações na tela, não falas. As tabelas são apoio para a apresentação, não uma obrigação de leitura linha a linha.
