import pandas as pd

import gspread

from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_CREDENTIALS_FILE,
    SHEET_CONSOLIDADA_ID,
    SHEET_CONSOLIDADA_ABA
)


# =========================================================
# COLUNAS INTERNAS DO DATAFRAME
# =========================================================

COLUNAS_CONSOLIDADO = [

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

    "sugestao_melhoria",

    "id_planilha_origem",

    "arquivo_origem",

    "id_registro",

    "categoria_problema_reclamacao"

]


# =========================================================
# NOMES DAS COLUNAS NA PLANILHA
# =========================================================

NOMES_COLUNAS_PLANILHA = [

    "Data/Hora do Registro",

    "Projeto",

    "Ciclo",

    "Nome do Aluno",

    "Turma",

    "Modalidade",

    "CSAT (1 a 5)",

    "NPS (0 a 10)",

    "Principal problema para permanência",

    "Problema/Reclamação relatado",

    "Tipos de melhoria sugerida",

    "Sugestão de melhoria",

    "ID da planilha de origem",

    "Arquivo de origem",

    "id_registro",

    "Categorias dos problemas/reclamações"

]


# =========================================================
# PERMISSÕES
# =========================================================

SCOPES = [

    "https://www.googleapis.com/auth/drive",

    "https://www.googleapis.com/auth/spreadsheets"

]


# =========================================================
# CONEXÃO COM GOOGLE SHEETS
# =========================================================

def conectar_consolidado():

    credentials = Credentials.from_service_account_file(

        GOOGLE_CREDENTIALS_FILE,

        scopes=SCOPES

    )

    gc = gspread.authorize(credentials)

    planilha = gc.open_by_key(

        SHEET_CONSOLIDADA_ID

    )

    return planilha


# =========================================================
# OBTER / CRIAR ABA DADOS
# =========================================================

def obter_aba_dados():

    planilha = conectar_consolidado()

    print(
        f"Planilha consolidada: {planilha.title}"
    )

    print(
        f"Aba configurada: {SHEET_CONSOLIDADA_ABA}"
    )

    try:

        aba = planilha.worksheet(

            SHEET_CONSOLIDADA_ABA

        )

        print(
            f"Acessando aba existente: {aba.title}"
        )

    except gspread.WorksheetNotFound:

        print(
            f"Aba '{SHEET_CONSOLIDADA_ABA}' não existe."
        )

        print(
            "Criando nova aba..."
        )

        aba = planilha.add_worksheet(

            title=SHEET_CONSOLIDADA_ABA,

            rows=1000,

            cols=30

        )

    return aba


# =========================================================
# PREPARAR DATAFRAME
# =========================================================

def preparar_dataframe(df):

    df = df.copy()

    # -----------------------------------------------------
    # Garantir que todas as colunas existam
    # -----------------------------------------------------

    for coluna in COLUNAS_CONSOLIDADO:

        if coluna not in df.columns:

            df[coluna] = pd.NA

    # -----------------------------------------------------
    # Manter SOMENTE as colunas do consolidado
    # -----------------------------------------------------

    df = df[COLUNAS_CONSOLIDADO]

    # -----------------------------------------------------
    # Converter datas
    # -----------------------------------------------------

    if "datahora_registro" in df.columns:

        if pd.api.types.is_datetime64_any_dtype(
            df["datahora_registro"]
        ):

            df["datahora_registro"] = (

                df["datahora_registro"]

                .dt.strftime("%Y-%m-%d %H:%M:%S")

            )

    # -----------------------------------------------------
    # GARANTIR QUE CICLO, CSAT E NPS SEJAM NUMÉRICOS
    # -----------------------------------------------------

    colunas_numericas = [

        "ciclo",

        "csat",

        "nps"

    ]

    for coluna in colunas_numericas:

        df[coluna] = pd.to_numeric(

            df[coluna],

            errors="coerce"

        )

    # -----------------------------------------------------
    # Tratar valores ausentes das colunas numéricas
    # -----------------------------------------------------
    # Não usamos "Não informado" aqui porque essas colunas
    # precisam continuar numéricas.
    #
    # O Google Sheets receberá célula vazia quando não
    # houver valor.
    # -----------------------------------------------------

    for coluna in colunas_numericas:

        df[coluna] = df[coluna].astype(object)

        df[coluna] = df[coluna].where(

            df[coluna].notna(),

            None

        )

    # -----------------------------------------------------
    # Tratar valores ausentes das demais colunas
    # -----------------------------------------------------

    colunas_texto = [

        coluna

        for coluna in COLUNAS_CONSOLIDADO

        if coluna not in colunas_numericas

    ]

    for coluna in colunas_texto:

        df[coluna] = (

            df[coluna]

            .fillna("Não informado")

            .astype(str)

        )

    # -----------------------------------------------------
    # Garantir valores simples
    # -----------------------------------------------------

    # IMPORTANTE:
    # NÃO fazemos df.astype(str) aqui.
    #
    # Isso preserva:
    # ciclo -> número
    # csat  -> número
    # nps   -> número

    return df


# =========================================================
# SALVAR NOVOS REGISTROS
# =========================================================

def salvar_novos_registros(df):

    if df.empty:

        print("Nenhum registro para salvar.")

        return

    print(
        "Preparando registros para salvar..."
    )

    aba = obter_aba_dados()

    print(
        f"Aba encontrada: {aba.title}"
    )

    print(
        f"ID da planilha: {aba.spreadsheet.id}"
    )

    # -----------------------------------------------------
    # PREPARAR DATAFRAME
    # -----------------------------------------------------

    df = preparar_dataframe(df)

    print(
        f"Quantidade de registros: {len(df)}"
    )

    print(
        f"Quantidade de colunas: {len(df.columns)}"
    )

    # -----------------------------------------------------
    # VERIFICAR CABEÇALHO
    # -----------------------------------------------------

    registros_existentes = aba.get_all_values()

    if not registros_existentes:

        print(
            "Aba vazia. Criando cabeçalho..."
        )

        aba.update(

            "A1",

            [NOMES_COLUNAS_PLANILHA]

        )

    # -----------------------------------------------------
    # PREPARAR VALORES
    # -----------------------------------------------------

    # -----------------------------------------------------
    # PREPARAR VALORES
    # -----------------------------------------------------

    def _limpar_valor(valor):

        if valor is None:

            return ""

        if isinstance(valor, float) and pd.isna(valor):

            return ""

        return valor

    valores = [

        [_limpar_valor(v) for v in linha]

        for linha in df.values.tolist()

    ]

    print(
        f"Enviando {len(valores)} registros para o Google Sheets..."
    )

    # -----------------------------------------------------
    # SALVAR
    # -----------------------------------------------------

    resultado = aba.append_rows(

        valores,

        value_input_option="RAW"

    )

    print(
        "Google Sheets confirmou o salvamento."
    )

    print(
        f"Resultado: {resultado}"
    )

    # -----------------------------------------------------
    # VERIFICAÇÃO
    # -----------------------------------------------------

    total_linhas = len(
        aba.get_all_values()
    )

    print(
        f"Total de linhas na aba após salvamento: {total_linhas}"
    )


# =========================================================
# CARREGAR DADOS CONSOLIDADOS
# =========================================================

def carregar_dados_consolidados():
    aba = obter_aba_dados()

    dados = aba.get_all_records()

    if not dados:
        return pd.DataFrame()

    df = pd.DataFrame(dados)

    # =====================================================
    # CONVERTER NOMES DA PLANILHA PARA NOMES INTERNOS
    # =====================================================

    mapa_colunas = {
        "Data/Hora do Registro": "datahora_registro",
        "Projeto": "projeto",
        "Ciclo": "ciclo",
        "Nome do Aluno": "nome_aluno",
        "Turma": "turma",
        "Modalidade": "modalidade",
        "CSAT (1 a 5)": "csat",
        "NPS (0 a 10)": "nps",
        "Principal problema para permanência":
            "principal_problema_permanencia",
        "Problema/Reclamação":
            "problema_reclamacao",
        "Problema/Reclamação relatado":
            "problema_reclamacao",
        "Tipos de melhoria sugerida":
            "tipos_melhoria_sugerida",
        "Sugestão de melhoria":
            "sugestao_melhoria",
        "ID da planilha de origem":
            "id_planilha_origem",
        "Arquivo de origem":
            "arquivo_origem",
        "id_registro":
            "id_registro",
        "Categorias dos problemas/reclamações":
            "categoria_problema_reclamacao"
    }

    df = df.rename(columns=mapa_colunas)

    # =====================================================
    # GARANTIR COLUNAS INTERNAS
    # =====================================================

    for coluna in COLUNAS_CONSOLIDADO:
        if coluna not in df.columns:
            df[coluna] = pd.NA

    # =====================================================
    # MANTER SOMENTE AS COLUNAS INTERNAS
    # =====================================================

    df = df[COLUNAS_CONSOLIDADO]

    # =====================================================
    # CONVERTER CAMPOS NUMÉRICOS
    # =====================================================

    for coluna in ["ciclo", "csat", "nps"]:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    # =====================================================
    # DIAGNÓSTICO
    # =====================================================

    print("====================================")
    print("DIAGNÓSTICO DA BASE CONSOLIDADA")
    print("====================================")
    print("TOTAL DE REGISTROS:", len(df))
    print(
        "PROJETOS:",
        df["projeto"].dropna().unique().tolist()
    )
    print(
        "CICLOS:",
        df["ciclo"].dropna().unique().tolist()
    )
    print("TIPO CSAT:", df["csat"].dtype)
    print("TIPO NPS:", df["nps"].dtype)
    print(
        "CSAT:",
        df["csat"].head(10).tolist()
    )
    print(
        "NPS:",
        df["nps"].head(10).tolist()
    )
    print("====================================")

    
    return df


