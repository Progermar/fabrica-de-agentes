# ETL RFB - Fundacao

Comandos iniciais:

```bash
python -m etl.cli preflight --competencia 2026-08 --source-dir "D:\\Dados 14032026\\Projetos\\fabrica-de-agentes\\cnpj\\08-2026"
```

O preflight:

- descobre ZIPs RFB esperados;
- calcula fingerprint SHA-256 e metadados do membro interno;
- valida schema de controle `etl_control`;
- trava concorrencia por competencia;
- checa se o banco esta vazio para nova execucao;
- nao inicia carga.
