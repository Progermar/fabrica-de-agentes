from __future__ import annotations

from dataclasses import dataclass


RFB_TABLE_ORDER = [
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


@dataclass(frozen=True)
class TableDefinition:
    name: str
    create_sql: str
    expected_columns: tuple[str, ...]


RFB_TABLE_DEFINITIONS: tuple[TableDefinition, ...] = (
    TableDefinition(
        name="cnaes",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.cnaes (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="municipios",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.municipios (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="motivos",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.motivos (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="naturezas_juridicas",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.naturezas_juridicas (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="paises",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.paises (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="qualificacoes",
        expected_columns=("codigo", "descricao"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.qualificacoes (
            codigo TEXT PRIMARY KEY,
            descricao TEXT NOT NULL
        )
        """,
    ),
    TableDefinition(
        name="empresas",
        expected_columns=(
            "cnpj_basico",
            "razao_social",
            "natureza_juridica",
            "qualificacao_responsavel",
            "capital_social",
            "porte_empresa",
            "ente_federativo_responsavel",
        ),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.empresas (
            cnpj_basico TEXT PRIMARY KEY,
            razao_social TEXT,
            natureza_juridica TEXT,
            qualificacao_responsavel TEXT,
            capital_social TEXT,
            porte_empresa TEXT,
            ente_federativo_responsavel TEXT
        )
        """,
    ),
    TableDefinition(
        name="estabelecimentos",
        expected_columns=(
            "cnpj_basico",
            "cnpj_ordem",
            "cnpj_dv",
            "identificador_matriz_filial",
            "nome_fantasia",
            "situacao_cadastral",
            "data_situacao_cadastral",
            "motivo_situacao_cadastral",
            "nome_cidade_exterior",
            "pais",
            "data_inicio_atividade",
            "cnae_fiscal_principal",
            "cnae_fiscal_secundaria",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cep",
            "uf",
            "municipio",
            "ddd1",
            "telefone1",
            "ddd2",
            "telefone2",
            "ddd_fax",
            "fax",
            "correio_eletronico",
            "situacao_especial",
            "data_situacao_especial",
        ),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.estabelecimentos (
            cnpj_basico TEXT NOT NULL,
            cnpj_ordem TEXT NOT NULL,
            cnpj_dv TEXT NOT NULL,
            identificador_matriz_filial TEXT,
            nome_fantasia TEXT,
            situacao_cadastral TEXT,
            data_situacao_cadastral TEXT,
            motivo_situacao_cadastral TEXT,
            nome_cidade_exterior TEXT,
            pais TEXT,
            data_inicio_atividade TEXT,
            cnae_fiscal_principal TEXT,
            cnae_fiscal_secundaria TEXT,
            tipo_logradouro TEXT,
            logradouro TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            uf TEXT,
            municipio TEXT,
            ddd1 TEXT,
            telefone1 TEXT,
            ddd2 TEXT,
            telefone2 TEXT,
            ddd_fax TEXT,
            fax TEXT,
            correio_eletronico TEXT,
            situacao_especial TEXT,
            data_situacao_especial TEXT,
            PRIMARY KEY (cnpj_basico, cnpj_ordem, cnpj_dv)
        )
        """,
    ),
    TableDefinition(
        name="simples",
        expected_columns=(
            "cnpj_basico",
            "opcao_simples",
            "data_opcao_simples",
            "data_exclusao_simples",
            "opcao_mei",
            "data_opcao_mei",
            "data_exclusao_mei",
        ),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.simples (
            cnpj_basico TEXT PRIMARY KEY,
            opcao_simples TEXT,
            data_opcao_simples TEXT,
            data_exclusao_simples TEXT,
            opcao_mei TEXT,
            data_opcao_mei TEXT,
            data_exclusao_mei TEXT
        )
        """,
    ),
    TableDefinition(
        name="socios",
        expected_columns=(
            "cnpj_basico",
            "identificador_socio",
            "nome_socio",
            "cnpj_cpf_socio",
            "qualificacao_socio",
            "data_entrada_sociedade",
            "pais",
            "representante_legal",
            "nome_representante",
            "qualificacao_representante_legal",
            "faixa_etaria",
        ),
        create_sql="""
        CREATE TABLE IF NOT EXISTS public.socios (
            cnpj_basico TEXT NOT NULL,
            identificador_socio TEXT NOT NULL,
            nome_socio TEXT,
            cnpj_cpf_socio TEXT,
            qualificacao_socio TEXT,
            data_entrada_sociedade TEXT,
            pais TEXT,
            representante_legal TEXT,
            nome_representante TEXT,
            qualificacao_representante_legal TEXT,
            faixa_etaria TEXT
        )
        """,
    ),
)

AUXILIARY_LOAD_TABLES: tuple[str, ...] = (
    "motivos",
    "cnaes",
    "municipios",
    "naturezas_juridicas",
    "paises",
    "qualificacoes",
)

RFB_LOAD_TABLES: tuple[str, ...] = AUXILIARY_LOAD_TABLES + (
    "estabelecimentos",
    "empresas",
    "simples",
    "socios",
)


class RfbSchemaConflictError(RuntimeError):
    pass


class RfbSchemaInitializer:
    def ensure_rfb_schema(self, conn) -> None:
        try:
            with conn:
                with conn.cursor() as cursor:
                    for definition in RFB_TABLE_DEFINITIONS:
                        self._assert_compatible(cursor, definition)
                        self._normalize_nullable_columns(cursor, definition)
                        cursor.execute(definition.create_sql)
        except Exception:
            conn.rollback()
            raise

    def _assert_compatible(self, cursor, definition: TableDefinition) -> None:
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (definition.name,),
        )
        existing = cursor.fetchall()
        if not existing:
            return

        existing_columns = tuple(row[0] for row in existing)
        if existing_columns != definition.expected_columns:
            raise RfbSchemaConflictError(
                f"Tabela {definition.name} ja existe com colunas incompatíveis"
            )

    def _normalize_nullable_columns(self, cursor, definition: TableDefinition) -> None:
        if definition.name not in {"estabelecimentos", "empresas", "simples", "socios"}:
            return
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (definition.name,),
        )
        existing = cursor.fetchall()
        if not existing:
            return
        nullable_columns = [
            row[0]
            for row in existing
            if row[0] not in {
                "cnpj_basico",
                "cnpj_ordem",
                "cnpj_dv",
                "identificador_socio",
            }
            and row[1] == "NO"
        ]
        if not nullable_columns:
            return
        cursor.execute(
            f"ALTER TABLE public.{definition.name} "
            + ", ".join(f"ALTER COLUMN {column} DROP NOT NULL" for column in nullable_columns)
        )

    def validate_installed_tables(self, conn) -> None:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
                tables = [row[0] for row in cursor.fetchall()]

        expected = [definition.name for definition in RFB_TABLE_DEFINITIONS]
        if sorted(tables) != sorted(expected):
            raise RfbSchemaConflictError(
                f"Tabelas instaladas divergentes: {tables!r}"
            )
