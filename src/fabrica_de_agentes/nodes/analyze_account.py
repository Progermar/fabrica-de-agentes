"""No 5: Analy Account - Analise completa da conta."""

from fabrica_de_agentes.state import (
    AccountIntelligenceState,
    Opportunity,
    Stakeholder,
    TechSignal,
)


def analyze_account(state: AccountIntelligenceState) -> dict:
    """Realiza analise consolidada da conta com base nas evidencias.

    Na V1 real, este no usaria LLM para sintetizar evidencias em insights.
    Nesta versao esqueleto, gera analise mockada.
    """
    company = state.target_company

    stakeholders = [
        Stakeholder(
            name=f"Diretor de TI - {company}",
            role="Decisor tecnico",
            influence="Alta - decide compras de software",
            evidence="Evidencia inferida a partir de estrutura típica de empresas do segmento",
        ),
        Stakeholder(
            name=f"Diretor Financeiro - {company}",
            role="Decisor economico",
            influence="Alta - aprova orcamentos",
            evidence="Evidencia inferida - papel tipico em decisoes de TI",
        ),
    ]

    tech_signals = [
        TechSignal(
            technology="Sistema de gestao contabil",
            evidence="Comum em escritorios contabeis deste porte",
            confidence="baixa",
        ),
        TechSignal(
            technology="Planilhas ou ferramentas manuais",
            evidence="Possivel uso baseado em gaps de automacao",
            confidence="baixa",
        ),
    ]

    opportunities = [
        Opportunity(
            description="Automacao de processos contabeis com IA",
            alignment="Alinhado com portfólio de agentes de IA da Teklamatik",
            evidence="Escritorios contabeis frequentemente buscam automacao",
            priority="alta",
        ),
        Opportunity(
            description="Integracao entre sistemas legados",
            alignment="Ad integracoes e automacoes",
            evidence="Muitos escritorios usam sistemas desconectados",
            priority="media",
        ),
    ]

    return {
        "stakeholders": stakeholders,
        "tech_signals": tech_signals,
        "opportunities": opportunities,
    }
