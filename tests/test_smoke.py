"""Testes do Account Intelligence Agent."""

from fabrica_de_agentes.graph import build_graph
from fabrica_de_agentes.state import AccountIntelligenceState


def test_graph_compiles():
    """Verifica que o grafo compila sem erros."""
    graph = build_graph()
    assert graph is not None


def test_graph_executes_full_flow():
    """Verifica que o grafo executa do inicio ao fim com dados mockados."""
    graph = build_graph()

    initial_state = AccountIntelligenceState(
        target_company="Empresa Mock Ltda",
        max_loops=1,
    )

    result = graph.invoke(initial_state)

    # LangGraph invoke retorna um dict
    assert isinstance(result, dict), "Resultado deve ser um dict"

    # Verifica que o briefing foi gerado
    assert result["briefing_final"], "Briefing final nao foi gerado"
    assert "Empresa Mock Ltda" in result["briefing_final"]

    # Verifica que fontes foram coletadas
    assert len(result["sources"]) > 0, "Nenhuma fonte coletada"

    # Verifica que evidencias foram extraidas
    assert len(result["evidence"]) > 0, "Nenhuma evidencia extraida"

    # Verifica que stakeholders foram identificados
    assert len(result["stakeholders"]) > 0, "Nenhum stakeholder identificado"

    # Verifica que gaps foram listados
    assert len(result["gaps"]) > 0, "Nenhum gap listado"

    # Verifica que pontos de rapport existem
    assert len(result["rapport_points"]) > 0, "Nenhum ponto de rapport"


def test_graph_with_two_loops():
    """Verifica que o loop de pesquisa funciona corretamente."""
    graph = build_graph()

    initial_state = AccountIntelligenceState(
        target_company="Tech Solutions S.A.",
        max_loops=2,
    )

    result = graph.invoke(initial_state)

    # Com 2 loops, devemos ter mais de 3 fontes (3 por loop)
    assert len(result["sources"]) > 3, "Loop de pesquisa nao funcionou como esperado"
    assert result["loop_counter"] == 2, f"Contador de loop incorreto: {result['loop_counter']}"
    assert "Tech Solutions S.A." in result["briefing_final"]


def test_state_initialization():
    """Verifica que o estado inicializa corretamente."""
    state = AccountIntelligenceState(target_company="Test Corp")

    assert state.target_company == "Test Corp"
    assert state.loop_counter == 0
    assert state.max_loops == 2
    assert len(state.sources) == 0
    assert len(state.evidence) == 0
    assert len(state.stakeholders) == 0
    assert state.briefing_final == ""


def test_briefing_structure():
    """Verifica que o briefing contem todas as secoes esperadas."""
    graph = build_graph()

    initial_state = AccountIntelligenceState(
        target_company=" Contabilidade Express",
        max_loops=1,
    )

    result = graph.invoke(initial_state)
    briefing = result["briefing_final"]

    expected_sections = [
        "PERFIL DA CONTA",
        "STAKEHOLDER INTELLIGENCE",
        "TECHNOLOGY / STACK DISCOVERY",
        "OPPORTUNITY DISCOVERY",
        "RAPPORT E ESTRATEGIA COMERCIAL",
        "GAP ANALYSIS",
        "RASTREABILIDADE",
    ]

    for section in expected_sections:
        assert section in briefing, f"Secao '{section}' nao encontrada no briefing"
