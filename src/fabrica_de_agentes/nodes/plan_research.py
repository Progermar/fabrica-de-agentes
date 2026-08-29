"""No 2: Plan Research - Planejamento de queries de pesquisa."""

from fabrica_de_agentes.state import AccountIntelligenceState


def plan_research(state: AccountIntelligenceState) -> dict:
    """Planeja as queries de pesquisa com base no target.

    Na V1 real, este no usaria LLM para gerar queries otimizadas.
    Nesta versao esqueleto, mantem as queries ja existentes ou gera padrao.
    """
    company = state.target_company
    existing = state.research_queries

    if not existing:
        queries = [
            f"{company} empresa perfil porte localizacao",
            f"{company} decisores lideres executivos",
            f"{company} stack tecnologica ERP sistemas",
            f"{company} oportunidades mercado",
        ]
    else:
        queries = existing

    return {"research_queries": queries}
