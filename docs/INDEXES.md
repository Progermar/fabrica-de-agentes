# Dexa Prospect — Índices Otimizados (RFB 08/2026)

## Data da operação
2026-09-07

## Banco de dados
- **Nome:** dexaprospect
- **Container:** dexa-prospect-postgres
- **Porta:** 5433 (host) / 5432 (container)
- **Usuário:** dexaprospect_app

## Status Final

| Métrica | Antes | Depois |
|---------|-------|--------|
| Database size | 16 GB | 19 GB |
| Disco livre | 909 GB | 905 GB |
| Índices criados | 0 (novos) | 10 |
| ANALYZE | Nunca executado | Concluído |
| Backup final | — | rfb_2026-08_FINAL.dump (3.5 GB) |

## Índices Criados

### EMPRESAS

| Índice | Coluna | Tipo | Tamanho |
|--------|--------|------|---------|
| idx_empresas_razao | razao_social | btree | 1.471 MB |

### ESTABELECIMENTOS

| Índice | Coluna(s) | Tipo | Tamanho |
|--------|-----------|------|---------|
| idx_estab_cnae_principal | cnae_fiscal_principal | btree | 186 MB |
| idx_estab_cnae_uf | (cnae_fiscal_principal, uf) | btree | 192 MB |
| idx_estab_uf | uf | btree | 186 MB |
| idx_estab_municipio | municipio | btree | 187 MB |
| idx_estab_cnpj_basico | cnpj_basico | btree | 821 MB |
| idx_estab_situacao | situacao_cadastral | btree | 186 MB |
| idx_estab_motivo | motivo_situacao_cadastral | btree | 186 MB |

### MUNICIPIOS

| Índice | Coluna | Tipo | Tamanho |
|--------|--------|------|---------|
| idx_municipios_nome_trgm | descricao | GIN (pg_trgm) | 336 kB |

**Nota:** O nome do índice contém `nome` por convenção, mas a coluna real na tabela RFB é `descricao` (schema: `municipios.codigo`, `municipios.descricao`).

### SOCIOS

| Índice | Coluna | Tipo | Tamanho |
|--------|--------|------|---------|
| idx_socios_cnpj_basico | cnpj_basico | btree | 343 MB |

## Índices Históricos COBERTOS PELA PK (não criados)

| Índice Histórico | PK Existente |
|------------------|---------------|
| idx_empresas_cnpj_basico | empresas_pkey (cnpj_basico) |
| idx_estab_cnpj | estabelecimentos_pkey (cnpj_basico, cnpj_ordem, cnpj_dv) |
| idx_simples_cnpj_basico | simples_pkey (cnpj_basico) |
| idx_municipios_codigo | municipios_pkey (codigo) |
| idx_naturezas_juridicas_codigo | naturezas_juridicas_pkey (codigo) |
| idx_motivos_codigo | motivos_pkey (codigo) |

## Índice de CPF dos Sócios (pré-existente)

| Índice | Tabela | Coluna | Tamanho | Classificação |
|--------|--------|--------|---------|---------------|
| idx_socios_cnpj_cpf_socio | socios | cnpj_cpf_socio | 131 MB | **REMOVER POSTERIORMENTE** |

**Justificativa:** Backend não consulta por CPF; fonte RFB mascara CPFs (ex: `***101928**`); busca LIKE com leading wildcard não usa B-tree eficientemente.

## Resultado dos EXPLAIN

| Consulta | Índice Utilizado | Status |
|----------|------------------|--------|
| CNAE = '4754701' | idx_estab_cnae_principal | ✅ Index Scan |
| CNAE = '4754701' AND UF = 'SP' | idx_estab_cnae_uf | ✅ Bitmap Index Scan |
| UF = 'SP' | idx_estab_uf | ⚠️ Seq Scan (alta cardinalidade) |
| municipio = '7107' | idx_estab_municipio | ⚠️ Seq Scan (alta cardinalidade) |
| cnpj_basico = '08427096' | idx_estab_cnpj_basico | ✅ Index Scan |
| JOIN estab -> empresas | empresas_pkey + idx_estab_cnpj_basico | ✅ Nested Loop |
| JOIN estab -> municipios | idx_estab_cnpj_basico + municipios_pkey | ✅ Nested Loop |
| socios WHERE cnpj_basico = '42473600' | idx_socios_cnpj_basico | ✅ Index Scan |
| empresas WHERE razao_social ILIKE '%X%' | — | ⚠️ Seq Scan (leading wildcard) |
| municipios WHERE descricao % 'SAO PAULO' | idx_municipios_nome_trgm | ✅ Bitmap Index Scan |

## Validação Final (2026-09-07)

### Contagens

| Tabela | Contagem Esperada | Contagem Real | Status |
|--------|-------------------|---------------|--------|
| cnaes | 1.359 | 1.359 | ✅ |
| motivos | 63 | 63 | ✅ |
| municipios | 5.572 | 5.572 | ✅ |
| naturezas_juridicas | 91 | 91 | ✅ |
| paises | 255 | 255 | ✅ |
| qualificacoes | 68 | 68 | ✅ |
| empresas | 26.828.522 | 26.828.522 | ✅ |
| estabelecimentos | 28.148.920 | 28.148.920 | ✅ |
| simples | 23.151.707 | 23.151.707 | ✅ |
| socios | 14.458.308 | 14.458.308 | ✅ |

### Integridade

| Verificação | Resultado |
|-------------|-----------|
| estabelecimentos WHERE situacao_cadastral != '02' | 0 (todos ativos) |
| PK duplicates em estabelecimentos | 0 |
| DISTINCT cnpj_basico em estabelecimentos | 26.828.522 |
| estabelecimentos sem empresa | 0 |
| simples sem estabelecimento | 0 |
| socios sem estabelecimento | 0 |

### Backup Final

| Campo | Valor |
|-------|-------|
| Arquivo | rfb_2026-08_FINAL.dump |
| Tamanho | 3.500.993.484 bytes (3.5 GB) |
| SHA256 | 8AD70616E508159D9C10D965FF450A7619B502662D3BAB50DAD4C8D6BD5293B1 |
| Data/Hora | 2026-09-07 09:22:59 |

## Notas

- **UF e município:** Índices criados conforme manual, mas planner escolhe Seq Scan para consultas com alta cardinalidade (>10% da tabela). Índices úteis para filtros combinados (CNAE+UF) ou consultas seletivas.
- **Razão social:** B-tree não ajuda com `ILIKE '%padrão%'`. Útil para buscas por prefixo (`LIKE 'ANA%'`).
- **Município (trgm):** Coluna `descricao` (não `nome`) conforme schema RFB.
- **socios não tem PK:** Tabela socios não possui PRIMARY KEY definida. O idx_socios_cnpj_basico é o primeiro índice em cnpj_basico.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `sql/001_create_indexes.sql` | Script de criação dos índices |
| `docs/INDEXES.md` | Esta documentação |
