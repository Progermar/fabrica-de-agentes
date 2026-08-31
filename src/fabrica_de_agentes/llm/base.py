"""Abstracao base para provedores de LLM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Resposta padronizada do provedor de LLM."""

    text: str
    model: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost_dollars: float = 0.0


class LLMProvider(ABC):
    """Interface para provedores de LLM.

    Cada provedor implementa chat() e retorna texto estruturado.
    Os nos do LangGraph nao dependem diretamente da implementacao.
    """

    @abstractmethod
    def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Envia um prompt ao LLM e retorna a resposta."""

    def health_check(self) -> bool:
        """Verifica se o provedor esta disponivel."""
        return True
