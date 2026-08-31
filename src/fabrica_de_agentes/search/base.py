"""Abstracao base para provedores de busca."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """Resultado normalizado de uma busca web."""

    url: str
    title: str
    snippet: str = ""
    published_date: str | None = None
    score: float | None = None
    highlights: list[str] = field(default_factory=list)


@dataclass
class SearchResponse:
    """Resposta de uma busca com metadados de custo."""

    results: list[SearchResult]
    request_count: int = 0
    cost_dollars: float | None = None


class SearchProvider(ABC):
    """Interface para provedores de busca web.

    Cada provedor implementa search() e retorna resultados normalizados.
    O LangGraph nao depende diretamente da implementacao do provedor.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        num_results: int = 5,
    ) -> SearchResponse:
        """Realiza uma busca web e retorna resultados normalizados."""
