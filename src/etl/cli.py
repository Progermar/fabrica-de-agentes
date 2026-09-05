from __future__ import annotations

from etl.config import build_parser, load_config
from etl.preflight import PreflightContext, PreflightError, PreflightService


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "preflight":
        config = load_config(args)
        service = PreflightService(config=config)
        try:
            result = service.run(
                PreflightContext(
                    competencia=config.competencia,
                    source_dir=config.source_dir,
                    resume_execucao_id=args.resume_execucao_id,
                )
            )
        except PreflightError as exc:
            print(f"PREFLIGHT OK=False mensagem={exc}")
            return 1
        print(
            f"PREFLIGHT OK={result.preflight_ok} execucao_id={result.execucao_id} "
            f"zip_count={result.zip_count} fingerprint={result.source_fingerprint}"
        )
        if result.lease is not None:
            result.lease.release()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
