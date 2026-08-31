"""Configuracao centralizada do Agente de Inteligencia de Contas."""

import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuracoes do agente."""

    max_research_loops: int = 2
    search_results_per_query: int = 5
    llm_model: str = "gpt-4o-mini"
    search_provider: str = "exa"
    verbose: bool = True


_DEFAULT_CONFIG = AgentConfig()


def get_config() -> AgentConfig:
    """Retorna a configuracao padrao."""
    return _DEFAULT_CONFIG


def get_search_provider_name() -> str:
    """Retorna o nome do provedor de busca configurado.

    Verifica EXA_API_KEY para decidir se Exa esta disponivel.
    """
    config = get_config()
    if config.search_provider == "exa" and os.environ.get("EXA_API_KEY"):
        return "exa"
    return config.search_provider
