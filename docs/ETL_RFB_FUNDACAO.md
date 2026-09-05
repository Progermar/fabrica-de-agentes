# ETL RFB - Fundacao

Comandos iniciais:

```bash
$env:DB_PASS = "<senha-fornecida-pelo-ambiente>"
python -m etl.cli preflight --competencia 2026-08 --source-dir "D:\\Dados 14032026\\Projetos\\fabrica-de-agentes\\cnpj\\08-2026"
```

O preflight:

- descobre ZIPs RFB esperados;
- calcula fingerprint SHA-256 e metadados do membro interno;
- nao faz `testzip()` nem leitura integral do membro para validar EOF/CRC;
- valida schema de controle `etl_control`;
- trava concorrencia por competencia;
- checa se o banco esta vazio para nova execucao;
- nao inicia carga.

Host, porta, database e usuario aceitam CLI ou `DB_*`, com CLI prevalecendo.
A senha vem somente de `DB_PASS` e nunca e exibida pela CLI.
EOF/CRC do membro serao validados durante o processamento streaming, nao no preflight.
