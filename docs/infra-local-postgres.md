# PostgreSQL Local do Dexa Prospect

Banco dedicado para o Dexa Prospect, separado do PostgreSQL 16 instalado no Windows.

## Valores

- host: `127.0.0.1`
- porta: `5433`
- database: `dexaprospect`
- user: `dexaprospect_app`
- volume: `dexa_prospect_postgres_data`

## Subir

```powershell
docker compose --env-file .env.local -f docker-compose.db.yml up -d
```

## Parar sem destruir dados

```powershell
docker compose --env-file .env.local -f docker-compose.db.yml down
```

## Observações

- `.env.local` fica fora do Git.
- Não usar `docker compose down -v` no fluxo normal.
- O PostgreSQL do Windows em `127.0.0.1:5432` não é destino deste projeto.
