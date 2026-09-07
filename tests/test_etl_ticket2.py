from __future__ import annotations

import csv
import io
import os
import zipfile
from pathlib import Path

import pytest


def _pg_config():
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
    return {
        "host": host,
        "port": int(port),
        "dbname": name,
        "user": user,
        "password": password,
    }


def _connect():
    import psycopg2

    return psycopg2.connect(**_pg_config())


def _test_config(source_dir: Path):
    from etl.config import EtlConfig

    return EtlConfig(
        competencia="2026-08",
        source_dir=source_dir,
        db_host=os.environ["ETL_TEST_DB_HOST"],
        db_port=int(os.environ["ETL_TEST_DB_PORT"]),
        db_name=os.environ["ETL_TEST_DB_NAME"],
        db_user=os.environ["ETL_TEST_DB_USER"],
        db_password=os.environ["ETL_TEST_DB_PASSWORD"],
    )


def _make_zip(path: Path, member: str, content: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, content)


def _cleanup_competencia(
    competencia: str,
    clear_motivos: bool = False,
    clear_tables: tuple[str, ...] = (),
) -> None:
    db_name = os.getenv("ETL_TEST_DB_NAME")
    if not db_name:
        raise RuntimeError("ETL_TEST_DB_NAME deve apontar para banco de teste isolado")
    if db_name == "dexaprospect":
        raise RuntimeError("cleanup bloqueado para banco operacional")
    conn = _connect()
    with conn:
        with conn.cursor() as cursor:
            for table in (
                "motivos",
                "cnaes",
                "municipios",
                "naturezas_juridicas",
                "paises",
                "qualificacoes",
                "empresas",
                "estabelecimentos",
                "simples",
                "socios",
            ):
                cursor.execute(f"DELETE FROM public.{table}")
            for table in clear_tables:
                cursor.execute(f"DELETE FROM public.{table}")
            cursor.execute(
                "DELETE FROM etl_control.auditoria_arquivos WHERE execucao_id IN (SELECT execucao_id FROM etl_control.execucoes WHERE competencia = %s)",
                (competencia,),
            )
            cursor.execute(
                "DELETE FROM etl_control.checkpoints_arquivos WHERE execucao_id IN (SELECT execucao_id FROM etl_control.execucoes WHERE competencia = %s)",
                (competencia,),
            )
            cursor.execute(
                "DELETE FROM etl_control.execucoes WHERE competencia = %s",
                (competencia,),
            )
    conn.close()


def test_cleanup_competencia_bloqueia_banco_operacional(monkeypatch):
    monkeypatch.setenv("ETL_TEST_DB_NAME", "dexaprospect")
    with pytest.raises(RuntimeError, match="cleanup bloqueado"):
        _cleanup_competencia("2026-08")


def _write_complete_source(source: Path, table_rows: dict[str, bytes]) -> None:
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        if name in table_rows:
            _make_zip(source / name, "DADOS.CSV", table_rows[name])
        else:
            _make_zip(source / name, "arquivo.csv", b"x;y\n")


def _estabelecimento_row(
    cnpj_basico: str,
    situacao_cadastral: str,
    *,
    cnpj_ordem: str = "0001",
    cnpj_dv: str = "95",
    nome_fantasia: str = "",
    bytes_0x00: int = 0,
) -> list[str]:
    row = [
        cnpj_basico,
        cnpj_ordem,
        cnpj_dv,
        "1",
        nome_fantasia + ("\x00" * bytes_0x00),
        situacao_cadastral,
        "20260801",
        "0001",
        "EXTERIOR",
        "1058",
        "20260801",
        "6201501",
        "6201502",
        "RUA",
        "RUA TESTE",
        "123",
        "SALA 1",
        "CENTRO",
        "01001000",
        "SP",
        "3550308",
        "11",
        "33333333",
        "12",
        "44444444",
        "1234",
        "5678",
        "email@example.com",
        "N",
        "20260801",
    ]
    assert len(row) == 30
    return row


def _zip_csv_bytes(rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quotechar='"', lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("latin-1")


def _write_estabelecimentos_source(source: Path, malformed_zip_index: int | None = None) -> None:
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        if name != "Estabelecimentos0.zip" and not name.startswith("Estabelecimentos"):
            _make_zip(source / name, "arquivo.csv", b"x;y\n")

    for idx in range(10):
        zip_name = f"Estabelecimentos{idx}.zip"
        active_base = "10000000" if idx in {0, 1} else f"100000{idx:02d}"
        active_row = _estabelecimento_row(
            active_base,
            "02",
            cnpj_ordem=f"{idx + 1:04d}",
            cnpj_dv=f"{95 + idx:02d}",
            nome_fantasia="Ativo",
            bytes_0x00=5 if idx == 0 else 0,
        )
        inactive_row = _estabelecimento_row(
            f"200000{idx:02d}",
            "01",
            cnpj_ordem=f"{idx + 2001:04d}",
            cnpj_dv=f"{10 + idx:02d}",
            nome_fantasia="Inativo",
        )
        if malformed_zip_index == idx:
            active_row = active_row[:-1]
        _make_zip(source / zip_name, "ESTABELECIMENTOS.CSV", _zip_csv_bytes([active_row, inactive_row]))


def test_cli_exposes_init_and_load_commands():
    from etl.config import build_parser

    parser = build_parser()
    assert parser.parse_args(["init-rfb-schema"]).command == "init-rfb-schema"
    for table in ["motivos", "cnaes", "municipios", "naturezas_juridicas", "paises", "qualificacoes", "estabelecimentos"]:
        assert parser.parse_args([
            "load",
            "--competencia", "2026-08",
            "--source-dir", "08-2026",
            "--table", table,
        ]).command == "load"


@pytest.mark.integration
def test_init_rfb_schema_creates_only_10_tables_and_does_not_create_usuarios():
    from etl.rfb_schema import RfbSchemaInitializer

    conn = _connect()
    initializer = RfbSchemaInitializer()
    initializer.ensure_rfb_schema(conn)
    initializer.ensure_rfb_schema(conn)

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cursor.fetchall()]

    assert set(tables) == {
        "cnaes",
        "empresas",
        "estabelecimentos",
        "municipios",
        "motivos",
        "naturezas_juridicas",
        "paises",
        "qualificacoes",
        "simples",
        "socios",
    }
    conn.close()


@pytest.mark.integration
def test_preflight_passes_after_schema_init(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = Path(r"D:\Dados 14032026\Projetos\dexa-prospect\cnpj\08-2026")
    competencia = "2026-08"
    _cleanup_competencia(competencia)
    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()

    service = PreflightService(config=_test_config(source))
    result = service.run(PreflightContext(competencia, source))
    assert result.preflight_ok is True
    assert result.zip_count == 37
    assert result.lease is not None
    result.lease.release()
    _cleanup_competencia(competencia)


@pytest.mark.integration
def test_load_motivos_commits_and_is_idempotent(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        if name == "Motivos.zip":
            _make_zip(source / name, "MOTIVOS.CSV", b"01;Primeiro\n02;Segundo\n")
        else:
            _make_zip(source / name, "arquivo.csv", b"x;y\n")

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    assert preflight_result.lease is not None

    loader = RfbLoadService(config=_test_config(source))
    try:
        first = loader.load_table(
            "motivos",
            source,
            resume_execucao_id=preflight_result.execucao_id,
            lease=preflight_result.lease,
        )
        second = loader.load_table(
            "motivos",
            source,
            resume_execucao_id=preflight_result.execucao_id,
            lease=preflight_result.lease,
        )

        assert first.checkpoint_status == "COMMITTED"
        assert first.target_count_after == 2
        assert second.already_committed is True
        assert second.target_count_after == 2
    finally:
        preflight_result.lease.release()
        _cleanup_competencia(competencia, clear_motivos=True)


@pytest.mark.integration
def test_load_motivos_rolls_back_on_invalid_csv(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    source.mkdir()
    for name in [
        "Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip", "Simples.zip",
        "Cnaes.zip", "Municipios.zip", "Motivos.zip", "Naturezas.zip", "Paises.zip",
        "Qualificacoes.zip",
    ]:
        if name == "Motivos.zip":
            _make_zip(source / name, "MOTIVOS.CSV", b"01;Primeiro;EXTRA\n")
        else:
            _make_zip(source / name, "arquivo.csv", b"x;y\n")

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    assert preflight_result.lease is not None

    try:
        with pytest.raises(ValueError):
            loader.load_table(
                "motivos",
                source,
                resume_execucao_id=preflight_result.execucao_id,
                lease=preflight_result.lease,
            )
    finally:
        preflight_result.lease.release()
        _cleanup_competencia(competencia, clear_motivos=True)


@pytest.mark.integration
def test_load_motivos_rolls_back_on_failure_before_commit(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightError, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_complete_source(
        source,
        {"Motivos.zip": b"01;Primeiro\n02;Segundo\n"},
    )

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    try:
        with pytest.raises(RuntimeError, match="before_commit"):
            loader.load_table(
                "motivos",
                source,
                resume_execucao_id=preflight_result.execucao_id,
                lease=lease,
                failure_injector=lambda point: (_ for _ in ()).throw(RuntimeError(point))
                if point == "before_commit"
                else None,
            )
    finally:
        lease.release()

    _cleanup_competencia(competencia, clear_motivos=True)


@pytest.mark.integration
def test_load_motivos_reconcilia_after_crash_before_proof(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_complete_source(
        source,
        {"Motivos.zip": b"01;Primeiro\n02;Segundo\n"},
    )

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    try:
        with pytest.raises(RuntimeError, match="after_commit_before_proof"):
            loader.load_table(
                "motivos",
                source,
                resume_execucao_id=preflight_result.execucao_id,
                lease=lease,
                failure_injector=lambda point: (_ for _ in ()).throw(RuntimeError(point))
                if point == "after_commit_before_proof"
                else None,
            )
    finally:
        lease.release()

    recovered = loader.load_table(
        "motivos",
        source,
        resume_execucao_id=preflight_result.execucao_id,
        lease=None,
    )

    assert recovered.checkpoint_status == "COMMITTED"
    assert recovered.already_committed is True
    assert recovered.target_count_after == 2
    _cleanup_competencia(competencia, clear_motivos=True)


@pytest.mark.integration
def test_load_motivos_marks_inconsistent_on_count_mismatch(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightError, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_complete_source(
        source,
        {"Motivos.zip": b"01;Primeiro\n02;Segundo\n"},
    )

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    def injector(point: str) -> None:
        if point != "after_commit_before_proof":
            return
        conn = _connect()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO public.motivos (codigo, descricao) VALUES (%s, %s)", ("99", "Extra"))
        conn.close()

    try:
        with pytest.raises(PreflightError, match="inconsistente"):
            loader.load_table(
                "motivos",
                source,
                resume_execucao_id=preflight_result.execucao_id,
                lease=lease,
                failure_injector=injector,
            )
    finally:
        lease.release()
        _cleanup_competencia(competencia, clear_motivos=True)


@pytest.mark.integration
def test_load_all_auxiliary_tables_commit_in_sequence(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_complete_source(
        source,
        {
            "Motivos.zip": b"01;Primeiro\n02;Segundo\n",
            "Cnaes.zip": b"01;Atividade\n02;Outra\n",
            "Municipios.zip": b"01;Cidade A\n02;Cidade B\n",
            "Naturezas.zip": b"01;Natureza A\n02;Natureza B\n",
            "Paises.zip": b"01;Pais A\n02;Pais B\n",
            "Qualificacoes.zip": b"01;Qualificacao A\n02;Qualificacao B\n",
        },
    )

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia, clear_motivos=True)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    results = []
    try:
        for table in ["motivos", "cnaes", "municipios", "naturezas_juridicas", "paises", "qualificacoes"]:
            results.append(
                loader.load_table(
                    table,
                    source,
                    resume_execucao_id=preflight_result.execucao_id,
                    lease=lease,
                )
            )
    finally:
        lease.release()

    assert all(result.checkpoint_status == "COMMITTED" for result in results)
    assert {result.table for result in results} == {
        "motivos",
        "cnaes",
        "municipios",
        "naturezas_juridicas",
        "paises",
        "qualificacoes",
    }
    _cleanup_competencia(
        competencia,
        clear_motivos=True,
        clear_tables=(
            "cnaes",
            "municipios",
            "naturezas_juridicas",
            "paises",
            "qualificacoes",
        ),
    )


@pytest.mark.integration
def test_load_estabelecimentos_filters_situacao_02_and_builds_bitset(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_estabelecimentos_source(source)

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    try:
        result = loader.load_estabelecimentos(
            source,
            resume_execucao_id=preflight_result.execucao_id,
            lease=lease,
        )
    finally:
        lease.release()

    assert len(result.zip_results) == 10
    assert all(zip_result.checkpoint_status == "COMMITTED" for zip_result in result.zip_results)
    assert all(zip_result.source_records == 2 for zip_result in result.zip_results)
    assert all(zip_result.accepted_records == 1 for zip_result in result.zip_results)
    assert all(zip_result.discarded_records == 1 for zip_result in result.zip_results)
    assert result.zip_results[0].bytes_0x00_removidos == 5
    assert sum(zip_result.accepted_records for zip_result in result.zip_results) == 10
    assert result.bitset_result.unique_cnpjs_ativos == 9
    assert result.bitset_result.bits_marcados == 9

    conn = _connect()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM public.estabelecimentos")
            assert cursor.fetchone()[0] == 10
            cursor.execute("SELECT DISTINCT situacao_cadastral FROM public.estabelecimentos")
            assert [row[0] for row in cursor.fetchall()] == ["02"]
            cursor.execute("SELECT COUNT(*) FROM public.empresas")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM public.simples")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM public.socios")
            assert cursor.fetchone()[0] == 0
    conn.close()
    _cleanup_competencia(competencia)


@pytest.mark.integration
def test_load_estabelecimentos_rejects_wrong_column_count(tmp_path: Path):
    from etl.config import EtlConfig
    from etl.load import RfbLoadService
    from etl.preflight import PreflightContext, PreflightService
    from etl.rfb_schema import RfbSchemaInitializer

    source = tmp_path / "08-2026"
    competencia = "2026-08"
    _write_estabelecimentos_source(source, malformed_zip_index=3)

    conn = _connect()
    RfbSchemaInitializer().ensure_rfb_schema(conn)
    conn.close()
    _cleanup_competencia(competencia)

    preflight = PreflightService(config=_test_config(source))
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=_test_config(source))
    lease = preflight_result.lease
    assert lease is not None

    try:
        with pytest.raises(ValueError, match="estabelecimentos exige exatamente 30 colunas"):
            loader.load_estabelecimentos(
                source,
                resume_execucao_id=preflight_result.execucao_id,
                lease=lease,
            )
    finally:
        lease.release()
        _cleanup_competencia(competencia)
