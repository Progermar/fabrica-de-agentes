"""No 6: Gap Analysis - Analise de lacunas de informacao."""

from fabrica_de_agentes.state import AccountIntelligenceState, Gap, RapportPoint


def gap_analysis(state: AccountIntelligenceState) -> dict:
    """Identifica gaps de informacao e pontos de rapport.

    Na V1 real, este no usaria LLM para avaliar cobertura da pesquisa
    e decidir se novas iteracoes sao necessarias.
    Nesta versao esqueleto, gera gaps e rapport mockados.
    """
    gaps = [
        Gap(
            description="Identidade do decisor final de TI nao confirmada",
            criticality="alta",
            discovery_action="Perguntar diretamente no primeiro contato",
            priority_for_next_interaction=1,
        ),
        Gap(
            description="Stack tecnologica real nao verificada",
            criticality="alta",
            discovery_action="Pesquisar licitacoes ou revealacoes publicas",
            priority_for_next_interaction=2,
        ),
        Gap(
            description="Budget anual para TI desconhecido",
            criticality="media",
            discovery_action="Indag duranteDiscovery call",
            priority_for_next_interaction=3,
        ),
    ]

    rapport_points = [
        RapportPoint(
            topic="Segmento contabil",
            context="ComumInterest em eficiencia operacional",
            suggested_question=(
                "Como voces estao lidando com a demanda crescente de "
                "automatizacao dos processos contabeis?"
            ),
        ),
        RapportPoint(
            topic="Transformacao digital",
            context="Muitos escritorios estao em fase de migracao",
            suggested_question=(
                "Voces ja consideraram usar IA para automatizar "
                "tarefas repetitivas?"
            ),
        ),
    ]

    discovery_questions = [
        "Quem e o principal responsable por decisoes de TI na empresa?",
        "Quais sistemas voces usam atualmente para gestao contabil?",
        "Qual e o maior gargalo operacional que voces enfrentam hoje?",
    ]

    commercial_risks = [
        "Possivel resistencia a mudanca na equipe",
        "Budget limitado para novas ferramentas",
        "Concorrentes com solucoes ja estabelecidas",
    ]

    suggested_next_actions = [
        "Agendar Discovery call com diretor de TI",
        "Preparar demo personalizada para o segmento contabil",
        "Enviar material educativo sobre automacao com IA",
    ]

    return {
        "gaps": gaps,
        "rapport_points": rapport_points,
        "discovery_questions": discovery_questions,
        "commercial_risks": commercial_risks,
        "suggested_next_actions": suggested_next_actions,
    }
