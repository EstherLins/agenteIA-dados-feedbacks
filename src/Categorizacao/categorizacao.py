import pandas as pd
import requests
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import OLLAMA_URL, OLLAMA_MODEL


# =========================================================
# CATEGORIAS
# =========================================================

CATEGORIAS_PROBLEMAS = [
    "Infraestrutura da plataforma de ensino",
    "Organização e usabilidade do Discord",
    "Equipamento do aluno",
    "Falta de exemplos práticos",
    "Desconexão entre teoria e prática",
    "Ritmo inadequado a iniciantes",
    "Aula corrida / difícil de acompanhar",
    "Linguagem pouco acessível",
    "Baixa interação com o professor",
    "Material de apoio incompleto",
    "Conteúdo desatualizado",
    "Falta de profundidade",
    "Solicitação sem retorno",
    "Demora em dúvidas de suporte",
    "Falta de gestão de tempo",
]


# =========================================================
# CONFIGURAÇÕES
# =========================================================

# O cache será criado na mesma pasta deste arquivo
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))

ARQUIVO_CACHE = os.path.join(
    PASTA_ATUAL,
    "cache_categorizacao.json"
)

MAX_WORKERS = 4

# Quantas vezes cada texto será enviado ao Ollama
MAX_TENTATIVAS = 3

# Tempo máximo de espera por requisição
TIMEOUT_OLLAMA = 120

# Quantas rodadas completas podem acontecer
MAX_RODADAS = 10


# =========================================================
# PROMPT
# =========================================================

SYSTEM_PROMPT_CATEGORIZACAO = """
Você é um classificador de reclamações de alunos.

Sua tarefa é escolher EXATAMENTE UMA das categorias abaixo.

CATEGORIAS PERMITIDAS:

1. Infraestrutura da plataforma de ensino

2. Organização e usabilidade do Discord

3. Equipamento do aluno

4. Falta de exemplos práticos

5. Desconexão entre teoria e prática

6. Ritmo inadequado a iniciantes

7. Aula corrida / difícil de acompanhar

8. Linguagem pouco acessível

9. Baixa interação com o professor

10. Material de apoio incompleto

11. Conteúdo desatualizado

12. Falta de profundidade

13. Solicitação sem retorno

14. Demora em dúvidas de suporte

15. Falta de gestão de tempo

CRITÉRIOS:

Infraestrutura da plataforma de ensino:

- plataforma lenta
- travamentos
- problemas de login
- problemas de acesso
- sistema fora do ar
- erro na plataforma

Organização e usabilidade do Discord:

- dificuldade para encontrar canais
- canais confusos
- Discord desorganizado
- dificuldade para navegar no Discord

Equipamento do aluno:

- computador
- notebook
- celular
- máquina
- equipamento
- falta de computador
- falta de notebook
- equipamento insuficiente

Falta de exemplos práticos:

- falta de exemplos
- mais exemplos
- exemplos práticos
- exercícios práticos
- atividades práticas
- aplicações práticas

Desconexão entre teoria e prática:

- dificuldade de aplicar a teoria
- teoria distante da prática
- dificuldade de relacionar teoria e prática

Ritmo inadequado a iniciantes:

- curso difícil para iniciantes
- pressupõe conhecimento prévio
- aluno iniciante não consegue acompanhar por falta de conhecimento prévio

Aula corrida / difícil de acompanhar:

- aula muito rápida
- aula corrida
- ritmo muito rápido
- excesso de conteúdo em pouco tempo
- difícil acompanhar a aula

Linguagem pouco acessível:

- linguagem complicada
- termos técnicos difíceis
- explicação pouco clara
- linguagem muito técnica

Baixa interação com o professor:

- pouca interação
- professor não interage
- falta de perguntas e respostas
- dificuldade de conversar com professor

Material de apoio incompleto:

- falta de material
- material insuficiente
- apostila incompleta
- materiais complementares ausentes

Conteúdo desatualizado:

- conteúdo antigo
- conteúdo desatualizado
- tecnologia antiga
- informações defasadas

Falta de profundidade:

- conteúdo superficial
- pouco aprofundamento
- assunto superficial
- poderia aprofundar mais

Solicitação sem retorno:

- solicitação sem resposta
- pedido sem retorno
- ninguém respondeu
- solicitação ignorada

Demora em dúvidas de suporte:

- suporte demorou
- demora para responder
- demoraram para responder
- resposta demorou
- dúvida enviada ao suporte sem resposta rápida

Falta de gestão de tempo:

- dificuldade para reservar tempo
- falta de tempo disponível
- dificuldade para conciliar estudos
- tempo insuficiente para acompanhar atividades
- rotina apertada

REGRAS IMPORTANTES:

1. Escolha somente UMA categoria.

2. A categoria deve ser EXATAMENTE igual a uma das categorias permitidas.

3. Não crie categorias novas.

4. Use somente o texto recebido.

5. Não invente informações.

6. Priorize o problema principal da reclamação.

7. Se houver equipamento/computador, priorize "Equipamento do aluno".

8. Se houver problema técnico da plataforma, priorize "Infraestrutura da plataforma de ensino".

9. Se houver pedido de exemplos ou exercícios, priorize "Falta de exemplos práticos".

10. Se houver conteúdo superficial, priorize "Falta de profundidade".

11. Se houver reclamação sobre velocidade da aula, use "Aula corrida / difícil de acompanhar".

12. Não retorne "Outros".

13. Toda reclamação deve possuir uma categoria.

14. Quando houver dúvida, escolha a categoria mais próxima.

15. Se a reclamação for sobre o ALUNO não ter tempo disponível (rotina, agenda, dificuldade pessoal de organização), use "Falta de gestão de tempo". Se for sobre a AULA ser rápida demais ou exigir conhecimento prévio, use "Ritmo inadequado a iniciantes" ou "Aula corrida / difícil de acompanhar".

NÃO EXISTE A CATEGORIA "Outros".

Toda reclamação deve obrigatoriamente ser classificada
em UMA das categorias disponíveis.

Se nenhuma categoria for perfeitamente adequada,
escolha a categoria MAIS PRÓXIMA do problema apresentado.

Nunca retorne "Outros".

RESPONDA SOMENTE COM JSON:

{
    "categoria": "nome exato de UMA das 14 categorias"
}
"""


# =========================================================
# NORMALIZAR TEXTO
# =========================================================

def normalizar_cache(texto):

    return " ".join(
        str(texto)
        .strip()
        .lower()
        .split()
    )


# =========================================================
# VALIDAR CATEGORIA
# =========================================================

import re

def validar_categoria(categoria):

    if not categoria:
        return None

    categoria = str(categoria).strip()

    # remove prefixos tipo "6. ", "6-", "6)" etc.
    categoria = re.sub(r"^\d+\s*[\.\-\)]\s*", "", categoria)

    for categoria_valida in CATEGORIAS_PROBLEMAS:

        if categoria.lower() == categoria_valida.lower():
            return categoria_valida

    return None


# =========================================================
# CACHE PERSISTENTE
# =========================================================

def carregar_cache():

    if not os.path.exists(ARQUIVO_CACHE):

        print("Cache não encontrado. Criando novo cache...")

        return {}

    try:

        with open(
            ARQUIVO_CACHE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            cache = json.load(arquivo)

        cache_valido = {}

        for texto, categoria in cache.items():

            categoria_valida = validar_categoria(categoria)

            if categoria_valida:

                cache_valido[
                    normalizar_cache(texto)
                ] = categoria_valida

        print(
            f"Cache carregado: "
            f"{len(cache_valido)} reclamações já categorizadas."
        )

        return cache_valido

    except (json.JSONDecodeError, OSError) as erro:

        print(
            f"Erro ao carregar cache: {erro}"
        )

        return {}


# =========================================================
# CARREGAR CACHE AO INICIAR
# =========================================================

CACHE_CATEGORIZACAO = carregar_cache()


# =========================================================
# SALVAR CACHE
# =========================================================

def salvar_cache():

    try:

        # Criar pasta caso necessário
        os.makedirs(
            os.path.dirname(ARQUIVO_CACHE),
            exist_ok=True
        )

        # Arquivo temporário para evitar corrupção
        arquivo_temporario = (
            ARQUIVO_CACHE + ".tmp"
        )

        with open(
            arquivo_temporario,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                CACHE_CATEGORIZACAO,
                arquivo,
                ensure_ascii=False,
                indent=2
            )

        # Substituição segura
        os.replace(
            arquivo_temporario,
            ARQUIVO_CACHE
        )

        print(
            f"Cache salvo: "
            f"{len(CACHE_CATEGORIZACAO)} reclamações."
        )

    except OSError as erro:

        print(
            f"Erro ao salvar cache: {erro}"
        )


# =========================================================
# CLASSIFICAÇÃO RÁPIDA POR PALAVRAS-CHAVE
# =========================================================

def classificar_por_regras(texto):

    texto = normalizar_cache(texto)

    # -----------------------------------------------------
    # EQUIPAMENTO
    # -----------------------------------------------------

    palavras = [
        "computador",
        "notebook",
        "celular",
        "equipamento",
        "máquina",
        "maquina",
        "pc"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Equipamento do aluno"


    # -----------------------------------------------------
    # INFRAESTRUTURA DA PLATAFORMA
    # -----------------------------------------------------

    palavras = [
        "plataforma",
        "login",
        "travamento",
        "travando",
        "travou",
        "lentidão",
        "lentidao",
        "sistema",
        "acesso à plataforma",
        "acesso a plataforma"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Infraestrutura da plataforma de ensino"


    # -----------------------------------------------------
    # DISCORD
    # -----------------------------------------------------

    palavras = [
        "discord",
        "canal do discord",
        "canais do discord"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Organização e usabilidade do Discord"


    # -----------------------------------------------------
    # EXEMPLOS PRÁTICOS
    # -----------------------------------------------------

    palavras = [
        "exemplo prático",
        "exemplos práticos",
        "exemplo pratico",
        "exemplos praticos",
        "exercício prático",
        "exercícios práticos",
        "exercicio pratico",
        "exercicios praticos",
        "atividade prática",
        "atividades práticas",
        "atividades praticas",
        "aplicações práticas",
        "aplicacao pratica",
        "falta de exemplo",
        "falta de exemplos",
        "poucos exemplos"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Falta de exemplos práticos"


    # -----------------------------------------------------
    # FALTA DE PROFUNDIDADE
    # -----------------------------------------------------

    palavras = [
        "superficial",
        "superficiais",
        "pouco aprofundado",
        "pouco aprofundados",
        "aprofundar",
        "aprofundamento",
        "mais profundidade"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Falta de profundidade"


    # -----------------------------------------------------
    # AULA CORRIDA
    # -----------------------------------------------------

    palavras = [
        "muito rápido",
        "muito rapido",
        "rápido demais",
        "rapido demais",
        "aula corrida",
        "ritmo muito rápido",
        "ritmo muito rapido",
        "difícil de acompanhar",
        "dificil de acompanhar"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Aula corrida / difícil de acompanhar"


    # -----------------------------------------------------
    # RITMO PARA INICIANTES
    # -----------------------------------------------------

    palavras = [
        "iniciante",
        "iniciantes",
        "começando",
        "comecando",
        "conhecimento prévio",
        "conhecimento previo"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Ritmo inadequado a iniciantes"


    # -----------------------------------------------------
    # LINGUAGEM
    # -----------------------------------------------------

    palavras = [
        "linguagem complicada",
        "linguagem técnica",
        "linguagem tecnica",
        "termos técnicos",
        "termos tecnicos",
        "difícil compreender",
        "dificil compreender",
        "explicação pouco clara",
        "explicacao pouco clara"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Linguagem pouco acessível"


    # -----------------------------------------------------
    # INTERAÇÃO COM PROFESSOR
    # -----------------------------------------------------

    palavras = [
        "pouca interação",
        "pouca interacao",
        "professor não interage",
        "professor nao interage",
        "interação com o professor",
        "interacao com o professor",
        "perguntas e respostas"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Baixa interação com o professor"


    # -----------------------------------------------------
    # MATERIAL
    # -----------------------------------------------------

    palavras = [
        "material de apoio",
        "materiais de apoio",
        "apostila",
        "apostilas",
        "material complementar",
        "materiais complementares"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Material de apoio incompleto"


    # -----------------------------------------------------
    # CONTEÚDO DESATUALIZADO
    # -----------------------------------------------------

    palavras = [
        "desatualizado",
        "desatualizada",
        "desatualizados",
        "desatualizadas",
        "conteúdo antigo",
        "conteudo antigo",
        "tecnologia antiga"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Conteúdo desatualizado"


    # -----------------------------------------------------
    # SOLICITAÇÃO SEM RETORNO
    # -----------------------------------------------------

    palavras = [
        "sem retorno",
        "sem resposta",
        "não responderam",
        "nao responderam",
        "pedido sem resposta",
        "solicitação ignorada",
        "solicitacao ignorada"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Solicitação sem retorno"


    # -----------------------------------------------------
    # DEMORA NO SUPORTE
    # -----------------------------------------------------

    palavras = [
        "suporte demorou",
        "demora para responder",
        "demoraram para responder",
        "demorei para receber resposta",
        "demorei bastante para receber resposta",
        "demora no suporte",
        "resposta demorou"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Demora em dúvidas de suporte"


    # -----------------------------------------------------
    # DESCONEXÃO TEORIA / PRÁTICA
    # -----------------------------------------------------

    palavras = [
        "teoria e prática",
        "teoria e pratica",
        "aplicar a teoria",
        "aplicar o conteúdo na prática",
        "aplicar o conteudo na pratica"
    ]

    if any(palavra in texto for palavra in palavras):

        return "Desconexão entre teoria e prática"


    return None



# =========================================================
# CATEGORIZAR UM PROBLEMA
# =========================================================

def categorizar_problema(texto):

    # -----------------------------------------------------
    # VALOR VAZIO
    # -----------------------------------------------------

    if pd.isna(texto) or not str(texto).strip():

        return None

    texto = str(texto).strip()

    # -----------------------------------------------------
    # CHAVE DO CACHE
    # -----------------------------------------------------

    chave_cache = normalizar_cache(texto)

    # -----------------------------------------------------
    # VERIFICAR CACHE
    # -----------------------------------------------------

    if chave_cache in CACHE_CATEGORIZACAO:

        categoria_cache = validar_categoria(
            CACHE_CATEGORIZACAO[chave_cache]
        )

        if categoria_cache:

            return categoria_cache


    # -----------------------------------------------------
    # PRIMEIRO: REGRAS DETERMINÍSTICAS
    # -----------------------------------------------------

    categoria_regra = classificar_por_regras(texto)

    if categoria_regra:

        categoria_regra = validar_categoria(
            categoria_regra
        )

        if categoria_regra:

            CACHE_CATEGORIZACAO[
                chave_cache
            ] = categoria_regra

            salvar_cache()

            return categoria_regra


    # -----------------------------------------------------
    # SEGUNDO: OLLAMA
    # -----------------------------------------------------

    prompt = f"""
Reclamação do aluno:

{texto}

Retorne somente o JSON solicitado.
"""

    payload = {

        "model": OLLAMA_MODEL,

        "messages": [

            {
                "role": "system",
                "content": SYSTEM_PROMPT_CATEGORIZACAO
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        "stream": False,

        "keep_alive": -1,

        "format": "json",

        "options": {

            "temperature": 0,

            "num_predict": 30

        }

    }


    # -----------------------------------------------------
    # TENTATIVAS AUTOMÁTICAS
    # -----------------------------------------------------

    for tentativa in range(
        1,
        MAX_TENTATIVAS + 1
    ):

        try:

            print(
                f"Ollama - tentativa "
                f"{tentativa}/{MAX_TENTATIVAS} "
                f"para: {texto[:60]}..."
            )

            resposta = requests.post(

                f"{OLLAMA_URL}/api/chat",

                json=payload,

                timeout=TIMEOUT_OLLAMA

            )

            resposta.raise_for_status()

            resultado = resposta.json()

            conteudo = (

                resultado

                .get("message", {})

                .get("content", "")

                .strip()

            )


            # -------------------------------------------------
            # INTERPRETAR JSON
            # -------------------------------------------------

            try:

                dados = json.loads(conteudo)

            except json.JSONDecodeError:

                print(
                    f"Resposta inválida do Ollama "
                    f"na tentativa {tentativa}."
                )

                if tentativa < MAX_TENTATIVAS:

                    time.sleep(2)

                continue


            categoria = str(
                dados.get("categoria", "")
            ).strip()


            # -------------------------------------------------
            # VALIDAR CATEGORIA
            # -------------------------------------------------

            categoria_encontrada = validar_categoria(
                categoria
            )


            if categoria_encontrada:

                # ---------------------------------------------
                # SALVAR SOMENTE CATEGORIA VÁLIDA
                # ---------------------------------------------

                CACHE_CATEGORIZACAO[
                    chave_cache
                ] = categoria_encontrada

                # Salvar imediatamente
                salvar_cache()

                return categoria_encontrada


            print(
                f"Categoria inválida retornada pelo Ollama "
                f"na tentativa {tentativa}: {categoria}"
            )

            if tentativa < MAX_TENTATIVAS:

                time.sleep(2)


        except requests.Timeout:

            print(
                f"TIMEOUT na tentativa "
                f"{tentativa}/{MAX_TENTATIVAS}."
            )

            if tentativa < MAX_TENTATIVAS:

                print(
                    "Aguardando antes de tentar novamente..."
                )

                time.sleep(3)


        except requests.RequestException as erro:

            print(
                f"Erro ao categorizar "
                f"(tentativa {tentativa}/"
                f"{MAX_TENTATIVAS}): {erro}"
            )

            if tentativa < MAX_TENTATIVAS:

                time.sleep(3)


        except Exception as erro:

            print(
                f"Erro inesperado "
                f"(tentativa {tentativa}/"
                f"{MAX_TENTATIVAS}): {erro}"
            )

            if tentativa < MAX_TENTATIVAS:

                time.sleep(3)


    # -----------------------------------------------------
    # TODAS AS TENTATIVAS FALHARAM
    # -----------------------------------------------------

    print()
    print(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    print(
        "RECLAMAÇÃO NÃO CATEGORIZADA"
    )
    print(
        f"Texto: {texto}"
    )
    print(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    print()

    # IMPORTANTE:
    # NÃO salva None no cache.

    return None


# =========================================================
# CATEGORIZAR DATAFRAME
# =========================================================

def categorizar_dataframe(df):

    df = df.copy()

    # -----------------------------------------------------
    # GARANTIR COLUNA
    # -----------------------------------------------------

    df["categoria_problema_reclamacao"] = None

    if "problema_reclamacao" not in df.columns:

        return df


    # -----------------------------------------------------
    # OBTER TEXTOS
    # -----------------------------------------------------

    textos = (

        df["problema_reclamacao"]

        .dropna()

        .astype(str)

        .str.strip()

    )


    textos_unicos = [

        texto

        for texto in textos.unique()

        if texto

    ]


    if not textos_unicos:

        return df


    # -----------------------------------------------------
    # RESULTADOS
    # -----------------------------------------------------

    resultados = {}

    # -----------------------------------------------------
    # PRIMEIRO: APROVEITAR CACHE
    # -----------------------------------------------------

    textos_pendentes = []

    for texto in textos_unicos:

        chave = normalizar_cache(texto)

        categoria = validar_categoria(
            CACHE_CATEGORIZACAO.get(chave)
        )

        if categoria:

            resultados[texto] = categoria

        else:

            textos_pendentes.append(texto)


    print()
    print("=" * 60)
    print("ANÁLISE DO CACHE")
    print("=" * 60)

    print(
        f"Total de reclamações únicas: "
        f"{len(textos_unicos)}"
    )

    print(
        f"Encontradas no cache: "
        f"{len(resultados)}"
    )

    print(
        f"Precisam ser processadas: "
        f"{len(textos_pendentes)}"
    )

    print("=" * 60)


    # -----------------------------------------------------
    # PROCESSAMENTO DAS PENDENTES
    # -----------------------------------------------------

    rodada = 1

    while textos_pendentes:

        print()
        print("=" * 60)
        print(
            f"RODADA {rodada}/{MAX_RODADAS}"
        )
        print("=" * 60)

        print(
            f"Reclamações pendentes: "
            f"{len(textos_pendentes)}"
        )

        print("=" * 60)


        # -------------------------------------------------
        # RESULTADOS DA RODADA
        # -------------------------------------------------

        resultados_rodada = {}


        # -------------------------------------------------
        # PROCESSAMENTO PARALELO
        # -------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            tarefas = {

                executor.submit(
                    categorizar_problema,
                    texto
                ): texto

                for texto in textos_pendentes

            }


            for tarefa in as_completed(tarefas):

                texto = tarefas[tarefa]

                try:

                    categoria = tarefa.result()

                    categoria = validar_categoria(
                        categoria
                    )


                    if categoria:

                        resultados_rodada[
                            texto
                        ] = categoria

                    else:

                        resultados_rodada[
                            texto
                        ] = None


                except Exception as erro:

                    print(
                        f"Erro ao processar texto: "
                        f"{erro}"
                    )

                    resultados_rodada[
                        texto
                    ] = None


        # -------------------------------------------------
        # ADICIONAR RESULTADOS VÁLIDOS
        # -------------------------------------------------

        for texto, categoria in resultados_rodada.items():

            categoria = validar_categoria(
                categoria
            )

            if categoria:

                resultados[texto] = categoria


        # -------------------------------------------------
        # IDENTIFICAR PENDENTES
        # -------------------------------------------------

        textos_pendentes = [

            texto

            for texto in textos_pendentes

            if not validar_categoria(
                resultados.get(texto)
            )

        ]


        # -------------------------------------------------
        # PROGRESSO
        # -------------------------------------------------

        processadas = (

            len(textos_unicos)

            - len(textos_pendentes)

        )


        print()
        print(
            f"Processadas com sucesso: "
            f"{processadas}/{len(textos_unicos)}"
        )

        print(
            f"Pendentes: "
            f"{len(textos_pendentes)}"
        )


        # -------------------------------------------------
        # VERIFICAR CONCLUSÃO
        # -------------------------------------------------

        if not textos_pendentes:

            break


        # -------------------------------------------------
        # EVITAR LOOP INFINITO
        # -------------------------------------------------

        if rodada >= MAX_RODADAS:

            print()
            print("=" * 60)
            print(
                "LIMITE DE RODADAS ATINGIDO"
            )
            print("=" * 60)

            print(
                f"Ainda existem "
                f"{len(textos_pendentes)} "
                f"reclamações sem categoria válida."
            )

            print(
                "O processamento será interrompido "
                "para evitar loop infinito."
            )

            print("=" * 60)

            raise RuntimeError(
                "Processamento não concluído. "
                f"{len(textos_pendentes)} reclamações "
                "não possuem categoria válida."
            )


        # -------------------------------------------------
        # PRÓXIMA RODADA
        # -------------------------------------------------

        rodada += 1

        print()
        print(
            "Ainda existem reclamações sem "
            "categoria válida."
        )

        print(
            "Iniciando nova rodada..."
        )

        time.sleep(2)


    # =====================================================
    # APLICAR RESULTADOS
    # =====================================================

    df["categoria_problema_reclamacao"] = (

        df["problema_reclamacao"]

        .fillna("")

        .astype(str)

        .str.strip()

        .map(resultados)

    )


    # =====================================================
    # VALIDAÇÃO FINAL
    # =====================================================

    mask_reclamacoes = (

        df["problema_reclamacao"]

        .fillna("")

        .astype(str)

        .str.strip()

        != ""

    )


    categorias_invalidas = (

        df.loc[
            mask_reclamacoes,
            "categoria_problema_reclamacao"
        ]

        .apply(validar_categoria)

        .isna()

    )


    if categorias_invalidas.any():

        quantidade = categorias_invalidas.sum()

        print()
        print("=" * 60)
        print(
            "ERRO NA VALIDAÇÃO FINAL"
        )
        print("=" * 60)

        print(
            f"{quantidade} reclamações "
            "ainda não possuem categoria válida."
        )

        print("=" * 60)

        raise RuntimeError(
            "Processamento não concluído. "
            f"{quantidade} reclamações ainda "
            "não possuem categoria válida."
        )


    # =====================================================
    # SALVAR CACHE FINAL
    # =====================================================

    salvar_cache()


    # =====================================================
    # CONCLUSÃO
    # =====================================================

    print()
    print("=" * 60)
    print(
        "CATEGORIZAÇÃO CONCLUÍDA COM SUCESSO"
    )
    print("=" * 60)

    print(
        f"Total de reclamações únicas: "
        f"{len(textos_unicos)}"
    )

    print(
        "Todas possuem categoria válida."
    )

    print(
        f"Cache disponível em:"
    )

    print(
        ARQUIVO_CACHE
    )

    print("=" * 60)


    return df