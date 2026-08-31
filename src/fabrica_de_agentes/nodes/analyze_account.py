"""No 5: Analyze Account - Analise completa da conta."""

from __future__ import annotations

import json

from fabrica_de_agentes.llm.base import LLMProvider
from fabrica_de_agentes.state import (
    AccountIntelligenceState,
    Opportunity,
    Stakeholder,
    TechSignal,
)

SYSTEM_PROMPT = """\
Voce e um analista de inteligencia comercial B2B. Analise evidencias \
coletadas sobre uma empresa-alvo e produza analise estruturada.

Prioridade absoluta: identificar sistemas, ERPs, softwares contabeis/fiscais/\
folha, ferramentas de gestao e tecnologias que a empresa-alvo realmente utiliza.

Para empresa contabil, distinguir quando houver evidencia:
1. sistema contabil/fiscal/folha/ERP usado pela propria empresa;
2. sistema/plataforma usada para administrar carteira/processos internos;
3. ERPs recorrentes no ecossistema dos clientes;
4. fornecedor tecnologico dominante.

Se nao houver evidencia suficiente, retornar GAP. Nunca escolher um sistema \
por plausibilidade.

Cada conclusao deve ser classificada:
- fact: suportado diretamente por fonte relacionada a conta-alvo
- inference: conclusao plausivel derivada de evidencia
- hypothesis: hipotese comercial a validar
- gap: informacao relevante nao confirmada

Nao assumir que pessoa visivel e decisor final. Distinguir cargo observado \
de inferencia sobre influencia.

Retorne APENAS JSON valido no formato:
{
  "tech_signals": [
    {
      "technology": "nome do sistema/tecnologia",
      "purpose": "finalidade",
      "evidence": "evidencia que sustenta",
      "confidence": "alta|media|baixa",
      "claim_type": "fact|inference|hypothesis",
      "source_url": "url da fonte"
    }
  ],
  "stakeholders": [
    {
      "name": "nome ou cargo",
      "role": "funcao observada",
      "influence": "nivel de influencia inferido",
      "evidence": "evidencia",
      "claim_type": "fact|inference|hypothesis"
    }
  ],
  "opportunities": [
    {
      "description": "oportunidade",
      "alignment": "aderencia ao portfolio",
      "evidence": "evidencia",
      "priority": "alta|media|baixa",
      "claim_type": "inference|hypothesis"
    }
  ],
  "commercial_risks": ["risco 1", "risco 2"]
}
"""


def analyze_account(
    state: AccountIntelligenceState,
    llm: LLMProvider | None = None,
) -> dict:
    """Realiza analise consolidada da conta com base nas evidencias usando LLM.

    Se llm for None, retorna analise vazia (modo offline/teste).
    """
    if llm is None:
        return {
            "stakeholders": [],
            "tech_signals": [],
            "opportunities": [],
            "commercial_risks": [],
            "llm_requests_count": state.llm_requests_count,
        }

    company = state.target_company
    evidence_list = state.evidence

    evidence_text = ""
    for i, ev in enumerate(evidence_list, 1):
        evidence_text += (
            f"{i}. [{ev.claim_type.upper()}] {ev.claim}\n"
            f"   Fonte: {ev.source_url}\n"
            f"   Categoria: {ev.category} | Confianca: {ev.confidence}\n"
            f"   Contexto: {ev.context}\n\n"
        )

    if not evidence_text:
        evidence_text = "Nenhuma evidencia coletada ainda."

    prompt = f"""\
Empresa-alvo: {company}

Evidencias coletadas:
{evidence_text}

Analise as evidencias e produza a analise estruturada da conta.
Retorne APENAS JSON valido conforme instrucoes do system prompt."""

    response = llm.chat(prompt, system=SYSTEM_PROMPT)

    stakeholders: list[Stakeholder] = []
    tech_signals: list[TechSignal] = []
    opportunities: list[Opportunity] = []
    commercial_risks: list[str] = []

    try:
        data = json.loads(response.text)

        for ts in data.get("tech_signals", []):
            tech_signals.append(
                TechSignal(
                    technology=ts.get("technology", ""),
                    evidence=ts.get("evidence", ""),
                    confidence=ts.get("confidence", "media"),
                    source_url=ts.get("source_url", ""),
                )
            )

        for sh in data.get("stakeholders", []):
            stakeholders.append(
                Stakeholder(
                    name=sh.get("name", ""),
                    role=sh.get("role", ""),
                    influence=sh.get("influence", ""),
                    evidence=sh.get("evidence", ""),
                )
            )

        for op in data.get("opportunities", []):
            opportunities.append(
                Opportunity(
                    description=op.get("description", ""),
                    alignment=op.get("alignment", ""),
                    evidence=op.get("evidence", ""),
                    priority=op.get("priority", "media"),
                )
            )

        commercial_risks = data.get("commercial_risks", [])

    except (json.JSONDecodeError, KeyError):
        return {
            "stakeholders": [],
            "tech_signals": [],
            "opportunities": [],
            "commercial_risks": [],
            "llm_requests_count": state.llm_requests_count + 1,
            "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
        }

    return {
        "stakeholders": stakeholders,
        "tech_signals": tech_signals,
        "opportunities": opportunities,
        "commercial_risks": commercial_risks,
        "llm_requests_count": state.llm_requests_count + 1,
        "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
    }
