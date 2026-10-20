# FeedbackFlow — Agente de Análise de Feedbacks

Agente conversacional para consultar e analisar pesquisas de satisfação de alunos. O projeto integra uma base consolidada no Google Sheets, funções de análise em Python, um modelo de linguagem executado localmente pelo Ollama e uma interface web construída no Lovable.


## Visão geral

O FeedbackFlow transforma perguntas em linguagem natural em consultas aos dados de feedback. Python executa os cálculos e análises; o modelo de linguagem auxilia na interpretação das perguntas e na seleção de ferramentas quando a intenção não é identificada por regras diretas.

As respostas devem ser fundamentadas nos registros disponíveis, sem inventar números nem tratar correlação como prova de causalidade.

## Funcionalidades

Ferramentas Python disponíveis:

- **Métricas gerais:** total de respostas, CSAT médio, NPS médio e categoria principal.
- **Comparação de ciclos:** comparação de métricas entre ciclos de um projeto.
- **Cruzamento de variáveis:** distribuição das combinações entre variáveis disponíveis.
- **Correlação numérica:** cálculo da correlação entre CSAT e NPS.
- **Principais categorias:** categorias mais frequentes de problemas de permanência.
- **Comentários por categoria:** consulta de comentários associados a uma categoria.

A aplicação também inclui API FastAPI, integração com Ollama, leitura da base consolidada no Google Sheets, cache dos dados por cinco minutos, regras para algumas intenções frequentes e perguntas conhecidas fora do escopo, além da interface conversacional no Lovable.

## Arquitetura

```text
Usuário
  |
  v
Interface web (Lovable)
  |
  v
API FastAPI (/chat)
  |
  v
Agente (Agente/ollama.py)
  |                         \\
  |                          \\--> Modelo local via Ollama
  v
Ferramentas Python
  |
  v
Tratamento e métricas
  |
  v
Google Sheets — base consolidada
```

- **Lovable:** interface de conversa.
- **FastAPI (`api.py`):** recebe as requisições HTTP, valida a mensagem e retorna JSON.
- **Agente (`Agente/ollama.py`):** verifica algumas intenções e condições fora do escopo, chama o modelo quando necessário, executa ferramentas e organiza a resposta.
- **Prompts (`Agente/prompts.py`):** definem o papel do agente e os schemas das ferramentas.
- **Ferramentas (`Agente/ferramentas.py`):** conectam as funções de análise aos dados.
- **Tratamento (`Tratamento/metricas.py`):** executa cálculos e análises.
- **Google Sheets:** armazena a base consolidada.
- **Ollama:** executa o modelo de linguagem localmente.

## Estado atual e possibilidades de evolução

O FeedbackFlow foi desenvolvido para execução local, utilizando Python, FastAPI e Ollama para integrar um modelo de linguagem a ferramentas de análise de dados e a uma base consolidada de feedbacks educacionais. Essa configuração permite desenvolver e validar o agente sem depender de uma infraestrutura de produção.

A arquitetura estabelece uma base para evoluções futuras, como:

- **Hospedagem da API em servidor:** ampliar as possibilidades de disponibilidade e acesso, com a infraestrutura e os controles de segurança adequados.
- **Integração com modelos de IA mais avançados:** buscar melhorar a interpretação das solicitações e a qualidade das respostas.
- **Aprimoramento de desempenho e escalabilidade:** adaptar o sistema a maiores volumes de uso conforme a necessidade.

Essas possibilidades ainda não devem ser entendidas como funcionalidades implementadas. Os ganhos dependerão do modelo escolhido, da infraestrutura, dos custos envolvidos e da validação dos resultados. Hospedar a aplicação, por si só, não garante respostas melhores.

## Tecnologias

- Python
- FastAPI e Pydantic
- Requests
- Ollama
- Modelo `lukaspetrik/gemma3-tools:4b`
- Google Sheets e Google Drive
- gspread (conforme dependências do projeto)
- Lovable
- ngrok para expor temporariamente a API local durante testes

## Estrutura do projeto

A estrutura pode variar conforme os arquivos existentes no repositório. Os principais módulos conhecidos são:

```text
Agente - Análise de Feedbacks/
├── api.py
├── config.py
├── .env
├── requirements.txt
├── credentials/
│   └── service_account.json
├── Agente/
│   ├── ollama.py
│   ├── prompts.py
│   └── ferramentas.py
├── Tratamento/
│   └── metricas.py
└── Saida/
    └── shets_consolidada.py
```

> Confirme os nomes e a organização dos arquivos no repositório. O módulo `Saida/shets_consolidada.py` aparece com essa grafia no código atual.

## Pré-requisitos

- Python instalado.
- Ollama instalado e em execução.
- Modelo configurado no projeto disponível no Ollama.
- Acesso à planilha consolidada do Google Sheets.
- Conta de serviço Google com permissões adequadas.
- Variáveis de ambiente configuradas.

Confira os modelos instalados:

```powershell
ollama list
```

O modelo esperado na configuração atual é `lukaspetrik/gemma3-tools:4b`. Para baixá-lo, se necessário:

```powershell
ollama pull lukaspetrik/gemma3-tools:4b
```

A velocidade do modelo local depende do hardware, especialmente CPU, memória RAM e eventual aceleração por GPU.

## Configuração

### 1. Clonar o repositório

```bash
git clone URL_DO_SEU_REPOSITORIO
cd "Agente - Análise de Feedbacks"
```

Substitua `URL_DO_SEU_REPOSITORIO` pelo endereço real do repositório.

### 2. Criar ambiente virtual (recomendado)

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto e preencha as variáveis exigidas pelo `config.py`. A configuração conhecida inclui:

```dotenv
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=lukaspetrik/gemma3-tools:4b

GOOGLE_CREDENTIALS_FILE=credentials/service_account.json
GOOGLE_DRIVE_FOLDER_ID=ID_DA_PASTA_DO_GOOGLE_DRIVE
SHEET_CONSOLIDADA_ID=ID_DA_PLANILHA_CONSOLIDADA
SHEET_CONSOLIDADA_ABA=Dados
```

Os nomes exatos das variáveis relacionadas às planilhas de origem devem corresponder ao `config.py`; inclua também todas as outras variáveis que ele exigir.

**Não publique credenciais, tokens, chaves privadas, `.env` nem `credentials/service_account.json` no GitHub.** Inclua esses arquivos no `.gitignore`.

### 4. Configurar Google Sheets

1. Configure uma conta de serviço Google e habilite as APIs necessárias para Drive e Sheets.
2. Salve o JSON da conta de serviço em `credentials/service_account.json`.
3. Compartilhe as pastas e planilhas necessárias com o e-mail da conta de serviço.
4. Preencha os IDs e nomes das abas no `.env`.
5. Confirme que a aba consolidada configurada corresponde à planilha real.

O agente consulta a base consolidada. A execução da ingestão/consolidação depende dos módulos de pipeline existentes no repositório.

### 5. Verificar o Ollama

Confirme que o Ollama está respondendo e que o modelo esperado aparece em `ollama list`. Se o Ollama já estiver em execução, não é necessário iniciar outra instância.

## Como executar

Na raiz do projeto, inicie a API:

```powershell
uvicorn api:app
```

Endereços esperados:

- API local: `http://127.0.0.1:8000`
- Documentação interativa: `http://127.0.0.1:8000/docs`
- Verificação de saúde: `http://127.0.0.1:8000/health`

O endpoint `/health` deve retornar:

```json
{
  "status": "ok"
}
```

## Testar a API

1. Abra `http://127.0.0.1:8000/docs`.
2. Expanda `POST /chat` e clique em **Try it out**.
3. Use o formato mostrado no Swagger. O modelo atual da API recebe a propriedade `mensagem`, por exemplo:

```json
{
  "mensagem": "Quais são as três principais categorias de problemas para permanência?"
}
```

4. Clique em **Execute** e confira o status HTTP e o corpo da resposta.

A resposta inclui `resposta` e `ferramentas_utilizadas`. Perguntas fora do escopo também podem retornar HTTP 200, pois são tratadas como respostas válidas do agente.

> O `api.py` descrito aqui não registra uma rota `/pipeline/executar`. Para executar a consolidação, confira os módulos de pipeline presentes no repositório e os endpoints realmente listados em `/docs`.

## Integração com o Lovable

Como o Lovable está hospedado e a API roda no computador local, a interface hospedada não consegue acessar diretamente `localhost`. Para testes, o ngrok pode expor temporariamente a porta da API.

Em outro terminal:

```powershell
ngrok http 8000
```

Copie a URL HTTPS gerada e configure a interface para chamar:

```text
https://SUA-URL-NGROK/chat
```

O corpo da requisição deve seguir o contrato da API:

```json
{
  "mensagem": "Qual é o CSAT médio?"
}
```

A interface deve exibir o campo `resposta`. Não trate `ferramentas_utilizadas: []` como erro automaticamente: perguntas fora do escopo podem ser respondidas sem executar ferramentas.

**Segurança:** use ngrok para testes, não exponha credenciais no frontend e restrinja CORS antes de disponibilizar a aplicação publicamente. Ter HTTPS via ngrok não significa que a API esteja pronta para produção.

## Exemplos de perguntas

- “Quantas respostas existem na base?”
- “Qual é o CSAT médio?”
- “Qual é o NPS médio?”
- “Quais são as três principais categorias de problemas de permanência?”
- “Qual é a correlação entre CSAT e NPS?”
- “Compare os ciclos do Projeto 1.”
- “Cruze ciclo e CSAT.”
- “Quais comentários aparecem na categoria Suporte?”

Os nomes de projetos, categorias e variáveis precisam corresponder aos valores da base e às opções aceitas pelas ferramentas.

## Escopo e limitações

O agente foi desenvolvido para analisar dados de feedback dos alunos: projetos, ciclos, CSAT, NPS, problemas, reclamações, comentários e sugestões de melhoria.

Perguntas que não possam ser respondidas com esses dados devem receber uma resposta que informe a limitação, sem inventar informações.

A implementação combina regras Python para algumas perguntas conhecidas, um modelo de linguagem local para auxiliar na interpretação de outras perguntas e ferramentas Python para calcular resultados. A detecção de fora do escopo ainda depende parcialmente de padrões explícitos: um prompt, sozinho, não garante que todas as perguntas fora do domínio sejam identificadas corretamente.

Outras limitações:

- Os resultados dependem da consistência e atualização da planilha consolidada.
- O cache dura cinco minutos; alterações na planilha podem não aparecer imediatamente.
- O tempo de resposta do modelo local varia conforme o hardware.
- A versão atual foi estruturada para execução local; hospedagem em servidor e adoção de um modelo mais avançado são possibilidades de evolução, não recursos já implantados.
- A média das respostas NPS (escala de 0 a 10) não é o NPS clássico, calculado pela diferença entre os percentuais de promotores e detratores.
- Correlação indica associação estatística, não causalidade.
- A API local precisa ser exposta ou implantada para ser acessada fora do computador.
- Não presuma que existe uma rota de pipeline se ela não estiver registrada no código e na documentação `/docs`.

## Solução de problemas

### A API não inicia

Confirme que o terminal está na pasta raiz, que o ambiente Python está ativado, que as dependências foram instaladas e que as variáveis do `.env` estão preenchidas. Verifique erros de importação no terminal.

### O endpoint `/chat` retorna erro

- Consulte o terminal do Uvicorn.
- Confira o corpo da requisição: a propriedade de entrada é `mensagem`.
- Verifique `OLLAMA_URL` e `OLLAMA_MODEL`.
- Confirme que o Ollama está em execução e que o modelo aparece em `ollama list`.

### O agente demora para responder

O modelo roda localmente, então o tempo depende do hardware e da complexidade da chamada. As rotas Python diretas podem evitar uma chamada ao modelo quando reconhecem uma intenção já implementada.

### A interface mostra erro

- Confira `http://127.0.0.1:8000/health`.
- Verifique se a URL atual do ngrok termina em `/chat`.
- Confira no navegador o status HTTP e o corpo da resposta.
- Confirme que o frontend lê o campo `resposta`.
- Uma resposta válida com `ferramentas_utilizadas: []` não é, por si só, uma falha.

### Os números não refletem a planilha atualizada

O cache dura cinco minutos. Aguarde sua expiração ou use a rotina de recarga existente no código, se aplicável. Confirme também o ID da planilha e o nome da aba configurados.

## Melhorias futuras

- Ampliar testes automatizados para perguntas dentro e fora do escopo.
- Tornar mais robusta a decisão entre responder, chamar uma ferramenta ou recusar uma pergunta.
- Melhorar o registro de erros e tempos de resposta.
- Implementar autenticação e restringir CORS antes de uma implantação pública.
- Documentar e automatizar a execução do pipeline conforme os módulos realmente disponíveis.
- Criar testes de integração entre interface, API, modelo e Google Sheets.
- Avaliar a hospedagem da API em servidor e a integração com um modelo de IA mais avançado, considerando segurança, custos e desempenho.
