# Fábrica de Agentes

Plataforma interna para criação rápida, governada e reutilizável de agentes especializados de IA.

A proposta é começar resolvendo uma necessidade real da própria Teklamatik e, a partir da arquitetura validada, transformar a fábrica em uma nova capacidade interna e potencial linha de produtos e serviços para o mercado.

## Missão

Construir uma Fábrica de Agentes cuja primeira V1 seja um **Agente de Inteligência de Contas** capaz de:

> Levantar tudo o que for publicamente possível sobre uma conta-alvo, identificar decisores e influenciadores, mapear gaps de informação, descobrir oportunidades reais para o portfólio da Teklamatik e preparar o vendedor para construir rapport e conduzir a estratégia comercial.

## Agente #001 — Account Intelligence Agent

### Problema central

A pesquisa comercial atual é limitada e pode deixar lacunas críticas na compreensão de uma conta, inclusive sobre decisores, influenciadores, poder de veto, stack tecnológica e oportunidades reais de negócio.

Informações não encontradas não devem ser inventadas. Devem permanecer explicitamente registradas como **GAP comercial** a ser trabalhado pelo vendedor durante o relacionamento com a conta.

### Usuário inicial

Vendedor técnico/comercial da Teklamatik preparando-se para reuniões com contas-alvo, inicialmente com foco em escritórios contábeis de médio e grande porte.

A arquitetura deverá permitir posteriormente adaptar o agente para pesquisa e qualificação de contas em outros nichos.

## V1 esperada

A V1 recebe a identificação de uma empresa-alvo e produz um briefing comercial auditável contendo, quando houver evidência pública disponível:

1. **Perfil da conta**
   - empresa, atuação, porte e localização;
   - segmentos atendidos;
   - estrutura e movimentos relevantes;
   - notícias, conteúdos e acontecimentos úteis para contexto comercial.

2. **Stakeholder Intelligence**
   - decisores;
   - influenciadores;
   - patrocinadores potenciais;
   - decisor econômico;
   - poder de veto;
   - cadeia provável de decisão.

3. **Technology / Stack Discovery**
   - ERP e sistemas corporativos identificados;
   - sistemas usados pelo escritório para administrar sua operação/carteira;
   - portais, plataformas, automações e fornecedores tecnológicos;
   - evidência e nível de confiança para cada inferência.

4. **Opportunity Discovery**
   - hipóteses de dores e necessidades;
   - oportunidades aderentes ao portfólio Teklamatik;
   - inicialmente considerar Radar, RAG, agentes de IA, integrações/automações, infraestrutura, data center e suporte.

5. **Rapport e estratégia comercial**
   - fatos relevantes para abertura de conversa;
   - pontos de rapport profissional;
   - perguntas de descoberta;
   - riscos comerciais;
   - próximas ações sugeridas.

6. **GAP Analysis**
   - informações estratégicas não encontradas;
   - criticidade do gap;
   - o que deve ser descoberto comercialmente;
   - prioridade para a próxima interação com a conta.

7. **Rastreabilidade**
   - fontes consultadas;
   - evidências associadas às conclusões relevantes;
   - distinção clara entre fato encontrado, inferência e informação não confirmada.

## Princípios da V1

- Não inventar informações ausentes.
- Toda inferência relevante deve possuir nível de confiança e evidência.
- Informação crítica não encontrada deve virar GAP.
- O agente apoia o vendedor; não substitui o trabalho de relacionamento.
- Pesquisa deve ser profunda o suficiente para apoiar uma reunião real, mas possuir guardrails de custo e tempo.
- Arquitetura deve permitir troca de provedores de busca e LLM sem reconstruir o agente.
- LangGraph será usado onde estado, iteração, decisões condicionais e análise de gaps justificarem sua utilização.
- Evitar overengineering: primeiro validar uma V1 funcional.

## Critério de sucesso da V1

A missão da V1 estará cumprida quando, a partir de uma conta-alvo real, o agente conseguir produzir automaticamente um briefing utilizável antes de uma reunião comercial que:

- revele informações relevantes que uma pesquisa comercial rasa normalmente não entregaria;
- apresente stakeholders e possíveis decisores com evidências;
- tente descobrir a stack tecnológica da conta;
- identifique oportunidades plausíveis para a Teklamatik;
- forneça pontos úteis de rapport;
- apresente claramente os gaps ainda não resolvidos;
- permita ao vendedor saber **o que já sabemos, o que apenas inferimos e o que ainda precisamos descobrir**;
- mantenha fontes suficientes para auditoria das informações.

## Fora da V1

A primeira versão não precisa incluir:

- CRM completo;
- automação de cadência comercial;
- múltiplos agentes de outros departamentos;
- auditoria de estações de trabalho;
- interface sofisticada;
- arquitetura definitiva para escala;
- todas as integrações futuras da fábrica.

Esses itens poderão ser avaliados depois que o Agente #001 comprovar valor em uso real.

## Papéis no desenvolvimento

- **Produto / decisão de negócio:** Rogério
- **Governança e arquitetura:** camada de governança do projeto
- **Execução técnica:** Mimo / OpenCode
- **Fonte persistente de verdade:** este repositório

## Estado atual

Projeto iniciado. Repositório criado e missão da V1 consolidada. Próximo passo: definir a arquitetura mínima e implementar o primeiro fluxo executável do Agente #001.
