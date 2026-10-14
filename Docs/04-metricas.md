
# Avaliação e Métricas — Agente de Análise de Feedbacks

## Como Avaliar seu Agente

A avaliação do **Agente de Análise de Feedbacks (FeedbackFlow)** foi realizada por meio de testes estruturados, considerando perguntas sobre os dados consolidados das pesquisas de satisfação e perguntas fora do escopo. A arquitetura inclui um backend Python com FastAPI, ferramentas analíticas determinísticas e execução local do Gemma 3 4B por meio do Ollama, com suporte a chamadas de ferramentas.

Os testes verificaram:
- assertividade;
- segurança contra informações inventadas;
- coerência;
- funcionamento das ferramentas de análise;
- tratamento de perguntas fora do escopo;
- integração entre agente, API e frontend.

---

## Métricas de Qualidade

| Métrica | O que avalia | Resultado dos testes |
|---------|--------------|----------------------|
| **Assertividade** | O agente respondeu ao que foi perguntado usando os dados corretos da base? | **Aprovado nos cenários documentados** — os valores registrados nos testes foram conferidos com a base consolidada. |
| **Segurança** | O agente evitou inventar informações quando não possuía ferramenta ou dado adequado? | **Aprovado no cenário fora do escopo documentado** — informou que não tinha ferramenta para consultar a informação em tempo real. |
| **Coerência** | A resposta é compatível com a pergunta e com os dados analisados? | **Aprovado nos cenários documentados** — as respostas apresentaram valores calculados e contexto compatível com as consultas testadas. |

> [!NOTE]
> Os resultados e números apresentados neste documento correspondem à base consolidada de **244 registros** utilizada nos testes documentados. Eles não devem ser tratados como valores atuais caso a base seja atualizada.

---

## Exemplos de Cenários de Teste

### Teste 1: Métricas gerais

- **Pergunta:** "Qual é o total de respostas?"
- **Resposta esperada:** Informar a quantidade total de registros existentes na base.
- **Resultado:** [x] Correto  [ ] Incorreto
- **Resultado obtido:** **244 respostas**
- **Status:** Aprovado

### Teste 2: Média de CSAT e NPS

- **Pergunta:** "Qual é o CSAT médio e o NPS médio?"
- **Resposta esperada:** Informar as médias calculadas a partir dos dados consolidados.
- **Resultado:** [x] Correto  [ ] Incorreto
- **Resultado obtido:** **CSAT médio: 3,67 | NPS médio: 7,32**
- **Status:** Aprovado

### Teste 3: Principal problema para permanência

- **Pergunta:** "Qual é a principal categoria de problema para permanência?"
- **Resposta esperada:** Informar a categoria com maior frequência na base.
- **Resultado:** [x] Correto  [ ] Incorreto
- **Resultado obtido:** **Acesso a equipamentos — 51 registros**
- **Status:** Aprovado

### Teste 4: Principais categorias de problemas

- **Pergunta:** "Quais são as 3 principais categorias de problemas?"
- **Resposta esperada:** Retornar somente as três categorias mais frequentes.
- **Resultado:** [x] Correto  [ ] Incorreto
- **Status:** Aprovado

> O documento original não registra os nomes e as frequências retornadas nesse teste; por isso, eles não são inferidos aqui.

### Teste 5: Cruzamento entre CSAT e ciclo

- **Pergunta:** "Cruze CSAT e ciclo."
- **Resposta esperada:** Apresentar a distribuição das respostas de CSAT em cada ciclo.
- **Resultado:** [x] Correto  [ ] Incorreto

| Ciclo | Total de respostas | CSAT médio | CSAT 4–5 | % CSAT 4–5 | CSAT 1–2 | % CSAT 1–2 |
|------|--------------------:|-----------:|---------:|-----------:|---------:|-----------:|
| 1 | 235 | 3,69 | 147 | 62,55% | 31 | 13,19% |
| 2 | 9 | 3,33 | 5 | 55,56% | 2 | 22,22% |

**Diferença entre as médias de CSAT:** 0,35 ponto.

> As amostras dos ciclos são diferentes, portanto a comparação deve ser interpretada com cautela.

### Teste 6: Cruzamento entre ciclo e principal problema

- **Pergunta:** "Cruze ciclo e principal problema para permanência."
- **Resultado:** [x] Correto  [ ] Incorreto

| Categoria | Ciclo 1 | Ciclo 2 |
|-----------|--------:|--------:|
| Acesso a equipamentos | 49 | 2 |
| Qualidade do conteúdo | 48 | 2 |
| Plataforma utilizada | 47 | 2 |
| Suporte | 46 | 2 |
| Didática de ensino | 45 | 1 |

**Total analisado:** 244 registros.

> Os valores representam frequências observadas no cruzamento e não indicam, por si só, relação de causa e efeito.

### Teste 7: Correlação entre CSAT e NPS

- **Pergunta:** "Qual é a correlação entre CSAT e NPS?"
- **Resultado:** [x] Correto  [ ] Incorreto
- **Correlação obtida:** **-0,013**
- **Registros considerados:** **244**

A correlação linear observada é negativa e muito próxima de zero, indicando ausência de associação linear relevante nesse conjunto de registros. Esse resultado não demonstra causalidade.

> Correlação não demonstra relação de causa e efeito entre CSAT e NPS.

### Teste 8: Cruzamento entre CSAT e categoria de problemas

- **Pergunta:** "Cruze CSAT e categorias de problemas ou reclamações."
- **Resultado:** [x] Correto  [ ] Incorreto

| CSAT | Principais categorias observadas |
|-----:|----------------------------------|
| 1 | Conteúdo desatualizado (2), Demora em dúvidas de suporte (2), Falta de exemplos práticos (2), Falta de profundidade (2), Equipamento do aluno (1) |
| 2 | Infraestrutura da plataforma de ensino (4), Falta de exemplos práticos (3), Falta de profundidade (3), Demora em dúvidas de suporte (2), Organização e usabilidade do Discord (2) |
| 3 | Infraestrutura da plataforma (13), Falta de profundidade (10), Equipamento do aluno (8), Demora em dúvidas de suporte (7), Solicitação sem retorno (6) |
| 4 | Equipamento do aluno (19), Infraestrutura da plataforma (11), Demora em dúvidas de suporte (10), Falta de profundidade (10), Aula corrida (8) |
| 5 | Solicitação sem retorno (9), Equipamento do aluno (8), Falta de exemplos práticos (8), Infraestrutura da plataforma (7), Demora em dúvidas de suporte (5) |

### Teste 9: Pergunta fora do escopo

- **Pergunta:** "Qual é a previsão do tempo para Fortaleza hoje?"
- **Resposta esperada:** O agente deve informar que não possui ferramenta para consultar dados meteorológicos em tempo real, sem inventar uma previsão.
- **Resultado:** [x] Correto  [ ] Incorreto

**Resposta obtida:**

> "Eu não tenho acesso a ferramentas para consultar dados em tempo real. Portanto, não posso fornecer a previsão do tempo para Fortaleza hoje."

**Status:** Aprovado.

Esse teste confirmou o comportamento de segurança esperado: o agente não inventou uma informação externa à sua base e às suas ferramentas.

---

## Resultados

### O que funcionou bem:

- [x] Consulta das métricas gerais da base.
- [x] Cálculo de CSAT médio.
- [x] Cálculo de NPS médio.
- [x] Identificação da principal categoria de problema.
- [x] Consulta das principais categorias.
- [x] Cruzamento entre variáveis.
- [x] Comparação entre ciclos.
- [x] Correlação entre CSAT e NPS.
- [x] Tratamento de perguntas fora do escopo.
- [x] Uso de ferramentas para consultas relacionadas aos dados.
- [x] Respostas sem invenção de dados.
- [x] Integração entre agente, API e frontend.

### O que pode melhorar:

- [ ] Reduzir a latência das respostas do modelo.
- [ ] Avaliar alternativas para melhorar o desempenho da inferência do Gemma em CPU.
- [ ] Ampliar a quantidade e a variedade de cenários de teste.
- [ ] Monitorar erros, tempos de resposta e falhas de ferramentas.
- [ ] Repetir os testes após alterações no prompt, no modelo, nas ferramentas ou na base consolidada.

---

## Métricas Avançadas

### Latência

Durante os testes documentados, foi observado um tempo de inferência de aproximadamente 162 segundos em uma chamada. O modelo é executado localmente por meio do Ollama, e a medição foi feita no ambiente de desenvolvimento com processamento pela CPU. Esse tempo é uma observação de um teste específico, não uma média nem uma garantia de latência em todas as consultas. A execução local reduz a dependência de APIs de LLM pagas, mas o desempenho varia conforme o hardware, o tamanho da entrada e a complexidade da consulta.

### Ferramentas

O backend disponibiliza ferramentas específicas para consultar e analisar a base. A lista abaixo reflete os nomes registrados na documentação do projeto; a disponibilidade efetiva depende da configuração executada:

- `calcular_metricas`
- `comparar_ciclos`
- `cruzar_variaveis`
- `correlacionar_numericas`
- `top_categorias_problemas`
- `comentarios_por_categoria`

### Base de dados utilizada nos testes

- **244 registros**
- Projetos: **Projeto 1, Projeto 2 e Projeto 4**
- Ciclos: **1 e 2**
- CSAT: escala de **1 a 5**
- NPS: escala de **0 a 10**

### Conclusão

Nos cenários registrados neste documento, o agente consultou a base de feedbacks, utilizou as ferramentas de análise e apresentou resultados coerentes com os dados disponíveis.

O comportamento fora do escopo também foi validado no teste documentado: diante de uma pergunta sobre previsão do tempo em tempo real, o agente informou a limitação sem inventar uma resposta.

O principal ponto técnico observado foi a **latência da inferência do modelo em CPU**. Para manter os resultados confiáveis, recomenda-se ampliar a suíte de testes e repetir a validação sempre que houver mudanças no modelo, no prompt, nas ferramentas ou nos dados.
