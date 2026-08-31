"""Testes do modulo de busca - SearchProvider, adapters e deduplicacao."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from fabrica_de_agentes.graph import build_graph
from fabrica_de_agentes.nodes.search_sources import (
    _deduplicate_urls,
    _search_result_to_source,
    search_sources,
)
from fabrica_de_agentes.search.base import SearchProvider, SearchResponse, SearchResult
from fabrica_de_agentes.search.exa_provider import ExaSearchProvider
from fabrica_de_agentes.search.mock_provider import MockSearchProvider
from fabrica_de_agentes.state import AccountIntelligenceState, Source

# =============================================================================
# Testes do adapter Exa com cliente/API mockado
# =============================================================================


class TestExaSearchProvider:
    """Testes do ExaSearchProvider com cliente mockado."""

    def test_exa_requires_api_key(self):
        """Falha com mensagem clara na ausencia de EXA_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="EXA_API_KEY"):
                ExaSearchProvider()

    def test_exa_uses_explicit_key(self):
        """Aceita chave passada explicitamente no construtor."""
        with patch.dict(os.environ, {}, clear=True):
            provider = ExaSearchProvider(api_key="test-key-123")
            assert provider._api_key == "test-key-123"

    def test_exa_uses_env_key(self):
        """Le EXA_API_KEY do ambiente quando nao passada explicitamente."""
        with patch.dict(os.environ, {"EXA_API_KEY": "env-key-456"}):
            provider = ExaSearchProvider()
            assert provider._api_key == "env-key-456"

    def test_exa_search_normalizes_results(self):
        """Verifica que resultados da Exa sao normalizados para SearchResult."""
        mock_result = MagicMock()
        mock_result.url = "https://example.com/article"
        mock_result.title = "Article Title"
        mock_result.highlights = ["Highlight 1", "Highlight 2"]
        mock_result.published_date = "2025-06-01T00:00:00.000Z"
        mock_result.score = 0.95

        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_response.cost_dollars = MagicMock()
        mock_response.cost_dollars.total = 0.005

        mock_exa = MagicMock()
        mock_exa.search.return_value = mock_response

        with patch("exa_py.Exa", return_value=mock_exa):
            provider = ExaSearchProvider(api_key="test-key")
            response = provider.search("test query", num_results=1)

        assert isinstance(response, SearchResponse)
        assert len(response.results) == 1

        result = response.results[0]
        assert isinstance(result, SearchResult)
        assert result.url == "https://example.com/article"
        assert result.title == "Article Title"
        assert result.snippet == "Highlight 1 Highlight 2"
        assert result.published_date == "2025-06-01T00:00:00.000Z"
        assert result.score == 0.95
        assert result.highlights == ["Highlight 1", "Highlight 2"]

        assert response.request_count == 1
        assert response.cost_dollars == 0.005

    def test_exa_search_handles_no_highlights(self):
        """Trata resultados sem highlights."""
        mock_result = MagicMock()
        mock_result.url = "https://example.com/plain"
        mock_result.title = "Plain Page"
        mock_result.highlights = []
        mock_result.published_date = None
        mock_result.score = 0.5

        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_response.cost_dollars = None

        mock_exa = MagicMock()
        mock_exa.search.return_value = mock_response

        with patch("exa_py.Exa", return_value=mock_exa):
            provider = ExaSearchProvider(api_key="test-key")
            response = provider.search("query")

        result = response.results[0]
        assert result.snippet == ""
        assert result.published_date is None
        assert response.cost_dollars is None

    def test_exa_search_handles_no_title(self):
        """Trata resultados sem titulo."""
        mock_result = MagicMock()
        mock_result.url = "https://example.com/no-title"
        mock_result.title = None
        mock_result.highlights = ["Some highlight"]
        mock_result.published_date = None
        mock_result.score = 0.7

        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_response.cost_dollars = None

        mock_exa = MagicMock()
        mock_exa.search.return_value = mock_response

        with patch("exa_py.Exa", return_value=mock_exa):
            provider = ExaSearchProvider(api_key="test-key")
            response = provider.search("query")

        assert response.results[0].title == ""


# =============================================================================
# Testes de normalizacao de resultados para Source
# =============================================================================


class TestSearchResultNormalization:
    """Testes de conversao de SearchResult para Source."""

    def test_search_result_to_source(self):
        """Verifica conversao correta de SearchResult para Source."""
        result = SearchResult(
            url="https://example.com/test",
            title="Test Title",
            snippet="Test snippet text",
            published_date="2025-01-01",
            score=0.8,
            highlights=["highlight1"],
        )

        source = _search_result_to_source(result)

        assert isinstance(source, Source)
        assert source.url == "https://example.com/test"
        assert source.title == "Test Title"
        assert source.snippet == "Test snippet text"
        assert source.content == "Test snippet text"

    def test_search_result_to_source_minimal(self):
        """Verifica conversao com dados minimos."""
        result = SearchResult(url="https://example.com/min", title="Min")

        source = _search_result_to_source(result)

        assert source.url == "https://example.com/min"
        assert source.title == "Min"
        assert source.snippet == ""
        assert source.content == ""


# =============================================================================
# Testes de deduplicacao de URL
# =============================================================================


class TestUrlDeduplication:
    """Testes de deduplicacao de URLs."""

    def test_deduplicate_removes_duplicates(self):
        """Remove URLs duplicadas, mantendo a primeira ocorrencia."""
        sources = [
            Source(url="https://example.com/a", title="A1"),
            Source(url="https://example.com/b", title="B"),
            Source(url="https://example.com/a", title="A2"),
            Source(url="https://example.com/c", title="C"),
            Source(url="https://example.com/b", title="B2"),
        ]

        result = _deduplicate_urls(sources)

        assert len(result) == 3
        assert result[0].title == "A1"
        assert result[1].title == "B"
        assert result[2].title == "C"

    def test_deduplicate_preserves_order(self):
        """Mantem a ordem de aparicao."""
        sources = [
            Source(url="https://x.com/3", title="Third"),
            Source(url="https://x.com/1", title="First"),
            Source(url="https://x.com/2", title="Second"),
            Source(url="https://x.com/3", title="Third-dup"),
        ]

        result = _deduplicate_urls(sources)

        urls = [s.url for s in result]
        assert urls == ["https://x.com/3", "https://x.com/1", "https://x.com/2"]

    def test_deduplicate_empty_list(self):
        """Lida com lista vazia."""
        assert _deduplicate_urls([]) == []

    def test_deduplicate_no_duplicates(self):
        """Nao altera lista sem duplicatas."""
        sources = [
            Source(url="https://a.com", title="A"),
            Source(url="https://b.com", title="B"),
        ]

        result = _deduplicate_urls(sources)
        assert len(result) == 2


# =============================================================================
# Testes do MockSearchProvider
# =============================================================================


class TestMockSearchProvider:
    """Testes do provedor mockado."""

    def test_mock_returns_results(self):
        """Verifica que o mock retorna resultados."""
        provider = MockSearchProvider(results_per_query=3)
        response = provider.search("test query")

        assert len(response.results) == 3
        assert response.request_count == 1
        assert response.cost_dollars is None

    def test_mock_respects_num_results(self):
        """Verifica que respeita o limite de resultados."""
        provider = MockSearchProvider(results_per_query=5)
        response = provider.search("query", num_results=2)

        assert len(response.results) == 2

    def test_mock_tracks_requests(self):
        """Verifica que conta requisicoes."""
        provider = MockSearchProvider()
        assert provider.total_requests == 0

        provider.search("query1")
        assert provider.total_requests == 1

        provider.search("query2")
        assert provider.total_requests == 2

    def test_mock_results_have_required_fields(self):
        """Verifica que todos os campos obrigatorios estao presentes."""
        provider = MockSearchProvider()
        response = provider.search("query")

        for result in response.results:
            assert isinstance(result, SearchResult)
            assert result.url
            assert result.title
            assert result.snippet


# =============================================================================
# Testes do no search_sources com provider fake/mockado
# =============================================================================


class TestSearchSourcesNode:
    """Testes do no search_sources com provider injetado."""

    def test_search_sources_with_mock_provider(self):
        """Verifica execucao do no com provider mock."""
        provider = MockSearchProvider(results_per_query=2)
        state = AccountIntelligenceState(
            target_company="Test Corp",
            research_queries=["query1", "query2"],
            max_loops=2,
        )

        result = search_sources(state, provider=provider)

        assert "sources" in result
        assert len(result["sources"]) == 4  # 2 queries x 2 results
        assert result["loop_counter"] == 1
        assert result["search_requests_count"] == 2

    def test_search_sources_deduplicates_urls(self):
        """Verifica deduplicacao ao acumular fontes."""
        provider = MockSearchProvider(results_per_query=2)
        existing_source = Source(
            url="https://example.com/mock/1/1",
            title="Existing",
        )

        state = AccountIntelligenceState(
            target_company="Test Corp",
            research_queries=["query1"],
            sources=[existing_source],
            all_source_urls=["https://example.com/mock/1/1"],
            max_loops=2,
        )

        result = search_sources(state, provider=provider)

        # A fonte existente com URL duplicada deve ser descartada
        urls = [s.url for s in result["sources"]]
        assert urls.count("https://example.com/mock/1/1") == 1

    def test_search_sources_accumulates_cost(self):
        """Verifica acumulacao de custo entre iteracoes."""
        provider = MockSearchProvider()

        state = AccountIntelligenceState(
            target_company="Cost Test",
            research_queries=["query1"],
            search_requests_count=2,
            search_cost_dollars=0.01,
            max_loops=2,
        )

        result = search_sources(state, provider=provider)

        assert result["search_requests_count"] == 3
        # MockSearchProvider retorna cost=None, entao acumula 0.01 + 0.0
        assert result["search_cost_dollars"] == 0.01

    def test_search_sources_handles_empty_queries(self):
        """Lida com lista vazia de queries."""
        provider = MockSearchProvider()
        state = AccountIntelligenceState(
            target_company="Empty",
            research_queries=[],
        )

        result = search_sources(state, provider=provider)

        assert result["sources"] == []
        assert result["loop_counter"] == 1

    def test_search_sources_handles_provider_error(self):
        """Lida com erros do provider sem interromper fluxo."""
        failing_provider = MagicMock(spec=SearchProvider)
        failing_provider.search.side_effect = Exception("API error")

        state = AccountIntelligenceState(
            target_company="Error Test",
            research_queries=["query1"],
        )

        result = search_sources(state, provider=failing_provider)

        # Deve retornar vazio sem levantar excecao
        assert result["sources"] == []
        assert result["loop_counter"] == 1


# =============================================================================
# Teste de ausencia de EXA_API_KEY na execucao real
# =============================================================================


class TestExaApiKeyAbsence:
    """Testes de comportamento na ausencia de EXA_API_KEY."""

    def test_exa_fails_without_key_in_env(self):
        """ExaSearchProvider falha sem chave no ambiente."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="EXA_API_KEY"):
                ExaSearchProvider()

    def test_exa_fails_with_empty_key(self):
        """ExaSearchProvider falha com chave vazia."""
        with patch.dict(os.environ, {"EXA_API_KEY": ""}, clear=True):
            with pytest.raises(ValueError, match="EXA_API_KEY"):
                ExaSearchProvider()


# =============================================================================
# Smoke tests do grafo sem internet e sem chave real
# =============================================================================


class TestGraphSmokeOffline:
    """Smoke tests que validam o grafo completo sem internet."""

    def test_full_flow_offline(self):
        """Grafo executa completo com mock, sem conexao."""
        graph = build_graph(provider=MockSearchProvider())

        state = AccountIntelligenceState(
            target_company="Offline Corp",
            max_loops=1,
        )

        result = graph.invoke(state)

        assert result["briefing_final"]
        assert len(result["sources"]) > 0
        assert result["search_requests_count"] > 0
        assert "Offline Corp" in result["briefing_final"]

    def test_full_flow_two_loops_offline(self):
        """Grafo executa com 2 loops完全 offline."""
        graph = build_graph(provider=MockSearchProvider(results_per_query=2))

        state = AccountIntelligenceState(
            target_company="Loop Test",
            max_loops=2,
        )

        result = graph.invoke(state)

        assert result["loop_counter"] == 2
        assert len(result["sources"]) > 4
        assert result["search_requests_count"] == 6  # 3 queries x 2 loops

    def test_graph_without_provider_uses_mock(self):
        """Grafo sem provider injetado usa mock por padrao."""
        graph = build_graph()

        state = AccountIntelligenceState(
            target_company="Default Mock",
            max_loops=1,
        )

        result = graph.invoke(state)
        assert result["briefing_final"]
