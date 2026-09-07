from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from etl.rfb_schema import RFB_LOAD_TABLES


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

    def add_db_args(target: argparse.ArgumentParser) -> None:
        target.add_argument("--db-host")
        target.add_argument("--db-port", type=int)
        target.add_argument("--database")
        target.add_argument("--db-name", dest="database", help=argparse.SUPPRESS)
        target.add_argument("--db-user")

    preflight = subparsers.add_parser("preflight", help="Executa preflight sem iniciar carga")
    add_db_args(preflight)
    preflight.add_argument("--competencia", required=True)
    preflight.add_argument("--source-dir", required=True)
    preflight.add_argument("--resume-execucao-id")

    init_schema = subparsers.add_parser("init-rfb-schema", help="Cria schema RFB seguro")
    add_db_args(init_schema)

    load = subparsers.add_parser("load", help="Carrega tabela RFB autorizada")
    add_db_args(load)
    load.add_argument("--competencia", required=True)
    load.add_argument("--source-dir", required=True)
    load.add_argument("--table", required=True, choices=list(RFB_LOAD_TABLES))
    load.add_argument("--resume-execucao-id")

    return parser


def load_config(args: argparse.Namespace) -> EtlConfig:
    return EtlConfig(
        competencia=getattr(args, "competencia", ""),
        source_dir=Path(getattr(args, "source_dir", ".")),
        db_host=getattr(args, "db_host", None) or os.getenv("DB_HOST", "127.0.0.1"),
        db_port=getattr(args, "db_port", None) or int(os.getenv("DB_PORT", "5432")),
        db_name=getattr(args, "database", None) or os.getenv("DB_NAME", "postgres"),
        db_user=getattr(args, "db_user", None) or os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASS", ""),
    )
