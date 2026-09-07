-- ============================================================
-- Dexa Prospect - Optimized Indexes (RFB 08/2026)
-- Restauração do conjunto canônico de índices do manual histórico
-- Data: 2026-09-07
-- ============================================================
-- Execução: CREATE INDEX CONCURRENTLY (não bloqueia tabela)
-- Requer: pg_trgm para índice GIN de município
-- ============================================================

-- 1. Extensão pg_trgm para busca por similaridade
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Índices EMPRESAS (além da PK)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empresas_razao
    ON public.empresas USING btree (razao_social);

-- 3. Índices ESTABELECIMENTOS (além da PK)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_cnae_principal
    ON public.estabelecimentos USING btree (cnae_fiscal_principal);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_cnae_uf
    ON public.estabelecimentos USING btree (cnae_fiscal_principal, uf);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_uf
    ON public.estabelecimentos USING btree (uf);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_municipio
    ON public.estabelecimentos USING btree (municipio);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_cnpj_basico
    ON public.estabelecimentos USING btree (cnpj_basico);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_situacao
    ON public.estabelecimentos USING btree (situacao_cadastral);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_estab_motivo
    ON public.estabelecimentos USING btree (motivo_situacao_cadastral);

-- 4. Índice MUNICIPIOS (GIN + pg_trgm para autocomplete)
-- Nota: coluna 'descricao' (não 'nome') conforme schema RFB
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_municipios_nome_trgm
    ON public.municipios USING gin (descricao gin_trgm_ops);

-- 5. Índice SOCIOS (além da PK inexistente)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_socios_cnpj_basico
    ON public.socios USING btree (cnpj_basico);

-- 6. ANALYZE nas tabelas afetadas
ANALYZE public.empresas;
ANALYZE public.estabelecimentos;
ANALYZE public.simples;
ANALYZE public.socios;
ANALYZE public.municipios;
ANALYZE public.cnaes;
ANALYZE public.motivos;
ANALYZE public.naturezas_juridicas;
ANALYZE public.paises;
ANALYZE public.qualificacoes;
