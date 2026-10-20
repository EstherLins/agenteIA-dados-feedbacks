import gspread

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_DRIVE_FOLDER_ID,
    SHEET_FONTE_ABA
)


# =========================================================
# PERMISSÕES
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]


# =========================================================
# CONEXÃO GOOGLE
# =========================================================

def criar_credenciais():

    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=SCOPES
    )

    return credentials


def conectar_drive():

    credentials = criar_credenciais()

    drive = build(
        "drive",
        "v3",
        credentials=credentials
    )

    return drive


def conectar_sheets():

    credentials = criar_credenciais()

    gc = gspread.authorize(
        credentials
    )

    return gc


# =========================================================
# ENCONTRAR PLANILHAS NA PASTA
# =========================================================

def listar_planilhas():

    drive = conectar_drive()

    query = (
        f"'{GOOGLE_DRIVE_FOLDER_ID}' "
        "in parents "
        "and mimeType = "
        "'application/vnd.google-apps.spreadsheet' "
        "and trashed = false"
    )

    resultado = drive.files().list(
        q=query,
        fields="files(id, name, modifiedTime)",
        orderBy="name"
    ).execute()

    arquivos = resultado.get(
        "files",
        []
    )

    return arquivos


# =========================================================
# LER UMA PLANILHA
# =========================================================

def ler_planilha(
    gc,
    arquivo
):

    spreadsheet_id = arquivo["id"]

    nome_arquivo = arquivo["name"]

    planilha = gc.open_by_key(
        spreadsheet_id
    )

    try:

        aba = planilha.worksheet(
            SHEET_FONTE_ABA
        )

    except gspread.WorksheetNotFound:

        print(
            f"Aba '{SHEET_FONTE_ABA}' "
            f"não encontrada em: {nome_arquivo}"
        )

        return None

    dados = aba.get_all_records()

    if not dados:

        return None

    import pandas as pd

    df = pd.DataFrame(
        dados
    )

    # Identificação da fonte
    df["id_planilha_origem"] = (
        spreadsheet_id
    )

    df["arquivo_origem"] = (
        nome_arquivo
    )

    return df


# =========================================================
# COLETAR TODAS AS PLANILHAS
# =========================================================

def coletar_todas_planilhas():
    arquivos = listar_planilhas()
    gc = conectar_sheets()

    dados_coletados = []

    for arquivo in arquivos:
        print(f"Lendo: {arquivo['name']}")

        try:
            df = ler_planilha(gc, arquivo)

            if df is not None:
                dados_coletados.append(df)
                print(f"OK: {arquivo['name']}")

        except Exception as e:
            print(f"ERRO ao ler {arquivo['name']}: {e}")

    return dados_coletados