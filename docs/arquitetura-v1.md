# Arquitetura V1 — Account Intelligence Agent

## Objetivo desta decisão

Conectar o esqueleto LangGraph já validado a fontes reais da web e a LLMs reais, preservando rastreabilidade, controle de custo e possibilidade de troca de fornecedores.

## Arquitetura escolhida para a V1

```text
Conta-alvo
   ↓
LangGraph
   ↓
plan_research
   ↓
SearchProvider
   └── Brave Search API
   ↓
ContentExtractor
   └── Firecrawl
   ↓
extract_evidence
   ↓
LLMProvider
   └── OpenAI
   ↓
analyze_account
   ↓
gap_analysis
   ├── gap pesquisável → nova query → SearchProvider
   └── suficiente / limite → build_briefing
```

## Responsabilidades

### Brave Search API

Responsável por descobrir fontes públicas relevantes: sites institucionais, notícias, vagas, entrevistas, perfis profissionais públicos, parceiros, páginas de tecnologia e demais sinais úteis.

A busca não deve ser acoplada diretamente ao nó do LangGraph. Criar uma interface simples `SearchProvider` para permitir substituição futura do provedor.

### Firecrawl

Responsável por obter e normalizar o conteúdo das páginas selecionadas para Markdown/texto limpo.

Criar uma interface simples `ContentExtractor` para permitir substituição futura.

Não usar crawling indiscriminado. Extrair somente URLs selecionadas pela etapa de pesquisa/ranking.

### OpenAI

Responsável por tarefas que exigem interpretação:

- gerar e refinar consultas de pesquisa;
- extrair evidências estruturadas;
- classificar evidências;
- identificar stakeholders e sinais tecnológicos;
- criar hipóteses de oportunidade;
- analisar gaps;
- sintetizar o briefing final.

Criar uma camada `LLMProvider`/configuração para evitar espalhar chamadas específicas do fornecedor pelos nós.

## Estratégia de modelos da V1

Começar simples:

- modelo econômico/intermediário para geração de queries, extração, classificação e sumarização;
- modelo mais forte somente se testes reais mostrarem necessidade em `gap_analysis` ou síntese final.

Não criar roteamento sofisticado de modelos antes de medir qualidade, custo e latência da V1.

## Princípio de evidência

O sistema deve distinguir explicitamente:

1. **FATO** — suportado diretamente por fonte pública;
2. **INFERÊNCIA** — conclusão plausível baseada em uma ou mais evidências;
3. **GAP** — informação importante ainda não confirmada.

Nenhuma inferência deve ser apresentada como fato.

Cada evidência relevante deve manter, no mínimo:

- claim;
- URL da fonte;
- título da fonte;
- trecho/contexto utilizado;
- categoria;
- nível de confiança;
- data da coleta quando disponível.

## Estratégia de Gap Analysis

`gap_analysis` não deve apenas verificar o contador de loops.

Deve decidir:

- quais gaps são relevantes para a missão comercial;
- quais gaps ainda podem ser pesquisados publicamente;
- qual nova consulta deve ser executada para tentar resolvê-los;
- quais gaps devem permanecer para descoberta comercial humana.

Gaps críticos típicos:

- decisor econômico não identificado;
- poder de veto não identificado;
- cadeia de aprovação desconhecida;
- ERP/sistema principal não confirmado;
- sistemas usados para administrar a carteira não identificados;
- fornecedor tecnológico dominante desconhecido.

O limite de loops continua existindo como guardrail de custo.

## Guardrails iniciais de custo

Valores de configuração, não regras definitivas:

- máximo de 12 consultas web por conta;
- máximo de 30 páginas extraídas por conta;
- máximo de 3 ciclos de Gap Analysis;
- limite de tamanho de conteúdo enviado ao LLM por página;
- deduplicação de URLs antes de extração;
- não reler a mesma URL durante a mesma pesquisa;
- registrar quantidade de buscas, páginas, chamadas de LLM e tokens quando disponíveis.

Os limites serão ajustados com base em pesquisas reais.

## Segurança e segredos

Chaves nunca entram no repositório.

Variáveis esperadas inicialmente:

```text
BRAVE_API_KEY
FIRECRAWL_API_KEY
OPENAI_API_KEY
```

Fornecer apenas `.env.example` sem valores reais.

## Fora desta fase

Não implementar agora:

- banco de dados persistente;
- UI sofisticada;
- CRM;
- RAG;
- MCP;
- n8n;
- autenticação multiusuário;
- crawling massivo;
- múltiplos provedores ativos simultaneamente;
- roteamento complexo entre vários modelos.

## Critério para avançar

Esta arquitetura estará validada quando o agente executar uma pesquisa real de ponta a ponta para uma conta-alvo, gerar evidências rastreáveis, produzir gaps coerentes e entregar um briefing comercial útil sem ultrapassar os guardrails definidos.
