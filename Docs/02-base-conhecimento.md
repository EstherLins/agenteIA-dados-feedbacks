# Base de Conhecimento — FeedbackFlow

# 1. Objetivo

A base de conhecimento define a estrutura dos dados utilizados pelo FeedbackFlow e como esses dados são disponibilizados ao agente.

O sistema analisa pesquisas de satisfação de alunos de diferentes projetos e ciclos. O Python é responsável pelo tratamento e pelos cálculos; o agente interpreta as perguntas e utiliza as ferramentas disponíveis para consultar os dados.

---

# 2. Fontes de Dados

O sistema utiliza cinco planilhas de pesquisa de satisfação como fontes de entrada.

Cada planilha representa uma fonte de respostas. As fontes podem representar:

- diferentes projetos;
- diferentes ciclos;
- diferentes turmas;
- diferentes períodos.

A estrutura das planilhas pode variar entre as fontes. Por isso, o pipeline Python padroniza os dados antes de consolidá-los.

A base consolidada é a fonte consultada pelas ferramentas analíticas. Os indicadores retornados dependem dos registros que estiverem presentes nessa planilha no momento em que os dados forem carregados.

---

# 3. Pipeline de Tratamento

O pipeline Python é responsável por ler as planilhas de origem, padronizar os dados e consolidá-los.

```text
Planilhas de pesquisa (5 fontes)
     ↓
Leitura dos dados
     ↓
Padronização dos nomes das colunas
     ↓
Tratamento dos tipos de dados
     ↓
Tratamento de valores ausentes
     ↓
Normalização dos campos e categorias
     ↓
Tratamento das datas
     ↓
Consolidação
     ↓
Google Sheets Consolidada
```

A estrutura contempla o tratamento e a padronização necessários à consolidação. A anonimização não deve ser considerada garantida sem uma etapa específica implementada e validada para esse fim.

---

# 4. Google Sheets Consolidada

Após o tratamento, os dados são armazenados em uma Google Sheets consolidada. Essa planilha é a fonte de dados utilizada pelas ferramentas analíticas do agente.

Estrutura geral:

```text
Planilhas de pesquisa
        ↓
Pipeline Python
        ↓
Google Sheets Consolidada
        ↓
Funções analíticas Python
        ↓
Agente / FastAPI
        ↓
Ollama com Gemma 3 4B compatível com tool calling
        ↓
Resposta enviada ao Lovable
```

O backend pode utilizar cache temporário dos dados consolidados. Portanto, uma alteração na planilha pode não aparecer imediatamente se o cache ainda estiver válido; a implementação utiliza uma janela de cache de cinco minutos e também possui mecanismo de recarga.

---

# 5. Campos dos Dados

A base consolidada utiliza nomes internos padronizados, incluindo:

- `datahora_registro`
- `projeto`
- `ciclo`
- `nome_aluno`
- `turma`
- `modalidade`
- `csat`
- `nps`
- `principal_problema_permanencia`
- `problema_reclamacao`
- `tipos_melhoria_sugerida`
- `sugestao_melhoria`
- `id_planilha_origem`
- `arquivo_origem`
- `id_registro`
- `categoria_problema_reclamacao`

Os nomes apresentados são os identificadores internos utilizados pelo tratamento e pelas funções analíticas. Os cabeçalhos visíveis nas planilhas de origem podem ser diferentes e são mapeados para o padrão interno.

---

# 6. Padronização

O pipeline padroniza os nomes das colunas e os tipos de dados antes da consolidação.

Exemplo:

```text
Fonte 1:
Projeto

Fonte 2:
Nome do Projeto

Fonte 3:
Projeto/Curso
```

Após o tratamento, os nomes equivalentes são representados pelo campo interno:

```text
projeto
```

O mesmo princípio é aplicado aos demais campos. Os campos `ciclo`, `csat` e `nps` são tratados como numéricos; valores textuais ausentes recebem um valor indicativo, enquanto os valores numéricos ausentes permanecem sem valor numérico.

---

# 7. Tratamento de Categorias

As categorias são utilizadas para agrupar problemas e reclamações. Entre os valores presentes na base de teste estão:

```text
Acesso a equipamentos
Plataforma utilizada
Qualidade do conteúdo
Didática de ensino
Suporte
```

As funções podem agrupar os registros a partir dos campos de problema e categoria disponíveis. A padronização de variações de escrita deve ocorrer no tratamento dos dados para que os agrupamentos não sejam distorcidos por diferenças de nomenclatura.

---

# 8. Indicadores

O agente pode consultar indicadores calculados pelas funções Python.

## CSAT

Indicador de satisfação do aluno, registrado na escala de 1 a 5.

```text
1 a 5
```

A média de CSAT é calculada a partir dos valores numéricos válidos que atendem aos filtros da consulta.

---

## NPS

Indicador de recomendação, registrado na escala de 0 a 10.

```text
0 a 10
```

O NPS é tratado como um indicador distinto da nota individual de recomendação. A forma de cálculo do indicador NPS deve seguir a implementação da ferramenta correspondente; não deve ser inferida apenas a partir da média das notas.

---

# 9. Ferramentas do Agente

As ferramentas analíticas são executadas em Python. O modelo pode selecionar uma ferramenta e fornecer seus argumentos, mas os cálculos são realizados pelo código.

## `calcular_metricas()`

Retorna indicadores agregados, como total de respostas, CSAT médio, NPS médio e categoria mais frequente do principal problema para permanência, conforme os filtros aplicados.

Exemplo ilustrativo de estrutura de resultado:

```json
{
  "projeto": "Projeto A",
  "ciclo": 2,
  "total_respostas": 120,
  "csat_medio": 4.1
}
```

Os valores desse exemplo são apenas ilustrativos, não representam necessariamente os dados atuais da planilha.

---

## `comparar_ciclos()`

Compara indicadores entre ciclos de um mesmo projeto. A comparação deve considerar o total de respostas de cada ciclo, pois tamanhos de amostra diferentes afetam a interpretação dos resultados.

Exemplo de estrutura:

```json
{
  "projeto": "Projeto A",
  "ciclo_1": {
    "csat": 3.8
  },
  "ciclo_2": {
    "csat": 4.1
  }
}
```

Os valores são ilustrativos.

---

## `cruzar_variaveis()`

Realiza cruzamentos entre variáveis para observar como as respostas se distribuem entre grupos.

Exemplo:

```text
Modalidade
×
Principal problema para permanência
```

---

## `correlacionar_numericas()`

Analisa a associação entre variáveis numéricas.

Exemplo:

```text
CSAT × NPS
```

Correlação indica associação estatística e, por si só, não demonstra causalidade.

---

## `top_categorias_problemas()`

Identifica as categorias de problemas mais frequentes, permitindo observar quais temas aparecem mais nos registros.

Exemplo:

```text
Categorias de problemas
→ quantidade de registros por categoria
```

---

## `comentarios_por_categoria()`

Recupera ou organiza comentários associados a uma categoria de problema ou reclamação, de acordo com os filtros aceitos pela ferramenta.

Exemplo:

```text
Categoria:
Plataforma utilizada
```

---

# 10. Fluxo de Consulta

Quando o usuário faz uma pergunta, o sistema pode seguir um fluxo com chamada de ferramenta ou tratar diretamente algumas intenções reconhecidas pelo backend.

Fluxo com ferramenta:

```text
Usuário
   ↓
Lovable
   ↓
FastAPI (/chat)
   ↓
Agente Python
   ↓
Ollama / Gemma 3 compatível com tool calling
   ↓
Seleção da ferramenta e argumentos
   ↓
Função analítica Python
   ↓
Google Sheets Consolidada / dados carregados
   ↓
Resultado estruturado
   ↓
Agente interpreta e prepara a resposta, quando necessário
   ↓
FastAPI
   ↓
Lovable
   ↓
Usuário
```

Para algumas perguntas diretas, o backend pode identificar a intenção e executar o caminho adequado sem exigir todas as etapas de tool calling. Quando o resultado de uma ferramenta já está estruturado, o backend também pode formatá-lo diretamente, evitando uma chamada adicional ao modelo.

Perguntas que exigem informações externas em tempo real, como previsão do tempo, não devem receber respostas inventadas se o agente não tiver uma ferramenta ou fonte capaz de consultá-las.

---

# 11. Papel do LLM

O LLM não é responsável por:

- armazenar os dados;
- limpar ou consolidar as planilhas;
- normalizar os registros;
- realizar os cálculos oficiais dos indicadores;
- alterar a planilha;
- excluir registros.

O LLM é responsável por:

- interpretar a pergunta;
- identificar a intenção;
- selecionar ferramentas quando necessário;
- fornecer argumentos para as ferramentas;
- interpretar os resultados retornados;
- redigir respostas em linguagem natural quando necessário.

Os cálculos e filtros analíticos devem permanecer nas funções Python. A resposta deve refletir os resultados retornados pelas ferramentas, sem inventar dados ausentes.

---

# 12. Fonte de Verdade

A fonte de dados utilizada pelo agente é:

```text
Google Sheets Consolidada
```

O Ollama não acessa a planilha diretamente. A leitura e os cálculos ocorrem por meio das funções Python executadas no backend.

Como o backend pode manter os dados em cache por até cinco minutos, a resposta pode refletir a última carga válida, e não necessariamente uma alteração feita segundos antes na planilha.

---

# 13. Segurança dos Dados

A Google Sheets Consolidada não deve ser exposta diretamente ao usuário final.

As credenciais de acesso à planilha devem permanecer no backend. O Lovable não deve receber:

- credenciais;
- tokens;
- chaves de API;
- credenciais do Google;
- informações internas da infraestrutura.

A API disponibiliza o endpoint de conversa `/chat`; a documentação e os recursos de diagnóstico do backend devem ser usados de acordo com a configuração do ambiente. A URL pública do ngrok é um meio de acesso de desenvolvimento e pode mudar quando o túnel é reiniciado.

---

# 14. Princípio Central

```text
Planilhas de pesquisa
    ↓
Pipeline Python
    ↓
Tratamento e consolidação
    ↓
Google Sheets Consolidada
    ↓
Funções analíticas Python
    ↓
Agente / FastAPI
    ↓
Ollama com Gemma 3 compatível com tool calling
    ↓
FastAPI
    ↓
Lovable
    ↓
Usuário
```

A separação de responsabilidades deve ser preservada durante toda a evolução do projeto: os dados são tratados e calculados pelo Python, o modelo interpreta as perguntas e a API coordena a comunicação entre o frontend e o agente.
