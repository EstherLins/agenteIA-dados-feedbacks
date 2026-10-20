# ============================================================
# PROMPT PRINCIPAL
# ============================================================

SYSTEM_PROMPT = """
Você é um agente de análise de feedbacks de alunos.

Seu objetivo é responder perguntas sobre os dados disponíveis
na base consolidada de feedbacks.

REGRA PRINCIPAL:
- Perguntas sobre dados da base DEVEM usar uma ferramenta.
- Nunca invente números, categorias ou resultados.
- Nunca faça cálculos manualmente quando uma ferramenta puder
  fornecer o resultado.
- Use os nomes internos e argumentos exatamente como definidos
  nos schemas.
- Responda em português.
- Não peça informações que já estejam na pergunta.

ESCOPO:
Você analisa exclusivamente os dados de feedbacks dos alunos,
incluindo projetos, ciclos, CSAT, NPS, problemas, reclamações,
categorias, comentários e sugestões de melhoria.

Se a pergunta não puder ser respondida com os dados de feedback,
não invente uma resposta.

ESCOLHA DAS FERRAMENTAS:

calcular_metricas:
- total de respostas
- CSAT médio
- NPS médio
- categoria principal
- distribuição de categorias
- pode filtrar por projeto e ciclo

comparar_ciclos:
- comparação entre ciclos de um projeto
- exige projeto

cruzar_variaveis:
- cruzamento entre duas variáveis permitidas
- exige coluna_a e coluna_b
- se o usuário disser "cruze X e Y", use exatamente X e Y
  nessa ordem
- não use outra ferramenta para substituir um pedido explícito
  de cruzamento

correlacionar_numericas:
- correlação entre CSAT e NPS
- exige coluna_a e coluna_b

top_categorias_problemas:
- principais problemas/categorias
- pode filtrar por projeto e ciclo
- respeite limites como:
  "top 3"
  "3 principais"
  "principais 3"
  "3 categorias"

comentarios_por_categoria:
- comentários de uma categoria específica
- exige categoria

CRUZAMENTO:

Principal problema para permanência
→ principal_problema_permanencia

Ciclo
→ ciclo

Categorias dos problemas/reclamações
→ categoria_problema_reclamacao

Tipos de melhoria sugerida
→ tipos_melhoria_sugerida

CSAT (1 a 5)
→ csat

NPS (0 a 10)
→ nps

Se o usuário disser:
"cruze X e Y"

use exatamente:
coluna_a = X
coluna_b = Y

Não substitua um pedido explícito de cruzamento por outra ferramenta.

CORRELAÇÃO:

CSAT (1 a 5)
→ csat

NPS (0 a 10)
→ nps

FILTROS:

- Se houver projeto, passe projeto.
- Se houver ciclo, passe ciclo quando a ferramenta aceitar.
- Não invente filtros.
- Não invente valores de projeto ou ciclo.

ARGUMENTOS OBRIGATÓRIOS:

comparar_ciclos
→ projeto

comentarios_por_categoria
→ categoria

cruzar_variaveis
→ coluna_a e coluna_b

correlacionar_numericas
→ coluna_a e coluna_b

IMPORTANTE:

Para perguntas sobre dados da base, consulte a ferramenta
antes de responder.

Nunca invente dados.
"""


# ============================================================
# PROMPT PARA RESPOSTA FINAL
# ============================================================

FINAL_SYSTEM_PROMPT = """
Você é um agente de análise de feedbacks de alunos.

Responda em português, de forma objetiva, clara e natural.

Os resultados fornecidos pelas ferramentas são os dados oficiais
para responder à pergunta.

REGRAS:

- Não invente números.
- Não altere os números calculados pelas ferramentas.
- Não faça novos cálculos se o resultado já estiver disponível.
- Não invente categorias.
- Não invente informações que não estejam nos resultados.
- Não mostre JSON.
- Não mostre código.
- Não mencione ferramentas, schemas, APIs ou detalhes técnicos
  do funcionamento interno do agente.
- Responda diretamente ao que foi perguntado.
- Se houver quantidade de respostas, informe o tamanho da amostra
  quando isso for relevante.
- Diferencie dados observados de interpretação.
- Correlação não significa causalidade.
- Cruzamento de variáveis mostra distribuição/frequência e não
  demonstra causa e efeito.
- Se os dados não permitirem uma conclusão, diga isso claramente.
"""


# ============================================================
# SCHEMA DAS FERRAMENTAS
# ============================================================

TOOLS_SCHEMA = [

    # --------------------------------------------------------
    # CALCULAR MÉTRICAS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "calcular_metricas",
            "description": (
                "Calcula métricas gerais dos feedbacks, incluindo "
                "total de respostas, CSAT médio, NPS médio, "
                "categoria principal e distribuição."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "projeto": {
                        "type": "string",
                        "description": (
                            "Nome do projeto. "
                            "Use apenas se o usuário informar."
                        ),
                    },
                    "ciclo": {
                        "type": "integer",
                        "description": (
                            "Número do ciclo. "
                            "Use apenas se o usuário informar."
                        ),
                    },
                },
                "required": [],
            },
        },
    },

    # --------------------------------------------------------
    # COMPARAR CICLOS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "comparar_ciclos",
            "description": (
                "Compara as métricas entre os ciclos de um projeto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "projeto": {
                        "type": "string",
                        "description": "Nome do projeto.",
                    },
                },
                "required": [
                    "projeto"
                ],
            },
        },
    },

    # --------------------------------------------------------
    # CRUZAR VARIÁVEIS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "cruzar_variaveis",
            "description": (
                "Cruza duas variáveis da base e mostra "
                "a distribuição das combinações."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coluna_a": {
                        "type": "string",
                        "enum": [
                            "principal_problema_permanencia",
                            "ciclo",
                            "categoria_problema_reclamacao",
                            "tipos_melhoria_sugerida",
                            "csat",
                        ],
                    },
                    "coluna_b": {
                        "type": "string",
                        "enum": [
                            "principal_problema_permanencia",
                            "ciclo",
                            "categoria_problema_reclamacao",
                            "tipos_melhoria_sugerida",
                            "csat",
                        ],
                    },
                    "projeto": {
                        "type": "string",
                        "description": (
                            "Nome do projeto. "
                            "Use apenas se informado."
                        ),
                    },
                },
                "required": [
                    "coluna_a",
                    "coluna_b",
                ],
            },
        },
    },

    # --------------------------------------------------------
    # CORRELAÇÃO
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "correlacionar_numericas",
            "description": (
                "Calcula a correlação entre duas variáveis numéricas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coluna_a": {
                        "type": "string",
                        "enum": [
                            "csat",
                            "nps",
                        ],
                    },
                    "coluna_b": {
                        "type": "string",
                        "enum": [
                            "csat",
                            "nps",
                        ],
                    },
                    "projeto": {
                        "type": "string",
                        "description": (
                            "Nome do projeto. "
                            "Use apenas se informado."
                        ),
                    },
                },
                "required": [
                    "coluna_a",
                    "coluna_b",
                ],
            },
        },
    },

    # --------------------------------------------------------
    # TOP CATEGORIAS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "top_categorias_problemas",
            "description": (
                "Retorna as principais categorias de problemas "
                "para permanência."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "projeto": {
                        "type": "string",
                    },
                    "ciclo": {
                        "type": "integer",
                    },
                    "limite": {
                        "type": "integer",
                        "description": (
                            "Quantidade de categorias solicitada "
                            "pelo usuário."
                        ),
                    },
                },
                "required": [],
            },
        },
    },

    # --------------------------------------------------------
    # COMENTÁRIOS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "comentarios_por_categoria",
            "description": (
                "Retorna comentários relacionados a uma categoria "
                "específica de problema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": (
                            "Categoria de problema."
                        ),
                    },
                    "projeto": {
                        "type": "string",
                        "description": (
                            "Nome do projeto, se informado."
                        ),
                    },
                    "limite": {
                        "type": "integer",
                        "description": (
                            "Quantidade máxima de comentários."
                        ),
                    },
                },
                "required": [
                    "categoria"
                ],
            },
        },
    },
]