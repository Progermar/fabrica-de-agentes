"""Testes do Account Intelligence Agent."""

from fabrica_de_agentes.graph import build_graph
from fabrica_de_agentes.search.mock_provider import MockSearchProvider
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

    assert isinstance(result, dict), "Resultado deve ser um dict"

    assert result["briefing_final"], "Briefing final nao foi gerado"
    assert "Empresa Mock Ltda" in result["briefing_final"]

    assert len(result["sources"]) > 0, "Nenhuma fonte coletada"

    assert len(result["gaps"]) == 0, "Gaps devem estar vazios sem LLM"
    assert len(result["stakeholders"]) == 0, "Stakeholders devem estar vazios sem LLM"


def test_graph_with_two_loops():
    """Verifica que o loop de pesquisa funciona corretamente."""
    graph = build_graph()

    initial_state = AccountIntelligenceState(
        target_company="Tech Solutions S.A.",
        max_loops=2,
    )

    result = graph.invoke(initial_state)

    assert len(result["sources"]) > 3, "Loop de pesquisa nao funcionou como esperado"
    assert result["loop_counter"] == 2, f"Contador de loop incorreto: {result['loop_counter']}"
    assert "Tech Solutions S.A." in result["briefing_final"]


def test_state_initialization():
    """Verifica que o estado inicializa corretamente."""
    state = AccountIntelligenceState(target_company="Test Corp")

    assert state.target_company == "Test Corp"
    assert state.loop_counter == 0
    assert state.max_loops == 2
    assert state.max_results_per_query == 5
    assert state.max_queries_per_cycle == 3
    assert len(state.sources) == 0
    assert len(state.evidence) == 0
    assert len(state.stakeholders) == 0
    assert state.briefing_final == ""
    assert state.search_requests_count == 0
    assert state.search_cost_dollars == 0.0
    assert state.llm_requests_count == 0
    assert state.llm_cost_dollars == 0.0


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
        "FONTES E RASTREABILIDADE",
    ]

    for section in expected_sections:
        assert section in briefing, f"Secao '{section}' nao encontrada no briefing"

    assert "Chamadas de LLM realizadas" in briefing
    assert "Evidencias coletadas" in briefing


def test_graph_with_mock_provider_explicit():
    """Verifica que o grafo funciona com provider mock injetado."""
    provider = MockSearchProvider(results_per_query=2)
    graph = build_graph(provider=provider)

    initial_state = AccountIntelligenceState(
        target_company="Empresa com Provider",
        max_loops=1,
    )

    result = graph.invoke(initial_state)

    assert result["briefing_final"], "Briefing nao gerado com provider mock"
    assert len(result["sources"]) > 0, "Nenhuma fonte com provider mock"
    assert result["search_requests_count"] > 0, "Contador de requisicoes nao atualizado"


def test_briefing_shows_search_metrics():
    """Verifica que o briefing mostra metricas de busca."""
    provider = MockSearchProvider()
    graph = build_graph(provider=provider)

    initial_state = AccountIntelligenceState(
        target_company="Metrics Test",
        max_loops=1,
    )

    result = graph.invoke(initial_state)
    briefing = result["briefing_final"]

    assert "Requisicoes de busca realizadas" in briefing


def test_briefing_no_mock_disclaimer():
    """Verifica que o briefing NAO contem aviso de dados mockados (V1-03)."""
    graph = build_graph(provider=MockSearchProvider())

    initial_state = AccountIntelligenceState(
        target_company="No Mock Test",
        max_loops=1,
    )

    result = graph.invoke(initial_state)
    briefing = result["briefing_final"]

    assert "MOCKADO" not in briefing
    assert "DADOS PARCIALMENTE MOCKADOS" not in briefing


def test_briefing_shows_llm_metrics():
    """Verifica que o briefing mostra metricas de LLM."""
    graph = build_graph(provider=MockSearchProvider())

    initial_state = AccountIntelligenceState(
        target_company="LLM Metrics",
        max_loops=1,
    )

    result = graph.invoke(initial_state)
    briefing = result["briefing_final"]

    assert "Chamadas de LLM realizadas" in briefing
    assert "Fatos confirmados" in briefing
    assert "Inferencias" in briefing
    assert "Hipoteses" in briefing
