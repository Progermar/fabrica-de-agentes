"""Provedor de busca mockado para testes offline."""

from __future__ import annotations

from fabrica_de_agentes.search.base import SearchProvider, SearchResponse, SearchResult


class MockSearchProvider(SearchProvider):
    """Provedor que retorna resultados ficticios sem acesso a internet.

    Util para testes unitarios e smoke tests do grafo.
    """

    def __init__(self, results_per_query: int = 3):
        self._results_per_query = results_per_query
        self._request_count = 0

    @property
    def total_requests(self) -> int:
        """Numero total de requisicoes realizadas."""
        return self._request_count

    def search(
        self,
        query: str,
        num_results: int = 5,
    ) -> SearchResponse:
        """Retorna resultados mockados baseados na query."""
        self._request_count += 1
        count = min(num_results, self._results_per_query)

        results: list[SearchResult] = []
        for i in range(count):
            results.append(
                SearchResult(
                    url=f"https://example.com/mock/{self._request_count}/{i+1}",
                    title=f"Resultado {i+1} para '{query}'",
                    snippet=f"Trecho mockado da busca sobre '{query}'.",
                    published_date="2025-01-01T00:00:00.000Z",
                    score=0.9 - (i * 0.1),
                    highlights=[
                        f"Destaque {i+1} sobre '{query}'.",
                    ],
                )
            )

        return SearchResponse(
            results=results,
            request_count=1,
            cost_dollars=None,
        )
