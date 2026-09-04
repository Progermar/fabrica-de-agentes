# CHECKPOINT — Account Intelligence

**Data:** 2026-09-03
**Status:** BASELINE FUNCIONAL — BDO GOLDEN CASE APROVADO
**Commit técnico:** `d91ef18`
**Branch:** `main`

---

## Configuração Validada

| Componente | Configuração |
|------------|--------------|
| Search Provider | Exa |
| LLM Provider | OpenCode HTTP V1 |
| Modelo | `openai/gpt-5.4-mini` |
| Custo LLM | $0 |

---

## Métricas BDO Brasil

| Métrica | Valor |
|---------|-------|
| Buscas Exa | 3 |
| Custo Exa | US$ 0.0210 |
| Chamadas LLM | 3 |
| Custo LLM | US$ 0 |
| Fontes consultadas | 13 |
| Evidências coletadas | 42 |
| Gaps identificados | 6 |

---

## Qualidade

| Item | Status |
|------|--------|
| Testes | 87 passando |
| Ruff | Limpo |
| Secrets | Nenhum encontrado |

---

## Problemas Resolvidos

- OpenCode API V1: model vai na criação da sessão, não na mensagem
- `OPENCODE_MODEL`: formato `providerID/modelID`
- `OPENCODE_SERVER_URL`: suporte a URL customizada
- `info.error`: detecção e RuntimeError claro
- Markdown fences: strip antes de JSON parse
- Golden Case BDO: baseline aprovada

---

## Próximo Gate

**Intercont Contabilidade Empresarial** — disciplina contra alucinação.

Ground truth: Intercont utiliza Radar/WK. NÃO fornecer ao agente.
