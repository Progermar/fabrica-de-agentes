"""Testes do modulo de LLM - OpenCodeProvider, nos de analise e integracao."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from fabrica_de_agentes.graph import build_graph
from fabrica_de_agentes.llm.base import LLMProvider, LLMResponse
from fabrica_de_agentes.llm.opencode_provider import OpenCodeProvider
from fabrica_de_agentes.nodes.analyze_account import analyze_account
from fabrica_de_agentes.nodes.extract_evidence import extract_evidence
from fabrica_de_agentes.nodes.gap_analysis import gap_analysis
from fabrica_de_agentes.search.mock_provider import MockSearchProvider
from fabrica_de_agentes.state import (
    AccountIntelligenceState,
    Evidence,
    Source,
)

# Import build_graph only where needed to avoid circular imports


# =============================================================================
# Testes do OpenCodeProvider com HTTP mockado
# =============================================================================


class TestOpenCodeProvider:
    """Testes do OpenCodeProvider com cliente HTTP mockado."""

    def test_requires_password(self):
        """Falha com mensagem clara na ausencia de OPENCODE_SERVER_PASSWORD."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENCODE_SERVER_PASSWORD"):
                OpenCodeProvider(password="")

    def test_uses_explicit_password(self):
        """Aceita senha passada explicitamente no construtor."""
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenCodeProvider(password="test-pw-123")
            assert provider._password == "test-pw-123"

    def test_uses_env_password(self):
        """Le OPENCODE_SERVER_PASSWORD do ambiente."""
        with patch.dict(os.environ, {"OPENCODE_SERVER_PASSWORD": "env-pw-456"}):
            provider = OpenCodeProvider()
            assert provider._password == "env-pw-456"

    def test_health_check_success(self):
        """Health check retorna True quando servidor responde."""
        provider = OpenCodeProvider(password="test-pw")

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"healthy": True, "version": "1.0.0"}
        ).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            assert provider.health_check() is True

    def test_health_check_failure(self):
        """Health check retorna False quando servidor falha."""
        provider = OpenCodeProvider(password="test-pw")

        with patch("urllib.request.urlopen", side_effect=RuntimeError("connection refused")):
            assert provider.health_check() is False

    def test_chat_valid_response(self):
        """Parsing de resposta valida do OpenCode."""
        provider = OpenCodeProvider(password="test-pw")

        session_response = MagicMock()
        session_response.read.return_value = json.dumps(
            {"id": "ses_test123"}
        ).encode()
        session_response.__enter__ = lambda s: s
        session_response.__exit__ = MagicMock(return_value=False)

        chat_response = MagicMock()
        chat_response.read.return_value = json.dumps(
            {
                "info": {
                    "modelID": "gpt-4o",
                    "tokens": {"input": 100, "output": 50},
                    "cost": 0.01,
                },
                "parts": [
                    {"type": "text", "text": '{"result": "ok"}'},
                ],
            }
        ).encode()
        chat_response.__enter__ = lambda s: s
        chat_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[session_response, chat_response]):
            result = provider.chat("test prompt")

        assert isinstance(result, LLMResponse)
        assert result.text == '{"result": "ok"}'
        assert result.model == "gpt-4o"
        assert result.tokens_input == 100
        assert result.tokens_output == 50
        assert result.cost_dollars == 0.01

    def test_chat_invalid_json_response(self):
        """Trata resposta que nao e JSON valido."""
        provider = OpenCodeProvider(password="test-pw")

        session_response = MagicMock()
        session_response.read.return_value = json.dumps(
            {"id": "ses_test123"}
        ).encode()
        session_response.__enter__ = lambda s: s
        session_response.__exit__ = MagicMock(return_value=False)

        chat_response = MagicMock()
        chat_response.read.return_value = b"not json at all"
        chat_response.__enter__ = lambda s: s
        chat_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[session_response, chat_response]):
            result = provider.chat("test prompt")

        assert isinstance(result, LLMResponse)
        assert "not json at all" in result.text

    def test_chat_server_unavailable(self):
        """Lida com servidor indisponivel."""
        provider = OpenCodeProvider(password="test-pw")

        with patch("urllib.request.urlopen", side_effect=RuntimeError("connection refused")):
            with pytest.raises(RuntimeError, match="indisponivel"):
                provider.chat("test prompt")


# =============================================================================
# Testes de extract_evidence com LLM mockado
# =============================================================================


class TestExtractEvidence:
    """Testes do no extract_evidence com LLM injetado."""

    def test_returns_empty_when_no_llm(self):
        """Retorna evidencias vazias quando llm e None."""
        state = AccountIntelligenceState(target_company="Test")
        result = extract_evidence(state, llm=None)
        assert result["evidence"] == []

    def test_returns_empty_when_no_sources(self):
        """Retorna evidencias vazias quando nao ha fontes."""
        state = AccountIntelligenceState(target_company="Test", sources=[])
        mock_llm = MagicMock(spec=LLMProvider)
        result = extract_evidence(state, llm=mock_llm)
        assert result["evidence"] == []

    def test_source_relevance_classification(self):
        """Fonte homonima/irrelevante nao vira evidencia."""
        state = AccountIntelligenceState(
            target_company="BDO Brasil",
            sources=[
                Source(
                    url="https://example.com/bdo-unrelated",
                    title="BDO Something Else",
                    snippet="A unrelated company",
                ),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/bdo-unrelated",
                            "relevant": False,
                            "relevance_reason": "Empresa diferente, homonimo",
                            "claims": [],
                        }
                    ]
                }
            )
        )

        result = extract_evidence(state, llm=mock_llm)

        assert len(result["evidence"]) == 0
        assert state.sources[0].relevant is False

    def test_evidence_maintains_url_title_context(self):
        """Evidencia preserva URL, titulo e contexto da fonte."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            sources=[
                Source(
                    url="https://example.com/article",
                    title="Article Title",
                    snippet="Important snippet",
                ),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/article",
                            "relevant": True,
                            "relevance_reason": "Artigo sobre a empresa",
                            "claims": [
                                {
                                    "claim": "Test Corp usa TOTVS",
                                    "claim_type": "fact",
                                    "category": "stack",
                                    "confidence": "alta",
                                    "context": "Trecho do artigo mencionando TOTVS",
                                }
                            ],
                        }
                    ]
                }
            )
        )

        result = extract_evidence(state, llm=mock_llm)

        assert len(result["evidence"]) == 1
        ev = result["evidence"][0]
        assert ev.source_url == "https://example.com/article"
        assert ev.source_title == "Article Title"
        assert ev.context == "Trecho do artigo mencionando TOTVS"
        assert ev.claim_type == "fact"

    def test_system_not_confirmed_generates_gap(self):
        """Sistema nao confirmado deve gerar evidencia tipo gap, nao palpite."""
        state = AccountIntelligenceState(
            target_company="Contabilidade Teste",
            sources=[
                Source(
                    url="https://example.com/contabilidade",
                    title="Contabilidade Teste",
                    snippet="Escritorio de contabilidade",
                ),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/contabilidade",
                            "relevant": True,
                            "relevance_reason": "Site da empresa",
                            "claims": [
                                {
                                    "claim": "Sistema ERP principal nao identificado",
                                    "claim_type": "gap",
                                    "category": "stack",
                                    "confidence": "baixa",
                                    "context": "Nao ha mencao publica ao sistema",
                                }
                            ],
                        }
                    ]
                }
            )
        )

        result = extract_evidence(state, llm=mock_llm)

        assert len(result["evidence"]) == 1
        assert result["evidence"][0].claim_type == "gap"

    def test_system_confirmed_generates_tech_signal(self):
        """Sistema confirmado por fonte gera evidencia tipo fact."""
        state = AccountIntelligenceState(
            target_company="BDO Brasil",
            sources=[
                Source(
                    url="https://example.com/bdo-totvs",
                    title="BDO usa TOTVS Protheus",
                    snippet="BDO Brasil utiliza TOTVS Protheus para BPO",
                ),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/bdo-totvs",
                            "relevant": True,
                            "relevance_reason": "Artigo confirma uso do TOTVS",
                            "claims": [
                                {
                                    "claim": (
                                "BDO Brasil utiliza TOTVS Protheus para BPO"
                            ),
                                    "claim_type": "fact",
                                    "category": "stack",
                                    "confidence": "alta",
                                    "context": "Artigo menciona explicitamente TOTVS Protheus",
                                }
                            ],
                        }
                    ]
                }
            )
        )

        result = extract_evidence(state, llm=mock_llm)

        assert len(result["evidence"]) == 1
        ev = result["evidence"][0]
        assert ev.claim_type == "fact"
        assert ev.confidence == "alta"
        assert "TOTVS" in ev.claim


# =============================================================================
# Testes de analyze_account com LLM mockado
# =============================================================================


class TestAnalyzeAccount:
    """Testes do no analyze_account com LLM injetado."""

    def test_returns_empty_when_no_llm(self):
        """Retorna analise vazia quando llm e None."""
        state = AccountIntelligenceState(target_company="Test")
        result = analyze_account(state, llm=None)
        assert result["stakeholders"] == []
        assert result["tech_signals"] == []

    def test_stakeholder_not_assumed_decisor(self):
        """Nao assume que pessoa visivel e decisor final."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            evidence=[
                Evidence(
                    claim="Joao Silva trabalha na empresa",
                    source_url="https://linkedin.com/joao",
                    category="stakeholder",
                    confidence="media",
                    claim_type="inference",
                ),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "tech_signals": [],
                    "stakeholders": [
                        {
                            "name": "Joao Silva",
                            "role": "Funcionario de TI",
                            "influence": "Desconhecida - cargo observado, nao decisor confirmado",
                            "evidence": "Perfil publico no LinkedIn",
                            "claim_type": "inference",
                        }
                    ],
                    "opportunities": [],
                    "commercial_risks": [],
                }
            )
        )

        result = analyze_account(state, llm=mock_llm)

        assert len(result["stakeholders"]) == 1
        sh = result["stakeholders"][0]
        assert "Desconhecida" in sh.influence or "inferido" in sh.influence.lower()

    def test_opportunity_without_evidence_is_hypothesis(self):
        """Oportunidade sem evidencia deve ser hipotes, nao fato."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            evidence=[],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "tech_signals": [],
                    "stakeholders": [],
                    "opportunities": [
                        {
                            "description": "Automacao com IA",
                            "alignment": "Ad IA da Teklamatik",
                            "evidence": "Sem evidencia direta",
                            "priority": "media",
                            "claim_type": "hypothesis",
                        }
                    ],
                    "commercial_risks": [],
                }
            )
        )

        result = analyze_account(state, llm=mock_llm)

        assert len(result["opportunities"]) == 1


# =============================================================================
# Testes de gap_analysis com LLM mockado
# =============================================================================


class TestGapAnalysis:
    """Testes do no gap_analysis com LLM injetado."""

    def test_returns_empty_when_no_llm(self):
        """Retorna gaps vazios quando llm e None."""
        state = AccountIntelligenceState(target_company="Test")
        result = gap_analysis(state, llm=None)
        assert result["gaps"] == []

    def test_researchable_gap_generates_new_query(self):
        """Gap pesquisavel gera nova query quando ha loop disponivel."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            loop_counter=0,
            max_loops=2,
            evidence=[
                Evidence(
                    claim="Empresa atua no segmento contabil",
                    source_url="https://example.com",
                    category="perfil",
                    confidence="media",
                    claim_type="inference",
                ),
            ],
            all_source_urls=["https://example.com"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps(
                {
                    "gaps": [
                        {
                            "description": "ERP principal nao confirmado",
                            "criticality": "alta",
                            "discovery_action": "Pesquisar vagas e licitacoes",
                            "new_query": "Test Corp ERP licitacao vaga",
                            "priority_for_next_interaction": 1,
                        }
                    ],
                    "rapport_points": [],
                    "discovery_questions": ["Qual sistema voces usam?"],
                    "suggested_next_actions": ["Agendar call"],
                }
            )
        )

        result = gap_analysis(state, llm=mock_llm)

        assert len(result["gaps"]) == 1
        assert result["gaps"][0].criticality == "alta"


# =============================================================================
# Testes de smoke do grafo totalmente offline
# =============================================================================


class TestGraphSmokeOffline:
    """Smoke tests que validam o grafo completo sem internet e sem LLM."""

    def test_full_flow_offline_no_llm(self):
        """Grafo executa completo com mock, sem conexao e sem LLM."""
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
        assert len(result["evidence"]) == 0
        assert len(result["stakeholders"]) == 0
        assert len(result["tech_signals"]) == 0

    def test_briefing_no_mock_data_offline(self):
        """Briefing nao contem dados mockados quando executado offline."""
        graph = build_graph(provider=MockSearchProvider())

        state = AccountIntelligenceState(
            target_company="No Mock Offline",
            max_loops=1,
        )

        result = graph.invoke(state)
        briefing = result["briefing_final"]

        assert "MOCKADO" not in briefing
        assert "DADOS PARCIALMENTE MOCKADOS" not in briefing
        assert "Chamadas de LLM realizadas: 0" in briefing


# =============================================================================
# Testes de integracao extract_evidence -> analyze_account -> gap_analysis
# =============================================================================


class TestAnalysisPipeline:
    """Testes de integracao dos nos de analise com LLM mockado."""

    def test_pipeline_with_mock_llm(self):
        """Pipeline completo com LLM mockado produz dados estruturados."""
        mock_llm = MagicMock(spec=LLMProvider)

        extract_response = {
            "sources": [
                {
                    "url": "https://example.com/bdo",
                    "relevant": True,
                    "relevance_reason": "Site da empresa",
                    "claims": [
                        {
                            "claim": "BDO Brasil usa TOTVS Protheus",
                            "claim_type": "fact",
                            "category": "stack",
                            "confidence": "alta",
                            "context": "Trecho do site",
                        }
                    ],
                }
            ]
        }

        analyze_response = {
            "tech_signals": [
                {
                    "technology": "TOTVS Protheus",
                    "purpose": "ERP contabil",
                    "evidence": "Confirmado por fonte publica",
                    "confidence": "alta",
                    "claim_type": "fact",
                    "source_url": "https://example.com/bdo",
                }
            ],
            "stakeholders": [
                {
                    "name": "Diretor de TI",
                    "role": "Decisor tecnico",
                    "influence": "Alta",
                    "evidence": "Evidencia publica",
                    "claim_type": "inference",
                }
            ],
            "opportunities": [],
            "commercial_risks": ["Concorrente estabelecido"],
        }

        gap_response = {
            "gaps": [
                {
                    "description": "Decisor economico nao identificado",
                    "criticality": "alta",
                    "discovery_action": "Perguntar na Discovery call",
                    "new_query": "",
                    "priority_for_next_interaction": 1,
                }
            ],
            "rapport_points": [
                {
                    "topic": "Transformacao digital",
                    "context": "Setor contabel em migracao",
                    "suggested_question": "Como esta a digitalizacao?",
                }
            ],
            "discovery_questions": ["Quem decide compras de TI?"],
            "suggested_next_actions": ["Agendar call"],
        }

        mock_llm.chat.side_effect = [
            LLMResponse(text=json.dumps(extract_response)),
            LLMResponse(text=json.dumps(analyze_response)),
            LLMResponse(text=json.dumps(gap_response)),
        ]

        state = AccountIntelligenceState(
            target_company="BDO Brasil",
            sources=[
                Source(
                    url="https://example.com/bdo",
                    title="BDO Brasil",
                    snippet="Site institucional",
                ),
            ],
            max_loops=1,
        )

        r1 = extract_evidence(state, llm=mock_llm)
        state.evidence = r1["evidence"]
        state.llm_requests_count = r1.get("llm_requests_count", 0)
        state.llm_cost_dollars = r1.get("llm_cost_dollars", 0)

        r2 = analyze_account(state, llm=mock_llm)
        state.tech_signals = r2["tech_signals"]
        state.stakeholders = r2["stakeholders"]
        state.opportunities = r2["opportunities"]
        state.commercial_risks = r2.get("commercial_risks", [])
        state.llm_requests_count = r2.get("llm_requests_count", state.llm_requests_count)
        state.llm_cost_dollars = r2.get("llm_cost_dollars", state.llm_cost_dollars)

        r3 = gap_analysis(state, llm=mock_llm)
        state.gaps = r3["gaps"]
        state.rapport_points = r3["rapport_points"]
        state.discovery_questions = r3["discovery_questions"]
        state.suggested_next_actions = r3["suggested_next_actions"]

        assert len(state.evidence) == 1
        assert state.evidence[0].claim_type == "fact"
        assert len(state.tech_signals) == 1
        assert state.tech_signals[0].technology == "TOTVS Protheus"
        assert len(state.stakeholders) == 1
        assert len(state.gaps) == 1
        assert state.gaps[0].criticality == "alta"
        assert len(state.rapport_points) == 1
        assert state.llm_requests_count >= 2
