"""No 3: Search Sources - Busca de fontes na web."""

from fabrica_de_agentes.state import AccountIntelligenceState, Source


def search_sources(state: AccountIntelligenceState) -> dict:
    """Realiza busca nas fontes para cada query.

    Na V1 real, este no conectaria a APIs de busca (DuckDuckGo, etc).
    Nesta versao esqueleto, gera fontes mockadas para validacao do fluxo.
    """
    company = state.target_company
    queries = state.research_queries
    loop = state.loop_counter

    new_sources: list[Source] = []
    new_urls: list[str] = []

    for i, query in enumerate(queries[:3]):
        source = Source(
            url=f"https://example.com/{company.lower().replace(' ', '-')}/"
            f"loop{loop+1}/{i+1}",
            title=f"Fonte {i+1} (loop {loop+1}): Resultado para '{query}'",
            snippet=f"Resumo mockado da busca sobre '{query}' para {company}.",
            content=(
                f"Conteudo completo mockado da fonte {i+1} (loop {loop+1}) "
                f"sobre {company}. Esta fonte contem informacoes relevantes "
                f"para a analise da empresa-alvo, incluindo dados sobre "
                f"operacoes, lideres e stack tecnologica."
            ),
        )
        new_sources.append(source)
        new_urls.append(source.url)

    # Acumula com fontes existentes
    all_sources = list(state.sources) + new_sources
    all_urls = list(state.all_source_urls) + new_urls

    return {
        "sources": all_sources,
        "all_source_urls": all_urls,
        "loop_counter": loop + 1,
    }
