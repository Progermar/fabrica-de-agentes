"""No 1: Analyze Target - Analise inicial da empresa-alvo."""

from fabrica_de_agentes.state import AccountIntelligenceState


def analyze_target(state: AccountIntelligenceState) -> dict:
    """Analisa a empresa-alvo e prepara contexto para pesquisa.

    Prioriza queries de tecnologia/ERP primeiro, depois perfil, depois decisores.
    Nao cita fornecedores especificos.
    """
    company = state.target_company

    return {
        "research_queries": [
            f"{company} sistemas ERP tecnologia stack software",
            f"{company} automacao processos workflow integracao",
            f"{company} empresa perfil atuacao porte localizacao",
            f"{company} decisores lideres executivos gestores",
        ],
    }
