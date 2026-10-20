import time

from Tratamento import metricas
from Saida import shets_consolidada


# ============================================================
# CACHE
# ============================================================

_CACHE = {
    "df": None,
    "carregado_em": 0,
}

# 5 minutos
_TTL_SEGUNDOS = 300


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

def obter_dados():

    agora = time.time()

    precisa_carregar = (
        _CACHE["df"] is None
        or
        (
            agora - _CACHE["carregado_em"]
            > _TTL_SEGUNDOS
        )
    )

    if precisa_carregar:

        print("=" * 70)
        print("CARREGANDO BASE CONSOLIDADA")
        print("=" * 70)

        _CACHE["df"] = (
            shets_consolidada
            .carregar_dados_consolidados()
        )

        _CACHE["carregado_em"] = agora

        print(
            "REGISTROS CARREGADOS:",
            len(_CACHE["df"])
        )

    return _CACHE["df"]


# ============================================================
# FORÇAR RECARGA
# ============================================================

def forcar_recarga():

    print("=" * 70)
    print("FORÇANDO RECARGA DA BASE")
    print("=" * 70)

    _CACHE["df"] = (
        shets_consolidada
        .carregar_dados_consolidados()
    )

    _CACHE["carregado_em"] = time.time()

    print(
        "REGISTROS CARREGADOS:",
        len(_CACHE["df"])
    )


# ============================================================
# MÉTRICAS
# ============================================================

def calcular_metricas(
    projeto=None,
    ciclo=None
):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.calcular_metricas(
        df,
        projeto,
        ciclo
    )


# ============================================================
# COMPARAR CICLOS
# ============================================================

def comparar_ciclos(projeto):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.comparar_ciclos(
        df,
        projeto
    )


# ============================================================
# CRUZAR VARIÁVEIS
# ============================================================

def cruzar_variaveis(
    coluna_a,
    coluna_b,
    projeto=None
):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.cruzar_variaveis(
        df,
        coluna_a,
        coluna_b,
        projeto
    )


# ============================================================
# CORRELAÇÃO
# ============================================================

def correlacionar_numericas(
    coluna_a,
    coluna_b,
    projeto=None
):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.correlacionar_numericas(
        df,
        coluna_a,
        coluna_b,
        projeto
    )


# ============================================================
# TOP CATEGORIAS
# ============================================================

def top_categorias_problemas(
    projeto=None,
    ciclo=None,
    limite=5
):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.top_categorias_problemas(
        df,
        projeto,
        ciclo,
        limite
    )


# ============================================================
# COMENTÁRIOS POR CATEGORIA
# ============================================================

def comentarios_por_categoria(
    categoria,
    projeto=None,
    limite=5
):

    df = obter_dados()

    if df.empty:
        return {
            "erro":
                "Base consolidada ainda não possui dados."
        }

    return metricas.comentarios_por_categoria(
        df,
        categoria,
        projeto,
        limite
    )


# ============================================================
# FERRAMENTAS DISPONÍVEIS
# ============================================================

FERRAMENTAS_DISPONIVEIS = {

    "calcular_metricas":
        calcular_metricas,

    "comparar_ciclos":
        comparar_ciclos,

    "cruzar_variaveis":
        cruzar_variaveis,

    "correlacionar_numericas":
        correlacionar_numericas,

    "top_categorias_problemas":
        top_categorias_problemas,

    "comentarios_por_categoria":
        comentarios_por_categoria,
}