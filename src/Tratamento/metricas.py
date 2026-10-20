import pandas as pd


# ============================================================
# COLUNAS NUMÉRICAS VÁLIDAS
# ============================================================

COLUNAS_NUMERICAS_VALIDAS = [
    "csat",
    "nps",
]


# ============================================================
# VALIDAÇÃO DE PROJETO
# ============================================================

def validar_projeto(df, projeto):

    if projeto is None:
        return

    projetos = sorted(
        df["projeto"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if str(projeto) not in projetos:
        raise ValueError(
            f"Projeto '{projeto}' não encontrado. "
            f"Projetos disponíveis: {projetos}"
        )


# ============================================================
# FILTRO
# ============================================================

def filtrar(
    df,
    projeto=None,
    ciclo=None
):

    resultado = df.copy()

    if projeto is not None:

        validar_projeto(
            resultado,
            projeto
        )

        resultado = resultado[
            resultado["projeto"].astype(str)
            == str(projeto)
        ]

    if ciclo is not None:

        resultado = resultado[
            pd.to_numeric(
                resultado["ciclo"],
                errors="coerce"
            )
            == ciclo
        ]

    return resultado


# ============================================================
# MÉTRICAS GERAIS
# ============================================================

def calcular_metricas(
    df,
    projeto=None,
    ciclo=None
):

    df_filtrado = filtrar(
        df,
        projeto,
        ciclo
    )

    if df_filtrado.empty:
        raise ValueError(
            "Nenhum registro encontrado para os filtros informados."
        )

    csat = pd.to_numeric(
        df_filtrado["csat"],
        errors="coerce"
    )

    nps = pd.to_numeric(
        df_filtrado["nps"],
        errors="coerce"
    )

    principal = (
        df_filtrado[
            "principal_problema_permanencia"
        ]
        .dropna()
        .astype(str)
    )

    if not principal.empty:
        categoria_principal = (
            principal
            .value_counts()
            .index[0]
        )

        distribuicao = (
            principal
            .value_counts()
            .to_dict()
        )

    else:
        categoria_principal = None
        distribuicao = {}

    return {

        "projeto": projeto,

        "ciclo": ciclo,

        "total_respostas":
            len(df_filtrado),

        "csat_medio":
            round(
                csat.mean(),
                2
            )
            if csat.notna().any()
            else None,

        "nps_medio":
            round(
                nps.mean(),
                2
            )
            if nps.notna().any()
            else None,

        "categoria_principal":
            categoria_principal,

        "distribuicao_categorias":
            distribuicao,
    }


# ============================================================
# COMPARAR CICLOS
# ============================================================

def comparar_ciclos(
    df,
    projeto
):

    validar_projeto(
        df,
        projeto
    )

    df_projeto = filtrar(
        df,
        projeto=projeto
    )

    ciclos = sorted(
        pd.to_numeric(
            df_projeto["ciclo"],
            errors="coerce"
        )
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if len(ciclos) < 2:
        raise ValueError(
            "O projeto informado não possui pelo menos dois ciclos."
        )

    resultado = {
        "projeto": projeto
    }

    for ciclo in ciclos:

        dados = filtrar(
            df_projeto,
            ciclo=ciclo
        )

        csat = pd.to_numeric(
            dados["csat"],
            errors="coerce"
        )

        nps = pd.to_numeric(
            dados["nps"],
            errors="coerce"
        )

        resultado[
            f"ciclo_{ciclo}"
        ] = {

            "total_respostas":
                len(dados),

            "csat_medio":
                round(
                    csat.mean(),
                    2
                )
                if csat.notna().any()
                else None,

            "nps_medio":
                round(
                    nps.mean(),
                    2
                )
                if nps.notna().any()
                else None,
        }

    return resultado


# ============================================================
# CRUZAMENTO DE VARIÁVEIS
# ============================================================

def cruzar_variaveis(
    df,
    coluna_a,
    coluna_b,
    projeto=None
):

    colunas_validas = [
        "principal_problema_permanencia",
        "ciclo",
        "categoria_problema_reclamacao",
        "tipos_melhoria_sugerida",
        "csat",
    ]

    if coluna_a not in colunas_validas:
        raise ValueError(
            f"Variável inválida: {coluna_a}"
        )

    if coluna_b not in colunas_validas:
        raise ValueError(
            f"Variável inválida: {coluna_b}"
        )

    df_filtrado = filtrar(
        df,
        projeto=projeto
    )

    dados = df_filtrado[
        [
            coluna_a,
            coluna_b
        ]
    ].copy()

    dados = dados.dropna(
        subset=[
            coluna_a,
            coluna_b
        ]
    )

    if dados.empty:
        raise ValueError(
            "Não existem dados suficientes para realizar o cruzamento."
        )

    # --------------------------------------------------------
    # Normalização numérica
    # --------------------------------------------------------

    if coluna_a == "csat":
        dados[coluna_a] = pd.to_numeric(
            dados[coluna_a],
            errors="coerce"
        )

    if coluna_b == "csat":
        dados[coluna_b] = pd.to_numeric(
            dados[coluna_b],
            errors="coerce"
        )

    if coluna_a == "ciclo":
        dados[coluna_a] = pd.to_numeric(
            dados[coluna_a],
            errors="coerce"
        )

    if coluna_b == "ciclo":
        dados[coluna_b] = pd.to_numeric(
            dados[coluna_b],
            errors="coerce"
        )

    dados = dados.dropna()

    tabela = (
        dados
        .groupby(
            [
                coluna_a,
                coluna_b
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="quantidade"
        )
    )

    resultado = []

    for _, linha in tabela.iterrows():

        resultado.append({

            coluna_a:
                linha[coluna_a],

            coluna_b:
                linha[coluna_b],

            "quantidade":
                int(linha["quantidade"]),
        })

    resposta = {

        "projeto":
            projeto,

        "variavel_a":
            coluna_a,

        "variavel_b":
            coluna_b,

        "total_registros":
            len(dados),

        "resultado":
            resultado,
    }

    # --------------------------------------------------------
    # Análise específica ciclo × CSAT
    # --------------------------------------------------------

    if {
        coluna_a,
        coluna_b
    } == {
        "ciclo",
        "csat"
    }:

        analise = {}

        ciclos = sorted(
            dados["ciclo"]
            .dropna()
            .unique()
            .tolist()
        )

        for ciclo in ciclos:

            ciclo_dados = dados[
                dados["ciclo"] == ciclo
            ]

            csat_valores = pd.to_numeric(
                ciclo_dados["csat"],
                errors="coerce"
            ).dropna()

            total = len(csat_valores)

            csat_medio = (
                csat_valores.mean()
                if total > 0
                else None
            )

            csat_4_5 = int(
                (
                    csat_valores
                    .isin([4, 5])
                ).sum()
            )

            csat_1_2 = int(
                (
                    csat_valores
                    .isin([1, 2])
                ).sum()
            )

            percentual_4_5 = (
                (csat_4_5 / total) * 100
                if total > 0
                else 0
            )

            percentual_1_2 = (
                (csat_1_2 / total) * 100
                if total > 0
                else 0
            )

            analise[
                f"ciclo_{int(ciclo)}"
            ] = {

                "total_respostas":
                    total,

                "csat_medio":
                    round(
                        csat_medio,
                        2
                    )
                    if csat_medio is not None
                    else None,

                "csat_4_5":
                    csat_4_5,

                "percentual_csat_4_5":
                    round(
                        percentual_4_5,
                        2
                    ),

                "csat_1_2":
                    csat_1_2,

                "percentual_csat_1_2":
                    round(
                        percentual_1_2,
                        2
                    ),
            }

        if len(analise) >= 2:

            chaves = sorted(
                analise.keys()
            )

            primeiro = analise[chaves[0]]
            segundo = analise[chaves[1]]

            diferenca_media = (
                primeiro["csat_medio"]
                - segundo["csat_medio"]
            )

            diferenca_percentual = (
                primeiro["percentual_csat_4_5"]
                - segundo["percentual_csat_4_5"]
            )

            maior_media = (
                chaves[0]
                if primeiro["csat_medio"]
                > segundo["csat_medio"]
                else chaves[1]
            )

            maior_percentual = (
                chaves[0]
                if primeiro["percentual_csat_4_5"]
                > segundo["percentual_csat_4_5"]
                else chaves[1]
            )

            analise["comparacao"] = {

                "ciclos_comparados": [
                    int(
                        chaves[0].replace(
                            "ciclo_",
                            ""
                        )
                    ),
                    int(
                        chaves[1].replace(
                            "ciclo_",
                            ""
                        )
                    ),
                ],

                "diferenca_csat_medio":
                    round(
                        diferenca_media,
                        2
                    ),

                "diferenca_percentual_csat_4_5":
                    round(
                        diferenca_percentual,
                        2
                    ),

                "maior_csat_medio":
                    maior_media,

                "maior_percentual_csat_4_5":
                    maior_percentual,

                "amostras_diferentes":
                    primeiro["total_respostas"]
                    !=
                    segundo["total_respostas"],
            }

        resposta["analise"] = analise

    return resposta


# ============================================================
# CORRELAÇÃO
# ============================================================

def correlacionar_numericas(
    df,
    coluna_a,
    coluna_b,
    projeto=None
):

    if coluna_a not in COLUNAS_NUMERICAS_VALIDAS:
        raise ValueError(
            f"Variável numérica inválida: {coluna_a}"
        )

    if coluna_b not in COLUNAS_NUMERICAS_VALIDAS:
        raise ValueError(
            f"Variável numérica inválida: {coluna_b}"
        )

    if coluna_a == coluna_b:
        raise ValueError(
            "As duas variáveis precisam ser diferentes."
        )

    dados = filtrar(
        df,
        projeto=projeto
    )[
        [
            coluna_a,
            coluna_b
        ]
    ].copy()

    dados[coluna_a] = pd.to_numeric(
        dados[coluna_a],
        errors="coerce"
    )

    dados[coluna_b] = pd.to_numeric(
        dados[coluna_b],
        errors="coerce"
    )

    dados = dados.dropna()

    if len(dados) < 3:
        raise ValueError(
            "Não existem registros suficientes para calcular a correlação."
        )

    correlacao = dados[
        coluna_a
    ].corr(
        dados[coluna_b]
    )

    return {

        "projeto":
            projeto,

        "variavel_a":
            coluna_a,

        "variavel_b":
            coluna_b,

        "correlacao":
            round(
                float(correlacao),
                3
            ),

        "registros":
            len(dados),
    }


# ============================================================
# TOP CATEGORIAS
# ============================================================

def top_categorias_problemas(
    df,
    projeto=None,
    ciclo=None,
    limite=5
):

    dados = filtrar(
        df,
        projeto,
        ciclo
    )

    if dados.empty:
        raise ValueError(
            "Nenhum registro encontrado para os filtros informados."
        )

    categorias = (
        dados[
            "principal_problema_permanencia"
        ]
        .dropna()
        .astype(str)
    )

    contagem = (
        categorias
        .value_counts()
    )

    total = contagem.sum()

    resultado = []

    for categoria, quantidade in (
        contagem
        .head(limite)
        .items()
    ):

        percentual = (
            quantidade / total * 100
        )

        resultado.append({

            "categoria":
                categoria,

            "quantidade":
                int(quantidade),

            "percentual":
                round(
                    percentual,
                    2
                ),
        })

    return {

        "projeto":
            projeto,

        "ciclo":
            ciclo,

        "categorias":
            resultado,
    }


# ============================================================
# COMENTÁRIOS POR CATEGORIA
# ============================================================

def comentarios_por_categoria(
    df,
    categoria,
    projeto=None,
    limite=5
):

    dados = filtrar(
        df,
        projeto=projeto
    )

    dados = dados[
        dados[
            "principal_problema_permanencia"
        ]
        .astype(str)
        .str.strip()
        ==
        str(categoria).strip()
    ]

    if dados.empty:
        return {

            "categoria":
                categoria,

            "total_na_categoria":
                0,

            "exemplos":
                [],
        }

    comentarios = (
        dados[
            "problema_reclamacao"
        ]
        .dropna()
        .astype(str)
        .str.strip()
    )

    comentarios = comentarios[
        comentarios != ""
    ]

    exemplos = (
        comentarios
        .drop_duplicates()
        .head(limite)
        .tolist()
    )

    return {

        "categoria":
            categoria,

        "projeto":
            projeto,

        "total_na_categoria":
            len(dados),

        "exemplos":
            exemplos,
    }