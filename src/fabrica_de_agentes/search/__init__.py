"""Abstracoes para provedores de busca web."""

from fabrica_de_agentes.search.base import SearchProvider, SearchResult
from fabrica_de_agentes.search.exa_provider import ExaSearchProvider
from fabrica_de_agentes.search.mock_provider import MockSearchProvider

__all__ = [
    "SearchResult",
    "SearchProvider",
    "ExaSearchProvider",
    "MockSearchProvider",
]
