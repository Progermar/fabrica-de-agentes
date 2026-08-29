"""Interface de linha de comando para executar o Account Intelligence Agent."""

from fabrica_de_agentes.config import get_config
from fabrica_de_agentes.graph import account_intelligence_graph
from fabrica_de_agentes.state import AccountIntelligenceState


def run_agent(target_company: str, max_loops: int | None = None) -> str:
    """Executa o agente para uma empresa-alvo e retorna o briefing."""
    config = get_config()
    loops = max_loops if max_loops is not None else config.max_research_loops

    initial_state = AccountIntelligenceState(
        target_company=target_company,
        max_loops=loops,
    )

    result = account_intelligence_graph.invoke(initial_state)
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
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  Account Intelligence Agent")
    print(f"  Empresa-alvo: {args.company}")
    print(f"{'='*60}\n")

    briefing = run_agent(args.company, args.max_loops)
    print(briefing)


if __name__ == "__main__":
    main()
