import unicodedata
import re
import pandas as pd


# =========================================================
# MAPA DE COLUNAS
# =========================================================

MAPA_COLUNAS = {
    "datahora_registro": [
        "data/hora do registro",
        "data hora do registro",
        "data do registro",
        "datahora_registro"
    ],

    "projeto": [
        "projeto",
        "nome do projeto",
        "projeto/curso",
        "curso"
    ],

    "ciclo": [
        "ciclo"
    ],

    "nome_aluno": [
        "nome do aluno",
        "aluno",
        "nome"
    ],

    "turma": [
        "turma",
        "turma/modulo",
        "turma/módulo",
        "modulo",
        "módulo"
    ],

    "modalidade": [
        "modalidade"
    ],

    "csat": [
        "csat (1 a 5)",
        "csat"
    ],

    "nps": [
        "nps (0 a 10)",
        "nps"
    ],

    "principal_problema_permanencia": [
        "principal problema para permanência",
        "principal problema para permanencia",
        "principal problema"
    ],

    "problema_reclamacao": [
        "problema/reclamação",
        "problema/reclamacao",
        "problema/reclamação relatado",
        "problema/reclamacao relatado",
        "reclamação",
        "reclamacao"
    ],

    "tipos_melhoria_sugerida": [
        "tipos de melhoria sugerida",
        "tipo de melhoria sugerida"
    ],

    "sugestao_melhoria": [
        "sugestão de melhoria",
        "sugestao de melhoria",
        "sugestão",
        "sugestao"
    ],

}


VALORES_AUSENTES = {
    "",
    " ",
    "na",
    "n/a",
    "nao informado",
    "não informado",
    "nao se aplica",
    "não se aplica",
    "-",
    "--"
}

def tratar_valor_ausente(valor):
    """
    Padroniza diferentes formas de ausência de resposta.

    Valores vazios ou equivalentes a 'não informado'
    são convertidos para 'Não informado'.
    """

    if pd.isna(valor):
        return "Não informado"

    valor = str(valor).strip()

    if valor.lower() in VALORES_AUSENTES:
        return "Não informado"

    return valor


def _normalizar_texto(texto):
    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def _construir_mapa_invertido():

    mapa_invertido = {}

    for coluna_padrao, variantes in MAPA_COLUNAS.items():

        for variante in variantes:

            mapa_invertido[
                _normalizar_texto(variante)
            ] = coluna_padrao

    return mapa_invertido


MAPA_INVERTIDO = _construir_mapa_invertido()


# =========================================================
# PADRONIZAÇÃO DE NOMES DE COLUNAS
# =========================================================

def padronizar_colunas(df):

    df = df.copy()

    novas_colunas = {}

    for coluna in df.columns:

        chave = _normalizar_texto(coluna)

        novas_colunas[coluna] = MAPA_INVERTIDO.get(
            chave,
            chave
        )

    df = df.rename(
        columns=novas_colunas
    )

    return df


# =========================================================
# CATEGORIAS JÁ INFORMADAS PELO RESPONDENTE
# =========================================================

CATEGORIAS_VALIDAS = [
    "Acesso a equipamentos",
    "Plataforma utilizada",
    "Qualidade do conteúdo",
    "Didática de ensino",
    "Suporte",
]

_MAPA_CATEGORIAS = {
    _normalizar_texto(c): c
    for c in CATEGORIAS_VALIDAS
}


def padronizar_categoria(valor):

    if pd.isna(valor) or not str(valor).strip():

        return "Não informado"

    chave = _normalizar_texto(valor)

    return _MAPA_CATEGORIAS.get(
        chave,
        "Não informado"
    )


# =========================================================
# VALIDAÇÃO ESTRUTURAL DA PLANILHA
# =========================================================

COLUNAS_OBRIGATORIAS = [
    "datahora_registro",
    "projeto",
    "ciclo",
    "nome_aluno",
    "turma",
    "modalidade",
    "csat",
    "nps",
    "principal_problema_permanencia",
    "problema_reclamacao",
    "tipos_melhoria_sugerida",
]


def validar_estrutura(df):
    """
    Verifica se a planilha possui todas as colunas
    obrigatórias para entrar no consolidado.
    """

    colunas_faltantes = [
        coluna
        for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in df.columns
    ]

    if colunas_faltantes:
        return {
            "valida": False,
            "erro": (
                "Planilha não possui todas as colunas obrigatórias. "
                f"Colunas faltantes: {colunas_faltantes}"
            )
        }

    return {
        "valida": True,
        "erro": None
    }

# =========================================================
# TRATAMENTO DE TIPOS E VALORES
# =========================================================

def tratar_tipos(df):

    df = df.copy()

    # =====================================================
    # CICLO
    # =====================================================

    if "ciclo" in df.columns:
        df["ciclo"] = pd.to_numeric(
            df["ciclo"],
            errors="coerce"
        ).astype("Int64")

    # =====================================================
    # CSAT
    # =====================================================

    if "csat" in df.columns:

        df["csat"] = pd.to_numeric(
            df["csat"],
            errors="coerce"
        )

        # Valores fora da escala 1-5
        # são considerados ausentes.
        df.loc[
            ~df["csat"].between(1, 5)
            & df["csat"].notna(),
            "csat"
        ] = pd.NA

    # =====================================================
    # NPS
    # =====================================================

    if "nps" in df.columns:

        df["nps"] = pd.to_numeric(
            df["nps"],
            errors="coerce"
        )

        # Valores fora da escala 0-10
        # são considerados ausentes.
        df.loc[
            ~df["nps"].between(0, 10)
            & df["nps"].notna(),
            "nps"
        ] = pd.NA

    # =====================================================
    # DATA/HORA
    # =====================================================

    if "datahora_registro" in df.columns:

        df["datahora_registro"] = pd.to_datetime(
            df["datahora_registro"],
            dayfirst=True,
            errors="coerce"
        )

    # =====================================================
    # CAMPOS TEXTUAIS
    # =====================================================

    colunas_textuais = [
    "projeto",
    "nome_aluno",
    "turma",
    "modalidade",
    "tipos_melhoria_sugerida",
    "sugestao_melhoria",
    "problema_reclamacao"
    ]

    for coluna in colunas_textuais:

        if coluna in df.columns:

            df[coluna] = (
                df[coluna]
                .apply(tratar_valor_ausente)
        )

    # =====================================================
    # CATEGORIA DO PROBLEMA DE PERMANÊNCIA
    # =====================================================

    if "principal_problema_permanencia" in df.columns:

        df["principal_problema_permanencia"] = (
            df["principal_problema_permanencia"]
            .apply(padronizar_categoria)
        )

    return df


# =========================================================
# ANONIMIZAÇÃO
# =========================================================

def anonimizar(df):

    """
    Mantém os dados pessoais na planilha consolidada.

    A proteção contra exposição dos dados pessoais será feita
    pelas regras do agente no SYSTEM_PROMPT.
    """

    return df.copy()


# =========================================================
# TRATAMENTO COMPLETO
# =========================================================

def tratar_dataframe(df):

    # 1. Padronizar nomes das colunas
    df = padronizar_colunas(df)

    # 2. Validar estrutura
    validacao = validar_estrutura(df)

    if not validacao["valida"]:
        raise ValueError(validacao["erro"])

    # 3. Tratar tipos e valores
    df = tratar_tipos(df)

    return df


# =========================================================
# TRATAMENTO DE TODAS AS PLANILHAS
# =========================================================

def tratar_lista_planilhas(lista_dfs):

    if not lista_dfs:

        return pd.DataFrame()

    tratados = [
        tratar_dataframe(df)
        for df in lista_dfs
    ]

    consolidado = pd.concat(
        tratados,
        ignore_index=True,
        sort=False
    )

    return consolidado