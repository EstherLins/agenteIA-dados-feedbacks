import pandas as pd


# =========================================================
# CRIAR ID ÚNICO DO REGISTRO
# =========================================================

def gerar_id_registro(row):
    datahora = row["datahora_registro"]
    projeto = str(row["projeto"]).strip()
    ciclo = str(row["ciclo"]).strip()

    # Formata a data/hora com precisão de segundos
    if pd.notna(datahora):
        datahora = pd.to_datetime(datahora).strftime(
            "%Y%m%d%H%M%S"
        )
    else:
        datahora = "SEM_DATA"

    return f"{datahora}_{projeto}_{ciclo}"


# =========================================================
# ADICIONAR ID AOS REGISTROS
# =========================================================

def adicionar_id_registro(df):

    df = df.copy()

    df["id_registro"] = df.apply(
        gerar_id_registro,
        axis=1
    )

    return df


# =========================================================
# IDENTIFICAR NOVOS REGISTROS
# =========================================================

def identificar_novos_registros(
    df,
    ids_existentes
):

    df = df.copy()

    df_novos = df[
        ~df["id_registro"].isin(
            ids_existentes
        )
    ].copy()

    return df_novos


from config import (
    GOOGLE_CREDENTIALS_FILE,
    SHEET_CONSOLIDADA_ID,
    SHEET_CONTROLE_ABA
)

import gspread


# =========================================================
# CONECTAR À PLANILHA CONSOLIDADA
# =========================================================

def conectar_consolidado():

    gc = gspread.service_account(
        filename=GOOGLE_CREDENTIALS_FILE
    )

    planilha = gc.open_by_key(
        SHEET_CONSOLIDADA_ID
    )

    return planilha


# =========================================================
# LER CONTROLE
# =========================================================

def obter_ids_processados():

    planilha = conectar_consolidado()

    try:

        aba = planilha.worksheet(
            SHEET_CONTROLE_ABA
        )

    except gspread.WorksheetNotFound:

        aba = planilha.add_worksheet(
            title=SHEET_CONTROLE_ABA,
            rows=1000,
            cols=5
        )

        aba.update(
            range_name="A1:E1",
            values=[[
                "id_registro",
                "id_planilha_origem",
                "arquivo_origem",
                "data_processamento",
                "status"
            ]]
        )

        return set()

    dados = aba.get_all_records()

    if not dados:

        return set()

    df_controle = pd.DataFrame(
        dados
    )

    if "id_registro" not in df_controle.columns:

        return set()

    ids = set(
        df_controle[
            "id_registro"
        ]
        .astype(str)
        .tolist()
    )

    return ids


from datetime import datetime


def registrar_processamento(
    df
):

    if df.empty:

        return

    planilha = conectar_consolidado()

    aba = planilha.worksheet(
        SHEET_CONTROLE_ABA
    )

    agora = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    registros = []

    for _, row in df.iterrows():

        registros.append([
            row["id_registro"],
            row.get(
                "id_planilha_origem",
                ""
            ),
            row.get(
                "arquivo_origem",
                ""
            ),
            agora,
            "processado"
        ])

    aba.append_rows(
        registros,
        value_input_option="RAW"
    )