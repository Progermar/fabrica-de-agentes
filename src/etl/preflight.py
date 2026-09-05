from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from etl.control import (
    AdvisoryLockManager,
    ControlRepository,
    ExecutionStatus,
    RFB_TABLES,
    tables_are_empty,
)
from etl.source import ZipInventory, discover_zip_inventory, missing_required_zip_kinds


class PreflightError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreflightContext:
    competencia: str
    source_dir: Path
    resume_execucao_id: str | None = None


@dataclass(frozen=True)
class PreflightResult:
    execucao_id: str
    competencia: str
    source_dir: Path
    source_fingerprint: str
    zip_count: int
    load_started: bool = False
    preflight_ok: bool = True
    message: str = "OK"


class _DefaultSourceChecker:
    def __init__(self, data_conn) -> None:
        self.data_conn = data_conn

    def table_counts(self) -> dict[str, int]:
        with self.data_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                """
            )
            existing = {row[0] for row in cursor.fetchall()}

            missing = [table for table in RFB_TABLES if table not in existing]
            if missing:
                raise PreflightError(
                    "Tabelas RFB ausentes no banco de destino: "
                    + ", ".join(sorted(missing))
                )

            counts: dict[str, int] = {}
            for table in RFB_TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                counts[table] = int(cursor.fetchone()[0])
        return counts


@dataclass(frozen=True)
class PostgresConnections:
    control: object
    data: object


class _DefaultPostgresFactory:
    def __init__(self, settings: dict[str, object]) -> None:
        self.settings = settings

    def __call__(self):
        return open_postgres_connections(self.settings)


def open_postgres_connections(settings: dict[str, object]):
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover - depends on runtime image
        raise RuntimeError("psycopg2 nao esta disponivel neste ambiente") from exc

    conn_kwargs = {
        "host": str(settings["db_host"]),
        "port": int(str(settings["db_port"])),
        "dbname": str(settings["db_name"]),
        "user": str(settings["db_user"]),
        "password": str(settings["db_password"]),
    }
    control = psycopg2.connect(**conn_kwargs)
    data = psycopg2.connect(**conn_kwargs)
    return PostgresConnections(control=control, data=data)


class ResumeStore:
    def __init__(self, control_repo: ControlRepository | None = None) -> None:
        self.control_repo = control_repo or ControlRepository()

    def load_execution(
        self,
        conn_or_execucao_id,
        execucao_id: str | None = None,
    ) -> dict[str, object] | None:
        if execucao_id is None:
            return self.control_repo.load_execution(
                conn_or_execucao_id,
                conn_or_execucao_id,
            )
        return self.control_repo.load_execution(conn_or_execucao_id, execucao_id)


class PreflightService:
    def __init__(
        self,
        postgres_factory=None,
        source_checker=None,
        control_repo: ControlRepository | None = None,
        resume_store=None,
        lock_manager: AdvisoryLockManager | None = None,
    ) -> None:
        self.postgres_factory = postgres_factory or _DefaultPostgresFactory(
            _default_db_settings()
        )
        self.source_checker = source_checker
        self.control_repo = control_repo or ControlRepository()
        self.resume_store = resume_store or ResumeStore(self.control_repo)
        self.lock_manager = lock_manager or AdvisoryLockManager(
            project_name="fabrica-de-agentes-etl"
        )

    def run(self, ctx: PreflightContext) -> PreflightResult:
        inventory = discover_zip_inventory(ctx.source_dir)
        self._validate_inventory(inventory)

        postgres = self.postgres_factory()
        control_conn = postgres.control
        data_conn = postgres.data

        self.control_repo.ensure_schema(control_conn)
        self.lock_manager.acquire(control_conn, ctx.competencia)

        source_fingerprint = inventory.fingerprint
        execution_id = ctx.resume_execucao_id or str(uuid4())

        if ctx.resume_execucao_id:
            try:
                existing = self.resume_store.load_execution(control_conn, ctx.resume_execucao_id)
            except TypeError:
                existing = self.resume_store.load_execution(ctx.resume_execucao_id)
            if existing is None:
                raise PreflightError(
                    f"Execucao para retomar nao encontrada: {ctx.resume_execucao_id}"
                )
            if existing["competencia"] != ctx.competencia:
                raise PreflightError("Retomada inconsistente: competencia divergente")
            existing_fingerprint = existing.get("origem_fingerprint") or existing.get(
                "source_fingerprint"
            )
            if existing_fingerprint != source_fingerprint:
                raise PreflightError("Retomada inconsistente: fingerprint divergente")
        else:
            counts = self._get_table_counts(data_conn)
            if not tables_are_empty(counts):
                raise PreflightError("Banco nao esta vazio para nova execucao")
            self.control_repo.insert_execution(
                control_conn,
                execucao_id=execution_id,
                competencia=ctx.competencia,
                origem_diretorio=str(ctx.source_dir),
                origem_fingerprint=source_fingerprint,
                origem_zip_base_dir=str(ctx.source_dir),
                status=ExecutionStatus.PENDING,
            )

        self._check_disk_space(ctx.source_dir)

        return PreflightResult(
            execucao_id=execution_id,
            competencia=ctx.competencia,
            source_dir=ctx.source_dir,
            source_fingerprint=source_fingerprint,
            zip_count=len(inventory.zip_files),
            load_started=False,
            preflight_ok=True,
            message="OK",
        )

    def _validate_inventory(self, inventory: ZipInventory) -> None:
        missing = missing_required_zip_kinds(inventory)
        if missing:
            raise PreflightError(f"ZIPs obrigatorios ausentes: {', '.join(sorted(missing))}")

    def _get_table_counts(self, data_conn) -> dict[str, int]:
        if self.source_checker is not None:
            return self.source_checker.table_counts()
        return _DefaultSourceChecker(data_conn).table_counts()

    def _check_disk_space(self, source_dir: Path) -> None:
        root = Path(source_dir).anchor or str(source_dir)
        usage = shutil.disk_usage(root)
        if usage.free <= 0:
            raise PreflightError("Espaco em disco insuficiente")


def _default_db_settings() -> dict[str, object]:
    return {
        "db_host": os.getenv("DB_HOST", "127.0.0.1"),
        "db_port": int(os.getenv("DB_PORT", "5432")),
        "db_name": os.getenv("DB_NAME", "postgres"),
        "db_user": os.getenv("DB_USER", "postgres"),
        "db_password": os.getenv("DB_PASS", "postgres"),
    }
