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

        with patch("urllib.request.urlopen", side_effect=RuntimeError("conn refused")):
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
        """Trata resposta que nao e JSON valido no nivel HTTP."""
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

        with patch("urllib.request.urlopen", side_effect=RuntimeError("conn refused")):
            with pytest.raises(RuntimeError, match="indisponivel"):
                provider.chat("test prompt")

    def test_chat_uses_system_field_separately(self):
        """Verifica que system e enviado como campo separado, nao concatenado."""
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
                "info": {"modelID": "gpt-4o", "tokens": {"input": 10, "output": 5}, "cost": 0.001},
                "parts": [{"type": "text", "text": "ok"}],
            }
        ).encode()
        chat_response.__enter__ = lambda s: s
        chat_response.__exit__ = MagicMock(return_value=False)

        captured_requests = []

        def capture_urlopen(req, **kwargs):
            captured_requests.append(req)
            if len(captured_requests) == 1:
                return session_response
            return chat_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            provider.chat("user prompt", system="system instruction")

        msg_request = captured_requests[1]
        body = json.loads(msg_request.data.decode())

        assert "system" in body
        assert body["system"] == "system instruction"
        assert body["parts"][0]["text"] == "user prompt"
        assert "system instruction" not in body["parts"][0]["text"]

    def test_chat_uses_agent_field(self):
        """Verifica que agent e enviado na mensagem."""
        provider = OpenCodeProvider(password="test-pw", agent="my-agent")

        session_response = MagicMock()
        session_response.read.return_value = json.dumps(
            {"id": "ses_test123"}
        ).encode()
        session_response.__enter__ = lambda s: s
        session_response.__exit__ = MagicMock(return_value=False)

        chat_response = MagicMock()
        chat_response.read.return_value = json.dumps(
            {
                "info": {"modelID": "gpt-4o", "tokens": {"input": 10, "output": 5}, "cost": 0.001},
                "parts": [{"type": "text", "text": "ok"}],
            }
        ).encode()
        chat_response.__enter__ = lambda s: s
        chat_response.__exit__ = MagicMock(return_value=False)

        captured_requests = []

        def capture_urlopen(req, **kwargs):
            captured_requests.append(req)
            if len(captured_requests) == 1:
                return session_response
            return chat_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            provider.chat("test")

        msg_request = captured_requests[1]
        body = json.loads(msg_request.data.decode())

        assert body.get("agent") == "my-agent"


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
            text=json.dumps({
                "sources": [{
                    "url": "https://example.com/bdo-unrelated",
                    "relevant": False,
                    "relevance_reason": "Empresa diferente",
                    "claims": [],
                }]
            })
        )

        result = extract_evidence(state, llm=mock_llm)
        assert len(result["evidence"]) == 0
        assert state.sources[0].relevant is False

    def test_evidence_maintains_url_title_context(self):
        """Evidencia preserva URL, titulo e contexto da fonte."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            sources=[
                Source(url="https://example.com/art", title="Title", snippet="Snippet"),
            ],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "sources": [{
                    "url": "https://example.com/art",
                    "relevant": True,
                    "relevance_reason": "Sobre a empresa",
                    "claims": [{
                        "claim": "Test Corp usa ERP X",
                        "claim_type": "fact",
                        "category": "stack",
                        "confidence": "alta",
                        "context": "Trecho do artigo",
                    }],
                }]
            })
        )

        result = extract_evidence(state, llm=mock_llm)
        assert len(result["evidence"]) == 1
        ev = result["evidence"][0]
        assert ev.source_url == "https://example.com/art"
        assert ev.source_title == "Title"
        assert ev.context == "Trecho do artigo"
        assert ev.claim_type == "fact"

    def test_system_not_confirmed_generates_gap(self):
        """Sistema nao confirmado gera evidencia tipo gap."""
        state = AccountIntelligenceState(
            target_company="Contabilidade Teste",
            sources=[Source(url="https://ex.com/c", title="C", snippet="s")],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "sources": [{
                    "url": "https://ex.com/c",
                    "relevant": True,
                    "relevance_reason": "Site da empresa",
                    "claims": [{
                        "claim": "Sistema ERP nao identificado",
                        "claim_type": "gap",
                        "category": "stack",
                        "confidence": "baixa",
                        "context": "Nao ha mencao",
                    }],
                }]
            })
        )

        result = extract_evidence(state, llm=mock_llm)
        assert len(result["evidence"]) == 1
        assert result["evidence"][0].claim_type == "gap"

    def test_json_invalid_raises_error(self):
        """JSON invalido na resposta do LLM levanta RuntimeError claro."""
        state = AccountIntelligenceState(
            target_company="Test",
            sources=[Source(url="https://ex.com", title="T", snippet="s")],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(text="Nao sou JSON valido")

        with pytest.raises(RuntimeError, match="extract_evidence.*JSON valido"):
            extract_evidence(state, llm=mock_llm)

    def test_only_new_sources_analyzed(self):
        """Analisa somente fontes novas, nao reanalisa fontes ja processadas."""
        state = AccountIntelligenceState(
            target_company="Test",
            sources=[
                Source(url="https://ex.com/old", title="Old", snippet="s"),
                Source(url="https://ex.com/new", title="New", snippet="s"),
            ],
            analyzed_source_urls=["https://ex.com/old"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "sources": [{
                    "url": "https://ex.com/new",
                    "relevant": True,
                    "relevance_reason": "Nova fonte",
                    "claims": [{
                        "claim": "Claim novo",
                        "claim_type": "fact",
                        "category": "perfil",
                        "confidence": "alta",
                        "context": "ctx",
                    }],
                }]
            })
        )

        extract_evidence(state, llm=mock_llm)

        call_args = mock_llm.chat.call_args
        prompt_text = call_args[0][0]
        assert "https://ex.com/old" not in prompt_text
        assert "https://ex.com/new" in prompt_text

    def test_deduplicates_evidence(self):
        """Evidencias duplicadas (source_url, claim, claim_type) sao removidas."""
        state = AccountIntelligenceState(
            target_company="Test",
            sources=[Source(url="https://ex.com/a", title="A", snippet="s")],
            evidence=[
                Evidence(
                    claim="Claim duplicado",
                    source_url="https://ex.com/a",
                    claim_type="fact",
                    category="stack",
                ),
            ],
            analyzed_source_urls=["https://ex.com/a"],
        )

        mock_llm = MagicMock(spec=LLMProvider)

        result = extract_evidence(state, llm=mock_llm)

        assert len(result["evidence"]) == 1
        assert result["evidence"][0].claim == "Claim duplicado"
        mock_llm.chat.assert_not_called()


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
                    claim="Joao Silva trabalha la",
                    source_url="https://linkedin.com/joao",
                    category="stakeholder",
                    confidence="media",
                    claim_type="inference",
                ),
            ],
            all_source_urls=["https://linkedin.com/joao"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "tech_signals": [],
                "stakeholders": [{
                    "name": "Joao Silva",
                    "role": "Funcionario de TI",
                    "influence": "Desconhecida - cargo observado",
                    "evidence": "LinkedIn",
                    "claim_type": "inference",
                    "source_url": "https://linkedin.com/joao",
                }],
                "opportunities": [],
                "commercial_risks": [],
            })
        )

        result = analyze_account(state, llm=mock_llm)
        assert len(result["stakeholders"]) == 1
        sh = result["stakeholders"][0]
        assert sh.claim_type == "inference"
        assert sh.source_url == "https://linkedin.com/joao"

    def test_opportunity_without_evidence_is_hypothesis(self):
        """Oportunidade sem evidencia deve ser hipotes."""
        state = AccountIntelligenceState(target_company="Test Corp", evidence=[])

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "tech_signals": [],
                "stakeholders": [],
                "opportunities": [{
                    "description": "Automacao com IA",
                    "alignment": "Portfolio Teklamatik",
                    "evidence": "Sem evidencia",
                    "priority": "media",
                    "claim_type": "hypothesis",
                }],
                "commercial_risks": [],
            })
        )

        result = analyze_account(state, llm=mock_llm)
        assert len(result["opportunities"]) == 1
        assert result["opportunities"][0].claim_type == "hypothesis"

    def test_json_invalid_raises_error(self):
        """JSON invalido levanta RuntimeError claro."""
        state = AccountIntelligenceState(target_company="Test", evidence=[])

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(text="invalid json!!!")

        with pytest.raises(RuntimeError, match="analyze_account.*JSON valido"):
            analyze_account(state, llm=mock_llm)

    def test_tech_signal_preserves_purpose(self):
        """TechSignal preserva purpose do LLM."""
        state = AccountIntelligenceState(target_company="Test", evidence=[])

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "tech_signals": [{
                    "technology": "Sistema X",
                    "purpose": "Gestao contabil",
                    "evidence": "Evidencia",
                    "confidence": "alta",
                    "claim_type": "fact",
                    "source_url": "https://ex.com/a",
                }],
                "stakeholders": [],
                "opportunities": [],
                "commercial_risks": [],
            })
        )

        result = analyze_account(state, llm=mock_llm)
        assert result["tech_signals"][0].purpose == "Gestao contabil"
        assert result["tech_signals"][0].claim_type == "fact"

    def test_invalid_source_url_rejected(self):
        """URL invalida (nao nas fontes) e rejeitada."""
        state = AccountIntelligenceState(
            target_company="Test",
            evidence=[],
            all_source_urls=["https://ex.com/real"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "tech_signals": [{
                    "technology": "Sys",
                    "purpose": "",
                    "evidence": "ev",
                    "confidence": "media",
                    "claim_type": "inference",
                    "source_url": "https://invented.com/fake",
                }],
                "stakeholders": [],
                "opportunities": [],
                "commercial_risks": [],
            })
        )

        result = analyze_account(state, llm=mock_llm)
        assert result["tech_signals"][0].source_url == ""


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
        assert result["has_new_researchable_gap"] is False

    def test_researchable_gap_generates_new_query(self):
        """Gap pesquisavel gera nova query e seta has_new_researchable_gap."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            loop_counter=0,
            max_loops=2,
            evidence=[
                Evidence(
                    claim="Empresa contabil",
                    source_url="https://ex.com",
                    category="perfil",
                    confidence="media",
                    claim_type="inference",
                ),
            ],
            all_source_urls=["https://ex.com"],
            research_queries=["query original"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "gaps": [{
                    "description": "ERP nao confirmado",
                    "criticality": "alta",
                    "discovery_action": "Pesquisar vagas",
                    "new_query": "Test Corp licitacao ERP vaga",
                    "priority_for_next_interaction": 1,
                }],
                "rapport_points": [],
                "discovery_questions": [],
                "suggested_next_actions": [],
            })
        )

        result = gap_analysis(state, llm=mock_llm)

        assert result["has_new_researchable_gap"] is True
        assert "Test Corp licitacao ERP vaga" in result["next_research_queries"]

    def test_no_researchable_gap_sets_flag_false(self):
        """Gap nao pesquisavel (new_query vazio) nao seta flag de loop."""
        state = AccountIntelligenceState(
            target_company="Test Corp",
            loop_counter=0,
            max_loops=2,
            evidence=[],
            all_source_urls=[],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "gaps": [{
                    "description": "Decisor nao identificado",
                    "criticality": "alta",
                    "discovery_action": "Perguntar na call",
                    "new_query": "",
                    "priority_for_next_interaction": 1,
                }],
                "rapport_points": [],
                "discovery_questions": [],
                "suggested_next_actions": [],
            })
        )

        result = gap_analysis(state, llm=mock_llm)
        assert result["has_new_researchable_gap"] is False
        assert result["next_research_queries"] == []

    def test_json_invalid_raises_error(self):
        """JSON invalido levanta RuntimeError claro."""
        state = AccountIntelligenceState(target_company="Test", evidence=[])

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(text="NOT JSON")

        with pytest.raises(RuntimeError, match="gap_analysis.*JSON valido"):
            gap_analysis(state, llm=mock_llm)

    def test_duplicate_query_not_added(self):
        """Query ja executada nao e adicionada a next_research_queries."""
        state = AccountIntelligenceState(
            target_company="Test",
            evidence=[],
            all_source_urls=[],
            research_queries=["Test Corp ERP"],
        )

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "gaps": [{
                    "description": "Gap",
                    "criticality": "alta",
                    "discovery_action": "Pesquisar",
                    "new_query": "Test Corp ERP",
                    "priority_for_next_interaction": 1,
                }],
                "rapport_points": [],
                "discovery_questions": [],
                "suggested_next_actions": [],
            })
        )

        result = gap_analysis(state, llm=mock_llm)
        assert result["next_research_queries"] == []


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

    def test_briefing_no_mock_data_offline(self):
        """Briefing nao contem dados mockados quando executado offline."""
        graph = build_graph(provider=MockSearchProvider())

        state = AccountIntelligenceState(
            target_company="No Mock",
            max_loops=1,
        )

        result = graph.invoke(state)
        briefing = result["briefing_final"]

        assert "MOCKADO" not in briefing
        assert "DADOS PARCIALMENTE MOCKADOS" not in briefing

    def test_require_llm_fails_without_llm(self):
        """require_llm=True falha se llm for None."""
        with pytest.raises(ValueError, match="requer LLM"):
            build_graph(provider=MockSearchProvider(), require_llm=True)


# =============================================================================
# Testes de integracao: gap_analysis -> search_sources com nova query
# =============================================================================


class TestGapLoopIntegration:
    """Testes de integracao do loop de gap_analysis com search_sources."""

    def test_gap_new_query_feeds_search(self):
        """Nova query do gap_analysis e usada pelo search_sources no proximo ciclo."""
        mock_llm = MagicMock(spec=LLMProvider)

        extract_resp = {
            "sources": [{
                "url": "https://ex.com/a",
                "relevant": True,
                "relevance_reason": "ok",
                "claims": [{
                    "claim": "Empresa contabil",
                    "claim_type": "inference",
                    "category": "perfil",
                    "confidence": "media",
                    "context": "ctx",
                }],
            }]
        }

        analyze_resp = {
            "tech_signals": [],
            "stakeholders": [],
            "opportunities": [],
            "commercial_risks": [],
        }

        gap_resp = {
            "gaps": [{
                "description": "ERP nao confirmado",
                "criticality": "alta",
                "discovery_action": "Pesquisar vagas",
                "new_query": "Empresa vagas licitacao ERP",
                "priority_for_next_interaction": 1,
            }],
            "rapport_points": [],
            "discovery_questions": [],
            "suggested_next_actions": [],
        }

        gap_resp_final = {
            "gaps": [],
            "rapport_points": [],
            "discovery_questions": [],
            "suggested_next_actions": [],
        }

        mock_llm.chat.side_effect = [
            LLMResponse(text=json.dumps(extract_resp)),
            LLMResponse(text=json.dumps(analyze_resp)),
            LLMResponse(text=json.dumps(gap_resp)),
            LLMResponse(text=json.dumps(extract_resp)),
            LLMResponse(text=json.dumps(analyze_resp)),
            LLMResponse(text=json.dumps(gap_resp_final)),
        ]

        graph = build_graph(provider=MockSearchProvider(results_per_query=2), llm=mock_llm)

        state = AccountIntelligenceState(
            target_company="Test Loop",
            max_loops=2,
        )

        result = graph.invoke(state)

        assert result["loop_counter"] == 2
        assert "Empresa vagas licitacao ERP" in result["research_queries"]

    def test_no_gap_stops_loop(self):
        """Sem nova query pesquisavel, grafo finaliza mesmo com loops disponiveis."""
        mock_llm = MagicMock(spec=LLMProvider)

        extract_resp = {
            "sources": [{
                "url": "https://ex.com/a",
                "relevant": True,
                "relevance_reason": "ok",
                "claims": [{
                    "claim": "Claim",
                    "claim_type": "fact",
                    "category": "perfil",
                    "confidence": "alta",
                    "context": "ctx",
                }],
            }]
        }

        analyze_resp = {
            "tech_signals": [],
            "stakeholders": [],
            "opportunities": [],
            "commercial_risks": [],
        }

        gap_resp = {
            "gaps": [{
                "description": "Decisor nao identificado",
                "criticality": "alta",
                "discovery_action": "Perguntar na call",
                "new_query": "",
                "priority_for_next_interaction": 1,
            }],
            "rapport_points": [],
            "discovery_questions": [],
            "suggested_next_actions": [],
        }

        mock_llm.chat.side_effect = [
            LLMResponse(text=json.dumps(extract_resp)),
            LLMResponse(text=json.dumps(analyze_resp)),
            LLMResponse(text=json.dumps(gap_resp)),
        ]

        graph = build_graph(provider=MockSearchProvider(), llm=mock_llm)

        state = AccountIntelligenceState(
            target_company="No Gap Loop",
            max_loops=3,
        )

        result = graph.invoke(state)

        assert result["loop_counter"] == 1
        assert result["has_new_researchable_gap"] is False

    def test_two_cycles_no_duplicate_evidence(self):
        """Dois ciclos nao geram evidencias duplicadas mesmos com URLs diferentes."""
        mock_llm = MagicMock(spec=LLMProvider)

        extract_resp_1 = {
            "sources": [{
                "url": "https://ex.com/a",
                "relevant": True,
                "relevance_reason": "ok",
                "claims": [{
                    "claim": "Claim unico",
                    "claim_type": "fact",
                    "category": "stack",
                    "confidence": "alta",
                    "context": "ctx",
                }],
            }]
        }

        extract_resp_2 = {
            "sources": [{
                "url": "https://ex.com/a",
                "relevant": True,
                "relevance_reason": "ok",
                "claims": [{
                    "claim": "Claim unico",
                    "claim_type": "fact",
                    "category": "stack",
                    "confidence": "alta",
                    "context": "ctx2",
                }],
            }]
        }

        analyze_resp = {
            "tech_signals": [],
            "stakeholders": [],
            "opportunities": [],
            "commercial_risks": [],
        }

        gap_resp_1 = {
            "gaps": [{
                "description": "Gap",
                "criticality": "alta",
                "discovery_action": "Pesquisar",
                "new_query": "Teste licitacao vaga",
                "priority_for_next_interaction": 1,
            }],
            "rapport_points": [],
            "discovery_questions": [],
            "suggested_next_actions": [],
        }

        gap_resp_2 = {
            "gaps": [],
            "rapport_points": [],
            "discovery_questions": [],
            "suggested_next_actions": [],
        }

        mock_llm.chat.side_effect = [
            LLMResponse(text=json.dumps(extract_resp_1)),
            LLMResponse(text=json.dumps(analyze_resp)),
            LLMResponse(text=json.dumps(gap_resp_1)),
            LLMResponse(text=json.dumps(extract_resp_2)),
            LLMResponse(text=json.dumps(analyze_resp)),
            LLMResponse(text=json.dumps(gap_resp_2)),
        ]

        graph = build_graph(provider=MockSearchProvider(results_per_query=2), llm=mock_llm)

        state = AccountIntelligenceState(
            target_company="Dedup Test",
            max_loops=2,
        )

        result = graph.invoke(state)

        claim_count = sum(
            1 for e in result["evidence"] if e.claim == "Claim unico"
        )
        assert claim_count == 1
