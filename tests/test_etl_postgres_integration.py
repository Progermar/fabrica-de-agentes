from __future__ import annotations

import os
from uuid import uuid4

import psycopg2
import pytest

from etl.control import (
    AdvisoryLockManager,
    ControlRepository,
    ExecutionStatus,
    InvalidStateTransitionError,
    LockAcquisitionError,
)


def connection():
    host = os.getenv("ETL_TEST_DB_HOST")
    port = os.getenv("ETL_TEST_DB_PORT")
    name = os.getenv("ETL_TEST_DB_NAME")
    user = os.getenv("ETL_TEST_DB_USER")
    password = os.getenv("ETL_TEST_DB_PASSWORD")
    if not all([host, port, name, user, password]):
        raise RuntimeError("ETL_TEST_DB_* deve apontar para banco de teste isolado")
    if name == "dexaprospect":
        raise RuntimeError("Banco operacional bloqueado para testes destrutivos")
    assert host is not None and port is not None and name is not None and user is not None and password is not None
    return psycopg2.connect(
        host=host,
        port=int(port),
        dbname=name,
        user=user,
        password=password,
    )


@pytest.fixture
def control_records():
    record_id = str(uuid4())
    conn = connection()
    repo = ControlRepository()
    repo.ensure_schema(conn)
    yield conn, repo, record_id
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM etl_control.auditoria_arquivos WHERE execucao_id = %s",
                (record_id,),
            )
            cursor.execute(
                "DELETE FROM etl_control.checkpoints_arquivos WHERE execucao_id = %s",
                (record_id,),
            )
            cursor.execute(
                "DELETE FROM etl_control.execucoes WHERE execucao_id = %s",
                (record_id,),
            )
    conn.close()


@pytest.mark.integration
def test_control_persiste_schema_execucao_transicoes_e_auditoria(control_records):
    conn, repo, record_id = control_records
    competencia = f"2099-{record_id[-2:]}"
    repo.insert_execution(
        conn,
        execucao_id=record_id,
        competencia=competencia,
        origem_diretorio="integration-test",
        origem_fingerprint="integration-fingerprint",
        origem_zip_base_dir="integration-test",
    )
    repo.transition_execution(conn, record_id, ExecutionStatus.RUNNING, "started")
    repo.create_checkpoint(
        conn,
        execucao_id=record_id,
        zip_name="integration.zip",
        phase="integration",
        member_name="integration.csv",
        table_name="integration",
        order=1,
    )
    repo.transition_checkpoint(conn, record_id, "integration.zip", ExecutionStatus.RUNNING)
    repo.transition_checkpoint(
        conn, record_id, "integration.zip", ExecutionStatus.FAILED, "expected test failure"
    )

    with connection() as second:
        with second.cursor() as cursor:
            cursor.execute(
                "SELECT status, preflight_ok FROM etl_control.execucoes WHERE execucao_id = %s",
                (record_id,),
            )
            assert cursor.fetchone() == ("RUNNING", False)
            cursor.execute(
                "SELECT COUNT(*) FROM etl_control.auditoria_arquivos WHERE execucao_id = %s",
                (record_id,),
            )
            assert cursor.fetchone()[0] == 3


@pytest.mark.integration
def test_control_rejeita_transicao_invalida_e_faz_rollback(control_records):
    conn, repo, record_id = control_records
    repo.insert_execution(
        conn,
        execucao_id=record_id,
        competencia=f"2098-{record_id[-2:]}",
        origem_diretorio="integration-test",
        origem_fingerprint="integration-fingerprint",
        origem_zip_base_dir="integration-test",
    )
    with pytest.raises(InvalidStateTransitionError):
        repo.transition_execution(conn, record_id, ExecutionStatus.COMMITTED)
    with connection() as second:
        with second.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM etl_control.execucoes WHERE execucao_id = %s",
                (record_id,),
            )
            assert cursor.fetchone()[0] == "PENDING"


@pytest.mark.integration
def test_advisory_lock_real_exclusao_e_unlock():
    first = connection()
    second = connection()
    manager = AdvisoryLockManager(project_name="etl-integration-test")
    competencia = f"2097-{uuid4().hex[:6]}"
    key = manager.acquire(first, competencia)
    try:
        with pytest.raises(LockAcquisitionError):
            manager.acquire(second, competencia)
        manager.release(first, key)
        second_key = manager.acquire(second, competencia)
        manager.release(second, second_key)
    finally:
        first.close()
        second.close()
