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

    IMPORTANTE (V1-02): Somente a descoberta de fontes via Exa e real.
    Todas as secoes de analise (stakeholders, stack, oportunidades, rapport,
    gaps) contem dados mockados e NAO devem ser usados como briefing real.
    """
    company = state.target_company

    sections = []

    # Cabecalho
    sections.append(f"{'='*60}")
    sections.append("BRIEFING DE INTELIGENCIA DE CONTA")
    sections.append(f"Empresa-alvo: {company}")
    sections.append(f"{'='*60}\n")

    # AVISO CRITICO
    sections.append("!!! AVISO: DADOS PARCIALMENTE MOCKADOS !!!")
    sections.append(
        "Somente a secao de Fontes/Busca (Exa) contem dados reais."
    )
    sections.append(
        "As secoes abaixo (Perfil, Stakeholders, Stack, Oportunidades,"
    )
    sections.append(
        "  Rapport, Gaps) sao DADOS MOCKADOS para fins de demonstracao."
    )
    sections.append(
        "  NAO utilize este briefing como insumo comercial real."
    )
    sections.append(
        "  Aguarde a integracao da camada de inteligencia (LLM).\n"
    )

    # 1. Perfil da Conta
    sections.append("1. PERFIL DA CONTA")
    sections.append(f"  - Empresa: {company}")
    sections.append("  - Atuacao: Servicos contabeis (MOCKADO)")
    sections.append("  - Porte: Medio/Grande (MOCKADO)")
    sections.append("  - Localizacao: Brasil (MOCKADO)\n")

    # 2. Stakeholder Intelligence
    sections.append("2. STAKEHOLDER INTELLIGENCE (MOCKADO)")
    sections.append(_format_list(state.stakeholders, "stakeholders"))

    # 3. Technology / Stack Discovery
    sections.append("3. TECHNOLOGY / STACK DISCOVERY (MOCKADO)")
    sections.append(_format_list(state.tech_signals, "stack"))

    # 4. Opportunity Discovery
    sections.append("4. OPPORTUNITY DISCOVERY (MOCKADO)")
    sections.append(_format_list(state.opportunities, "oportunidades"))

    # 5. Rapport e Estrategia Comercial
    sections.append("5. RAPPORT E ESTRATEGIA COMERCIAL (MOCKADO)")
    sections.append("  Pontos de rapport:")
    sections.append(_format_list(state.rapport_points, "rapport"))
    sections.append("  Perguntas de descoberta:")
    sections.append(_format_list(state.discovery_questions, "perguntas"))
    sections.append("  Riscos comerciais:")
    sections.append(_format_list(state.commercial_risks, "riscos"))
    sections.append("  Proximas acoes sugeridas:")
    sections.append(_format_list(state.suggested_next_actions, "acoes"))

    # 6. GAP Analysis
    sections.append("6. GAP ANALYSIS (MOCKADO)")
    sections.append(_format_list(state.gaps, "gaps"))

    # 7. Fontes e Rastreabilidade (DADOS REAIS)
    sections.append("7. FONTES E RASTREABILIDADE (DADOS REAIS - EXA)")
    sections.append(f"  Fontes consultadas: {len(state.all_source_urls)}")
    for url in state.all_source_urls:
        sections.append(f"    - {url}")
    sections.append(f"\n  Requisicoes de busca realizadas: {state.search_requests_count}")
    if state.search_cost_dollars > 0:
        sections.append(
            f"  Custo estimado das buscas: ${state.search_cost_dollars:.4f}"
        )
    sections.append(f"\n  Evidencias coletadas: {len(state.evidence)}")
    sections.append(
        "  Nota: Fontes sao resultados de busca web, nao evidencias confirmadas."
    )
    sections.append(
        "  Cada fonte deve ser validada pelo vendedor antes de uso comercial.\n"
    )

    sections.append(f"{'='*60}")
    sections.append("FIM DO BRIEFING")
    sections.append(f"{'='*60}")

    briefing = "\n".join(sections)

    return {"briefing_final": briefing}
