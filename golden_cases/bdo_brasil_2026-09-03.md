# GOLDEN CASE — BDO Brasil

**Data:** 2026-09-03
**Status:** APROVADO — Baseline Funcional
**Versão do agente:** Account Intelligence

---

## Configuração da Execução

| Parâmetro | Valor |
|-----------|-------|
| Empresa-alvo | BDO Brasil |
| Search Provider | Exa |
| LLM Provider | OpenCode (HTTP V1) |
| Modelo | openai/gpt-5.4-mini |
| Max Loops | 1 |
| Custo Exa | $0.0210 |
| Custo LLM | $0 |
| Tokens LLM (input) | 694 |
| Tokens LLM (output) | 11 |

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Requisições de busca Exa | 3 |
| Fontes consultadas | 13 |
| Evidências coletadas | 42 |
| Fatos confirmados | 42 |
| Inferências | 0 |
| Hipóteses | 0 |
| Gaps de informação | 0 |
| Chamadas LLM | 3 |

---

## Evidências Principais

### TOTVS / Protheus (Uso Interno Confirmado)

- **Afirmação:** BDO Brasil adotou o TOTVS Backoffice Linha Protheus para gerir BPO e Controladoria
- **Confirmação:** Alta — case publicado em tiBahia.com e InforChannel
- **Detalhes:** 15 módulos implantados, 400+ clientes atendidos, base da área de BPO
- **Fontes:**
  - https://tibahia.com/case-de-sucesso/bdo-brasil-melhora-performance-e-padroniza-operacao-com-adocao-do-totvs-backoffice/
  - https://inforchannel.com.br/2022/12/09/bdo-brasil-padroniza-operacao-de-bpo-com-adocao-de-sistemas-da-totvs/

### SAP Business One (Serviço Oferecido a Clientes — NÃO uso interno)

- **Afirmação:** BDO divulga página própria sobre SAP Business One como ERP para clientes PME
- **Classificação:** Serviço de advisory/implementação para clientes
- **NÃO é prova de uso interno**
- **Fonte:** https://www.bdo.com.br/pt-br/servicos/advisory/sap-business-one/sap-business-one

### Automação e IA

- **Afirmação:** BDO usa Microsoft Power Automate, Copilot, UiPath e Azure OpenAI Services
- **Confirmação:** Alta — declaração oficial
- **Fonte:** https://www.bdo.com.br/en-gb/services/digital/data-and-analytics-consulting/intelligent-process-automation-solutions

### Ferramentas Próprias

- **Afirmação:** BDO desenvolveu ferramentas próprias para validação de obrigações, EFD-Contribuições, controle de ativos, P&D e telecom
- **Fonte:** https://www.bdo.com.br/pt-br/servicos/tax/obrigacoes-acessorias-servicos-de-it-tax-solutio

---

## Gaps Estratégicos

1. **ERP mestre da operação interna não confirmado por área** (crítico)
   - Há evidência de TOTVS no BPO e oferta SAP Business One, mas não há confirmação do ERP mestre por área/unidade
   - Ação: Confirmar em discovery call

2. **Decisor econômico para ERP/automação/IA não identificado** (crítico)
   - Sinais apontam para liderança de BPO/Sistemas, mas não confirmam quem aprova orçamento
   - Ação: Mapear sponsor econômico por entrevista direta

3. **Fornecedor dominante de tecnologia não confirmado** (crítico)
   - Há sinais de múltiplos stacks e coexistência de soluções, mas sem hierarquia clara por domínio
   - Ação: Investigar stack por domínio

4. **Gestão de carteira/relacionamento não identificada** (média)
5. **Poder de veto não identificado** (média)
6. **Cadeia de aprovação desconhecida** (média)

---

## Fontes Consultadas

1. https://www.bdo.com.br/pt-br/servicos/advisory/sap-business-one/sap-business-one
2. https://www.bdo.com.br/pt-br/servicos/outsourcing/automacao-e-ferramentas-tecnologicas
3. https://www.bdo.com.br/pt-br/servicos/outsourcing/parametrizacao-de-sistemas
4. https://tibahia.com/case-de-sucesso/bdo-brasil-melhora-performance-e-padroniza-operacao-com-adocao-do-totvs-backoffice/
5. https://pt.linkedin.com/posts/bdobrazil_bdobrasil-sapbusinessone-erp-activity-7424089676270960640-GMU5
6. https://inforchannel.com.br/2022/12/09/bdo-brasil-padroniza-operacao-de-bpo-com-adocao-de-sistemas-da-totvs/
7. https://www.bdo.com.br/pt-br/servicos/tax/obrigacoes-acessorias-servicos-de-it-tax-solutio
8. https://www.bdo.com.br/en-gb/services/digital/data-and-analytics-consulting/intelligent-process-automation-solutions
9. https://www.bdo.com.br/pt-br/sobre/bdo-brazil
10. https://www.bdo.com.br/pt-br/bdo-brazil
11. https://linkedin.com/company/bdobrazil
12. https://pt.wikipedia.org/wiki/BDO
13. https://pitchbook.com/profiles/advisor/149402-35

---

## Critérios de Regressão

Versões futuras NÃO podem regredir nestes pontos:

1. **TOTVS/Protheus:** Encontrar quando as fontes o suportarem
2. **Uso interno vs serviço:** Distinguir claramente (TOTVS = uso interno; SAP B1 = serviço para clientes)
3. **SAP Business One:** NÃO tratar advisory como prova de uso interno
4. **URLs:** Preservar fontes e URLs de todas as evidências
5. **Decisor econômico:** NÃO inventar — registrar como GAP CRÍTICO quando não comprovado
6. **Poder de veto:** NÃO inventar — registrar como GAP quando não comprovado
7. **Classificação:** Inferências e hipóteses devem ser classificadas corretamente
8. **Gaps:** Manter gaps estratégicos quando não houver prova

---

## Aprovação

- **Gate BDO:** APROVADO
- **Pipeline:** Funcional ponta a ponta
- **Baseline:** Sim — primeiro Golden Case do Account Intelligence
