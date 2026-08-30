# Arquitetura V1 — Account Intelligence Agent

## Objetivo desta decisão

Conectar o esqueleto LangGraph já validado a fontes reais da web e a uma camada real de inteligência, preservando rastreabilidade, controle de custo e possibilidade de troca de fornecedores.

A V1 deve provar uma coisa: dado o nome de uma conta-alvo, o agente consegue pesquisar, distinguir evidência de hipótese, identificar gaps críticos e produzir um briefing comercial útil e auditável.

## Prioridade operacional da V1

Antes de qualquer outra conclusão comercial, o agente deve tentar descobrir **quais sistemas e tecnologias a conta-alvo realmente utiliza**.

Para empresas contábeis, separar quando possível:

1. sistema contábil/fiscal/folha/ERP usado na operação;
2. sistema usado para administrar a própria carteira de clientes e processos internos;
3. ERPs e plataformas recorrentes no ecossistema de clientes;
4. fornecedores tecnológicos dominantes ou com forte influência.

Se o sistema principal não puder ser confirmado com evidência pública, isso deve permanecer como **GAP CRÍTICO**, nunca como palpite apresentado como fato.

## Arquitetura escolhida para a V1

```text
Conta-alvo
   ↓
LangGraph
   ↓
analyze_target
   ├── identidade da empresa
   ├── domínio/site correto
   └── contexto mínimo para evitar homônimos
   ↓
plan_research
   ↓
SearchProvider
   ├── Exa — descoberta principal
   └── Brave — validação/complemento em etapa posterior
   ↓
entity_relevance
   ├── pertence à conta-alvo? → manter
   └── homônimo/ruído? → descartar
   ↓
ContentExtractor
   └── Firecrawl — etapa posterior
   ↓
extract_evidence
   ↓
LLMProvider
   └── OpenCode — etapa posterior
   ↓
analyze_account
   ↓
gap_analysis
   ├── gap pesquisável → gerar nova query → SearchProvider
   └── suficiente / limite → build_briefing
```

## Responsabilidades

### Exa

É o provedor principal de descoberta da V1.

Responsável por localizar fontes públicas relevantes com boa busca semântica, especialmente:

- site institucional;
- páginas de tecnologia e portais;
- vagas atuais e históricas;
- perfis profissionais públicos;
- notícias, entrevistas e eventos;
- parceiros e fornecedores;
- documentos e páginas que indiquem sistemas utilizados;
- sinais de stakeholders e decisores;
- sinais de oportunidades e problemas operacionais.

A Exa deve ficar atrás de uma abstração simples `SearchProvider`. Os nós do LangGraph não devem conhecer detalhes do SDK/API do fornecedor.

### Brave Search

Será uma segunda fonte de descoberta e validação, adicionada depois da integração inicial da Exa.

Sua função é complementar a busca semântica com pesquisa web ampla, termos exatos, conteúdo recente e validação cruzada.

Não faz parte da implementação da issue V1-02.

### Validação de relevância da entidade

Resultados de busca não são evidências automaticamente.

Antes de extrair uma afirmação, o sistema deve verificar se a fonte realmente se refere à conta-alvo. Homônimos e empresas com nomes muito semelhantes devem ser descartados.

Sinais úteis para validação:

- domínio oficial;
- nome empresarial/marca;
- cidade/endereço quando disponível;
- LinkedIn correto;
- CNPJ quando público e útil;
- contexto explícito da página.

Uma fonte tecnicamente relevante, mas sem relação comprovada com a conta-alvo, não pode sustentar uma conclusão sobre a conta.

### Firecrawl

Responsável, em etapa posterior, por obter e normalizar o conteúdo das páginas selecionadas para Markdown/texto limpo.

Criar uma interface simples `ContentExtractor` para permitir substituição futura.

Não usar crawling indiscriminado. Extrair somente URLs selecionadas pela etapa de pesquisa/ranking.

### OpenCode

Será a camada de inteligência da V1 em etapa posterior, evitando dependência obrigatória de uma conta separada da OpenAI API.

Responsabilidades esperadas:

- gerar e refinar consultas de pesquisa;
- extrair evidências estruturadas;
- classificar evidências;
- validar relação entre fonte e conta-alvo;
- identificar stakeholders e sinais tecnológicos;
- criar hipóteses de oportunidade;
- analisar gaps;
- decidir quando uma nova busca é justificável;
- sintetizar o briefing final.

Criar uma abstração `LLMProvider` para evitar espalhar chamadas específicas do executor/modelo pelos nós.

A forma programática exata de integração com OpenCode deve ser validada antes da issue correspondente; não assumir contrato HTTP/CLI sem teste.

## Princípio de evidência

O sistema deve distinguir explicitamente:

1. **FATO CONFIRMADO** — suportado diretamente por fonte pública relacionada à conta-alvo;
2. **INFERÊNCIA BASEADA EM EVIDÊNCIA** — conclusão plausível baseada em uma ou mais evidências;
3. **HIPÓTESE COMERCIAL** — possibilidade a investigar, não apresentada como realidade confirmada;
4. **GAP** — informação importante ainda não confirmada.

Nenhuma inferência ou hipótese deve ser apresentada como fato.

Cada evidência relevante deve manter, no mínimo:

- claim;
- URL da fonte;
- título da fonte;
- trecho/contexto utilizado;
- categoria;
- nível de confiança;
- data/publicação quando disponível;
- data da coleta;
- relação validada com a conta-alvo.

Para sinais de tecnologia, registrar quando possível:

- sistema/vendor;
- finalidade;
- evidência;
- confiança;
- recência/último sinal observado;
- classificação: confirmado, inferido ou hipótese.

## Estratégia de Gap Analysis

`gap_analysis` não deve simplesmente repetir pesquisas até atingir `max_loops`.

Deve decidir:

- quais gaps são relevantes para a missão comercial;
- quais gaps ainda podem ser pesquisados publicamente;
- qual estratégia de pesquisa ainda não foi tentada;
- qual nova consulta deve ser executada;
- quais gaps devem permanecer para descoberta comercial humana.

Gaps críticos típicos:

- ERP/sistema principal não confirmado;
- sistema usado para administrar a carteira não identificado;
- fornecedor tecnológico dominante desconhecido;
- decisor econômico não identificado;
- poder de veto não identificado;
- cadeia de aprovação desconhecida;
- sponsor não identificado;
- influência do fornecedor atual desconhecida.

O limite de loops continua existindo como guardrail de custo.

## Estratégias de pesquisa para um GAP de sistema

Se a primeira busca não confirmar o sistema utilizado, o agente deve mudar a estratégia em vez de apenas reformular a mesma consulta.

Exemplos de frentes:

- vagas e requisitos técnicos;
- perfis profissionais e histórico de funcionários;
- páginas de login e portais;
- subdomínios e URLs externas;
- PDFs, manuais, apresentações e materiais históricos;
- parceiros e páginas de integração;
- notícias e cases de fornecedores;
- páginas de ajuda/tutorial;
- menções antigas que possam revelar tecnologia ainda relevante.

O resultado final pode continuar sendo “não confirmado”. Isso é um resultado válido e deve gerar uma pergunta de descoberta comercial.

## Aprendizado dos testes manuais com Exa

Antes da integração, a Exa foi testada manualmente no modo Auto em duas contas conhecidas.

### BDO Brasil

A busca neutra conseguiu localizar evidência forte sobre uso do TOTVS Backoffice — Linha Protheus na operação de BPO/Controladoria, além de stakeholders relacionados. Também retornou resultados tecnicamente relacionados, porém não pertencentes à conta-alvo.

Aprendizado: a Exa tem alto valor de descoberta quando existe conteúdo público rico, mas exige filtro de relevância da entidade.

### Intercont Contabilidade Empresarial

Duas buscas neutras/focadas não conseguiram localizar publicamente o sistema conhecido externamente pelo usuário. A busca também retornou empresas com nomes semelhantes e páginas genéricas de ERP.

Aprendizado: Exa não deve ser tratada como fonte única nem como resposta final. Falha em localizar uma informação deve acionar Gap Analysis e mudança de estratégia/fonte, sem inventar conclusão.

## Guardrails iniciais de custo

Valores de configuração, não regras definitivas:

- máximo de 12 consultas web por conta;
- máximo de 30 páginas extraídas por conta;
- máximo de 3 ciclos de Gap Analysis;
- limite de tamanho de conteúdo enviado à camada de inteligência por página;
- deduplicação de URLs antes de extração;
- não reler a mesma URL durante a mesma pesquisa;
- registrar quantidade de buscas, páginas, chamadas de inteligência e métricas de custo/tokens quando disponíveis.

Os limites serão ajustados com base em pesquisas reais.

## Segurança e segredos

Chaves nunca entram no repositório.

Variáveis esperadas conforme as integrações forem sendo adicionadas:

```text
EXA_API_KEY
BRAVE_API_KEY
FIRECRAWL_API_KEY
```

OpenCode deve usar sua própria configuração/credenciais fora do repositório.

Fornecer apenas `.env.example` sem valores reais.

## Sequência incremental de implementação

1. **V1-02 — Exa:** busca real principal via `SearchProvider`.
2. **V1-03 — Brave:** segunda fonte para complemento/validação.
3. **V1-04 — Firecrawl:** extração limpa das páginas selecionadas.
4. **V1-05 — OpenCode:** interpretação, evidência estruturada e Gap Analysis real.
5. Executar pesquisa ponta a ponta em uma conta real conhecida e medir qualidade, custo e latência.

A ordem pode ser ajustada pela Governança se testes mostrarem necessidade, mas novas possibilidades não entram automaticamente na V1.

## Fora desta fase

Não implementar agora:

- banco de dados persistente;
- UI sofisticada;
- CRM;
- RAG;
- MCP;
- n8n;
- autenticação multiusuário;
- crawling massivo;
- roteamento complexo entre vários modelos;
- agentes de outras áreas da futura Fábrica de Agentes.

## Critério para avançar

Esta arquitetura estará validada quando o agente executar uma pesquisa real de ponta a ponta para uma conta-alvo, gerar evidências rastreáveis, descartar ruído de entidade, manter gaps honestos, realizar pesquisa iterativa quando justificável e entregar um briefing comercial útil sem ultrapassar os guardrails definidos.
