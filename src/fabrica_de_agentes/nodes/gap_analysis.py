"""No 6: Gap Analysis - Analise de lacunas de informacao."""

from __future__ import annotations

import json

from fabrica_de_agentes.llm.base import LLMProvider
from fabrica_de_agentes.state import AccountIntelligenceState, Gap, RapportPoint

SYSTEM_PROMPT = """\
Voce e um analista de inteligencia comercial. Analise as evidencias e gaps \
identificados sobre uma empresa-alvo e produza:

1. GAPS de informacao com prioridade:
   - sistema/ERP principal nao confirmado
   - gestao da carteira nao identificada
   - fornecedor dominante desconhecido
   - decisor economico nao identificado
   - poder de veto nao identificado
   - cadeia de aprovacao desconhecida

   Cada gap deve indicar:
   - description: o que falta descobrir
   - criticality: "alta", "media", "baixa"
   - discovery_action: como descobrir comercialmente
   - new_query: query sugerida para nova pesquisa (se pesquisavel)
   - priority_for_next_interaction: 1-5

2. PONTOS DE RAPPORT:
   - topic: tema de conexao
   - context: por que e relevante
   - suggested_question: pergunta sugerida

3. PERGUNTAS DE DESCOBERTA:
   - Lista de perguntas para Discovery call

4. ACOES SUGERIDAS:
   - Proximos passos concretos

Retorne APENAS JSON valido no formato:
{
  "gaps": [
    {
      "description": "o que falta",
      "criticality": "alta|media|baixa",
      "discovery_action": "como descobrir",
      "new_query": "query para pesquisa (ou vazio)",
      "priority_for_next_interaction": 1
    }
  ],
  "rapport_points": [
    {
      "topic": "tema",
      "context": "contexto",
      "suggested_question": "pergunta"
    }
  ],
  "discovery_questions": ["pergunta 1", "pergunta 2"],
  "suggested_next_actions": ["acao 1", "acao 2"]
}
"""


def gap_analysis(
    state: AccountIntelligenceState,
    llm: LLMProvider | None = None,
) -> dict:
    """Identifica gaps de informacao e decide se novas pesquisas sao necessarias.

    Se llm for None, retorna gaps e rapport vazios (modo offline/teste).
    """
    if llm is None:
        return {
            "gaps": [],
            "rapport_points": [],
            "discovery_questions": [],
            "commercial_risks": [],
            "suggested_next_actions": [],
            "llm_requests_count": state.llm_requests_count,
        }

    company = state.target_company
    evidence_list = state.evidence
    tech_signals = state.tech_signals
    stakeholders = state.stakeholders
    existing_urls = set(state.all_source_urls)

    evidence_text = ""
    for i, ev in enumerate(evidence_list, 1):
        evidence_text += (
            f"{i}. [{ev.claim_type.upper()}] {ev.claim}\n"
            f"   Fonte: {ev.source_url} | Cat: {ev.category}\n\n"
        )

    tech_text = ""
    for ts in tech_signals:
        tech_text += (
            f"- {ts.technology} [{ts.confidence}]: {ts.evidence}\n"
        )

    stakeholder_text = ""
    for sh in stakeholders:
        stakeholder_text += (
            f"- {sh.name} ({sh.role}): {sh.influence}\n"
        )

    prompt = f"""\
Empresa-alvo: {company}

Evidencias coletadas:
{evidence_text or 'Nenhuma'}

Stack tecnologica identificada:
{tech_text or 'Nenhuma'}

Stakeholders identificados:
{stakeholder_text or 'Nenhum'}

URLs ja pesquisadas: {len(existing_urls)}

Analise os gaps de informacao e produza a analise estruturada.
Para cada gap pesquisavel, sugira uma query de pesquisa alternativa \
(diferente das ja tentadas).
Retorne APENAS JSON valido conforme instrucoes do system prompt."""

    response = llm.chat(prompt, system=SYSTEM_PROMPT)

    gaps: list[Gap] = []
    rapport_points: list[RapportPoint] = []
    discovery_questions: list[str] = []
    suggested_next_actions: list[str] = []

    try:
        data = json.loads(response.text)

        for g in data.get("gaps", []):
            gaps.append(
                Gap(
                    description=g.get("description", ""),
                    criticality=g.get("criticality", "media"),
                    discovery_action=g.get("discovery_action", ""),
                    priority_for_next_interaction=g.get(
                        "priority_for_next_interaction", 3
                    ),
                )
            )

        for rp in data.get("rapport_points", []):
            rapport_points.append(
                RapportPoint(
                    topic=rp.get("topic", ""),
                    context=rp.get("context", ""),
                    suggested_question=rp.get("suggested_question", ""),
                )
            )

        discovery_questions = data.get("discovery_questions", [])
        suggested_next_actions = data.get("suggested_next_actions", [])

    except (json.JSONDecodeError, KeyError):
        return {
            "gaps": [],
            "rapport_points": [],
            "discovery_questions": [],
            "commercial_risks": [],
            "suggested_next_actions": [],
            "llm_requests_count": state.llm_requests_count + 1,
            "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
        }

    return {
        "gaps": gaps,
        "rapport_points": rapport_points,
        "discovery_questions": discovery_questions,
        "commercial_risks": state.commercial_risks,
        "suggested_next_actions": suggested_next_actions,
        "llm_requests_count": state.llm_requests_count + 1,
        "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
    }
