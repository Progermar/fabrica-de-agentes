# Como Criar um Assistente de Deep Research Gratuito com LangGraph

## 1. Visão Geral

Este documento descreve o desenvolvimento de um fluxo de **Deep Research** utilizando o framework **LangGraph**. O objetivo é construir um sistema que, a partir de um tópico de entrada, realiza pesquisa profunda na internet e entrega um relatório detalhado, sem depender de ferramentas privadas como o ChatGPT.

O fluxo utiliza:
- **LangGraph** para orquestração do workflow baseado em grafos
- **DuckDuckGo Search API** para busca web gratuita
- **OpenAI API** (GPT-4o / GPT-4o Mini) como LLM
- **Markdownify** para conversão de HTML para Markdown
- **Chainlit** (opcional) para interface de chat

Alternativas de LLM mencionadas: Ollama (local), Groq (gratuita).

---

## 2. Fundamentos do LangGraph

### 2.1. O que é LangGraph

LangGraph é um framework de agentes de IA criado pela LangChain, projetado para construir, implementar e gerenciar fluxos de trabalho complexos de agentes generativos. Ele é baseado na **teoria dos grafos**.

### 2.2. Componentes Principais

| Componente | Descrição |
|------------|-----------|
| **Nós (Nodes)** | Representam as ações/etapas do workflow. Cada nó é uma função Python. |
| **Arestas (Edges)** | Direcionam o fluxo de informação entre os nós (origem → destino). |
| **Estado (State)** | Estrutura de dados compartilhada (geralmente um `TypedDict`) que percorre todo o grafo. Cada nó lê e atualiza variáveis do estado. |
| **Start Node** | Nó inicializador que indica onde o grafo começa. |
| **End Node** | Nó finalizador que indica onde o grafo termina. |

### 2.3. Como o Estado Funciona

- O estado é inicializado com valores de entrada do usuário.
- Cada nó recebe o estado como **primeiro parâmetro obrigatório**.
- O nó processa as informações e retorna um dicionário com as variáveis que deseja atualizar no estado.
- A aresta transfere o estado atualizado para o próximo nó.
- O estado percorre: `start → nó1 → nó2 → ... → end`.

### 2.4. Outros Componentes Comuns nos Nós

- **Chat Models (LLMs)**: Tomam decisões ou criam/atualizam informações no estado.
- **Tools**: Ferramentas externas (APIs, acesso a diretórios, busca web).
- **Messages**: Mensagens do tipo `system`, `human` e `ai`, padrão dos chat models.

---

## 3. Arquitetura do Deep Research

### 3.1. Conceito

Deep Research é um fluxo que realiza pesquisa de informações sobre um tópico solicitado pelo usuário e, como resultado, cria um documento detalhado sobre o tema, utilizando diferentes fontes de informação.

**Importante**: este exemplo utiliza um **fluxo orientado** (não agentico). O LLM não toma decisões sobre o caminho; as arestas e o fluxo são definidos manualmente pelo desenvolvedor.

### 3.2. Tecnologias Utilizadas

| Tecnologia | Função |
|------------|--------|
| LangGraph | Orquestração do workflow em grafo |
| DuckDuckGo Search API | Busca web gratuita e aberta |
| OpenAI API | Modelo de linguagem (GPT-4o Mini para queries, GPT-4o para sumarização e escrita) |
| Markdownify | Converte HTML de páginas web para Markdown estruturado |
| Chainlit | Interface de chat (opcional) |

### 3.3. Fluxo de Execução (Diagrama)

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│   START     │────▶│ Gerador de Consulta │────▶│ Realiza Pesquisa│
└─────────────┘     │        Web          │     │   (DuckDuckGo)  │
                    └─────────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────────┐     ┌─────────────────────┐   ┌─────────────────┐
│  Inclui Fontes      │◄────│   Escritor Deep     │◄──│ Organizador /   │
│    Finais           │     │     Research        │   │   Resumidor     │
└────────┬────────────┘     └─────────────────────┘   └─────────────────┘
         │                              ▲
         │                              │
         ▼                              │
    ┌─────────┐     ┌──────────────┐   │
    │   END   │◄────│ Analista de  │───┘
    └─────────┘     │     Gaps     │
                    └──────┬───────┘
                           │
                           │ (se precisa mais info)
                           └────────────────────────────┘
```

### 3.4. Etapas do Fluxo

1. **Entrada do usuário**: tópico de pesquisa.
2. **Gerador de consulta web**: LLM cria uma query otimizada para busca.
3. **Realiza pesquisa**: DuckDuckGo busca 3 fontes; extrai URL, título, resumo e conteúdo completo (via Markdownify).
4. **Organizador / Resumidor**: LLM (GPT-4o) resume as 3 fontes em um sumário estruturado.
5. **Escritor Deep Research**: LLM (GPT-4o, temp=0.3) constrói ou atualiza o relatório de pesquisa profunda.
6. **Analista de Gaps**: LLM avalia se o relatório precisa de mais informações. Se sim, gera uma nova query secundária e retorna ao passo 3.
7. **Controle de loop**: contador limita o número máximo de iterações (ex: 2-3 loops).
8. **Inclui fontes finais**: concatena todas as URLs únicas ao final do relatório.
9. **End**: entrega o relatório final ao usuário.

---

## 4. Implementação Detalhada

### 4.1. Estrutura de Arquivos

```
repositorio/
├── main.py                 # Ponto de entrada e invocação do grafo
├── interface.py            # Integração com Chainlit (chat UI)
├── state.py                # Definição do estado (TypedDict)
├── funcoes_auxiliadoras.py # Funções auxiliares (formatação, busca, etc.)
```

### 4.2. Definição do Estado (`state.py`)

O estado utiliza `TypedDict` com `Annotated` e reducers (operador de adição) para listas.

```python
from typing import TypedDict, Annotated
from operator import add

class EstadoFluxoPrincipal(TypedDict):
    topico_pesquisa: str           # Tópico informado pelo usuário
    consulta_pesquisa_web: str     # Query gerada pelo LLM para busca
    resultados_web: Annotated[list, add]  # Lista de resultados de cada pesquisa
    fontes: Annotated[list, add]   # Lista de referências (título + URL)
    contador_loop_pesquisa: int    # Contador de iterações do loop
    max_loop_pesquisa: int         # Limite máximo de iterações
    sumarios_pesquisa: Annotated[list, add]  # Lista de sumários gerados
    resultado_final: str           # Relatório de pesquisa profunda final
```

**Variáveis principais:**
- `topico_pesquisa`: entrada do usuário.
- `consulta_pesquisa_web`: query otimizada pelo LLM.
- `resultados_web`: lista com conteúdo das páginas pesquisadas (acumulativo via reducer).
- `fontes`: referências bibliográficas acumuladas.
- `contador_loop_pesquisa` / `max_loop_pesquisa`: controle de iteração.
- `sumarios_pesquisa`: sumários de cada rodada de pesquisa.
- `resultado_final`: documento final de deep research.

### 4.3. Função de Busca Web (DuckDuckGo + Markdownify)

```python
from duckduckgo_search import DDGS
import requests
from markdownify import markdownify as md

def duckduckgo_pesquisa(consulta: str, max_resultados: int = 3):
    resultados = []
    with DDGS() as ddgs:
        busca = ddgs.text(consulta, max_results=max_resultados)
        for item in busca:
            url = item["href"]
            titulo = item["title"]
            resumo = item["body"]
            # Extrai conteúdo completo da página
            html = requests.get(url, timeout=10).text
            conteudo_completo = md(html)
            resultados.append({
                "titulo": titulo,
                "url": url,
                "resumo": resumo,
                "conteudo_completo": conteudo_completo
            })
    return resultados
```

**Retorno**: lista de dicionários com `titulo`, `url`, `resumo`, `conteudo_completo`.

### 4.4. Nós do Grafo

#### Nó 1: Gerador de Consulta Web

- **Modelo**: GPT-4o Mini
- **Saída estruturada**: classe Pydantic com `consulta` e `racional`
- **Entrada**: `topico_pesquisa` do estado
- **Saída**: atualiza `consulta_pesquisa_web`

**Prompt do sistema:**
> Aja como um pesquisador experiente. Com base no tópico de pesquisa e na data atual, gere uma consulta web otimizada para retornar diversas fontes relevantes sobre o tema.

#### Nó 2: Realiza Pesquisa

- Recebe `consulta_pesquisa_web` do estado.
- Executa `duckduckgo_pesquisa()`.
- Formata os resultados em texto único.
- Extrai título e URL para referências bibliográficas.
- Atualiza:
  - `resultados_web` (append)
  - `fontes` (append)
  - `contador_loop_pesquisa` (incrementa +1)

#### Nó 3: Organizador e Resumidor das Fontes

- **Modelo**: GPT-4o
- **Entrada**: último resultado de `resultados_web` (sempre pegar o último da lista, pois é acumulativo)
- **Saída**: atualiza `sumarios_pesquisa`

**Prompt do sistema:**
> Aja como um especialista em processamento de linguagem natural com 15 anos de experiência em resumos automáticos de textos técnicos. Com base no contexto pesquisado, crie um sumário estruturado a partir do tópico de pesquisa.

#### Nó 4: Escritor de Pesquisa Profunda

- **Modelo**: GPT-4o, temperatura=0.3
- **Função**: inicializa ou atualiza o documento de pesquisa profunda.
- **Lógica**:
  - Se `resultado_final` estiver vazio (iteração 0): inicia novo relatório.
  - Se já existir (iteração > 0): atualiza com novas informações.
- **Saída**: atualiza `resultado_final`

**Prompt do sistema:**
> Aja como um pesquisador acadêmico altamente qualificado com mais de 20 anos de experiência. Sua especialidade é coletar, interpretar e organizar informações dispersas em pesquisas profundas a partir de múltiplas fontes.

**Instruções incluídas:**
- Formato de saída esperado
- Pontos importantes e atenção
- Sumário da última pesquisa
- Estado atual da pesquisa profunda (iniciada ou não)

#### Nó 5: Analista de Gaps

- **Modelo**: GPT-4o Mini
- **Função**: avaliar se o relatório precisa de informações complementares.
- **Se sim**: gera nova query secundária.
- **Saída**: atualiza `consulta_pesquisa_web` com a nova query.

**Prompt do sistema:**
> Analise o relatório de pesquisa profunda atual e identifique gaps de informação. Se houver conteúdo faltante, gere uma nova consulta web para pesquisar informações complementares. Explique o raciocínio.

#### Nó 6: Inclui Fontes Finais

- **Função**: pega todas as URLs armazenadas em `fontes`, remove duplicatas.
- Concatena as referências bibliográficas ao final de `resultado_final`.
- **Saída**: atualiza `resultado_final` com o relatório completo + referências.

### 4.5. Arestas e Controle de Fluxo

#### Arestas Direcionais (fixas)

```
start → gerador_consulta_web
gerador_consulta_web → realiza_pesquisa
realiza_pesquisa → organizador_resumidor
organizador_resumidor → escritor_deep_research
escritor_deep_research → analista_gaps
analista_gaps → rota
inclui_fontes → end
```

#### Aresta Condicional (Rota)

O nó `rota` decide o próximo passo com base no estado:

```python
def rota(state: EstadoFluxoPrincipal):
    if state["contador_loop_pesquisa"] < state["max_loop_pesquisa"]:
        return "realiza_pesquisa"   # continua pesquisando
    else:
        return "inclui_fontes"      # finaliza
```

- Se o contador ainda não atingiu o máximo: volta para `realiza_pesquisa` com a nova query do analista.
- Se atingiu o limite: vai para `inclui_fontes` e depois `end`.

### 4.6. Montagem do Grafo

```python
from langgraph.graph import StateGraph, END

# Inicializa o construtor com o estado customizado
graph_builder = StateGraph(EstadoFluxoPrincipal)

# Adiciona os nós
graph_builder.add_node("gerador_consulta_web", gerador_consulta_web)
graph_builder.add_node("realiza_pesquisa", realiza_pesquisa)
graph_builder.add_node("organizador_resumidor", organizador_resumidor)
graph_builder.add_node("escritor_deep_research", escritor_deep_research)
graph_builder.add_node("analista_gaps", analista_gaps)
graph_builder.add_node("inclui_fontes", inclui_fontes)

# Arestas fixas
graph_builder.set_entry_point("gerador_consulta_web")
graph_builder.add_edge("gerador_consulta_web", "realiza_pesquisa")
graph_builder.add_edge("realiza_pesquisa", "organizador_resumidor")
graph_builder.add_edge("organizador_resumidor", "escritor_deep_research")
graph_builder.add_edge("escritor_deep_research", "analista_gaps")

# Aresta condicional
graph_builder.add_conditional_edges(
    "analista_gaps",
    rota,
    {
        "realiza_pesquisa": "realiza_pesquisa",
        "inclui_fontes": "inclui_fontes"
    }
)

# Aresta final
graph_builder.add_edge("inclui_fontes", END)

# Compila
graph = graph_builder.compile()
```

### 4.7. Invocação do Grafo

```python
# Estado inicial
estado_inicial = {
    "topico_pesquisa": "Me dê uma pesquisa profunda sobre o novo Papa eleito hoje",
    "consulta_pesquisa_web": "",
    "resultados_web": [],
    "fontes": [],
    "contador_loop_pesquisa": 0,
    "max_loop_pesquisa": 2,  # ou 3
    "sumarios_pesquisa": [],
    "resultado_final": ""
}

# Executa
resultado = graph.invoke(estado_inicial)
print(resultado["resultado_final"])
```

---

## 5. Testes e Resultados

### 5.1. Teste 1: Novo Papa Eleito

**Tópico**: "Me dê uma pesquisa profunda sobre o novo Papa eleito hoje"

**Execução**:
- Passou pelo gerador de consulta web
- Realizou pesquisas em 3 sites
- Criou a primeira pesquisa profunda
- Identificou necessidade de nova pesquisa
- Executou 3 iterações no total
- Incluiu todas as fontes no relatório final

**Estrutura do relatório gerado**:
- Título: A Ascensão do Papa: Um Novo Capítulo da Igreja Católica
- Introdução
- Contexto da Eleição
- Perfil do Papa
- Discurso Inaugural
- Desafios e Oportunidades
- Implicações Globais
- Conclusão
- Referências Bibliográficas

### 5.2. Teste 2: Desafios na Adoção de IA pelas Empresas

**Tópico**: "Poderia me entregar uma pesquisa focando nos desafios encontrados pelas empresas na adoção de AI em seus processos? Seja detalhada e forneça dados quantitativos também."

**Configuração**: 1 loop (para acelerar a demonstração)

**Estrutura do relatório gerado**:
- Título: Desafios na Adoção de Inteligência Artificial pelas Empresas
- Introdução
- Desafios Técnicos
- Falta de Talento Especializado
- Custos de Implementação
- Questões Éticas e Privacidade
- Mudança Cultural e Resistência Interna
- Dados de Qualidade
- Medição de Retorno sobre Investimento (ROI)
- Conclusão
- Referências Bibliográficas

---

## 6. Interface com Chainlit

### 6.1. O que é Chainlit

Chainlit é uma biblioteca Python para construção de interfaces de chat, similar ao Streamlit, mas focada em aplicações conversacionais com LLMs.

### 6.2. Integração

- Arquivo: `interface.py`
- Requer: `pip install chainlit`
- Permite interação via navegador com o fluxo LangGraph.
- O usuário digita o tópico no chat e o sistema executa o grafo completo em background.
- Resultado exibido na interface como resposta do assistente.

---

## 7. Considerações e Extensões

### 7.1. Limitações

- **DuckDuckGo Search API** pode ter limites de taxa de requisição (rate limiting).
- O exemplo é simplificado para fins didáticos; o ChatGPT possui um deep research muito mais robusto.

### 7.2. Possíveis Melhorias

- Aumentar o número de parágrafos por tópico no relatório final.
- Utilizar ferramentas de busca pagas para maior confiabilidade e volume de dados.
- Adicionar leitura de PDFs como fonte de informação adicional.
- Aumentar o número de loops (`max_loop_pesquisa`) para pesquisas mais profundas.
- Substituir OpenAI por modelos locais (Ollama) ou APIs gratuitas (Groq) para reduzir custos.

### 7.3. Aprendizado Principal

O LangGraph não é complicado quando se entende:
1. Como cada componente funciona (nós, arestas, estado)
2. Como os componentes se conectam
3. Como construir fluxos orientados unindo nós e arestas de forma manual

A partir de exemplos simples como este, é possível construir soluções muito mais robustas.

---

## 8. Referências

- Código-fonte completo disponível no GitHub (link na descrição do vídeo original)
- Framework: LangGraph (LangChain)
- Busca: DuckDuckGo Search API
- Conversão HTML→Markdown: Markdownify
- Interface: Chainlit
- Autor: Gustavo Sacchi
