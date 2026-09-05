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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def rollback(self):
        pass

    def close(self):
        pass


class FakePostgres:
    def __init__(self, fetch_value=True):
        self.control = FakeConnection(fetch_value=fetch_value)
        self.data = FakeConnection(fetch_value=fetch_value)


class FakeControlRepository:
    def __init__(self):
        self.records = {}
        self.transitions = []

    def ensure_schema(self, conn):
        pass

    def insert_execution(self, conn, **kwargs):
        self.records[kwargs["execucao_id"]] = {
            "execucao_id": kwargs["execucao_id"],
            "competencia": kwargs["competencia"],
            "origem_fingerprint": kwargs["origem_fingerprint"],
            "status": kwargs["status"].value,
        }

    def load_execution(self, conn, execucao_id):
        return self.records.get(execucao_id)

    def mark_preflight(self, conn, execucao_id, message):
        self.records[execucao_id]["preflight_ok"] = True
        self.records[execucao_id]["preflight_mensagem"] = message

    def transition_execution(self, conn, execucao_id, to_status, message=None):
        self.records[execucao_id]["status"] = to_status.value
        self.transitions.append((execucao_id, to_status.value, message))


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
    from etl.control import AdvisoryLockManager, LockAcquisitionError

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
    from etl.preflight import PreflightContext, PreflightError, PreflightService

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
        control_repo=FakeControlRepository(),
    )

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_usuarios_nao_entra_na_verificacao_de_vazio():
    from etl.control import RFB_TABLES

    assert "usuarios" not in RFB_TABLES


def test_preflight_falha_se_zip_obrigatorio_ausente(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightError, PreflightService

    make_zip(tmp_path / "Empresas0.zip")

    service = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        control_repo=FakeControlRepository(),
    )
    ctx = PreflightContext(competencia="2026-08", source_dir=tmp_path, resume_execucao_id=None)

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_fingerprint_diferente_impede_retomada_silenciosa(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightError, PreflightService

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
        def load_execution(self, conn, execucao_id):
            return {
                "execucao_id": execucao_id,
                "competencia": "2026-08",
                "source_fingerprint": "abc",
                "status": "RUNNING",
            }

    service = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        resume_store=FakeResumeStore(),
        control_repo=FakeControlRepository(),
    )
    ctx = PreflightContext(
        competencia="2026-08",
        source_dir=tmp_path,
        resume_execucao_id="123",
    )

    with pytest.raises(PreflightError):
        service.run(ctx)


def test_preflight_nao_inicia_carga(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightService

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
        control_repo=FakeControlRepository(),
    )
    ctx = PreflightContext(competencia="2026-08", source_dir=tmp_path, resume_execucao_id=None)

    result = service.run(ctx)

    assert result.load_started is False


def test_configuracao_cli_precede_env_e_senha_vem_do_ambiente(monkeypatch):
    from etl.config import build_parser, load_config

    monkeypatch.setenv("DB_HOST", "env-host")
    monkeypatch.setenv("DB_PORT", "5440")
    monkeypatch.setenv("DB_NAME", "env-db")
    monkeypatch.setenv("DB_USER", "env-user")
    monkeypatch.setenv("DB_PASS", "env-secret")
    args = build_parser().parse_args([
        "preflight",
        "--competencia", "2026-08",
        "--source-dir", "08-2026",
        "--db-host", "cli-host",
        "--db-port", "5441",
        "--database", "cli-db",
        "--db-user", "cli-user",
    ])
    config = load_config(args)

    assert config.db_settings == {
        "db_host": "cli-host",
        "db_port": 5441,
        "db_name": "cli-db",
        "db_user": "cli-user",
        "db_password": "env-secret",
    }


def test_fingerprint_independe_da_ordem_dos_arquivos(tmp_path: Path):
    from etl.source import ZipInventory, inspect_zip_artifact

    names = ["Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip"]
    for name in names:
        make_zip(tmp_path / name)
    artifacts = [inspect_zip_artifact(tmp_path / name) for name in names]
    first = ZipInventory(zip_files=artifacts, ignored=[]).fingerprint
    second = ZipInventory(zip_files=list(reversed(artifacts)), ignored=[]).fingerprint
    assert first == second


@pytest.mark.parametrize("member_names", [[], ["a.csv", "b.csv"]])
def test_zip_sem_um_unico_membro_regular_falha(tmp_path: Path, member_names):
    from etl.source import SourceArtifactError, inspect_zip_artifact

    path = tmp_path / "Empresas0.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name in member_names:
            archive.writestr(name, b"x")
    with pytest.raises(SourceArtifactError):
        inspect_zip_artifact(path)


def test_zip_invalido_e_diretorio_inexistente_falham_com_erro_de_dominio(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightError, PreflightService

    invalid = tmp_path / "Empresas0.zip"
    invalid.write_bytes(b"not-a-zip")
    service = PreflightService()
    with pytest.raises(PreflightError):
        service.run(PreflightContext("2026-08", tmp_path))
    with pytest.raises(PreflightError):
        service.run(PreflightContext("2026-08", tmp_path / "missing"))


def test_competencia_do_diretorio_e_validada(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightError, PreflightService

    source = tmp_path / "08-2026"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        make_zip(source / name)
    with pytest.raises(PreflightError):
        PreflightService().run(PreflightContext("2026-09", source))


def test_preflight_atualiza_preflight_ok_e_running(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightService

    source = tmp_path / "08-2026"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        make_zip(source / name)
    repository = FakeControlRepository()

    class EmptySourceChecker:
        def table_counts(self):
            return {name: 0 for name in [
                "cnaes", "municipios", "motivos", "naturezas_juridicas", "paises",
                "qualificacoes", "empresas", "estabelecimentos", "simples", "socios",
            ]}

    result = PreflightService(
        postgres_factory=lambda: FakePostgres(),
        source_checker=EmptySourceChecker(),
        control_repo=repository,
    ).run(PreflightContext("2026-08", source))
    record = repository.records[result.execucao_id]
    assert record["preflight_ok"] is True
    assert record["status"] == "RUNNING"


def test_checker_de_tabelas_com_conjunto_incompleto_falha(tmp_path: Path):
    from etl.preflight import PreflightContext, PreflightError, PreflightService

    source = tmp_path / "08-2026"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        make_zip(source / name)
    with pytest.raises(PreflightError, match="conjunto incompleto"):
        PreflightService(
            postgres_factory=lambda: FakePostgres(),
            source_checker=type("IncompleteChecker", (), {
                "table_counts": lambda self: {"empresas": 0},
            })(),
            control_repo=FakeControlRepository(),
        ).run(PreflightContext("2026-08", source))


def test_configuracao_chega_a_factory_usada_pelo_preflight(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.preflight import PreflightContext, PreflightService

    captured = []

    def factory(config):
        captured.append(config.db_settings)
        return FakePostgres()

    source = tmp_path / "08-2026"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        make_zip(source / name)
    repository = FakeControlRepository()

    class EmptySourceChecker:
        def table_counts(self):
            return {name: 0 for name in [
                "cnaes", "municipios", "motivos", "naturezas_juridicas", "paises",
                "qualificacoes", "empresas", "estabelecimentos", "simples", "socios",
            ]}

    config = EtlConfig(
        "2026-08", source, "cli-host", 5441, "cli-db", "cli-user", "env-secret"
    )
    result = PreflightService(
        config=config,
        postgres_factory=factory,
        source_checker=EmptySourceChecker(),
        control_repo=repository,
    ).run(PreflightContext("2026-08", source))
    assert result.lease is not None
    result.lease.release()
    assert captured == [config.db_settings]
