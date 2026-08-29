"""No 7: Build Briefing - Montagem do briefing final."""

from fabrica_de_agentes.state import AccountIntelligenceState


def _format_list(items: list, label: str) -> str:
    """Formata uma lista para o briefing."""
    if not items:
        return f"  - Nenhuma informacao encontrada para {label}\n"
    lines = []
    for item in items:
        if hasattr(item, "__dict__"):
            attrs = []
            for k, v in item.__dict__.items():
                if v:
                    attrs.append(f"    {k}: {v}")
            lines.append("  - " + "\n".join(attrs))
        else:
            lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def build_briefing(state: AccountIntelligenceState) -> dict:
    """Constroi o briefing final de inteligencia da conta.

    Na V1 real, este no usaria LLM para sintetizar tudo em documento coeso.
    Nesta versao esqueleto, monta briefing estruturado com dados mockados.
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
    sections.append("  - Atuacao: Servicos contabeis (mockado)")
    sections.append("  - Porte: Medio/Grande (mockado)")
    sections.append("  - Localizacao: Brasil (mockado)\n")

    # 2. Stakeholder Intelligence
    sections.append("2. STAKEHOLDER INTELLIGENCE")
    sections.append(_format_list(state.stakeholders, "stakeholders"))

    # 3. Technology / Stack Discovery
    sections.append("3. TECHNOLOGY / STACK DISCOVERY")
    sections.append(_format_list(state.tech_signals, "stack"))

    # 4. Opportunity Discovery
    sections.append("4. OPPORTUNITY DISCOVERY")
    sections.append(_format_list(state.opportunities, "oportunidades"))

    # 5. Rapport e Estrategia Comercial
    sections.append("5. RAPPORT E ESTRATEGIA COMERCIAL")
    sections.append("  Pontos de rapport:")
    sections.append(_format_list(state.rapport_points, "rapport"))
    sections.append("  Perguntas de descoberta:")
    sections.append(_format_list(state.discovery_questions, "perguntas"))
    sections.append("  Riscos comerciais:")
    sections.append(_format_list(state.commercial_risks, "riscos"))
    sections.append("  Proximas acoes sugeridas:")
    sections.append(_format_list(state.suggested_next_actions, "acoes"))

    # 6. GAP Analysis
    sections.append("6. GAP ANALYSIS")
    sections.append(_format_list(state.gaps, "gaps"))

    # 7. Rastreabilidade
    sections.append("7. RASTREABILIDADE")
    sections.append(f"  Fontes consultadas: {len(state.all_source_urls)}")
    for url in state.all_source_urls:
        sections.append(f"    - {url}")
    sections.append(f"\n  Evidencias coletadas: {len(state.evidence)}")
    sections.append("  Nota: Todos os dados acima sao MOCKADOS para validacao do fluxo.")
    sections.append("  Em producao, serao conectados a LLMs e APIs de busca reais.\n")

    sections.append(f"{'='*60}")
    sections.append("FIM DO BRIEFING")
    sections.append(f"{'='*60}")

    briefing = "\n".join(sections)

    return {"briefing_final": briefing}
