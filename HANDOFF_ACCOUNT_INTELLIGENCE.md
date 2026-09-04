# HANDOFF — Account Intelligence Agent

**Data:** 2026-09-03
**Status:** BASELINE FUNCIONAL — Pronto para continuidade
**Golden Case:** BDO Brasil (`golden_cases/bdo_brasil_2026-09-03.md`)

---

## Objetivo

O Account Intelligence Agent coleta inteligência pública sobre uma empresa-alvo para apoio a equipes comerciais B2B. Produz briefing estruturado com perfil da conta, stack tecnológico, stakeholders, oportunidades, gaps e pontos de rapport.

---

## Arquitetura LangGraph

```
analyze_target
  → plan_research
    → search_sources
      → extract_evidence
        → analyze_account
          → gap_analysis
            → [loop se houver nova query pesquisável]
              → search_sources (ciclo seguinte)
                → extract_evidence
                  → analyze_account
                    → gap_analysis
                      → build_briefing
```

**Nós do grafo:**
- `analyze_target` — identifica empresa, domínio, contexto
- `plan_research` — gera queries iniciais de busca
- `search_sources` — busca fontes via search provider (Exa)
- `extract_evidence` — LLM extrai evidências das fontes
- `analyze_account` — LLM analisa stack, stakeholders, oportunidades
- `gap_analysis` — LLM identifica gaps e gera novas queries
- `build_briefing` — monta briefing final

---

## Search Provider — Exa

- **Provider:** `ExaSearchProvider`
- **Configuração:** `EXA_API_KEY` em variável de ambiente
- **Custo:** ~$0.007 por busca
- **Documentação:** `src/fabrica_de_agentes/search/exa_provider.py`

---

## LLM Provider — OpenCode

- **Provider:** `OpenCodeProvider`
- **Comunicação:** HTTP V1 com `opencode serve`
- **Modelo validado:** `openai/gpt-5.4-mini`

### Variáveis de Ambiente

| Variável | Valor | Obrigatória |
|----------|-------|-------------|
| `OPENCODE_SERVER_PASSWORD` | `<definir>` | Não (servidor pode ser unsecured) |
| `OPENCODE_SERVER_URL` | `http://127.0.0.1:4096` ou `http://host.docker.internal:4096` | Não (default: 127.0.0.1:4096) |
| `OPENCODE_MODEL` | `openai/gpt-5.4-mini` | Não (default: vazio = modelo do servidor) |
| `EXA_API_KEY` | `<definir>` | Sim (para busca Exa) |

### Finding Crítico — API V1

A API V2 (`/api/session/{id}/prompt`) **não expõe** o provider `openai`. A API V1 funciona corretamente.

**Requisição funcional:**

```
POST /session
Body: {"agent": "account-intelligence", "model": {"id": "gpt-5.4-mini", "providerID": "openai"}}

POST /session/{id}/message
Body: {"parts": [{"type": "text", "text": "..."}], "agent": "account-intelligence"}
```

**Regra:** O `model` vai na **criação da sessão**, NÃO na mensagem.

### OpenAI OAuth via OpenCode

O provider `openai` está conectado via OAuth no OpenCode desktop. O `opencode serve` expõe o provider via API V1 mesmo sem listar no `/api/provider`. O `opencode run -m openai/gpt-5.4-mini` também funciona (caminho CLI).

### Custo LLM

- **Custo reportado:** $0 (modelos OpenAI via OAuth no plano gratuito do OpenCode)
- **Tokens observados:** ~694 input, ~11 output por chamada simples

### Tratamento de Erros

O `OpenCodeProvider` detecta `info.error` na resposta V1 e gera `RuntimeError` com:
- nome do erro
- mensagem
- statusCode HTTP
- providerID e modelID

### Strip de Markdown Fences

Os nós `extract_evidence`, `analyze_account` e `gap_analysis` aplicam `_strip_markdown_fences()` antes de `json.loads()` para tratar respostas do LLM envolvidas em ` ```json...``` `.

---

## Regras de Classificação

| Classificação | Definição |
|---------------|-----------|
| **FATO CONFIRMADO** | Evidência direta e verificável em fonte pública |
| **INFERÊNCIA** | Dedução lógica a partir de fatos, sem confirmação direta |
| **HIPÓTESE** | Possibilidade plausível sem evidência suficiente |
| **GAP** | Informação estratégica ausente que deve ser investigada |

### Regras Críticas

1. **Nunca inventar** sistema, decisor ou poder de veto
2. **Decisor econômico** e **poder de veto** = GAP CRÍTICO quando não comprovados
3. **Distinguir** uso interno de oferta de serviço ao cliente
4. **SAP Business One advisory** NÃO é prova de uso interno
5. **Preservar** URLs e fontes de todas as evidências
6. **Classificar** inferências e hipóteses corretamente

---

## Golden Case — BDO Brasil

O primeiro Golden Case está em `golden_cases/bdo_brasil_2026-09-03.md`.

### Métricas da BDO

| Métrica | Valor |
|---------|-------|
| Buscas Exa | 3 |
| Custo Exa | $0.0210 |
| Chamadas LLM | 3 |
| Custo LLM | $0 |
| Fontes | 13 |
| Evidências | 42 |
| Gaps | 6 |

### Validações Aprovadas

- TOTVS/Protheus encontrado e classificado como uso interno
- SAP Business One classificado como serviço para clientes
- URLs preservadas
- Decisor econômico não inventado (gap crítico)
- Poder de veto não inventado (gap)
- Inferências e hipóteses classificadas corretamente

---

## Testes e Qualidade

- **87 testes** passando (`pytest tests/`)
- **Ruff** limpo (`ruff check src/ tests/`)
- **Sem secrets** nos arquivos commitados

---

## Segurança

- `.env` está em `.gitignore` — nunca commitado
- `.env.example` contém placeholders, não valores reais
- `OPENCODE_SERVER_PASSWORD` e `EXA_API_KEY` nunca aparecem em código fonte
- Golden case contém apenas métricas e fontes públicas

---

## Dockerização

| Estado | Descrição |
|--------|-----------|
| **IMPLEMENTADO** | `Dockerfile`, `docker-compose.yml`, `.dockerignore` criados |
| **VALIDADO** | Connectivity gate: container → host.docker.internal:4096 → OpenCode Server → GET /agent → account-intelligence FOUND |
| **NÃO VALIDADO** | Execução completa do pipeline via Docker (pendente) |
| **PLANEJADO** | Deploy em Hermes ou outro ambiente containerizado |

---

## Próximo Gate

**Intercont Contabilidade Empresarial**

- Disciplina contra alucinação
- Validar que o agente não inventa dados não encontrados

### Ground Truth (não fornecer ao agente)

O Product Owner sabe que a Intercont utiliza **Radar/WK** como ERP. Isso NÃO deve ser fornecido ao agente durante o teste. O agente deve descobrir (ou registrar como gap) por conta própria.

---

## Comandos Úteis

```bash
# Executar BDO
python -m fabrica_de_agentes.cli "BDO Brasil" --provider exa --llm opencode --max-loops 1

# Executar Intercont
python -m fabrica_de_agentes.cli "Intercont Contabilidade Empresarial" --provider exa --llm opencode --max-loops 1

# Testes
python -m pytest tests/ -v

# Lint
python -m ruff check src/ tests/
```
