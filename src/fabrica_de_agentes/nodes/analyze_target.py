"""No 1: Analyze Target - Analise inicial da empresa-alvo."""

from fabrica_de_agentes.state import AccountIntelligenceState


def analyze_target(state: AccountIntelligenceState) -> dict:
    """Analisa a empresa-alvo e prepara contexto para pesquisa.

    Na V1 real, este no usaria LLM para extrair informacoes iniciais.
    Nesta versao esqueleto, apenas registra o target no estado.
    """
    company = state.target_company

    return {
        "research_queries": [
            f"{company} empresa perfil atuacao",
            f"{company} stack tecnologica sistemas",
            f"{company} decisores lideres",
        ],
    }
