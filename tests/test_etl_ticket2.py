from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest


def _pg_config():
    password = os.getenv("ETL_TEST_DB_PASSWORD") or os.getenv("DB_PASS")
    if not password:
        pytest.skip("ETL_TEST_DB_PASSWORD ou DB_PASS nao configurado")
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": password,
    }


def _connect():
    import psycopg2

    return psycopg2.connect(**_pg_config())


def _make_zip(path: Path, member: str, content: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, content)


def _cleanup_competencia(
    competencia: str,
    clear_motivos: bool = False,
    clear_tables: tuple[str, ...] = (),
) -> None:
    conn = _connect()
    with conn:
        with conn.cursor() as cursor:
            if clear_motivos:
                cursor.execute("DELETE FROM public.motivos")
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


def test_cli_exposes_init_and_load_commands():
    from etl.config import build_parser

    parser = build_parser()
    assert parser.parse_args(["init-rfb-schema"]).command == "init-rfb-schema"
    for table in ["motivos", "cnaes", "municipios", "naturezas_juridicas", "paises", "qualificacoes"]:
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

    service = PreflightService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    assert preflight_result.lease is not None

    loader = RfbLoadService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=EtlConfig.from_environment())
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

    preflight = PreflightService(config=EtlConfig.from_environment())
    preflight_result = preflight.run(PreflightContext(competencia, source))
    loader = RfbLoadService(config=EtlConfig.from_environment())
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
