"""Abstracoes para provedores de LLM."""

from fabrica_de_agentes.llm.base import LLMProvider
from fabrica_de_agentes.llm.opencode_provider import OpenCodeProvider

__all__ = ["LLMProvider", "OpenCodeProvider"]
