"""Montagem do grafo LangGraph para Account Intelligence Agent."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from fabrica_de_agentes.llm.base import LLMProvider
from fabrica_de_agentes.nodes import (
    analyze_account,
    analyze_target,
    build_briefing,
    extract_evidence,
    gap_analysis,
    plan_research,
)
from fabrica_de_agentes.nodes.search_sources import search_sources
from fabrica_de_agentes.search.base import SearchProvider
from fabrica_de_agentes.state import AccountIntelligenceState


def _route_after_gap(state: AccountIntelligenceState) -> str:
    """Decide se continua pesquisando ou finaliza.

    Se o contador de loops nao atingiu o maximo, volta para search_sources.
    Caso contrario, segue para build_briefing.
    """
    if state.loop_counter < state.max_loops:
        return "search_sources"
    return "build_briefing"


def _make_search_sources_node(provider: SearchProvider | None = None):
    """Cria um wrapper do search_sources com provider injetado."""

    def _node(state: AccountIntelligenceState) -> dict:
        return search_sources(state, provider=provider)

    return _node


def _make_llm_node(llm: LLMProvider | None, base_fn):
    """Cria um wrapper de no LLM com provider injetado."""

    def _node(state: AccountIntelligenceState) -> dict:
        return base_fn(state, llm=llm)

    return _node


def build_graph(
    provider: SearchProvider | None = None,
    llm: LLMProvider | None = None,
):
    """Constroi e compila o grafo de Account Intelligence.

    Args:
        provider: Provedor de busca. Se None, usa MockSearchProvider.
        llm: Provedor de LLM. Se None, nos de analise retornam vazio.

    Fluxo:
        start -> analyze_target -> plan_research -> search_sources
        -> extract_evidence -> analyze_account -> gap_analysis
        -> [condicional] -> search_sources (loop) ou build_briefing -> end
    """
    graph_builder = StateGraph(AccountIntelligenceState)

    search_node = _make_search_sources_node(provider)
    evidence_node = _make_llm_node(llm, extract_evidence)
    account_node = _make_llm_node(llm, analyze_account)
    gap_node = _make_llm_node(llm, gap_analysis)

    # Adiciona nos
    graph_builder.add_node("analyze_target", analyze_target)
    graph_builder.add_node("plan_research", plan_research)
    graph_builder.add_node("search_sources", search_node)
    graph_builder.add_node("extract_evidence", evidence_node)
    graph_builder.add_node("analyze_account", account_node)
    graph_builder.add_node("gap_analysis", gap_node)
    graph_builder.add_node("build_briefing", build_briefing)

    # Ponto de entrada
    graph_builder.set_entry_point("analyze_target")

    # Arestas direcionais (fixas)
    graph_builder.add_edge("analyze_target", "plan_research")
    graph_builder.add_edge("plan_research", "search_sources")
    graph_builder.add_edge("search_sources", "extract_evidence")
    graph_builder.add_edge("extract_evidence", "analyze_account")
    graph_builder.add_edge("analyze_account", "gap_analysis")

    # Aresta condicional apos gap_analysis
    graph_builder.add_conditional_edges(
        "gap_analysis",
        _route_after_gap,
        {
            "search_sources": "search_sources",
            "build_briefing": "build_briefing",
        },
    )

    # Aresta final
    graph_builder.add_edge("build_briefing", END)

    return graph_builder.compile()


# Instancia compilada do grafo com mock (padrao para testes offline)
account_intelligence_graph = build_graph()
