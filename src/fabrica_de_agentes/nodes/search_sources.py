"""No 3: Search Sources - Busca de fontes na web."""

from __future__ import annotations

from fabrica_de_agentes.search.base import SearchProvider, SearchResult
from fabrica_de_agentes.state import AccountIntelligenceState, Source


def _deduplicate_urls(sources: list[Source]) -> list[Source]:
    """Remove fontes com URLs duplicadas, mantendo a primeira ocorrencia."""
    seen_urls: set[str] = set()
    unique: list[Source] = []
    for source in sources:
        if source.url not in seen_urls:
            seen_urls.add(source.url)
            unique.append(source)
    return unique


def _search_result_to_source(result: SearchResult) -> Source:
    """Converte um SearchResult normalizado para o modelo Source do estado."""
    return Source(
        url=result.url,
        title=result.title,
        snippet=result.snippet,
        content=result.snippet,
    )


def search_sources(
    state: AccountIntelligenceState,
    provider: SearchProvider | None = None,
) -> dict:
    """Realiza busca nas fontes para cada query usando o provider configurado.

    O provider e injetado como parametro opcional para permitir
    desacoplamento do LangGraph da implementacao de busca.
    Quando None, usa MockSearchProvider para manter compatibilidade
    com testes offline existentes.
    """
    if provider is None:
        from fabrica_de_agentes.search.mock_provider import MockSearchProvider

        provider = MockSearchProvider()

    queries = state.research_queries
    loop = state.loop_counter
    max_results = state.max_results_per_query if hasattr(state, "max_results_per_query") else 5

    new_sources: list[Source] = []
    new_urls: list[str] = []
    total_requests = 0
    total_cost = 0.0

    for query in queries[:3]:
        try:
            response = provider.search(
                query=query,
                num_results=max_results,
            )
            for result in response.results:
                source = _search_result_to_source(result)
                new_sources.append(source)
                new_urls.append(source.url)
            total_requests += response.request_count
            if response.cost_dollars is not None:
                total_cost += response.cost_dollars
        except Exception:
            # Em caso de erro na busca, registra mas nao interrompe o fluxo
            continue

    # Acumula com fontes existentes e deduplica
    all_sources = _deduplicate_urls(list(state.sources) + new_sources)
    all_urls = list(dict.fromkeys(state.all_source_urls + new_urls))

    return {
        "sources": all_sources,
        "all_source_urls": all_urls,
        "loop_counter": loop + 1,
        "search_requests_count": state.search_requests_count + total_requests,
        "search_cost_dollars": state.search_cost_dollars + total_cost,
    }
