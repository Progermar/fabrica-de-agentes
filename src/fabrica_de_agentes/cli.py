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


def run_agent(
    target_company: str,
    max_loops: int | None = None,
    provider_name: str | None = None,
) -> str:
    """Executa o agente para uma empresa-alvo e retorna o briefing."""
    config = get_config()
    loops = max_loops if max_loops is not None else config.max_research_loops

    name = provider_name or config.search_provider
    provider = _get_provider(name)

    graph = build_graph(provider=provider)

    initial_state = AccountIntelligenceState(
        target_company=target_company,
        max_loops=loops,
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
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  Account Intelligence Agent")
    print(f"  Empresa-alvo: {args.company}")
    print(f"{'='*60}\n")

    briefing = run_agent(args.company, args.max_loops, args.provider)
    print(briefing)


if __name__ == "__main__":
    main()
