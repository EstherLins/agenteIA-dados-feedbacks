import json
import re
import time
import requests

from config import OLLAMA_URL, OLLAMA_MODEL
from Agente import prompts
from Agente import ferramentas


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Mantém o modelo carregado por 10 minutos.
OLLAMA_KEEP_ALIVE = "10m"

# Quantidade máxima de tokens para tool calling.
MAX_TOKENS_FERRAMENTA = 64

# Quantidade máxima de tokens para resposta textual.
MAX_TOKENS_RESPOSTA = 120

# Tempo máximo de espera por chamada ao Ollama.
TIMEOUT_OLLAMA = 300


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def _normalizar_texto(texto):
    if not texto:
        return ""

    texto = texto.lower().strip()

    substituicoes = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "õ": "o",
        "ô": "o",
        "ö": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    return texto


# ============================================================
# DETECÇÃO DE FORA DO ESCOPO
# ============================================================


def _detectar_fora_escopo(pergunta):
    texto = _normalizar_texto(pergunta)

    # Comandos técnicos enviados por engano
    if re.match(
        r"^(ngrok|uvicorn|pip|python)\s+",
        texto
    ):
        return (
            "fora_escopo",
            "Isso parece ser um comando técnico, não uma pergunta "
            "sobre feedbacks. Posso ajudar a analisar os dados "
            "dos alunos ou orientar você sobre o projeto."
        )

    padroes = [
        # Tempo e clima
        r"\bprevisao do tempo\b",
        r"\bprevisao meteorologica\b",
        r"\bcomo esta o tempo\b",
        r"\bcomo esta o clima\b",
        r"\bvai chover\b",
        r"\btemperatura (hoje|agora)\b",

        # Notícias
        r"\bnoticias de hoje\b",
        r"\bnoticias agora\b",
        r"\bultimas noticias\b",

        # Trânsito
        r"\btransito agora\b",
        r"\bmelhor rota\b",
        r"\bcomo chegar\b",

        # Finanças
        r"\bcotacao do dolar\b",
        r"\bcotacao do euro\b",
        r"\b(preco|valor) do bitcoin\b",

        # Esportes
        r"\bplacar\b",
        r"\bquem ganhou o jogo\b",
        r"\bresultado do jogo\b",

        # Perguntas gerais conhecidas
        r"\bo cachorro consegue cantar\b",
        r"\bquem descobriu o brasil\b",
        r"\bcapital do brasil\b",
    ]

    for padrao in padroes:
        if re.search(padrao, texto):
            return (
                "fora_escopo",
                "Essa pergunta está fora do escopo do agente. "
                "Posso analisar os feedbacks dos alunos, incluindo "
                "CSAT, NPS, projetos, ciclos, problemas e sugestões "
                "de melhoria."
            )

    return None, None



# ============================================================
# DETECÇÃO DIRETA DE INTENÇÃO
# ============================================================

def _detectar_intencao_direta(pergunta):
    """
    Detecta perguntas muito claras que podem ser encaminhadas
    diretamente para uma ferramenta Python.

    Isso evita gastar ~2 minutos com o Gemma apenas para decidir
    qual ferramenta utilizar.
    """

    texto = _normalizar_texto(pergunta)

    # --------------------------------------------------------
    # MÉTRICAS GERAIS
    # --------------------------------------------------------

    indicadores_metricas = [
        "total de respostas",
        "total de registros",
        "quantas respostas",
        "quantos registros",
        "csat medio",
        "media de csat",
        "nps medio",
        "media de nps",
    ]

    if any(indicador in texto for indicador in indicadores_metricas):

        argumentos = {}

        # Projeto
        match_projeto = re.search(
            r"\bprojeto\s+([a-z0-9]+)\b",
            texto
        )

        if match_projeto:
            numero = match_projeto.group(1)
            argumentos["projeto"] = f"Projeto {numero}"

        # Ciclo
        match_ciclo = re.search(
            r"\bciclo\s+(\d+)\b",
            texto
        )

        if match_ciclo:
            argumentos["ciclo"] = int(match_ciclo.group(1))

        return "calcular_metricas", argumentos

    # --------------------------------------------------------
    # CORRELAÇÃO CSAT × NPS
    # --------------------------------------------------------

    palavras_correlacao = [
        "correlacao",
        "correlação",
        "relacao entre csat e nps",
        "relação entre csat e nps",
    ]

    if any(palavra in texto for palavra in palavras_correlacao):
        return (
            "correlacionar_numericas",
            {
                "coluna_a": "csat",
                "coluna_b": "nps",
            }
        )

    # --------------------------------------------------------
    # COMPARAÇÃO DE CICLOS
    # --------------------------------------------------------

    if (
        "comparar os ciclos" in texto
        or "compare os ciclos" in texto
        or "comparacao entre ciclos" in texto
        or "comparação entre ciclos" in texto
    ):
        match_projeto = re.search(
            r"\bprojeto\s+([a-z0-9]+)\b",
            texto
        )

        if match_projeto:
            numero = match_projeto.group(1)

            return (
                "comparar_ciclos",
                {
                    "projeto": f"Projeto {numero}"
                }
            )

    
    # --------------------------------------------------------
    # TOP CATEGORIAS DE PROBLEMAS
    # --------------------------------------------------------

    indicadores_top = [
        "principais problemas de permanencia",
        "principal problema de permanencia",
        "principais categorias de problemas",
        "categorias de problemas para permanencia",
        "problemas mais frequentes",
        "problemas mais comuns",
        "top problemas",
        "top categorias",
    ]

    if any(indicador in texto for indicador in indicadores_top):

        argumentos = {}

        limite = _detectar_limite(pergunta)

        if limite is not None:
            argumentos["limite"] = limite

        match_projeto = re.search(
            r"\bprojeto\s+([a-z0-9]+)\b",
            texto
        )

        if match_projeto:
            argumentos["projeto"] = (
                f"Projeto {match_projeto.group(1)}"
            )

        match_ciclo = re.search(
            r"\bciclo\s+(\d+)\b",
            texto
        )

        if match_ciclo:
            argumentos["ciclo"] = int(
                match_ciclo.group(1)
            )

        if limite is None:
            argumentos["limite"] = 5

        return (
            "top_categorias_problemas",
            argumentos
        )

    return None, None



# ============================================================
# CHAMADA AO OLLAMA
# ============================================================

def _chamar_ollama(
    mensagens,
    usar_ferramentas=True,
    max_tokens=None
):
    if max_tokens is None:
        max_tokens = MAX_TOKENS_RESPOSTA

    payload = {
        "model": OLLAMA_MODEL,
        "messages": mensagens,
        "stream": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": 0,
            "num_predict": max_tokens,
        },
    }

    if usar_ferramentas:
        payload["tools"] = prompts.TOOLS_SCHEMA

    print("\n" + "=" * 70)
    print("CHAMANDO OLLAMA")
    print("=" * 70)

    print("MODELO:", OLLAMA_MODEL)
    print("URL:", OLLAMA_URL)
    print("KEEP ALIVE:", OLLAMA_KEEP_ALIVE)
    print("MAX TOKENS:", max_tokens)
    print("USANDO FERRAMENTAS:", usar_ferramentas)

    if usar_ferramentas:
        print(
            "QUANTIDADE DE FERRAMENTAS:",
            len(prompts.TOOLS_SCHEMA)
        )

    inicio = time.time()

    try:
        resposta = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT_OLLAMA,
        )

        tempo = time.time() - inicio

        print(f"TEMPO OLLAMA: {tempo:.2f}s")
        print("STATUS OLLAMA:", resposta.status_code)

        if not resposta.ok:
            print("RESPOSTA OLLAMA:", resposta.text)

        resposta.raise_for_status()

        dados = resposta.json()

        print(
            "CONTEÚDO:",
            dados.get("message", {}).get("content", "")
        )

        tool_calls = dados.get(
            "message",
            {}
        ).get(
            "tool_calls",
            []
        )

        if tool_calls:
            print("TOOL CALLS:", len(tool_calls))
        else:
            print("TOOL CALLS: None")

        return dados

    except requests.Timeout as erro:
        tempo = time.time() - inicio

        print(
            f"TIMEOUT OLLAMA APÓS {tempo:.2f}s"
        )

        raise TimeoutError(
            "O modelo demorou mais tempo do que o permitido para responder."
        ) from erro

    except requests.RequestException as erro:
        print(
            "ERRO DE CONEXÃO COM OLLAMA:",
            erro
        )

        raise RuntimeError(
            f"Não foi possível comunicar com o Ollama: {erro}"
        ) from erro


# ============================================================
# EXECUÇÃO DE FERRAMENTAS
# ============================================================

def _executar_ferramenta(nome, argumentos):

    print("\n" + "-" * 70)
    print("EXECUTANDO FERRAMENTA")
    print("-" * 70)

    print("NOME:", nome)
    print("ARGUMENTOS:", argumentos)

    funcao = ferramentas.FERRAMENTAS_DISPONIVEIS.get(nome)

    if funcao is None:
        return {
            "erro": f"Ferramenta '{nome}' não está disponível."
        }

    try:
        resultado = funcao(**argumentos)

        print("RESULTADO DA FERRAMENTA:")
        print(resultado)

        return resultado

    except TypeError as erro:
        print("ERRO DE ARGUMENTOS:", erro)

        return {
            "erro": (
                f"Argumentos inválidos para a ferramenta "
                f"'{nome}': {erro}"
            )
        }

    except Exception as erro:
        print("ERRO NA FERRAMENTA:", erro)

        return {
            "erro": (
                f"Erro ao executar '{nome}': {erro}"
            )
        }


# ============================================================
# FORMATAÇÃO DE NÚMEROS
# ============================================================

def _numero_pt(valor, casas=2):

    if valor is None:
        return "N/A"

    try:
        return (
            f"{float(valor):.{casas}f}"
            .replace(".", ",")
        )

    except (TypeError, ValueError):
        return str(valor)


# ============================================================
# LIMITE PEDIDO PELO USUÁRIO
# ============================================================

def _detectar_limite(pergunta):

    texto = _normalizar_texto(pergunta)

    padroes = [
        r"\btop\s+(\d+)\b",
        r"\b(\d+)\s+principais\b",
        r"\bprincipais\s+(\d+)\b",
        r"\b(\d+)\s+categorias\b",
    ]

    for padrao in padroes:

        match = re.search(padrao, texto)

        if match:

            try:
                limite = int(match.group(1))

                if limite > 0:
                    return limite

            except ValueError:
                pass

    return None


# ============================================================
# FORMATADOR — MÉTRICAS
# ============================================================

def _resposta_calcular_metricas(resultado):

    if "erro" in resultado:
        return resultado["erro"]

    partes = []

    projeto = resultado.get("projeto")
    ciclo = resultado.get("ciclo")

    contexto = []

    if projeto:
        contexto.append(
            f"projeto {projeto}"
        )

    if ciclo is not None:
        contexto.append(
            f"ciclo {ciclo}"
        )

    if contexto:
        partes.append(
            f"Considerando {' e '.join(contexto)}, "
            f"foram encontradas "
            f"{resultado.get('total_respostas', 0)} respostas."
        )

    else:
        partes.append(
            f"Foram encontradas "
            f"{resultado.get('total_respostas', 0)} respostas."
        )

    if resultado.get("csat_medio") is not None:
        partes.append(
            f"CSAT médio: "
            f"{_numero_pt(resultado['csat_medio'])}."
        )

    if resultado.get("nps_medio") is not None:
        partes.append(
            f"NPS médio: "
            f"{_numero_pt(resultado['nps_medio'])}."
        )

    if resultado.get("categoria_principal"):
        partes.append(
            "Principal problema para permanência: "
            f"{resultado['categoria_principal']}."
        )

    return " ".join(partes)


# ============================================================
# FORMATADOR — CORRELAÇÃO
# ============================================================

def _resposta_correlacao(resultado):

    if "erro" in resultado:
        return resultado["erro"]

    correlacao = resultado.get("correlacao")
    registros = resultado.get("registros")

    if correlacao is None:
        return "Não foi possível calcular a correlação."

    valor = float(correlacao)
    absoluto = abs(valor)

    if absoluto < 0.10:
        intensidade = "praticamente inexistente"
    elif absoluto < 0.30:
        intensidade = "fraca"
    elif absoluto < 0.50:
        intensidade = "moderada"
    elif absoluto < 0.70:
        intensidade = "forte"
    else:
        intensidade = "muito forte"

    if valor > 0:
        direcao = "positiva"
    elif valor < 0:
        direcao = "negativa"
    else:
        direcao = "nula"

    resposta = (
        f"A correlação entre CSAT e NPS foi de "
        f"{_numero_pt(valor, 3)}, considerando "
        f"{registros} respostas. "
        f"O valor indica uma associação linear "
        f"{direcao} de intensidade {intensidade}. "
        "A correlação mostra associação entre as variáveis, "
        "mas não demonstra relação de causa e efeito."
    )

    return resposta


# ============================================================
# FORMATADOR — COMPARAÇÃO DE CICLOS
# ============================================================

def _resposta_comparar_ciclos(resultado):

    if "erro" in resultado:
        return resultado["erro"]

    projeto = resultado.get("projeto")

    ciclos = {}

    for chave, valor in resultado.items():

        if (
            isinstance(chave, str)
            and chave.startswith("ciclo_")
        ):
            ciclos[chave] = valor

    if not ciclos:
        return (
            "Não foram encontrados dados suficientes "
            "para comparar os ciclos."
        )

    partes = []

    if projeto:
        partes.append(
            f"Comparação dos ciclos do projeto {projeto}:"
        )

    for chave in sorted(ciclos.keys()):

        dados = ciclos[chave]

        numero = chave.replace("ciclo_", "")

        texto = (
            f"Ciclo {numero}: "
            f"{dados.get('total_respostas', 0)} respostas"
        )

        if dados.get("csat_medio") is not None:
            texto += (
                f", CSAT médio de "
                f"{_numero_pt(dados['csat_medio'])}"
            )

        if dados.get("nps_medio") is not None:
            texto += (
                f", NPS médio de "
                f"{_numero_pt(dados['nps_medio'])}"
            )

        partes.append(texto + ".")

    return " ".join(partes)


# ============================================================
# FORMATADOR — CRUZAMENTO
# ============================================================

def _resposta_cruzamento(resultado):

    if "erro" in resultado:
        return resultado["erro"]

    variavel_a = resultado.get("variavel_a")
    variavel_b = resultado.get("variavel_b")
    total = resultado.get("total_registros", 0)

    nomes = {
        "csat": "CSAT",
        "nps": "NPS",
        "ciclo": "ciclo",
        "principal_problema_permanencia":
            "principal problema para permanência",
        "categoria_problema_reclamacao":
            "categoria de problemas ou reclamações",
        "tipos_melhoria_sugerida":
            "tipo de melhoria sugerida",
    }

    nome_a = nomes.get(
        variavel_a,
        variavel_a
    )

    nome_b = nomes.get(
        variavel_b,
        variavel_b
    )

    linhas = resultado.get(
        "resultado",
        []
    )

    if not linhas:
        return (
            f"O cruzamento entre {nome_a} e {nome_b} "
            "não encontrou registros."
        )

    partes = [
        f"O cruzamento entre {nome_a} e {nome_b} "
        f"considerou {total} registros."
    ]

    grupos = {}

    for linha in linhas:

        valor_a = linha.get(variavel_a)
        valor_b = linha.get(variavel_b)
        quantidade = linha.get(
            "quantidade",
            0
        )

        grupos.setdefault(
            valor_a,
            []
        ).append(
            (valor_b, quantidade)
        )

    grupos_itens = list(
        grupos.items()
    )[:5]

    for valor_a, itens in grupos_itens:

        itens = sorted(
            itens,
            key=lambda item: item[1],
            reverse=True
        )[:5]

        detalhes = []

        for valor_b, quantidade in itens:

            detalhes.append(
                f"{valor_b}: {quantidade}"
            )

        partes.append(
            f"Para {nome_a} = {valor_a}, "
            f"{nome_b} ficou distribuído em "
            + "; ".join(detalhes)
            + "."
        )

    partes.append(
        "Esses valores representam frequências observadas "
        "no cruzamento e, por si só, não indicam relação "
        "de causa e efeito."
    )

    return " ".join(partes)


# ============================================================
# FORMATADOR — TOP CATEGORIAS
# ============================================================

def _resposta_top_categorias(
    resultado,
    pergunta_original
):

    if "erro" in resultado:
        return resultado["erro"]

    categorias = resultado.get(
        "categorias",
        []
    )

    if not categorias:
        return "Não foram encontradas categorias."

    limite = _detectar_limite(
        pergunta_original
    )

    if limite is None:
        limite = len(categorias)

    categorias = categorias[:limite]

    partes = [
        f"As {len(categorias)} principais categorias "
        "de problemas para permanência são:"
    ]

    for indice, categoria in enumerate(
        categorias,
        start=1
    ):

        nome = categoria.get(
            "categoria",
            "Não informado"
        )

        quantidade = categoria.get(
            "quantidade",
            0
        )

        percentual = categoria.get(
            "percentual"
        )

        if percentual is not None:

            partes.append(
                f"{indice}. {nome}: "
                f"{quantidade} "
                f"({_numero_pt(percentual)}%)."
            )

        else:

            partes.append(
                f"{indice}. {nome}: "
                f"{quantidade}."
            )

    return " ".join(partes)


# ============================================================
# FORMATADOR — COMENTÁRIOS
# ============================================================

def _resposta_comentarios_por_categoria(resultado):

    if "erro" in resultado:
        return resultado["erro"]

    categoria = resultado.get(
        "categoria"
    )

    total = resultado.get(
        "total_na_categoria",
        0
    )

    exemplos = resultado.get(
        "exemplos",
        []
    )

    if not exemplos:
        return (
            f"Não foram encontrados comentários "
            f"para a categoria {categoria}."
        )

    partes = [
        f"Foram encontrados {total} registros "
        f"na categoria {categoria}. "
        "Alguns comentários registrados foram:"
    ]

    for exemplo in exemplos:

        partes.append(
            f"- {exemplo}"
        )

    return " ".join(partes)


# ============================================================
# RESULTADOS ESTRUTURADOS
# ============================================================

def _resultado_estruturado(nome_ferramenta):

    return nome_ferramenta in {
        "calcular_metricas",
        "comparar_ciclos",
        "cruzar_variaveis",
        "correlacionar_numericas",
        "top_categorias_problemas",
        "comentarios_por_categoria",
    }


# ============================================================
# GERA RESPOSTA DIRETA
# ============================================================

def _gerar_resposta_direta(
    nome_ferramenta,
    resultado,
    pergunta_original
):

    if nome_ferramenta == "calcular_metricas":
        return _resposta_calcular_metricas(
            resultado
        )

    if nome_ferramenta == "comparar_ciclos":
        return _resposta_comparar_ciclos(
            resultado
        )

    if nome_ferramenta == "cruzar_variaveis":
        return _resposta_cruzamento(
            resultado
        )

    if nome_ferramenta == "correlacionar_numericas":
        return _resposta_correlacao(
            resultado
        )

    if nome_ferramenta == "top_categorias_problemas":
        return _resposta_top_categorias(
            resultado,
            pergunta_original
        )

    if nome_ferramenta == "comentarios_por_categoria":
        return _resposta_comentarios_por_categoria(
            resultado
        )

    return None


# ============================================================
# AGENTE PRINCIPAL
# ============================================================

def perguntar(pergunta):

    pergunta = (
        pergunta or ""
    ).strip()

    if not pergunta:
        return {
            "resposta": "Digite uma pergunta.",
            "ferramentas_utilizadas": []
        }

    # ========================================================
    # 1. FORA DO ESCOPO
    # ========================================================

    tipo_fora_escopo, resposta_fora_escopo = (
        _detectar_fora_escopo(pergunta)
    )

    if tipo_fora_escopo == "fora_escopo":

        return {
            "resposta": resposta_fora_escopo,
            "ferramentas_utilizadas": []
        }

    # ========================================================
    # 2. DETECÇÃO DIRETA
    # ========================================================

    nome_direto, argumentos_diretos = (
        _detectar_intencao_direta(pergunta)
    )

    if nome_direto:

        print("\n" + "=" * 70)
        print("INTENÇÃO DETECTADA DIRETAMENTE")
        print("=" * 70)

        print("FERRAMENTA:", nome_direto)
        print("ARGUMENTOS:", argumentos_diretos)

        inicio = time.time()

        resultado = _executar_ferramenta(
            nome_direto,
            argumentos_diretos
        )

        tempo = time.time() - inicio

        print(
            f"TEMPO FERRAMENTA: {tempo:.2f}s"
        )

        resposta_direta = _gerar_resposta_direta(
            nome_direto,
            resultado,
            pergunta
        )

        if resposta_direta:

            return {
                "resposta": resposta_direta,
                "ferramentas_utilizadas": [
                    nome_direto
                ]
            }

    # ========================================================
    # 3. PRIMEIRA CHAMADA AO GEMMA
    # ========================================================

    mensagens = [
        {
            "role": "system",
            "content": prompts.SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": pergunta,
        },
    ]

    resposta_modelo = _chamar_ollama(
        mensagens,
        usar_ferramentas=True,
        max_tokens=MAX_TOKENS_FERRAMENTA,
    )

    mensagem_modelo = resposta_modelo.get(
        "message",
        {}
    )

    chamadas = mensagem_modelo.get(
        "tool_calls",
        []
    )

    ferramentas_utilizadas = []

    # ========================================================
    # 4. RESPOSTA SEM FERRAMENTA
    # ========================================================

    if not chamadas:

        conteudo = (
            mensagem_modelo.get(
                "content",
                ""
            )
            .strip()
        )

        if not conteudo:

            conteudo = (
                "Não consegui gerar uma resposta "
                "para essa pergunta."
            )

        return {
            "resposta": conteudo,
            "ferramentas_utilizadas":
                ferramentas_utilizadas,
        }

    # ========================================================
    # 5. EXECUTA FERRAMENTAS
    # ========================================================

    resultados_ferramentas = []

    for chamada in chamadas:

        funcao = chamada.get(
            "function",
            {}
        )

        nome = funcao.get(
            "name"
        )

        argumentos = funcao.get(
            "arguments",
            {}
        )

        if isinstance(
            argumentos,
            str
        ):

            try:

                argumentos = json.loads(
                    argumentos
                )

            except json.JSONDecodeError:

                argumentos = {}

        ferramentas_utilizadas.append(
            nome
        )

        resultado = _executar_ferramenta(
            nome,
            argumentos
        )

        resultados_ferramentas.append(
            {
                "nome": nome,
                "argumentos": argumentos,
                "resultado": resultado,
            }
        )

    # ========================================================
    # 6. RESPOSTA DIRETA EM PYTHON
    # ========================================================

    if len(resultados_ferramentas) == 1:

        item = resultados_ferramentas[0]

        nome = item["nome"]

        resultado = item["resultado"]

        if _resultado_estruturado(nome):

            resposta_direta = _gerar_resposta_direta(
                nome,
                resultado,
                pergunta
            )

            if resposta_direta:

                return {
                    "resposta": resposta_direta,
                    "ferramentas_utilizadas":
                        ferramentas_utilizadas,
                }

    # ========================================================
    # 7. SEGUNDA CHAMADA AO GEMMA
    #
    # Só chega aqui quando:
    # - existem várias ferramentas; ou
    # - a ferramenta não possui formatter direto.
    # ========================================================

    resultados_compactados = []

    for item in resultados_ferramentas:

        resultados_compactados.append(
            {
                "ferramenta": item["nome"],
                "resultado": item["resultado"],
            }
        )

    mensagens_finais = [
        {
            "role": "system",
            "content":
                prompts.FINAL_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": pergunta,
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": chamadas,
        },
        {
            "role": "tool",
            "content": json.dumps(
                resultados_compactados,
                ensure_ascii=False,
            ),
        },
    ]

    resposta_final = _chamar_ollama(
        mensagens_finais,
        usar_ferramentas=False,
        max_tokens=MAX_TOKENS_RESPOSTA,
    )

    conteudo_final = (
        resposta_final
        .get("message", {})
        .get("content", "")
        .strip()
    )

    if not conteudo_final:

        conteudo_final = (
            "Os dados foram consultados, mas "
            "não foi possível gerar uma resposta textual."
        )

    return {
        "resposta": conteudo_final,
        "ferramentas_utilizadas":
            ferramentas_utilizadas,
    }