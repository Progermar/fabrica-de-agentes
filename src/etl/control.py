from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum

RFB_TABLES = [
    "cnaes",
    "municipios",
    "motivos",
    "naturezas_juridicas",
    "paises",
    "qualificacoes",
    "empresas",
    "estabelecimentos",
    "simples",
    "socios",
]


class ExecutionStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    INCONSISTENT = "INCONSISTENT"

    @classmethod
    def from_string(cls, value: str) -> ExecutionStatus:
        return cls(value.upper())


class LockAcquisitionError(RuntimeError):
    pass


class InvalidStateTransitionError(ValueError):
    pass


VALID_TRANSITIONS = {
    "PENDING": {"RUNNING"},
    "RUNNING": {"COMMITTED", "FAILED", "INCONSISTENT"},
    "FAILED": {"RUNNING"},
    "COMMITTED": set(),
    "INCONSISTENT": set(),
}


@dataclass(frozen=True)
class ExecutionRecord:
    execucao_id: str
    competencia: str
    origem_diretorio: str
    origem_fingerprint: str
    status: ExecutionStatus
    preflight_ok: bool = False
    preflight_mensagem: str | None = None


@dataclass(frozen=True)
class CheckpointRecord:
    execucao_id: str
    zip_nome: str
    status: ExecutionStatus
    ordem_execucao: int
    fase: str
    arquivo_interno: str
    tabela_destino: str
    source_records: int = 0
    accepted_records: int = 0
    discarded_records: int = 0
    sent_to_copy_records: int = 0
    bytes_0x00_removidos: int = 0
    checksum_sha256: str | None = None
    source_zip_size_bytes: int | None = None
    source_member_size_bytes: int | None = None
    source_member_crc32: str | None = None
    source_member_name: str | None = None
    source_eof_ok: bool = False
    source_crc_ok: bool = False
    source_fingerprint_ok: bool = False
    target_rowcount_before: int | None = None
    expected_target_count_after: int | None = None
    target_rowcount_after: int | None = None


def build_control_schema_sql() -> str:
    return """
CREATE SCHEMA IF NOT EXISTS etl_control;

CREATE TABLE IF NOT EXISTS etl_control.execucoes (
    execucao_id UUID PRIMARY KEY,
    origem_diretorio TEXT NOT NULL,
    origem_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('PENDING', 'RUNNING', 'COMMITTED', 'FAILED', 'INCONSISTENT')
    ),
    inicio_em TIMESTAMPTZ NULL,
    fim_em TIMESTAMPTZ NULL,
    host_nome TEXT NULL,
    processo_pid INT NULL,
    git_commit TEXT NULL,
    competencia TEXT NOT NULL,
    origem_zip_base_dir TEXT NOT NULL,
    preflight_ok BOOLEAN NOT NULL DEFAULT FALSE,
    preflight_mensagem TEXT NULL,
    observacao TEXT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS etl_control_execucoes_running_idx
    ON etl_control.execucoes (competencia)
    WHERE status = 'RUNNING';

CREATE TABLE IF NOT EXISTS etl_control.checkpoints_arquivos (
    execucao_id UUID NOT NULL REFERENCES etl_control.execucoes (execucao_id),
    ordem_execucao INT NOT NULL,
    fase TEXT NOT NULL,
    zip_tipo TEXT NOT NULL,
    zip_nome TEXT NOT NULL,
    arquivo_interno TEXT NOT NULL,
    tabela_destino TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('PENDING', 'RUNNING', 'COMMITTED', 'FAILED', 'INCONSISTENT')
    ),
    tentativa_numero INT NOT NULL DEFAULT 0,
    inicio_em TIMESTAMPTZ NULL,
    fim_em TIMESTAMPTZ NULL,
    source_records BIGINT NOT NULL DEFAULT 0,
    accepted_records BIGINT NOT NULL DEFAULT 0,
    discarded_records BIGINT NOT NULL DEFAULT 0,
    sent_to_copy_records BIGINT NOT NULL DEFAULT 0,
    newlines_fisicos BIGINT NULL,
    bytes_0x00_removidos BIGINT NOT NULL DEFAULT 0,
    checksum_sha256 TEXT NULL,
    source_zip_size_bytes BIGINT NULL,
    source_member_size_bytes BIGINT NULL,
    source_member_crc32 TEXT NULL,
    source_member_name TEXT NULL,
    source_eof_ok BOOLEAN NOT NULL DEFAULT FALSE,
    source_crc_ok BOOLEAN NOT NULL DEFAULT FALSE,
    source_fingerprint_ok BOOLEAN NOT NULL DEFAULT FALSE,
    tamanho_bytes_zip BIGINT NULL,
    tamanho_bytes_descompactado BIGINT NULL,
    mensagem_erro TEXT NULL,
    ultima_pulso_em TIMESTAMPTZ NULL,
    target_rowcount_before BIGINT NULL,
    expected_target_count_after BIGINT NULL,
    target_rowcount_after BIGINT NULL,
    PRIMARY KEY (execucao_id, zip_nome)
);

CREATE TABLE IF NOT EXISTS etl_control.auditoria_arquivos (
    auditoria_id BIGSERIAL PRIMARY KEY,
    execucao_id UUID NOT NULL,
    zip_nome TEXT NOT NULL,
    arquivo_interno TEXT NOT NULL,
    fase TEXT NOT NULL,
    de_status TEXT NULL,
    para_status TEXT NOT NULL,
    evento_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mensagem TEXT NULL,
    registros_csv_lidos BIGINT NULL,
    registros_aceitos BIGINT NULL,
    registros_enviados_copy BIGINT NULL,
    registros_descartados BIGINT NULL,
    bytes_0x00_removidos BIGINT NULL,
    checksum_sha256 TEXT NULL,
    duracao_ms BIGINT NULL,
    detalhe_json JSONB NULL
);
""".strip()


class AdvisoryLockManager:
    def __init__(self, project_name: str = "etl_rfb") -> None:
        self.project_name = project_name

    def acquire(self, conn, competencia: str) -> str:
        lock_key = f"{self.project_name}:{competencia}"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (lock_key,))
                acquired = bool(cursor.fetchone()[0])
        if not acquired:
            raise LockAcquisitionError(f"Execucao concorrente bloqueada para {competencia}")
        return lock_key

    def release(self, conn, lock_key: str) -> None:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(hashtext(%s))", (lock_key,))
                if not bool(cursor.fetchone()[0]):
                    raise LockAcquisitionError(f"Lock nao estava adquirido: {lock_key}")

    @contextmanager
    def session_lock(self, conn, competencia: str):
        lock_key = self.acquire(conn, competencia)
        try:
            yield lock_key
        finally:
            self.release(conn, lock_key)


class ControlRepository:
    def ensure_schema(self, conn) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(build_control_schema_sql())
        except Exception:
            conn.rollback()
            raise

    def insert_execution(
        self,
        conn,
        *,
        execucao_id: str,
        competencia: str,
        origem_diretorio: str,
        origem_fingerprint: str,
        origem_zip_base_dir: str,
        status: ExecutionStatus = ExecutionStatus.PENDING,
    ) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO etl_control.execucoes (
                            execucao_id, origem_diretorio, origem_fingerprint, status,
                            competencia, origem_zip_base_dir
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            execucao_id,
                            origem_diretorio,
                            origem_fingerprint,
                            status.value,
                            competencia,
                            origem_zip_base_dir,
                        ),
                    )
        except Exception:
            conn.rollback()
            raise

    def load_execution(self, conn, execucao_id: str) -> dict[str, object] | None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                """
                SELECT
                    execucao_id,
                    competencia,
                    origem_fingerprint,
                    status,
                    preflight_ok,
                    preflight_mensagem
                FROM etl_control.execucoes
                WHERE execucao_id = %s
                """,
                        (execucao_id,),
                    )
                    row = cursor.fetchone()
        except Exception:
            conn.rollback()
            raise
        if row is None:
            return None
        return {
            "execucao_id": row[0],
            "competencia": row[1],
            "origem_fingerprint": row[2],
            "status": row[3],
            "preflight_ok": row[4],
            "preflight_mensagem": row[5],
        }

    def mark_preflight(self, conn, execucao_id: str, message: str) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE etl_control.execucoes
                        SET preflight_ok = TRUE, preflight_mensagem = %s
                        WHERE execucao_id = %s
                        """,
                        (message, execucao_id),
                    )
        except Exception:
            conn.rollback()
            raise

    def transition_execution(
        self,
        conn,
        execucao_id: str,
        to_status: ExecutionStatus,
        message: str | None = None,
    ) -> None:
        self._transition(
            conn,
            table="execucoes",
            identity=(execucao_id,),
            to_status=to_status,
            message=message,
        )

    def transition_checkpoint(
        self,
        conn,
        execucao_id: str,
        zip_name: str,
        to_status: ExecutionStatus,
        message: str | None = None,
    ) -> None:
        self._transition(
            conn,
            table="checkpoints_arquivos",
            identity=(execucao_id, zip_name),
            to_status=to_status,
            message=message,
        )

    def create_checkpoint(
        self,
        conn,
        *,
        execucao_id: str,
        zip_name: str,
        phase: str,
        member_name: str,
        table_name: str,
        order: int,
    ) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO etl_control.checkpoints_arquivos
                            (execucao_id, ordem_execucao, fase, zip_tipo, zip_nome,
                             arquivo_interno, tabela_destino, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            execucao_id,
                            order,
                            phase,
                            phase,
                            zip_name,
                            member_name,
                            table_name,
                            ExecutionStatus.PENDING.value,
                        ),
                    )
        except Exception:
            conn.rollback()
            raise

    def load_checkpoint(
        self,
        conn,
        execucao_id: str,
        zip_name: str,
    ) -> CheckpointRecord | None:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        execucao_id,
                        zip_nome,
                        status,
                        ordem_execucao,
                        fase,
                        arquivo_interno,
                        tabela_destino,
                        source_records,
                        accepted_records,
                        discarded_records,
                        sent_to_copy_records,
                        bytes_0x00_removidos,
                        checksum_sha256,
                        source_zip_size_bytes,
                        source_member_size_bytes,
                        source_member_crc32,
                        source_member_name,
                        source_eof_ok,
                        source_crc_ok,
                        source_fingerprint_ok,
                        target_rowcount_before,
                        expected_target_count_after,
                        target_rowcount_after
                    FROM etl_control.checkpoints_arquivos
                    WHERE execucao_id = %s AND zip_nome = %s
                    """,
                    (execucao_id, zip_name),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return CheckpointRecord(
            execucao_id=row[0],
            zip_nome=row[1],
            status=ExecutionStatus(row[2]),
            ordem_execucao=row[3],
            fase=row[4],
            arquivo_interno=row[5],
            tabela_destino=row[6],
            source_records=row[7],
            accepted_records=row[8],
            discarded_records=row[9],
            sent_to_copy_records=row[10],
            bytes_0x00_removidos=row[11],
            checksum_sha256=row[12],
            source_zip_size_bytes=row[13],
            source_member_size_bytes=row[14],
            source_member_crc32=row[15],
            source_member_name=row[16],
            source_eof_ok=row[17],
            source_crc_ok=row[18],
            source_fingerprint_ok=row[19],
            target_rowcount_before=row[20],
            expected_target_count_after=row[21],
            target_rowcount_after=row[22],
        )

    def update_checkpoint_metrics(self, conn, execucao_id: str, zip_name: str, **metrics) -> None:
        if not metrics:
            return
        assignments = ", ".join(f"{key} = %s" for key in metrics)
        values = list(metrics.values()) + [execucao_id, zip_name]
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"""
                        UPDATE etl_control.checkpoints_arquivos
                        SET {assignments}
                        WHERE execucao_id = %s AND zip_nome = %s
                        """,
                        values,
                    )
        except Exception:
            conn.rollback()
            raise

    def _transition(self, conn, *, table, identity, to_status, message) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    if table == "execucoes":
                        cursor.execute(
                            """
                            SELECT status, competencia
                            FROM etl_control.execucoes
                            WHERE execucao_id = %s
                            FOR UPDATE
                            """,
                            identity,
                        )
                        row = cursor.fetchone()
                    else:
                        cursor.execute(
                            """
                            SELECT status, zip_nome, fase, arquivo_interno
                            FROM etl_control.checkpoints_arquivos
                            WHERE execucao_id = %s AND zip_nome = %s
                            FOR UPDATE
                            """,
                            identity,
                        )
                        row = cursor.fetchone()
                    if row is None:
                        raise InvalidStateTransitionError(f"Estado nao encontrado: {identity}")
                    current = str(row[0])
                    if to_status.value not in VALID_TRANSITIONS[current]:
                        raise InvalidStateTransitionError(
                            f"Transicao invalida: {current} -> {to_status.value}"
                        )
                    if table == "execucoes":
                        cursor.execute(
                            """
                            UPDATE etl_control.execucoes
                            SET status = %s,
                                preflight_mensagem = COALESCE(%s, preflight_mensagem)
                            WHERE execucao_id = %s
                            """,
                            (to_status.value, message, identity[0]),
                        )
                        archive_name = ""
                        internal_name = ""
                        phase = "execution"
                    else:
                        cursor.execute(
                            """
                            UPDATE etl_control.checkpoints_arquivos
                            SET status = %s,
                                mensagem_erro = COALESCE(%s, mensagem_erro)
                            WHERE execucao_id = %s AND zip_nome = %s
                            """,
                            (to_status.value, message, identity[0], identity[1]),
                        )
                        archive_name = identity[1]
                        internal_name = str(row[3])
                        phase = str(row[2])
                    cursor.execute(
                        """
                        INSERT INTO etl_control.auditoria_arquivos
                            (
                                execucao_id, zip_nome, arquivo_interno, fase,
                                de_status, para_status, mensagem
                            )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            identity[0], archive_name, internal_name, phase,
                            current, to_status.value, message,
                        ),
                    )
        except Exception:
            conn.rollback()
            raise


def tables_are_empty(counts: dict[str, int]) -> bool:
    for table in RFB_TABLES:
        if counts.get(table, 0) != 0:
            return False
    return True
