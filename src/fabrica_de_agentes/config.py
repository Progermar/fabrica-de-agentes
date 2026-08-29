"""Configuracao centralizada do Agente de Inteligencia de Contas."""

from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuracoes do agente."""

    max_research_loops: int = 2
    search_results_per_query: int = 5
    llm_model: str = "gpt-4o-mini"
    search_provider: str = "duckduckgo"
    verbose: bool = True


_DEFAULT_CONFIG = AgentConfig()


def get_config() -> AgentConfig:
    """Retorna a configuracao padrao."""
    return _DEFAULT_CONFIG
