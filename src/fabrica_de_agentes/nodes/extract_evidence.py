"""No 4: Extract Evidence - Extracao de evidencias das fontes."""

from __future__ import annotations

import json

from fabrica_de_agentes.llm.base import LLMProvider
from fabrica_de_agentes.state import AccountIntelligenceState, Evidence

SYSTEM_PROMPT = """\
Voce e um analista de inteligencia comercial. Analise fontes de pesquisa \
sobre uma empresa-alvo e extraia evidencias estruturadas.

Para cada fonte, classifique se e relevante para a conta-alvo.
Se relevante, extraia claims (afirmacoes) suportados pelo conteudo.

Cada claim deve ter:
- claim: afirmacao concreta extraida da fonte
- claim_type: "fact" (confirmado por fonte), "inference" (inferido), \
"hypothesis" (hipotese a validar), ou "gap" (informacao nao confirmada)
- category: "perfil", "stack", "stakeholder", "oportunidade", "rapport", "risco"
- confidence: "alta", "media", "baixa"
- context: trecho que sustenta a afirmacao

Fontes nao relevantes para a conta-alvo devem ser marcadas como irrelevantes.
Nao invente informacoes ausentes. Se a fonte nao contem evidencia util, retorne \
lista vazia de claims para ela.

Retorne APENAS JSON valido no formato:
{
  "sources": [
    {
      "url": "url da fonte",
      "relevant": true ou false,
      "relevance_reason": "motivo da decisao",
      "claims": [
        {
          "claim": "afirmacao",
          "claim_type": "fact|inference|hypothesis|gap",
          "category": "categoria",
          "confidence": "alta|media|baixa",
          "context": "trecho"
        }
      ]
    }
  ]
}
"""


def _build_source_block(source) -> str:
    """Monta bloco compacto de uma fonte para envio ao LLM."""
    lines = [f"URL: {source.url}", f"Titulo: {source.title}"]
    if source.published_date:
        lines.append(f"Data: {source.published_date}")
    if source.snippet:
        lines.append(f"Trecho: {source.snippet}")
    if source.highlights:
        lines.append(f"Destaques: {' | '.join(source.highlights[:3])}")
    return "\n".join(lines)


def extract_evidence(
    state: AccountIntelligenceState,
    llm: LLMProvider | None = None,
) -> dict:
    """Extrai evidencias estruturadas das fontes coletadas usando LLM.

    Se llm for None, retorna evidencias vazias (modo offline/teste).
    """
    if llm is None:
        return {"evidence": [], "llm_requests_count": state.llm_requests_count}

    company = state.target_company
    sources = state.sources

    if not sources:
        return {"evidence": [], "llm_requests_count": state.llm_requests_count}

    source_blocks = [_build_source_block(s) for s in sources]
    sources_text = "\n\n---\n\n".join(source_blocks)

    prompt = f"""\
Empresa-alvo: {company}

Analise as fontes abaixo e extraia evidencias relevantes para esta conta.

{sources_text}

Retorne APENAS JSON valido conforme instrucoes do system prompt."""

    response = llm.chat(prompt, system=SYSTEM_PROMPT)

    new_evidence: list[Evidence] = []

    try:
        data = json.loads(response.text)
        sources_data = data.get("sources", [])

        for src_data in sources_data:
            url = src_data.get("url", "")
            relevant = src_data.get("relevant", False)
            reason = src_data.get("relevance_reason", "")

            for src in sources:
                if src.url == url:
                    src.relevant = relevant
                    src.relevance_reason = reason
                    break

            if not relevant:
                continue

            for claim_data in src_data.get("claims", []):
                new_evidence.append(
                    Evidence(
                        claim=claim_data.get("claim", ""),
                        source_url=url,
                        source_title=next(
                            (s.title for s in sources if s.url == url), ""
                        ),
                        confidence=claim_data.get("confidence", "media"),
                        category=claim_data.get("category", ""),
                        claim_type=claim_data.get("claim_type", "inference"),
                        context=claim_data.get("context", ""),
                    )
                )
    except (json.JSONDecodeError, KeyError):
        return {
            "evidence": state.evidence,
            "llm_requests_count": state.llm_requests_count + 1,
            "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
        }

    all_evidence = list(state.evidence) + new_evidence

    return {
        "evidence": all_evidence,
        "llm_requests_count": state.llm_requests_count + 1,
        "llm_cost_dollars": state.llm_cost_dollars + response.cost_dollars,
    }
