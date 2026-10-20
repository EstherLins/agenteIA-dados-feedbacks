import os

from dotenv import load_dotenv


# ============================================================
# CARREGAR .ENV
# ============================================================

load_dotenv()


# ============================================================
# GOOGLE
# ============================================================

GOOGLE_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE"
)

GOOGLE_DRIVE_FOLDER_ID = os.getenv(
    "GOOGLE_DRIVE_FOLDER_ID"
)

SHEET_FONTE_ABA = os.getenv(
    "SHEET_FONTE_ABA",
    "Respostas"
)

SHEET_CONSOLIDADA_ID = os.getenv(
    "SHEET_CONSOLIDADA_ID"
)

SHEET_CONSOLIDADA_ABA = os.getenv(
    "SHEET_CONSOLIDADA_ABA",
    "Dados"
)

SHEET_CONTROLE_ABA = os.getenv(
    "SHEET_CONTROLE_ABA",
    "Controle_Processamento"
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "lukaspetrik/gemma3-tools:4b"
)

OLLAMA_KEEP_ALIVE = os.getenv(
    "OLLAMA_KEEP_ALIVE",
    "-1"
)


# ============================================================
# API
# ============================================================

API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1"
)

API_PORT = int(
    os.getenv(
        "API_PORT",
        "8000"
    )
)


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_config():

    obrigatorias = {

        "GOOGLE_CREDENTIALS_FILE":
            GOOGLE_CREDENTIALS_FILE,

        "GOOGLE_DRIVE_FOLDER_ID":
            GOOGLE_DRIVE_FOLDER_ID,

        "SHEET_CONSOLIDADA_ID":
            SHEET_CONSOLIDADA_ID,
    }

    faltando = [
        nome
        for nome, valor
        in obrigatorias.items()
        if not valor
    ]

    if faltando:

        raise RuntimeError(
            "Variáveis de ambiente obrigatórias "
            "não configuradas no .env: "
            + ", ".join(faltando)
        )
