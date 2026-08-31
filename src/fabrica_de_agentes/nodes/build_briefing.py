"""No 7: Build Briefing - Montagem do briefing final."""

from fabrica_de_agentes.state import AccountIntelligenceState

CLAIM_LABELS = {
    "fact": "FATO CONFIRMADO",
    "inference": "INFERENCIA",
    "hypothesis": "HIPOTESE",
    "gap": "GAP",
}


def _format_evidence_list(items: list, label: str) -> str:
    """Formata lista de evidencias com classificacao e fonte."""
    if not items:
        return f"  - Nenhuma informacao encontrada para {label}\n"
    lines = []
    for item in items:
        if hasattr(item, "claim_type") and hasattr(item, "source_url"):
            tag = CLAIM_LABELS.get(getattr(item, "claim_type", ""), "")
            prefix = f"[{tag}] " if tag else ""
            attrs = []
            for k, v in item.__dict__.items():
                if v and k not in ("claim_type",):
                    attrs.append(f"    {k}: {v}")
            lines.append(f"  - {prefix}" + "\n".join(attrs))
        elif hasattr(item, "__dict__"):
            attrs = []
            for k, v in item.__dict__.items():
                if v:
                    attrs.append(f"    {k}: {v}")
            lines.append("  - " + "\n".join(attrs))
        else:
            lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def _format_simple_list(items: list, label: str) -> str:
    """Formata lista simples (strings)."""
    if not items:
        return f"  - Nenhuma informacao encontrada para {label}\n"
    lines = [f"  - {item}" for item in items]
    return "\n".join(lines) + "\n"


def build_briefing(state: AccountIntelligenceState) -> dict:
    """Constroi o briefing final de inteligencia da conta.

    Monta briefing estruturado com dados reais de busca e analise LLM.
    Mostra classificacao (FATO/INFERENCIA/HIPOTESE/GAP) e fonte.
    """
    company = state.target_company

    sections = []

    # Cabecalho
    sections.append(f"{'='*60}")
    sections.append("BRIEFING DE INTELIGENCIA DE CONTA")
    sections.append(f"Empresa-alvo: {company}")
    sections.append(f"{'='*60}\n")

    # 1. Perfil da Conta
    sections.append("1. PERFIL DA CONTA")
    sections.append(f"  - Empresa: {company}")

    relevant_sources = [s for s in state.sources if s.relevant is True]
    if relevant_sources:
        sections.append(f"  - Fontes relevantes encontradas: {len(relevant_sources)}")
        for src in relevant_sources[:5]:
            sections.append(f"    * {src.title} ({src.url})")
    else:
        sections.append("  - Perfil detalhado nao confirmado por fontes publicas")
    sections.append("")

    # 2. Stakeholder Intelligence
    sections.append("2. STAKEHOLDER INTELLIGENCE")
    sections.append(_format_evidence_list(state.stakeholders, "stakeholders"))

    # 3. Technology / Stack Discovery
    sections.append("3. TECHNOLOGY / STACK DISCOVERY")
    sections.append(_format_evidence_list(state.tech_signals, "stack"))

    # 4. Opportunity Discovery
    sections.append("4. OPPORTUNITY DISCOVERY")
    sections.append(_format_evidence_list(state.opportunities, "oportunidades"))

    # 5. Rapport e Estrategia Comercial
    sections.append("5. RAPPORT E ESTRATEGIA COMERCIAL")
    sections.append("  Pontos de rapport:")
    sections.append(_format_simple_list(
        [f"{rp.topic}: {rp.suggested_question}" for rp in state.rapport_points],
        "rapport",
    ))
    sections.append("  Perguntas de descoberta:")
    sections.append(_format_simple_list(state.discovery_questions, "perguntas"))
    sections.append("  Riscos comerciais:")
    sections.append(_format_simple_list(state.commercial_risks, "riscos"))
    sections.append("  Proximas acoes sugeridas:")
    sections.append(_format_simple_list(state.suggested_next_actions, "acoes"))

    # 6. GAP Analysis
    sections.append("6. GAP ANALYSIS")
    sections.append(_format_evidence_list(state.gaps, "gaps"))

    # 7. Fontes e Rastreabilidade
    sections.append("7. FONTES E RASTREABILIDADE")
    sections.append(f"  Fontes consultadas: {len(state.all_source_urls)}")
    for url in state.all_source_urls:
        sections.append(f"    - {url}")
    sections.append(f"\n  Requisicoes de busca realizadas: {state.search_requests_count}")
    if state.search_cost_dollars > 0:
        sections.append(
            f"  Custo estimado das buscas: ${state.search_cost_dollars:.4f}"
        )
    sections.append(f"\n  Chamadas de LLM realizadas: {state.llm_requests_count}")
    if state.llm_cost_dollars > 0:
        sections.append(
            f"  Custo estimado da analise LLM: ${state.llm_cost_dollars:.4f}"
        )
    sections.append(f"\n  Evidencias coletadas: {len(state.evidence)}")

    facts = [e for e in state.evidence if e.claim_type == "fact"]
    inferences = [e for e in state.evidence if e.claim_type == "inference"]
    hypotheses = [e for e in state.evidence if e.claim_type == "hypothesis"]
    gaps_ev = [e for e in state.evidence if e.claim_type == "gap"]
    sections.append(f"    - Fatos confirmados: {len(facts)}")
    sections.append(f"    - Inferencias: {len(inferences)}")
    sections.append(f"    - Hipoteses: {len(hypotheses)}")
    sections.append(f"    - Gaps de informacao: {len(gaps_ev)}")

    if facts:
        sections.append("\n  Fatos confirmados:")
        for ev in facts:
            sections.append(f"    * [{ev.category}] {ev.claim}")
            sections.append(f"      Fonte: {ev.source_url}")

    if gaps_ev:
        sections.append("\n  Gaps de informacao:")
        for ev in gaps_ev:
            sections.append(f"    * [{ev.category}] {ev.claim}")

    sections.append(
        "\n  Nota: Fontes devem ser validadas pelo vendedor antes de uso comercial."
    )
    sections.append(
        "  Distincao entre fato, inferencia e hipotese indicada em cada item.\n"
    )

    sections.append(f"{'='*60}")
    sections.append("FIM DO BRIEFING")
    sections.append(f"{'='*60}")

    briefing = "\n".join(sections)

    return {"briefing_final": briefing}
