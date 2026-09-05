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

    @classmethod
    def from_environment(cls) -> EtlConfig:
        return cls(
            competencia="",
            source_dir=Path("."),
            db_host=os.getenv("DB_HOST", "127.0.0.1"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "postgres"),
            db_user=os.getenv("DB_USER", "postgres"),
            db_password=os.getenv("DB_PASS", ""),
        )

    @property
    def db_settings(self) -> dict[str, object]:
        return {
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": self.db_password,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="etl", description="ETL RFB 08/2026")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Executa preflight sem iniciar carga")
    preflight.add_argument("--competencia", required=True)
    preflight.add_argument("--source-dir", required=True)
    preflight.add_argument("--db-host")
    preflight.add_argument("--db-port", type=int)
    preflight.add_argument("--database")
    preflight.add_argument("--db-name", dest="database", help=argparse.SUPPRESS)
    preflight.add_argument("--db-user")
    preflight.add_argument("--resume-execucao-id")
    return parser


def load_config(args: argparse.Namespace) -> EtlConfig:
    return EtlConfig(
        competencia=args.competencia,
        source_dir=Path(args.source_dir),
        db_host=args.db_host or os.getenv("DB_HOST", "127.0.0.1"),
        db_port=args.db_port or int(os.getenv("DB_PORT", "5432")),
        db_name=args.database or os.getenv("DB_NAME", "postgres"),
        db_user=args.db_user or os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASS", ""),
    )
