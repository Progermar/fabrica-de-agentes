"""Definicao do estado compartilhado do grafo Account Intelligence Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Source:
    """Uma fonte consultada."""

    url: str
    title: str
    snippet: str = ""
    content: str = ""


@dataclass
class Evidence:
    """Uma evidencia extraida de uma fonte."""

    claim: str
    source_url: str
    confidence: Literal["alta", "media", "baixa"] = "media"
    category: str = ""


@dataclass
class Stakeholder:
    """Um stakeholders identificado na conta."""

    name: str
    role: str = ""
    influence: str = ""
    evidence: str = ""


@dataclass
class TechSignal:
    """Um sinal de stack tecnologica detectado."""

    technology: str
    evidence: str = ""
    confidence: Literal["alta", "media", "baixa"] = "media"
    source_url: str = ""


@dataclass
class Opportunity:
    """Uma oportunidade comercial identificada."""

    description: str
    alignment: str = ""
    evidence: str = ""
    priority: Literal["alta", "media", "baixa"] = "media"


@dataclass
class Gap:
    """Um gap de informacao identificado."""

    description: str
    criticality: Literal["alta", "media", "baixa"] = "media"
    discovery_action: str = ""
    priority_for_next_interaction: int = 0


@dataclass
class RapportPoint:
    """Um ponto de rapport para abertura de conversa."""

    topic: str
    context: str = ""
    suggested_question: str = ""


@dataclass
class AccountIntelligenceState:
    """Estado completo do fluxo de Account Intelligence.

    Cada no do grafo le e atualiza este estado conforme necessario.
    """

    # --- Entrada ---
    target_company: str = ""

    # --- Pesquisa ---
    research_queries: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)

    # --- Evidencias ---
    evidence: list[Evidence] = field(default_factory=list)

    # --- Analise ---
    stakeholders: list[Stakeholder] = field(default_factory=list)
    tech_signals: list[TechSignal] = field(default_factory=list)
    opportunities: list[Opportunity] = field(default_factory=list)

    # --- Rapport ---
    rapport_points: list[RapportPoint] = field(default_factory=list)
    discovery_questions: list[str] = field(default_factory=list)
    commercial_risks: list[str] = field(default_factory=list)
    suggested_next_actions: list[str] = field(default_factory=list)

    # --- Gaps ---
    gaps: list[Gap] = field(default_factory=list)

    # --- Briefing ---
    briefing_final: str = ""

    # --- Controle de loop ---
    loop_counter: int = 0
    max_loops: int = 2

    # --- Rastreabilidade ---
    all_source_urls: list[str] = field(default_factory=list)
