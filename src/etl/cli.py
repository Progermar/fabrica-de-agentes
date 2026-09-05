from __future__ import annotations

from etl.config import build_parser, load_config
from etl.preflight import PreflightContext, PreflightError, PreflightService
from etl.load import RfbLoadService
from etl.rfb_schema import RfbSchemaInitializer


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

    if args.command == "init-rfb-schema":
        config = load_config(args)
        service = PreflightService(config=config)
        postgres = service.postgres_factory(config)
        try:
            initializer = RfbSchemaInitializer()
            initializer.ensure_rfb_schema(postgres.control)
            initializer.validate_installed_tables(postgres.control)
        finally:
            getattr(postgres.control, "close")()
            getattr(postgres.data, "close")()
        return 0

    if args.command == "load":
        config = load_config(args)
        preflight = PreflightService(config=config)
        preflight_result = preflight.run(
            PreflightContext(
                competencia=config.competencia,
                source_dir=config.source_dir,
                resume_execucao_id=args.resume_execucao_id,
            )
        )
        loader = RfbLoadService(config=config)
        try:
            load_result = loader.load_table(
                args.table,
                config.source_dir,
                resume_execucao_id=preflight_result.execucao_id,
                lease=preflight_result.lease,
            )
            print(
                f"LOAD table={args.table} status={load_result.checkpoint_status} "
                f"rows={load_result.target_count_after}"
            )
            return 0
        finally:
            if preflight_result.lease is not None:
                preflight_result.lease.release()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
