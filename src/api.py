from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    API_HOST,
    API_PORT,
    validar_config,
)

from Agente import ollama


# ============================================================
# APLICAÇÃO
# ============================================================

app = FastAPI(
    title="FeedbackFlow API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELOS
# ============================================================

class PerguntaRequest(BaseModel):
    mensagem: str


class PerguntaResponse(BaseModel):
    resposta: str
    ferramentas_utilizadas: List[str]


# ============================================================
# CHAT
# ============================================================

@app.post(
    "/chat",
    response_model=PerguntaResponse
)
def chat(payload: PerguntaRequest):

    # --------------------------------------------------------
    # Validação da mensagem
    # --------------------------------------------------------

    if not payload.mensagem or not payload.mensagem.strip():
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia."
        )

    try:

        resultado = ollama.perguntar(
            payload.mensagem
        )

        # ----------------------------------------------------
        # Validação da resposta do agente
        # ----------------------------------------------------

        if not isinstance(resultado, dict):
            raise HTTPException(
                status_code=502,
                detail="O agente retornou uma resposta inválida."
            )

        resposta = resultado.get(
            "resposta",
            ""
        )

        ferramentas_utilizadas = resultado.get(
            "ferramentas_utilizadas",
            []
        )

        # Uma resposta textual é válida mesmo sem ferramentas.
        if not isinstance(resposta, str) or not resposta.strip():
            raise HTTPException(
                status_code=502,
                detail="O agente não retornou uma resposta textual."
            )

        if not isinstance(
            ferramentas_utilizadas,
            list
        ):
            ferramentas_utilizadas = []

        return PerguntaResponse(
            resposta=resposta.strip(),
            ferramentas_utilizadas=[
                str(ferramenta)
                for ferramenta in ferramentas_utilizadas
            ]
        )

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except TimeoutError as erro:

        print(
            "TIMEOUT NO AGENTE:",
            erro
        )

        raise HTTPException(
            status_code=504,
            detail=str(erro)
        )

    # --------------------------------------------------------
    # ERRO HTTP JÁ TRATADO
    # --------------------------------------------------------

    except HTTPException:
        raise

    # --------------------------------------------------------
    # OUTROS ERROS
    # --------------------------------------------------------

    except Exception as erro:

        print(
            "=" * 70
        )
        print(
            "ERRO NO ENDPOINT /chat"
        )
        print(
            "=" * 70
        )
        print(
            type(erro).__name__,
            ":",
            erro
        )

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a pergunta."
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    validar_config()

    import uvicorn

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=False
    )
