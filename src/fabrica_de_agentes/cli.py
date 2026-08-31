"""Interface de linha de comando para executar o Account Intelligence Agent."""

from __future__ import annotations

from fabrica_de_agentes.config import get_config
from fabrica_de_agentes.graph import build_graph
from fabrica_de_agentes.state import AccountIntelligenceState


def _get_provider(name: str):
    """Retorna o provedor de busca pelo nome."""
    if name == "exa":
        from fabrica_de_agentes.search.exa_provider import ExaSearchProvider

        return ExaSearchProvider()
    elif name == "mock":
        from fabrica_de_agentes.search.mock_provider import MockSearchProvider

        return MockSearchProvider()
    else:
        raise ValueError(f"Provedor desconhecido: {name}")


def _get_llm(name: str):
    """Retorna o provedor de LLM pelo nome."""
    if name == "opencode":
        from fabrica_de_agentes.llm.opencode_provider import OpenCodeProvider

        return OpenCodeProvider()
    elif name == "mock" or name == "none":
        return None
    else:
        raise ValueError(f"Provedor LLM desconhecido: {name}")


def run_agent(
    target_company: str,
    max_loops: int | None = None,
    provider_name: str | None = None,
    llm_name: str | None = None,
    require_llm: bool = False,
) -> str:
    """Executa o agente para uma empresa-alvo e retorna o briefing."""
    config = get_config()
    loops = max_loops if max_loops is not None else config.max_research_loops

    search_name = provider_name or config.search_provider
    provider = _get_provider(search_name)

    llm = None
    if llm_name:
        llm = _get_llm(llm_name)
    elif search_name != "mock":
        try:
            llm = _get_llm("opencode")
        except ValueError:
            llm = None

    graph = build_graph(provider=provider, llm=llm, require_llm=require_llm)

    initial_state = AccountIntelligenceState(
        target_company=target_company,
        max_loops=loops,
        max_results_per_query=config.search_results_per_query,
        max_queries_per_cycle=config.max_queries_per_cycle,
    )

    result = graph.invoke(initial_state)
    return result["briefing_final"]


def main():
    """Ponto de entrada CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Account Intelligence Agent - Fabrica de Agentes"
    )
    parser.add_argument(
        "company",
        type=str,
        help="Nome da empresa-alvo para pesquisa",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=None,
        help="Numero maximo de iteracoes de pesquisa (padrao: 2)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["exa", "mock"],
        default=None,
        help="Provedor de busca (padrao: exa se EXA_API_KEY configurada)",
    )
    parser.add_argument(
        "--llm",
        type=str,
        choices=["opencode", "mock", "none"],
        default=None,
        help="Provedor de LLM (padrao: opencode se OPENCODE_SERVER_PASSWORD configurada)",
    )
    parser.add_argument(
        "--require-llm",
        action="store_true",
        help="Falha se LLM nao estiver disponivel (execucao comercial)",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  Account Intelligence Agent")
    print(f"  Empresa-alvo: {args.company}")
    print(f"{'='*60}\n")

    briefing = run_agent(
        args.company,
        args.max_loops,
        args.provider,
        args.llm,
        args.require_llm,
    )
    print(briefing)


if __name__ == "__main__":
    main()
