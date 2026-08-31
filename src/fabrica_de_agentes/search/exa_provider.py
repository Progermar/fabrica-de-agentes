"""Provedor de busca usando a API Exa."""

from __future__ import annotations

import os

from fabrica_de_agentes.search.base import SearchProvider, SearchResponse, SearchResult


class ExaSearchProvider(SearchProvider):
    """Provedor de busca web usando o SDK oficial da Exa.

    Requer a variavel de ambiente EXA_API_KEY.
    Falha com mensagem clara na ausencia de chave.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("EXA_API_KEY")
        if not self._api_key:
            raise ValueError(
                "EXA_API_KEY nao configurada. "
                "Defina a variavel de ambiente EXA_API_KEY com sua chave da Exa. "
                "Obtenha em https://dashboard.exa.ai/api-keys"
            )

    def _get_client(self):
        """Cria o cliente Exa sob demanda para evitar import precoce."""
        from exa_py import Exa

        return Exa(api_key=self._api_key)

    def search(
        self,
        query: str,
        num_results: int = 5,
    ) -> SearchResponse:
        """Realiza busca via Exa API e normaliza os resultados.

        Usa type='auto' e highlights como recomendado pela documentacao.
        """
        exa = self._get_client()

        response = exa.search(
            query,
            type="auto",
            num_results=num_results,
            contents={"highlights": True},
        )

        results: list[SearchResult] = []
        for item in response.results:
            highlights = item.highlights if item.highlights else []
            results.append(
                SearchResult(
                    url=item.url,
                    title=item.title or "",
                    snippet=" ".join(highlights) if highlights else "",
                    published_date=item.published_date,
                    score=item.score,
                    highlights=highlights,
                )
            )

        cost = None
        if response.cost_dollars is not None:
            cost = response.cost_dollars.total

        return SearchResponse(
            results=results,
            request_count=1,
            cost_dollars=cost,
        )
