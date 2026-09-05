from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest


def make_zip(path: Path, member_name: str = "arquivo.csv", content: bytes = b"A;B\n1;2\n") -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member_name, content)


class FakeCursor:
    def __init__(self, fetch_value=True):
        self.fetch_value = fetch_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return (self.fetch_value,)


class FakeConnection:
    def __init__(self, fetch_value=True):
        self.fetch_value = fetch_value

    def cursor(self):
        return FakeCursor(self.fetch_value)


class FakePostgres:
    def __init__(self, fetch_value=True):
        self.control = FakeConnection(fetch_value=fetch_value)
        self.data = FakeConnection(fetch_value=fetch_value)


def test_discover_zips_ignora_download_zip_e_classifica_grupos(tmp_path: Path):
    from etl.source import discover_zip_inventory

    make_zip(tmp_path / "Empresas0.zip")
    make_zip(tmp_path / "Estabelecimentos0.zip")
    make_zip(tmp_path / "Socios0.zip")
    make_zip(tmp_path / "download.zip")

    inventory = discover_zip_inventory(tmp_path)

    assert [item.zip_name for item in inventory.ignored] == ["download.zip"]
    assert {item.kind for item in inventory.zip_files} >= {"Empresas", "Estabelecimentos", "Socios"}
    assert len(inventory.zip_files) == 3


def test_fingerprint_de_zip_e_deterministico_e_expoe_metadados(tmp_path: Path):
    from etl.source import inspect_zip_artifact

    zip_path = tmp_path / "Empresas0.zip"
    make_zip(zip_path, "K3241.K03200Y0.D60808.EMPRECSV", b"12345678;Empresa\n")

    artifact = inspect_zip_artifact(zip_path)

    assert artifact.zip_name == "Empresas0.zip"
    assert artifact.member_name == "K3241.K03200Y0.D60808.EMPRECSV"
    assert artifact.member_size_bytes == len(b"12345678;Empresa\n")
    assert artifact.member_crc32 == zipfile.ZipFile(zip_path).infolist()[0].CRC
    assert artifact.sha256 == hashlib.sha256(zip_path.read_bytes()).hexdigest()


def test_schema_control_tem_status_validos_e_idempotencia():
    from etl.control import ExecutionStatus, build_control_schema_sql

    sql = build_control_schema_sql()

    assert "CREATE SCHEMA IF NOT EXISTS etl_control" in sql
    assert "etl_control.execucoes" in sql
    assert "etl_control.checkpoints_arquivos" in sql
    assert "etl_control.auditoria_arquivos" in sql
    assert ExecutionStatus.from_string("RUNNING").value == "RUNNING"


def test_lista_de_tabelas_rfb_nao_inclui_usuarios():
    from etl.control import RFB_TABLES

    assert "usuarios" not in RFB_TABLES


def test_lock_concorrente_bloqueia_segunda_execucao():
    from etl.control import LockAcquisitionError, AdvisoryLockManager

    class FakeConn:
        def __init__(self, responses):
            self.responses = list(responses)
            self.closed = False

        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, sql, params=None):
            self.last_sql = sql
            self.last_params = params

        def fetchone(self):
            return (self.responses.pop(0),)

        def close(self):
            self.closed = True

    lock = AdvisoryLockManager(project_name="dexa-prospect")
    conn = FakeConn([True])
    lock.acquire(conn, "2026-08")

    with pytest.raises(LockAcquisitionError):
        lock.acquire(FakeConn([False]), "2026-08")


def test_nova_execucao_rejeita_destino_nao_vazio(tmp_path: Path):
    from etl.preflight import PreflightService, PreflightContext, PreflightError

    make_zip(tmp_path / "Empresas0.zip")
    make_zip(tmp_path / "Estabelecimentos0.zip")
    make_zip(tmp_path / "Socios0.zip")
    make_zip(tmp_path / "Simples.zip")
    make_zip(tmp_path / "Cnaes.zip")
    make_zip(tmp_path / "Municipios.zip")
    make_zip(tmp_path / "Motivos.zip")
    make_zip(tmp_path / "Naturezas.zip")
    make_zip(tmp_path / "Paises.zip")
    make_zip(tmp_path / "Qualificacoes.zip")

    class FakeSourceChecker:
        def __init__(self):
            self.called = False

        def table_counts(self):
            return {
                "cnaes": 0,
                "municipios": 0,
                "motivos": 0,
                "naturezas_juridicas": 0,
                "paises": 0,
                "qualificacoes": 0,
                "empresas": 1,
                "estabelecimentos": 0,
                "simples": 0,
                "socios": 0,
            }

    ctx = PreflightContext(
        competencia="2026-08",
        source_dir=tmp_path,
        resume_execucao_id=None,
    )

    service = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        source_checker=FakeSourceChecker(),
    )

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_usuarios_nao_entra_na_verificacao_de_vazio():
    from etl.control import RFB_TABLES

    assert "usuarios" not in RFB_TABLES


def test_preflight_falha_se_zip_obrigatorio_ausente(tmp_path: Path):
    from etl.preflight import PreflightService, PreflightContext, PreflightError

    make_zip(tmp_path / "Empresas0.zip")

    service = PreflightService(postgres_factory=lambda: FakePostgres())
    ctx = PreflightContext(competencia="2026-08", source_dir=tmp_path, resume_execucao_id=None)

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_fingerprint_diferente_impede_retomada_silenciosa(tmp_path: Path):
    from etl.preflight import PreflightService, PreflightContext, PreflightError

    make_zip(tmp_path / "Empresas0.zip")
    make_zip(tmp_path / "Estabelecimentos0.zip")
    make_zip(tmp_path / "Socios0.zip")
    make_zip(tmp_path / "Simples.zip")
    make_zip(tmp_path / "Cnaes.zip")
    make_zip(tmp_path / "Municipios.zip")
    make_zip(tmp_path / "Motivos.zip")
    make_zip(tmp_path / "Naturezas.zip")
    make_zip(tmp_path / "Paises.zip")
    make_zip(tmp_path / "Qualificacoes.zip")

    class FakeResumeStore:
        def load_execution(self, execucao_id):
            return {
                "execucao_id": execucao_id,
                "competencia": "2026-08",
                "source_fingerprint": "abc",
                "status": "RUNNING",
            }

    service = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        resume_store=FakeResumeStore(),
    )
    ctx = PreflightContext(
        competencia="2026-08",
        source_dir=tmp_path,
        resume_execucao_id="123",
    )

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_preflight_nao_inicia_carga(tmp_path: Path):
    from etl.preflight import PreflightService, PreflightContext

    make_zip(tmp_path / "Empresas0.zip")
    make_zip(tmp_path / "Estabelecimentos0.zip")
    make_zip(tmp_path / "Socios0.zip")
    make_zip(tmp_path / "Simples.zip")
    make_zip(tmp_path / "Cnaes.zip")
    make_zip(tmp_path / "Municipios.zip")
    make_zip(tmp_path / "Motivos.zip")
    make_zip(tmp_path / "Naturezas.zip")
    make_zip(tmp_path / "Paises.zip")
    make_zip(tmp_path / "Qualificacoes.zip")

    class FakeSourceChecker:
        def table_counts(self):
            tables = [
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
            return {name: 0 for name in tables}

    service = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        source_checker=FakeSourceChecker(),
    )
    ctx = PreflightContext(competencia="2026-08", source_dir=tmp_path, resume_execucao_id=None)

    result = service.run(ctx)

    assert result.load_started is False
