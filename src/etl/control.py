from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    INCONSISTENT = "INCONSISTENT"

    @classmethod
    def from_string(cls, value: str) -> "ExecutionStatus":
        return cls(value.upper())


class LockAcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionRecord:
    execucao_id: str
    competencia: str
    origem_diretorio: str
    origem_fingerprint: str
    status: ExecutionStatus
    preflight_ok: bool = False
    preflight_mensagem: str | None = None


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
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (lock_key,))
            acquired = bool(cursor.fetchone()[0])
        if not acquired:
            raise LockAcquisitionError(f"Execucao concorrente bloqueada para {competencia}")
        return lock_key


class ControlRepository:
    def ensure_schema(self, conn) -> None:
        with conn.cursor() as cursor:
            cursor.execute(build_control_schema_sql())

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

    def load_execution(self, conn, execucao_id: str) -> dict[str, object] | None:
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


def tables_are_empty(counts: dict[str, int]) -> bool:
    for table in RFB_TABLES:
        if counts.get(table, 0) != 0:
            return False
    return True
