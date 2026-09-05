from __future__ import annotations

import csv
import io
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from etl.config import EtlConfig
from etl.control import (
    AdvisoryLockManager,
    ControlRepository,
    ExecutionStatus,
    InvalidStateTransitionError,
)
from etl.preflight import PreflightLease, PreflightService, PreflightError
from etl.rfb_schema import RFB_TABLE_DEFINITIONS
from etl.source import inspect_zip_artifact


@dataclass(frozen=True)
class LoadResult:
    execucao_id: str
    table: str
    checkpoint_status: str
    already_committed: bool
    source_records: int
    accepted_records: int
    discarded_records: int
    sent_to_copy_records: int
    bytes_0x00_removidos: int
    target_count_before: int
    expected_target_count_after: int
    target_count_after: int
    source_eof_ok: bool
    source_crc_ok: bool
    source_fingerprint_ok: bool
    duration_ms: int


@dataclass(frozen=True)
class AuxiliaryLoadSpec:
    table: str
    zip_name: str
    order: int


AUXILIARY_LOAD_SPECS: dict[str, AuxiliaryLoadSpec] = {
    "motivos": AuxiliaryLoadSpec("motivos", "Motivos.zip", 1),
    "cnaes": AuxiliaryLoadSpec("cnaes", "Cnaes.zip", 2),
    "municipios": AuxiliaryLoadSpec("municipios", "Municipios.zip", 3),
    "naturezas_juridicas": AuxiliaryLoadSpec("naturezas_juridicas", "Naturezas.zip", 4),
    "paises": AuxiliaryLoadSpec("paises", "Paises.zip", 5),
    "qualificacoes": AuxiliaryLoadSpec("qualificacoes", "Qualificacoes.zip", 6),
}


class ZeroStrippingRaw(io.RawIOBase):
    def __init__(self, raw) -> None:
        self.raw = raw
        self.bytes_removed = 0

    def readable(self) -> bool:
        return True

    def readinto(self, b) -> int:
        view = memoryview(b)
        while True:
            chunk = self.raw.read(len(view))
            if not chunk:
                return 0
            filtered = chunk.replace(b"\x00", b"")
            self.bytes_removed += len(chunk) - len(filtered)
            if not filtered:
                continue
            n = min(len(view), len(filtered))
            view[:n] = filtered[:n]
            return n


class RfbLoadService:
    def __init__(
        self,
        config: EtlConfig,
        control_repo: ControlRepository | None = None,
        lock_manager: AdvisoryLockManager | None = None,
    ) -> None:
        self.config = config
        self.control_repo = control_repo or ControlRepository()
        self.lock_manager = lock_manager or AdvisoryLockManager(
            project_name="fabrica-de-agentes-etl"
        )

    def load_table(
        self,
        table: str,
        source_dir: Path | str,
        *,
        resume_execucao_id: str,
        lease: PreflightLease | None = None,
        failure_injector=None,
    ) -> LoadResult:
        spec = AUXILIARY_LOAD_SPECS.get(table)
        if spec is None:
            raise PreflightError("Neste ticket somente tabelas auxiliares podem ser carregadas")
        definition = self._table_definition(table)

        source_path = Path(source_dir)
        zip_path = source_path / spec.zip_name
        artifact = inspect_zip_artifact(zip_path)

        owns_lease = lease is None
        if lease is None:
            postgres = PreflightService(config=self.config).postgres_factory(self.config)
            control_conn = postgres.control
            data_conn = postgres.data
            lock_key = self.lock_manager.acquire(control_conn, self._competencia(source_path))
            lease = PreflightLease(control_conn, data_conn, self.lock_manager, lock_key)
        control_conn: Any = lease.control_conn
        data_conn: Any = lease.data_conn

        execucao = self.control_repo.load_execution(control_conn, resume_execucao_id)
        if execucao is None:
            raise PreflightError(f"Execucao nao encontrada: {resume_execucao_id}")

        if execucao["status"] not in {ExecutionStatus.RUNNING.value, ExecutionStatus.PENDING.value}:
            raise PreflightError("Execucao nao esta pronta para carga")

        existing = self.control_repo.load_checkpoint(control_conn, resume_execucao_id, spec.zip_name)
        if existing and existing.status == ExecutionStatus.COMMITTED:
            return LoadResult(
                execucao_id=resume_execucao_id,
                table=table,
                checkpoint_status=existing.status.value,
                already_committed=True,
                source_records=existing.source_records,
                accepted_records=existing.accepted_records,
                discarded_records=existing.discarded_records,
                sent_to_copy_records=existing.sent_to_copy_records,
                bytes_0x00_removidos=existing.bytes_0x00_removidos,
                target_count_before=existing.target_rowcount_before or 0,
                expected_target_count_after=existing.expected_target_count_after or 0,
                target_count_after=existing.target_rowcount_after or 0,
                source_eof_ok=existing.source_eof_ok,
                source_crc_ok=existing.source_crc_ok,
                source_fingerprint_ok=existing.source_fingerprint_ok,
                duration_ms=0,
            )

        if existing and existing.status == ExecutionStatus.RUNNING:
            current_count = self._count_rows(data_conn, table)
            if existing.target_rowcount_before is not None and current_count == existing.target_rowcount_before:
                self.control_repo.transition_checkpoint(
                    control_conn,
                    resume_execucao_id,
                    spec.zip_name,
                    ExecutionStatus.FAILED,
                    "Reconcilacao: commit nao ocorreu",
                )
            elif (
                existing.expected_target_count_after is not None
                and current_count == existing.expected_target_count_after
                and existing.source_eof_ok
                and existing.source_crc_ok
                and existing.source_fingerprint_ok
            ):
                self.control_repo.transition_checkpoint(
                    control_conn,
                    resume_execucao_id,
                    spec.zip_name,
                    ExecutionStatus.COMMITTED,
                    "Reconcilacao: dados ja commitados",
                )
                return LoadResult(
                    execucao_id=resume_execucao_id,
                    table=table,
                    checkpoint_status="COMMITTED",
                    already_committed=True,
                    source_records=existing.source_records,
                    accepted_records=existing.accepted_records,
                    discarded_records=existing.discarded_records,
                    sent_to_copy_records=existing.sent_to_copy_records,
                    bytes_0x00_removidos=existing.bytes_0x00_removidos,
                    target_count_before=existing.target_rowcount_before or 0,
                    expected_target_count_after=existing.expected_target_count_after or 0,
                    target_count_after=current_count,
                    source_eof_ok=True,
                    source_crc_ok=True,
                    source_fingerprint_ok=True,
                    duration_ms=0,
                )
            else:
                self.control_repo.transition_checkpoint(
                    control_conn,
                    resume_execucao_id,
                    spec.zip_name,
                    ExecutionStatus.INCONSISTENT,
                    "Reconcilacao inconclusiva",
                )
                raise PreflightError("Checkpoint RUNNING inconsistente")

        if not existing:
            self.control_repo.create_checkpoint(
                control_conn,
                execucao_id=resume_execucao_id,
                zip_name=spec.zip_name,
                phase=f"load-{table}",
                member_name=artifact.member_name,
                table_name=table,
                order=spec.order,
            )
        self.control_repo.transition_checkpoint(
            control_conn,
            resume_execucao_id,
            spec.zip_name,
            ExecutionStatus.RUNNING,
            f"Carregando {table}",
        )

        target_before = self._count_rows(data_conn, table)
        expected_after = target_before
        start = time.perf_counter()
        source_records = accepted_records = discarded_records = 0
        bytes_removed = 0
        copy_buffer = io.StringIO()
        writer = csv.writer(copy_buffer, delimiter=";", quotechar='"', lineterminator="\n")
        data_committed = False
        proof_done = False

        try:
            with zipfile.ZipFile(zip_path) as archive:
                member = next(member for member in archive.infolist() if not member.is_dir())
                with archive.open(member, "r") as raw_member:
                    filtered = ZeroStrippingRaw(raw_member)
                    with io.TextIOWrapper(io.BufferedReader(filtered), encoding="latin-1", newline="") as text_stream:
                        reader = csv.reader(text_stream, delimiter=";", quotechar='"')
                        with data_conn:
                            with data_conn.cursor() as cursor:
                                for row in reader:
                                    source_records += 1
                                    if len(row) != len(definition.expected_columns):
                                        raise ValueError(
                                            f"{table} exige exatamente {len(definition.expected_columns)} colunas"
                                        )
                                    writer.writerow(row)
                                    accepted_records += 1
                                    if copy_buffer.tell() >= 4 * 1024 * 1024:
                                        self._flush_copy(cursor, copy_buffer, table, definition.expected_columns)
                                if copy_buffer.tell() > 0:
                                    self._flush_copy(cursor, copy_buffer, table, definition.expected_columns)
                                if failure_injector is not None:
                                    failure_injector("before_commit")
                            data_committed = True
                    bytes_removed = filtered.bytes_removed
            self.control_repo.update_checkpoint_metrics(
                control_conn,
                resume_execucao_id,
                spec.zip_name,
                source_records=source_records,
                accepted_records=accepted_records,
                discarded_records=discarded_records,
                sent_to_copy_records=accepted_records,
                bytes_0x00_removidos=bytes_removed,
                checksum_sha256=artifact.sha256,
                source_zip_size_bytes=artifact.zip_size_bytes,
                source_member_size_bytes=artifact.member_size_bytes,
                source_member_crc32=str(artifact.member_crc32),
                source_member_name=artifact.member_name,
                source_eof_ok=True,
                source_crc_ok=True,
                source_fingerprint_ok=True,
                target_rowcount_before=target_before,
                expected_target_count_after=target_before + accepted_records,
            )
            if failure_injector is not None:
                failure_injector("after_commit_before_proof")
            target_after = self._count_rows(data_conn, table)
            proof_done = True
            if target_after != target_before + accepted_records:
                self.control_repo.transition_checkpoint(
                    control_conn,
                    resume_execucao_id,
                    spec.zip_name,
                    ExecutionStatus.INCONSISTENT,
                    "Contagem pos-commit divergente",
                )
                raise PreflightError("Contagem pos-commit inconsistente")
            self.control_repo.update_checkpoint_metrics(
                control_conn,
                resume_execucao_id,
                spec.zip_name,
                target_rowcount_after=target_after,
            )
            self.control_repo.transition_checkpoint(
                control_conn,
                resume_execucao_id,
                spec.zip_name,
                ExecutionStatus.COMMITTED,
                f"{table} carregado",
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return LoadResult(
                execucao_id=resume_execucao_id,
                table=table,
                checkpoint_status="COMMITTED",
                already_committed=False,
                source_records=source_records,
                accepted_records=accepted_records,
                discarded_records=discarded_records,
                sent_to_copy_records=accepted_records,
                bytes_0x00_removidos=bytes_removed,
                target_count_before=target_before,
                expected_target_count_after=target_before + accepted_records,
                target_count_after=target_after,
                source_eof_ok=True,
                source_crc_ok=True,
                source_fingerprint_ok=True,
                duration_ms=elapsed_ms,
            )
        except Exception as exc:
            if not data_committed:
                self.control_repo.transition_checkpoint(
                    control_conn,
                    resume_execucao_id,
                    spec.zip_name,
                    ExecutionStatus.FAILED,
                    str(exc),
                )
            elif data_committed and not proof_done:
                raise
            raise
        finally:
            if owns_lease and lease is not None:
                lease.release()

    def _flush_copy(
        self,
        cursor,
        buffer: io.StringIO,
        table: str,
        columns: tuple[str, ...],
    ) -> None:
        buffer.seek(0)
        cursor.copy_expert(
            f"""
            COPY public.{table} ({', '.join(columns)})
            FROM STDIN WITH (FORMAT csv, DELIMITER ';', QUOTE '"', ESCAPE '"')
            """,
            buffer,
        )
        buffer.seek(0)
        buffer.truncate(0)

    def _table_definition(self, table: str):
        for definition in RFB_TABLE_DEFINITIONS:
            if definition.name == table:
                return definition
        raise PreflightError(f"Tabela desconhecida: {table}")

    def _count_rows(self, conn, table: str) -> int:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
            row = cursor.fetchone()
            return int(row[0] if row else 0)

    def _competencia(self, source_dir: Path) -> str:
        name = source_dir.name
        if len(name) == 7 and name[2] == "-":
            return f"{name[3:7]}-{name[0:2]}"
        return self.config.competencia
