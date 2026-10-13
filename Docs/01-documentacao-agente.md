# Documentação do Agente — FeedbackFlow

# 1. Visão Geral

O FeedbackFlow é um agente de análise de pesquisas de satisfação acadêmica.

Seu objetivo é permitir que gestores e responsáveis pelos projetos consultem informações sobre os feedbacks dos alunos utilizando linguagem natural.

O sistema combina:

- Python;
- Google Sheets;
- FastAPI;
- Ollama;
- Lovable.

---

# 2. Problema

As pesquisas de satisfação são coletadas em diferentes planilhas.

Isso pode gerar:

- dados dispersos;
- estruturas diferentes;
- nomes de campos inconsistentes;
- dificuldade de consolidação;
- dificuldade de comparação entre ciclos;
- dificuldade de identificação de padrões;
- análises manuais demoradas.

---

# 3. Solução

O sistema utiliza um pipeline Python para transformar cinco planilhas de pesquisa em uma única base consolidada.

O fluxo é:

```text
5 Planilhas de Pesquisa
          ↓
      Pipeline Python
          ↓
Tratamento e Normalização
          ↓
Google Sheets Consolidada
          ↓
      Funções Python
          ↓
        FastAPI
          ↓
        Ollama
          ↓
        FastAPI
          ↓
        Lovable
          ↓
        Usuário
```

---

# 4. Arquitetura

```text
┌───────────────────────┐
│  PLANILHA DE PESQUISA │
│          1            │
└───────────┬───────────┘
            │
┌───────────────────────┐
│  PLANILHA DE PESQUISA │
│          2            │
└───────────┬───────────┘
            │
┌───────────────────────┐
│  PLANILHA DE PESQUISA │
│          3            │
└───────────┬───────────┘
            │
┌───────────────────────┐
│  PLANILHA DE PESQUISA │
│          4            │
└───────────┬───────────┘
            │
┌───────────────────────┐
│  PLANILHA DE PESQUISA │
│          5            │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│     PIPELINE PYTHON   │
│                       │
│ • Tratamento          │
│ • Normalização        │
│ • Padronização        │
│ • Anonimização        │
│ • Consolidação        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ GOOGLE SHEETS         │
│ CONSOLIDADA           │
│                       │
│ Fonte de dados        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│    FUNÇÕES PYTHON     │
│                       │
│ • Métricas            │
│ • Comparações         │
│ • Cruzamentos         │
│ • Correlações         │
│ • Reclamações         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       FASTAPI         │
│                       │
│ • Autenticação        │
│ • Validação           │
│ • Controle            │
│ • Comunicação         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│        OLLAMA         │
│                       │
│ • Gemma 3 4B          │
│ • Interpretação       │
│ • Native Tool Calling │
│ • Geração de resposta │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       FASTAPI         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│        LOVABLE        │
│                       │
│ • Chat                │
│ • Dashboard           │
│ • Gráficos            │
│ • Filtros             │
└───────────┬───────────┘
            │
            ▼
         USUÁRIO
```

---

# 5. Responsabilidade de Cada Camada

## Python — Pipeline

Responsável por:

- ler as cinco planilhas;
- tratar os dados;
- normalizar;
- padronizar;
- anonimizar;
- consolidar;
- enviar os dados para a Google Sheets consolidada.

---

## Google Sheets

Responsável por:

- armazenar os dados consolidados;
- servir como fonte para as consultas das funções Python.

A Google Sheets não deve ser exposta diretamente ao usuário.

---

## Python — Ferramentas

Responsável por:

- consultar os dados;
- realizar cálculos;
- gerar indicadores;
- executar cruzamentos;
- realizar análises autorizadas.

---

## FastAPI

Responsável por:

- receber solicitações do Lovable;
- controlar autenticação;
- validar requisições;
- controlar ferramentas;
- conversar com o Ollama;
- executar funções Python;
- retornar respostas.

---

## Ollama

Responsável por:

- interpretar perguntas;
- identificar intenções;
- realizar **native tool calling** quando necessário;
- selecionar as ferramentas disponíveis;
- enviar os argumentos das ferramentas;
- interpretar os resultados retornados pelo Python;
- gerar respostas em linguagem natural.

O modelo utilizado atualmente é o **Gemma 3 4B com suporte a ferramentas**, executado localmente pelo **Ollama**.

Para algumas perguntas simples e objetivas, o agente Python possui uma rota direta de intenção antes da chamada ao LLM. Isso reduz a latência sem substituir o native tool calling para perguntas que exigem interpretação do modelo.

---

## Lovable

Responsável pela interface.

Pode possuir:

- login;
- chat;
- histórico.

---

# 6. Fluxo Completo de uma Pergunta

Usuário:

> Qual foi o principal problema do Projeto A no Ciclo 2?

### Etapa 1

O usuário envia a pergunta pelo Lovable.

### Etapa 2

O Lovable envia a pergunta para:

```http
POST /chat
```

### Etapa 3

A FastAPI recebe e valida a solicitação.

### Etapa 4

A pergunta passa pelo agente Python, que verifica se existe uma intenção simples que pode ser resolvida diretamente.

### Etapa 5

Quando a pergunta exige interpretação do LLM, ela é enviada ao **Gemma 3 4B pelo Ollama**, utilizando native tool calling.

### Etapa 6

O modelo identifica a ferramenta necessária e fornece os argumentos.

Exemplo:

```text
calcular_metricas(
    projeto="Projeto A",
    ciclo=2
)
```

### Etapa 7

A função Python recebe a chamada da ferramenta e valida seus argumentos.

### Etapa 8

A ferramenta consulta a Google Sheets consolidada.

### Etapa 9

A função retorna o resultado calculado pelo Python.

Exemplo:

```json
{
  "projeto": "Projeto A",
  "ciclo": 2,
  "total_respostas": 115,
  "categoria_principal": "Plataforma utilizada",
  "percentual": 38
}
```

### Etapa 10

Quando necessário, o resultado retorna ao Gemma para geração da resposta em linguagem natural.

Para uma única ferramenta estruturada, o agente pode formatar a resposta diretamente em Python, evitando uma segunda chamada ao LLM.

### Etapa 11

O agente gera a resposta:

> No Projeto A, Ciclo 2, o principal problema identificado foi a Plataforma utilizada, representando 38% dos registros analisados.

### Etapa 12

A FastAPI retorna a resposta para o Lovable.

### Etapa 13

O Lovable apresenta a resposta ao usuário.

---

# 7. Endpoint Principal

O endpoint inicial pode ser:

```http
POST /chat
```

Requisição:

```json
{
  "mensagem": "Qual foi o principal problema do Projeto A no Ciclo 2?"
}
```

Resposta:

```json
{
  "resposta": "No Projeto A, Ciclo 2, o principal problema identificado foi a Plataforma utilizada, representando 38% dos registros analisados.",
  "projeto": "Projeto A",
  "ciclo": 2,
  "ferramentas_utilizadas": [
    "calcular_metricas"
  ]
}
```

---

# 8. Segurança

## Tratamento de perguntas fora do escopo

O agente possui validação para perguntas que não pertencem ao domínio de análise de feedbacks.

Exemplo:

> "Qual é a previsão do tempo para Fortaleza hoje?"

Nesse caso, o agente não inventa uma previsão. Ele informa que não possui acesso a ferramentas de dados meteorológicos em tempo real.

Uma resposta textual válida, mesmo sem utilização de ferramentas, é considerada uma resposta normal pelo backend.



## Lovable

O Lovable não deve possuir:

- credenciais do Google;
- tokens do Ollama;
- credenciais da API;
- credenciais da Google Sheets.

---

## Ollama

O Ollama não deve:

- acessar diretamente a Google Sheets;
- acessar diretamente credenciais;
- executar código arbitrário;
- alterar dados;
- excluir dados.

---

## FastAPI

A FastAPI deve:

- validar usuários;
- validar requisições;
- controlar permissões;
- controlar ferramentas;
- validar argumentos;
- proteger credenciais;
- controlar acesso aos dados.

---

# 9. Privacidade

O pipeline deve anonimizar ou remover informações pessoais antes que os dados sejam disponibilizados às ferramentas.

Sempre que possível, o agente deve trabalhar com:

- totais;
- médias;
- percentuais;
- categorias;
- distribuições;
- comparações agregadas.

---

# 10. Anti-Alucinação

O sistema deve seguir:

```text
LLM NÃO CALCULA
        ↓
Python CALCULA
        ↓
Resultado retorna
        ↓
LLM EXPLICA
```

Regras:

1. Não inventar números.
2. Não estimar valores.
3. Não criar dados inexistentes.
4. Não inventar categorias.
5. Não inventar respostas de alunos.
6. Não responder indicadores sem consultar a ferramenta.
7. Não executar código arbitrário.
8. Não acessar dados diretamente.
9. Informar quando não houver dados.
10. Respeitar o escopo das ferramentas.

---

# 11. Modelo e Execução Local

O LLM utilizado atualmente é o **Gemma 3 4B com suporte a ferramentas**, executado localmente por meio do **Ollama**.

A execução local permite desenvolver e testar o agente sem depender de uma API paga de LLM para cada consulta. A principal limitação observada é a latência, especialmente quando o modelo é executado utilizando CPU.

Durante os testes, uma chamada ao Ollama chegou a aproximadamente **162,17 segundos**. Essa latência está relacionada principalmente à inferência local e aos recursos de hardware disponíveis na máquina de desenvolvimento.

Para reduzir esse impacto, foram implementadas otimizações como:

- cache dos dados consolidados;
- retorno direto para ferramentas estruturadas quando possível;
- detecção direta de algumas intenções simples;
- redução de chamadas desnecessárias ao LLM;
- uso de `keep_alive` no Ollama.

# 12. Ferramentas Disponíveis

Atualmente, o agente possui seis ferramentas principais:

1. `calcular_metricas` — total de respostas, CSAT médio, NPS médio e categorias;
2. `comparar_ciclos` — comparação dos resultados entre ciclos;
3. `cruzar_variaveis` — cruzamento entre variáveis permitidas;
4. `correlacionar_numericas` — correlação entre CSAT e NPS;
5. `top_categorias_problemas` — principais categorias de problemas;
6. `comentarios_por_categoria` — comentários associados a uma categoria.

# 13. Dados Utilizados nos Testes

A base consolidada utilizada nos testes possui:

- **244 registros**;
- Projetos: **Projeto 1, Projeto 2 e Projeto 4**;
- Ciclos: **1 e 2**;
- CSAT em escala de **1 a 5**;
- NPS em escala de **0 a 10**.

# 14. Endpoint e Integração

O endpoint principal é:

```http
POST /chat
```

Formato de requisição:

```json
{
  "mensagem": "Qual é o total de respostas?"
}
```

Formato de resposta com ferramenta:

```json
{
  "resposta": "A base possui 244 respostas.",
  "ferramentas_utilizadas": [
    "calcular_metricas"
  ]
}
```

O backend também pode retornar uma resposta válida sem ferramentas:

```json
{
  "resposta": "Eu não tenho acesso a ferramentas para consultar dados em tempo real.",
  "ferramentas_utilizadas": []
}
```

Uma lista vazia em `ferramentas_utilizadas` não significa erro: a resposta pode ter sido produzida sem utilizar uma ferramenta.

# 15. Princípio Central

A arquitetura deve manter uma separação clara:

```text
PYTHON
Tratamento + Normalização + Cálculos
              ↓
GOOGLE SHEETS
Dados Consolidados
              ↓
FASTAPI
Controle + Segurança + Orquestração
              ↓
OLLAMA
Interpretação + Tool Calling
              ↓
FASTAPI
Resposta Controlada
              ↓
LOVABLE
Interface
              ↓
USUÁRIO
Consulta + Decisão
```

O objetivo é utilizar o LLM como uma camada de interpretação e interação, mantendo o processamento dos dados e os cálculos sob controle do código Python.
