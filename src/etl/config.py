from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EtlConfig:
    competencia: str
    source_dir: Path
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="etl", description="ETL RFB 08/2026")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Executa preflight sem iniciar carga")
    preflight.add_argument("--competencia", required=True)
    preflight.add_argument("--source-dir", required=True)
    preflight.add_argument("--db-host", default=os.getenv("DB_HOST", "127.0.0.1"))
    preflight.add_argument("--db-port", type=int, default=int(os.getenv("DB_PORT", "5432")))
    preflight.add_argument("--db-name", default=os.getenv("DB_NAME", "postgres"))
    preflight.add_argument("--db-user", default=os.getenv("DB_USER", "postgres"))
    preflight.add_argument("--db-password", default=os.getenv("DB_PASS", "postgres"))
    preflight.add_argument("--resume-execucao-id")
    return parser


def load_config(args: argparse.Namespace) -> EtlConfig:
    return EtlConfig(
        competencia=args.competencia,
        source_dir=Path(args.source_dir),
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
    )
