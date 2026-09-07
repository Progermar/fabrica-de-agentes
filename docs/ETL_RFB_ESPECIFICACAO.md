# Especificação Técnica - ETL RFB 08/2026

## 1. Objetivo

Definir o contrato técnico do novo ETL do Dexa Prospect para a base RFB 08/2026, com foco em:

- carga mensal determinística;
- controle transacional por ZIP;
- checkpoint e auditoria persistidos em PostgreSQL;
- filtragem de `estabelecimentos` por `situacao_cadastral = '02'`;
- filtro de `empresas`, `simples` e `socios` por conjunto ativo de `cnpj_basico`;
- portabilidade entre Windows, Docker/Hermes e futura VM Ubuntu/Teklamatik.

## 2. Escopo e não-escopo

### Incluído

- leitura streaming dos ZIPs da RFB;
- remoção de bytes `0x00` em streaming;
- decode Latin-1;
- parse CSV com `;`, aspas e sem header;
- carga em PostgreSQL com `COPY FROM STDIN`;
- checkpoint persistente em schema de controle;
- auditoria persistente em PostgreSQL;
- reconstrução determinística do estado após queda/reboot.

### Excluído

- implementação do ETL nesta missão;
- alterações em backend, frontend, schema atual, Docker ou Hermes;
- qualquer uso de SQLite ou arquivo local como fonte de verdade;
- qualquer dependência estrutural de Hermes;
- manipulação da tabela `usuarios` pelo ETL mensal.

## 3. Contrato de entrada RFB

Base validada pelo inspetor da missão anterior:

- 37 ZIPs relevantes;
- sem header;
- separador `;`;
- campos quoted;
- base tratada como Latin-1;
- 33 arquivos incompatíveis com UTF-8 / provável Latin-1;
- 4 arquivos ASCII puros;
- nenhum arquivo com evidência real de UTF-8 não-ASCII;
- `Estabelecimentos0.zip` contém exatamente 5 bytes `0x00`;
- demais 36 arquivos não possuem `0x00`.

Regra operacional:

- todos os arquivos são tratados de forma uniforme como Latin-1;
- bytes `0x00` devem ser removidos em streaming antes do parse CSV;
- não extrair arquivos permanentemente para disco;
- não gerar `.clean` gigantes.

Nota de auditoria:

- o inspector historico contava linhas fisicas usando bytes `\n`;
- a metrica oficial do ETL e a quantidade de registros produzidos pelo `csv.reader`;
- em `Estabelecimentos` 08/2026, o inspector registrou `72.789.645` linhas fisicas;
- o loader registrou `72.789.638` registros CSV logicos;
- a diferenca de `7` vem de `\n` internos em campos quoted.

## 4. Contrato de destino

O ETL deve respeitar o schema atual já validado.

Regras fixas:

- `capital_social` permanece `TEXT`;
- datas permanecem `TEXT`;
- `identificador_matriz_filial` mantém esse nome;
- códigos e identificadores continuam como `CHARACTER/TEXT`;
- não converter datas para `DATE` no ETL;
- não converter `capital_social` para `numeric`;
- preservar strings como `00000000` e zeros à esquerda;
- `usuarios` não faz parte da carga mensal da RFB.

## 5. Arquitetura do fluxo

Fluxo físico:

```text
Windows
→ valida checklist de ZIPs
→ lê ZIP em streaming
→ remove 0x00
→ decode Latin-1
→ parse CSV
→ filtra/converte mínimo necessário
→ COPY para PostgreSQL
→ validações por ZIP e por fase
→ pg_dump -Fc
→ transferência temporária para Hermes
→ futura migração para VM Ubuntu/Teklamatik
```

Princípio de portabilidade:

- tudo depende apenas de PostgreSQL, arquivos ZIP e Python;
- nenhuma etapa crítica depende do Hermes;
- o mesmo pacote deve rodar em Docker sem redesenho.

## 6. Pré-flight Operacional e Ordem das Fases

### 6.1 Gate obrigatório antes do primeiro `COPY`

Antes de qualquer carga, a execução deve validar e travar, em uma única decisão de preflight:

- PostgreSQL disponível;
- permissões necessárias;
- conexão de dados;
- conexão de controle;
- espaço livre em disco;
- espaço operacional suficiente para WAL;
- ausência de outra execução ativa da mesma competência;
- a carga mensal nova só pode começar em banco novo ou com todas as tabelas RFB de destino vazias;
- `usuarios` deve permanecer preservada e fora do ETL;
- nenhuma outra aplicação/processo pode escrever nas tabelas RFB durante a construção;
- competência solicitada corresponde aos ZIPs presentes;
- fingerprints dos ZIPs esperados registrados;
- tabelas RFB vazias para nova execução;
- `usuarios` existente e preservada quando aplicável.

Se qualquer item falhar, a execução deve retornar `PREFLIGHT OK = não` e não iniciar `COPY`.

A retomada da mesma execução é a única exceção à exigência de tabelas vazias.

O `etl_control` deve distinguir claramente entre:

- nova execução;
- retomada da mesma execução.

A aplicação não deve tratar um banco parcialmente carregado como base pronta.

### 6.2 Ordem das fases

1. Executar preflight operacional.
2. Criar ou reaproveitar a execução em `etl_control`.
3. Registrar `RUNNING` no controle e obter `execucao_id`.
4. Carregar tabelas auxiliares completas.
5. Carregar `estabelecimentos` com filtro `situacao_cadastral = '02'`.
6. Confirmar EOF, CRC e fingerprints de cada ZIP de `estabelecimentos`.
7. Registrar contagens finais da fonte e do destino.
8. Reconciliar e marcar `COMMITTED` somente após commit confirmado.
9. Reconstruir o bitset a partir de `estabelecimentos` reconciliados.
10. Carregar `empresas` filtrando pelo bitset.
11. Carregar `simples` filtrando pelo bitset.
12. Carregar `socios` filtrando pelo bitset.
13. Executar validações finais.
14. Criar índices pós-carga realmente necessários.
15. Gerar `pg_dump -Fc`.

## 7. Schema de controle

Todo o checkpoint e a auditoria ficam em PostgreSQL, em schema separado:

```sql
etl_control
```

### 7.1 Tabelas propostas

#### `etl_control.execucoes`

Fonte de verdade da execução mensal.

Campos mínimos:

- `execucao_id` UUID PK;
- `origem_diretorio` TEXT;
- `origem_fingerprint` TEXT;
- `status` TEXT (`PENDING`, `RUNNING`, `COMMITTED`, `FAILED`, `INCONSISTENT`);
- `inicio_em` TIMESTAMPTZ;
- `fim_em` TIMESTAMPTZ NULL;
- `host_nome` TEXT;
- `processo_pid` INT NULL;
- `git_commit` TEXT NULL;
- `competencia` TEXT NOT NULL;
- `origem_zip_base_dir` TEXT NOT NULL;
- `preflight_ok` BOOLEAN NOT NULL DEFAULT FALSE;
- `preflight_mensagem` TEXT NULL;
- `observacao` TEXT NULL.

#### `etl_control.checkpoints_arquivos`

Checkpoint corrente por ZIP dentro de uma execução.

Campos mínimos:

- `execucao_id` UUID FK;
- `ordem_execucao` INT;
- `fase` TEXT;
- `zip_tipo` TEXT;
- `zip_nome` TEXT;
- `arquivo_interno` TEXT;
- `tabela_destino` TEXT;
- `status` TEXT (`PENDING`, `RUNNING`, `COMMITTED`, `FAILED`, `INCONSISTENT`);
- `tentativa_numero` INT;
- `inicio_em` TIMESTAMPTZ NULL;
- `fim_em` TIMESTAMPTZ NULL;
- `source_records` BIGINT DEFAULT 0;
- `accepted_records` BIGINT DEFAULT 0;
- `discarded_records` BIGINT DEFAULT 0;
- `sent_to_copy_records` BIGINT DEFAULT 0;
- `newlines_fisicos` BIGINT NULL;
- `bytes_0x00_removidos` BIGINT DEFAULT 0;
- `checksum_sha256` TEXT NULL;
- `source_zip_size_bytes` BIGINT NULL;
- `source_member_size_bytes` BIGINT NULL;
- `source_member_crc32` TEXT NULL;
- `source_member_name` TEXT NULL;
- `source_eof_ok` BOOLEAN NOT NULL DEFAULT FALSE;
- `source_crc_ok` BOOLEAN NOT NULL DEFAULT FALSE;
- `source_fingerprint_ok` BOOLEAN NOT NULL DEFAULT FALSE;
- `tamanho_bytes_zip` BIGINT NULL;
- `tamanho_bytes_descompactado` BIGINT NULL;
- `mensagem_erro` TEXT NULL;
- `ultima_pulso_em` TIMESTAMPTZ NULL;
- `target_rowcount_before` BIGINT NULL;
- `expected_target_count_after` BIGINT NULL;
- `target_rowcount_after` BIGINT NULL.

Equivalência semântica dos contadores:

- `source_records` = `registros_csv_lidos`;
- `accepted_records` = `registros_aceitos`;
- `discarded_records` = `registros_descartados`;
- `sent_to_copy_records` = `registros_enviados_copy`.

Regras:

- existe uma linha corrente por ZIP por execução;
- a retomada da mesma execução reutiliza o mesmo `execucao_id`;
- uma nova execução sempre cria um novo `execucao_id`;
- o estado corrente é atualizado em place;
- histórico de transições vai para a auditoria.

#### `etl_control.auditoria_arquivos`

Registro imutável de eventos.

Campos mínimos:

- `auditoria_id` BIGSERIAL PK;
- `execucao_id` UUID;
- `zip_nome` TEXT;
- `arquivo_interno` TEXT;
- `fase` TEXT;
- `de_status` TEXT NULL;
- `para_status` TEXT;
- `evento_em` TIMESTAMPTZ;
- `mensagem` TEXT NULL;
- `registros_csv_lidos` BIGINT NULL;
- `registros_aceitos` BIGINT NULL;
- `registros_enviados_copy` BIGINT NULL;
- `registros_descartados` BIGINT NULL;
- `bytes_0x00_removidos` BIGINT NULL;
- `checksum_sha256` TEXT NULL;
- `duracao_ms` BIGINT NULL;
- `detalhe_json` JSONB NULL.

### 7.2 Estados permitidos

- `PENDING`
- `RUNNING`
- `COMMITTED`
- `FAILED`
- `INCONSISTENT`

Transições válidas:

- `PENDING -> RUNNING`
- `RUNNING -> COMMITTED`
- `RUNNING -> FAILED`
- `RUNNING -> INCONSISTENT`
- `FAILED -> RUNNING` (retry)

## 8. Transações

Regra absoluta:

- **1 ZIP = 1 transação de dados**.

### 8.1 Separação de conexões

Devem existir duas conexões lógicas distintas:

- conexão de dados: transação longa que faz `COPY`;
- conexão de controle: transações curtas para checkpoint e auditoria.

O controle nunca pode depender do rollback da transação de dados.

### 8.2 Sequência por ZIP

1. abrir ou retomar checkpoint `RUNNING` no controle;
2. registrar fingerprint e contagens iniciais esperadas quando disponíveis;
3. iniciar transação de dados;
4. ler ZIP inteiro em streaming;
5. aplicar filtro/transformação;
6. escrever via `COPY`;
7. validar EOF, CRC e contagens da fonte;
8. persistir no controle todas as evidências já conhecidas antes do commit;
9. executar `COMMIT` da transação de dados;
10. executar a prova pós-commit no PostgreSQL;
11. confirmar `COUNT(*) atual == expected_target_count_after`;
12. somente depois disso, gravar `etl_control.status = COMMITTED` em transação de controle separada;
13. registrar auditoria final.

Invariável absoluta:

- `COMMITTED` significa: a transação de dados foi confirmada e a prova pós-commit foi validada com sucesso.
- é proibido gravar `COMMITTED` apenas porque o `COMMIT` SQL retornou sucesso.

Janela de crash formal:

- se o crash ocorrer entre os passos 9 e 10, o estado pode permanecer `RUNNING`;
- na retomada, a decisão não é textual, é matemática e baseada em evidência do banco;
- nunca assumir sucesso apenas pelo status.

### 8.3 Regras de falha

Se ocorrer qualquer erro em:

- leitura ZIP;
- CSV;
- decode;
- conexão;
- PostgreSQL;
- falta de disco temporário;
- `COPY`;
- exceção Python;
- inconsistência de contagem.

então:

- a transação de dados deve sofrer `ROLLBACK`;
- o checkpoint deve ser gravado como `FAILED` em transação de controle separada;
- a mensagem de erro deve persistir.

## 9. Estratégia de checkpoint e retomada

### 9.1 Fonte de verdade

O PostgreSQL em `etl_control` é a fonte de verdade do estado.

### 9.2 Regra de retomada

Na retomada:

- `COMMITTED` é ignorado;
- `FAILED` é reiniciado desde o começo;
- `PENDING` continua normalmente;
- `RUNNING` é considerado estado pendente de reconciliação;
- `INCONSISTENT` bloqueia continuidade automática e exige auditoria.

### 9.3 Reconciliação matemática de `RUNNING`

Para cada ZIP, registrar pelo menos:

- `target_count_before`;
- `source_records`;
- `accepted_records`;
- `expected_target_count_after`.

Regra:

```text
expected_target_count_after = target_count_before + accepted_records
```

Na retomada de um ZIP em `RUNNING`:

- **CASO A**: `COUNT(*) atual == target_count_before`
  - interpretação: a transação de dados não foi confirmada;
  - marcar `FAILED`;
  - reprocessar o ZIP integralmente.

- **CASO B**: `COUNT(*) atual == expected_target_count_after`
  - interpretação: a transação de dados foi confirmada;
  - após validar também identidade/fingerprint da fonte e a prova pós-commit;
  - promover para `COMMITTED`;
  - não repetir o ZIP.

- **CASO C**: qualquer outro resultado
  - estado inconsistente;
  - não repetir automaticamente;
  - não promover;
  - parar a execução;
  - exigir auditoria/intervenção;
  - marcar `INCONSISTENT`.

O caso `INCONSISTENT` também deve ser usado quando:

- o fingerprint divergir;
- a CRC/EOF não bater;
- houver evidência contraditória entre controle e banco;
- não for possível provar com segurança se o ZIP foi carregado.

Essa regra depende obrigatoriamente de:

- destino inicialmente vazio;
- execução exclusiva;
- ausência de escritores concorrentes.

### 9.4 Persistência de `FAILED`

`FAILED` precisa permanecer gravado mesmo que a transação de dados tenha sido revertida.

Solução adotada:

- controle em conexão separada;
- gravação do estado `FAILED` fora da transação de dados;
- audit trail imutável em `etl_control.auditoria_arquivos`.

### 9.5 Estados e contenção concorrente

Execução concorrente da mesma competência deve ser impedida com lock nativo do PostgreSQL, preferencialmente `pg_advisory_lock`, adquirido no preflight e liberado no fim da execução.

### 9.6 Estratégia do bitset

- o bitset de CNPJs ativos é memória transitória da execução;
- ele não é fonte persistente de verdade;
- não deve ser reaproveitado após crash/reboot;
- depois que todos os ZIPs de `estabelecimentos` estiverem `COMMITTED` e reconciliados, reconstruir o bitset a partir da tabela `estabelecimentos`;
- como o ETL já importa somente situação `02`, o bitset pode ser reconstruído usando `cnpj_basico` da tabela;
- se qualquer ZIP de `estabelecimentos` ainda não estiver `COMMITTED`, não iniciar `empresas`, `simples` e `socios`.

## 10. Bitset de CNPJs ativos

### 10.1 Premissa validada

Microteste em `Empresas0-9`:

- 69.523.304 registros analisados;
- 100% com 8 caracteres;
- 100% numéricos;
- zero alfanuméricos;
- zero anomalias.

### 10.2 Modelo em memória

- bitset de 100.000.000 posições;
- custo aproximado: 12,5 MB;
- índice = inteiro do `cnpj_basico` de 8 dígitos;
- o valor textual original é preservado para o PostgreSQL.

### 10.3 Quando construir

O bitset é construído somente depois que todos os ZIPs de `estabelecimentos` estiverem `COMMITTED` e reconciliados.

### 10.4 Fonte de reconstrução

O bitset não é persistido como fonte primária.

Ele é reconstruído de forma determinística no restart a partir do PostgreSQL:

- streaming de `SELECT cnpj_basico FROM estabelecimentos WHERE situacao_cadastral = '02'`;
- marcação dos bits em RAM;
- nenhuma dependência externa ao banco.

Essa é a solução mais simples e segura porque:

- evita fonte secundária de verdade;
- mantém portabilidade;
- é determinística;
- funciona após queda ou reboot;
- não exige armazenar 100M bits fora do banco.

## 11. Algoritmo por tipo de arquivo

### 11.1 Tabelas auxiliares

Arquivos completos:

- `cnaes`
- `municipios`
- `motivos`
- `naturezas_juridicas`
- `paises`
- `qualificacoes`

Regra:

- importar todos os registros;
- preservar zeros à esquerda;
- preservar códigos textuais;
- sem header;
- Latin-1;
- `COPY` direto;
- checkpoint por ZIP.

### 11.2 `estabelecimentos`

Pipeline conceitual:

```text
ZIP
→ streaming
→ remover 0x00
→ decode Latin-1
→ csv.reader
→ validar quantidade exata de colunas
→ filtrar somente situacao_cadastral = '02'
→ descartar demais registros
→ COPY para PostgreSQL
```

Regra definitiva:

- **não filtrar por `motivo_situacao_cadastral`** no ETL;
- o motivo é preservado como dado bruto.
- o parser deve suportar campos quoted e newline dentro de campo quoted;
- qualquer registro estruturalmente inválido aborta o ZIP;
- campos vazios devem ser preservados conforme o contrato do schema.

### 11.3 `empresas`

- carregar somente linhas cujo `cnpj_basico` esteja presente no bitset de ativos;
- `cnpj_basico` é preservado textual;
- nenhuma outra filtragem de negócio.

### 11.4 `simples`

- carregar somente linhas cujo `cnpj_basico` esteja presente no bitset de ativos;
- campos preservados como texto.

### 11.5 `socios`

- carregar somente linhas cujo `cnpj_basico` esteja presente no bitset de ativos;
- preservar todos os campos brutos;
- sem normalização adicional.
- `socios` não possui primary key no schema atual; por isso, uma retomada de ZIP em `RUNNING` exige a mesma reconciliação matemática de contagem antes de qualquer retry.
- se `COUNT(*) == expected_target_count_after`, promover para `COMMITTED`;
- se `COUNT(*) == target_count_before`, marcar `FAILED` e repetir;
- qualquer outro resultado deve bloquear a execução com `INCONSISTENT`.

## 12. Mecanismo de carga

Abordagem obrigatória:

```text
Python
→ zipfile streaming
→ TextIOWrapper Latin-1
→ csv.reader
→ filtro/transformação mínima
→ buffer pequeno e contínuo
→ PostgreSQL COPY FROM STDIN
```

### 12.1 Estratégia de buffer

Recomendação:

- buffer por lote, não por arquivo completo;
- limite por lote em torno de 4 a 16 MiB, ou equivalente em linhas;
- flush frequente para não acumular milhões de linhas em RAM;
- nunca manter o ZIP inteiro em memória.

### 12.2 Regras de COPY

- usar `COPY ... FROM STDIN WITH (FORMAT csv, DELIMITER ';', QUOTE '"', ESCAPE '"')`;
- não usar `INSERT` linha a linha;
- respeitar campos vazios e aspas originais;
- não converter datas para tipos SQL no ETL;
- o buffer deve ser pequeno e contínuo, com flush frequente;
- a contagem oficial deve ser baseada em registros retornados pelo `csv.reader`, não em `\n`.

## 13. Validações obrigatórias

### 13.1 Por ZIP

- EOF real atingido;
- CRC do membro validado;
- SHA-256 do ZIP compactado registrado;
- tamanho do ZIP registrado;
- nome do membro interno registrado;
- tamanho do membro interno registrado;
- CRC32 do membro registrado;
- registros_csv_lidos contabilizados;
- registros_aceitos contabilizados;
- registros_descartados contabilizados;
- registros_enviados_copy contabilizados;
- bytes `0x00` contabilizados;
- `COPY` concluído;
- `COMMIT` confirmado.

Opcionalmente:

- `newlines_fisicos` podem ser registrados apenas como métrica técnica;
- nunca como prova oficial de quantidade de registros.

### 13.2 Por fase

- totais esperados vs carregados;
- checagem de PK/duplicatas quando aplicável;
- referências essenciais entre tabelas;
- apenas `situacao_cadastral = '02'` em `estabelecimentos`.

Para cada ZIP:

- `source_records = registros_aceitos + registros_descartados`;
- `registros_aceitos = registros_enviados_copy`;
- `expected_target_count_after = target_count_before + accepted_records`.

### 13.3 Validação SQL obrigatória

```sql
SELECT DISTINCT situacao_cadastral
FROM estabelecimentos;
```

Resultado esperado:

```text
02
```

### 13.4 Validação cruzada

Após carregar `empresas`:

- cada `cnpj_basico` carregado em `estabelecimentos` deve encontrar a empresa correspondente;
- inconsistências devem falhar a execução.

### 13.5 Prova pós-commit por ZIP

Depois de cada ZIP:

- consultar `COUNT(*)` da tabela destino;
- comparar com `expected_target_count_after`;
- somente considerar a carga consistente se `COUNT(*) == expected_target_count_after`.

Se o `COMMIT` dos dados funcionar, mas a prova pós-commit falhar:

- não marcar `FAILED`;
- marcar `INCONSISTENT`;
- parar a execução;
- não repetir automaticamente;
- exigir auditoria.

Para `estabelecimentos`:

- `registros_aceitos == registros_enviados_copy`;
- `registros_aceitos = registros_csv_lidos - registros_descartados`.

A prova acumulada só é válida porque:

- a tabela começou vazia;
- há somente uma execução;
- não há escritores externos.

## 14. Auditoria por arquivo

Cada ZIP precisa registrar, no mínimo:

- execução/id;
- tipo de arquivo;
- nome ZIP;
- nome do arquivo interno;
- status;
- início;
- fim;
- registros_csv_lidos;
- registros_aceitos;
- registros_descartados;
- registros_enviados_copy;
- target_count_before;
- expected_target_count_after;
- target_count_after;
- bytes `0x00` removidos;
- EOF real atingido;
- CRC validado;
- SHA-256 do ZIP compactado;
- tamanho do ZIP;
- nome do membro interno;
- tamanho do membro interno;
- CRC32 do membro;
- mensagem de erro, se houver;
- duração;
- checksum SHA-256 ou identificação equivalente.

Para `estabelecimentos`:

- `registros_aceitos == registros_enviados_copy` é obrigatório antes do `COMMIT`;
- `COUNT(*)` pós-commit deve fechar com `expected_target_count_after`.

## 15. Smokes tests

Além das validações quantitativas, prever smoke tests de registros conhecidos.

Regras:

- não hardcodear CNPJ sem encontrá-lo primeiro na base 08/2026;
- usar um canário histórico relacionado à Art Closet / Ana Paula de Sant Ana - ME apenas após descoberta real na base;
- confirmar:
  - empresa encontrada;
  - estabelecimento ativo encontrado;
  - joins funcionando;
  - filtros retornando o registro.

### 15.1 Caso histórico: metade do arquivo

Uma carga parcial não pode ser considerada válida porque:

- 1 ZIP = 1 transação;
- `COPY` interrompido não recebe `COMMIT`;
- EOF real é obrigatório;
- CRC é obrigatório;
- registros CSV são contabilizados;
- fingerprint é registrada;
- a contagem acumulada esperada é registrada;
- o `COUNT(*)` pós-commit precisa fechar;
- o checkpoint só vira `COMMITTED` após commit confirmado;
- `RUNNING` após crash é reconciliado matematicamente.

Se o novo ETL sofrer exatamente a mesma falha histórica e apenas metade de `Estabelecimentos0` for processada, as barreiras que impedem validação silenciosa são:

- rollback da transação de dados;
- `RUNNING` no controle;
- CRC inválido ou EOF não atingido;
- `source_records`/`accepted_records` inconsistentes;
- `COUNT(*) != expected_target_count_after`;
- ausência de promoção para `COMMITTED`.

O smoke test da Art Closet continua complementar, nunca único mecanismo de detecção.

## 16. Índices

### 16.1 Regra de timing

- não criar índices pesados durante a carga;
- criar tabelas;
- carregar e validar;
- somente depois criar índices.

### 16.2 Índices a preservar pós-carga

- `idx_estab_cnae_principal`
- `idx_estab_cnae_uf`
- `idx_estab_uf`
- `idx_estab_municipio`
- `idx_estab_cnpj_basico`
- `idx_estab_situacao`
- `idx_estab_motivo`
- `idx_empresas_razao`
- `idx_socios_cnpj_basico` se o join com `socios` continuar

### 16.3 Índices redundantes que não devem ser recriados

- `idx_estab_cnpj`
- `idx_empresas_cnpj_basico`
- `idx_municipios_codigo`
- `idx_simples_cnpj_basico`
- `idx_naturezas_juridicas_codigo`
- `idx_motivos_codigo`

### 16.4 Município e `unaccent`

A estratégia final do índice de município será tratada como decisão separada do backend/contrato de busca.

## 17. Ordem recomendada de carga das tabelas

1. `cnaes`
2. `municipios`
3. `motivos`
4. `naturezas_juridicas`
5. `paises`
6. `qualificacoes`
7. `estabelecimentos`
8. reconstrução do bitset de CNPJs ativos
9. `empresas`
10. `simples`
11. `socios`

## 18. Tratamento de erros

Qualquer erro em ZIP deve resultar em:

- `ROLLBACK` da transação de dados;
- checkpoint `FAILED` em controle;
- mensagem persistida;
- execução retomável.

Erros considerados críticos:

- ZIP corrompido;
- falha de leitura;
- falha de decode/parsing;
- falha de `COPY`;
- falha de commit;
- inconsistência de contagem;
- falta de espaço em disco temporário;
- queda do processo ou reboot no meio da execução.

## 19. Critérios de sucesso/falha

### Sucesso por ZIP

- status `COMMITTED`;
- EOF atingido;
- contagens fechadas;
- `COPY` concluído;
- commit confirmado;
- auditoria persistida.

### Falha por ZIP

- qualquer erro crítico;
- `FAILED` persistido;
- rollback de dados executado;
- retomada permitida sem ambiguidade.

### Sucesso da execução mensal

- todos os ZIPs planejados processados;
- apenas `estabelecimentos` com `situacao_cadastral = '02'`;
- bitset reconstruído e aplicado;
- validações finais aprovadas;
- backup `pg_dump -Fc` gerado.

## 20. Riscos conhecidos

- `Estabelecimentos0.zip` contém `0x00`; a limpeza em streaming é obrigatória.
- `RUNNING` pode ficar pendente se houver queda entre commit de dados e commit do controle; a reconciliação por contagem resolve o caso.
- `COPY` em grandes arquivos exige buffer curto e flush frequente.
- `unaccent` no índice de município exige decisão técnica separada da implementação do ETL.
- índices redundantes da schema atual não devem ser recriados durante a carga.

### 20.1 Matriz de falhas

| cenário | estado dos dados | estado esperado do checkpoint | ação na retomada | risco residual |
|---|---|---|---|---|
| ZIP corrompido | nada confirmado | `FAILED` | reiniciar ZIP após corrigir fonte | baixo |
| arquivo interno truncado | nada confirmado | `FAILED` | reiniciar ZIP | baixo |
| byte inválido | nada confirmado | `FAILED` | reiniciar ZIP | baixo |
| registro CSV inválido | nada confirmado | `FAILED` | reiniciar ZIP | baixo |
| `0x00` | removido em streaming | `COMMITTED` se contagens fecharem | manter auditoria | baixo |
| falta de espaço | rollback ou abort | `FAILED` | liberar espaço e reiniciar | médio |
| PostgreSQL indisponível | nenhum commit válido | `RUNNING` ou `FAILED` reconciliado | reconciliar e reiniciar | médio |
| processo Python encerrado | rollback se antes do commit | `RUNNING` | reconciliar matematicamente | alto se não houver prova pós-commit |
| reboot Windows | estado depende do ponto de queda | `RUNNING`/`FAILED`/`COMMITTED` | reconciliar pelo banco | alto |
| Docker reiniciado | igual a queda de conexão | `RUNNING` | reconciliar pelo banco | médio |
| `COPY` interrompido | rollback | `FAILED` | reiniciar ZIP | baixo |
| commit falha | dados não devem ser considerados confirmados | `FAILED` | reiniciar ZIP | médio |
| commit funciona mas prova pós-commit falha | dados confirmados, prova pendente ou inválida | `INCONSISTENT` | parar e exigir auditoria | alto |
| crash entre commit dos dados e prova pós-commit | dados confirmados, checkpoint ainda `RUNNING` | `RUNNING` | reconciliar matematicamente | alto |
| checkpoint atualizado mas processo cai imediatamente | dados confirmados e prova já validada | `COMMITTED` | validar e seguir | baixo |
| retomada após `RUNNING` abandonado | indeterminado até prova | `RUNNING` | reconhecer `target_count_before` vs `expected_target_count_after` | alto se destino não estiver vazio |

## 21. Decisões já fechadas

- nova execução exige banco novo ou tabelas RFB vazias;
- retomada da mesma execução é a única exceção;
- preflight operacional obrigatório antes do primeiro `COPY`;
- contenção concorrente por lock nativo do PostgreSQL (`pg_advisory_lock`);
- checkpoint e auditoria em PostgreSQL, schema `etl_control`;
- sem SQLite e sem arquivo local como fonte de verdade;
- sem header;
- Latin-1 para todos os arquivos;
- `0x00` removido em streaming;
- `estabelecimentos` apenas com `situacao_cadastral = '02'`;
- `motivo_situacao_cadastral` preservado bruto;
- `capital_social` como `TEXT`;
- datas como `TEXT`;
- `identificador_matriz_filial` preservado;
- `usuarios` fora do ETL.

## 22. Pontos que ainda exigem decisão antes da implementação

Nenhum ponto bloqueante adicional para implementar o ETL foi identificado nesta especificação.

## 23. Status final

**ESPECIFICAÇÃO PRONTA PARA IMPLEMENTAÇÃO**
