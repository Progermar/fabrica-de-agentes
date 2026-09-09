# GOLDEN CASE — TEKLAMATIK SISTEMAS DE GESTAO EMPRESARIAL LTDA

**Data:** 2026-09-09
**Status:** VALIDADO EM TESTE LIVE CONTROLADO
**Versão do agente:** Account Intelligence (Live)
**CNPJ de referência:** 42.473.600/0001-17

---

## Configuração da Execução

| Parâmetro | Valor |
|-----------|-------|
| Empresa-alvo | TEKLAMATIK SISTEMAS DE GESTAO EMPRESARIAL LTDA |
| Search Provider | Exa (`ExaSearchProvider`) |
| LLM Provider | OpenCode (`OpenCodeProvider`) |
| Modelo | opencode/mimo-v2.5-free |
| Loops | 2 |
| Custo Exa | $0.0420 |
| Custo LLM | $0.0000 |
| Tempo Total | 317.74s |

---

## Métricas de Execução

| Métrica | Valor |
|---------|-------|
| Requisições de busca Exa | 6 |
| Custo Exa total | $0.0420 |
| Chamadas LLM | 6 |
| Custo LLM total | $0.0000 |
| Fontes consultadas | 14 |
| Evidências coletadas | 36 |
| Fatos confirmados | 36 |
| Inferências | 0 |
| Hipóteses | 0 |
| Gaps de evidência | 0 |
| Gaps estratégicos | 7 |

---

## Briefing Final Completo

```text
============================================================
BRIEFING DE INTELIGENCIA DE CONTA
Empresa-alvo: TEKLAMATIK SISTEMAS DE GESTAO EMPRESARIAL LTDA
============================================================

1. PERFIL DA CONTA
  - Empresa: TEKLAMATIK SISTEMAS DE GESTAO EMPRESARIAL LTDA
  - Fontes relevantes encontradas: 9
    * Produtos - Radar Empresarial - Teklamatik (https://teklamatik.com.br/solucoes/software-gestao-wkradar)
    * Linha Radar Empresarial - Teklamatik (https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial)
    * Teklamatik Serviços (https://linkedin.com/company/teklamatik)
    * Sobre a Empresa - Teklamatik (https://teklamatik.com.br/sobre-a-empresa)
    * Validação de Selos de Certificação e Classificação de Canais | WK (https://canais.wk.com.br/validacao/40167)

2. STAKEHOLDER INTELLIGENCE
  - [GAP]     name: Não identificado
    role: Diretoria/Proprietário
    influence: Não foi possível identificar nomes de decisores nas fontes fornecidas
    evidence: Nenhuma menção a nomes de dirigentes nas evidências coletadas
  - [INFERENCIA]     name: Equipe de Consultores de Implantação
    role: Implantação de ERP WK Radar em clientes
    influence: Alta — contato direto com clientes, podem influenciar decisões de manutenção/expansão de contratos
    evidence: Vaga publicada em 2026 para Consultor(a) de Implantação de ERP com conhecimento nos módulos de Controladoria, Fiscal e Financeiro.
    source_url: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e

3. TECHNOLOGY / STACK DISCOVERY
  - [FATO CONFIRMADO]     technology: WK Radar ERP
    purpose: ERP completo para gestão empresarial (Vendas, Finanças, Materiais, Produção, Custos, Serviços, Controladoria, RH, GED, BI, Qualidade)
    evidence: Teklamatik é revenda dos produtos WK-Radar para o estado de São Paulo. Parceria de 30 anos com a WK-Sistemas.
    confidence: alta
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: Radar Web (módulo WK Radar)
    purpose: Acesso remoto via internet para lançamentos contábeis, financeiros, estoque, MTFiscal, cadastro de pedidos por representantes e cotações com fornecedores
    evidence: Radar Web permite lançamentos (Contábil, Financeiro, Estoque e MTFiscal) via internet. Representantes cadastram pedidos on-line.
    confidence: alta
    source_url: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
  - [FATO CONFIRMADO]     technology: Metodologia TECSAD
    purpose: Metodologia exclusiva de implantação de Sistemas Administrativos
    evidence: Metodologia exclusiva TECSAD - Tecnologia de Implantação de Sistemas Administrativos.
    confidence: alta
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: HubSpot
    purpose: CRM / Marketing Automation
    evidence: Tech Stack listada no LinkedIn inclui hubspot.
    confidence: media
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: RD Station
    purpose: Marketing Automation / Geração de leads
    evidence: Tech Stack listada no LinkedIn inclui rd station.
    confidence: media
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: Snovio
    purpose: Prospecção de leads / Busca de contatos corporativos
    evidence: Tech Stack listada no LinkedIn inclui snovio.
    confidence: media
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: Linux / Windows 10
    purpose: Infraestrutura de TI
    evidence: Tech Stack listada no LinkedIn inclui linux e windows 10.
    confidence: media
    source_url: https://linkedin.com/company/teklamatik
  - [FATO CONFIRMADO]     technology: JSON / Publica
    purpose: Integrações ou ferramentas auxiliares
    evidence: Tech Stack listada no LinkedIn inclui json e publica.
    confidence: baixa
    source_url: https://linkedin.com/company/teklamatik

4. OPPORTUNITY DISCOVERY
  - [INFERENCIA]     description: RAG / Agentes de IA para suporte e knowledge base dos 1000+ clientes do WK Radar
    alignment: Forte — Teklamatik atende 1000+ clientes com ERP WK Radar e oferece suporte técnico. Um sistema RAG com base de conhecimento do WK Radar poderia automatizar respostas a dúvidas frequentes de parametrização, módulos e processos, reduzindo custo de suporte.
    evidence: Carteira ativa com mais de 1.000 clientes atendidos diariamente. Soluções incluem Suporte Técnico e Help Desk/Service Desk. Metodologia TECSAD foca em treinamento de usuários.
    priority: alta
    source_url: https://teklamatik.com.br/sobre-a-empresa
  - [HIPOTESE]     description: Automação de processos (n8n/workflows) para fluxos de implantação e suporte
    alignment: Médio-Alto — A metodologia TECSAD e o processo de implantação ponta a ponta podem se beneficiar de automação de workflows para padronizar e acelerar entregas.
    evidence: Metodologia TECSAD para implantação. Contratação de consultores de implantação. Processo descrito como 'conduzir implantações de ERP ponta a ponta, levantar e mapear processos, parametrizar sistemas e treinar usuários'.
    priority: media
    source_url: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
  - [INFERENCIA]     description: Integrações via API entre WK Radar e outros sistemas dos clientes
    alignment: Médio — WK Radar já possui 'Tecnologia de integração com outros sistemas' como diferencial. Oferecer serviço de integração via API pode ser extensão natural da consultoria.
    evidence: Diferenciais do WK Radar incluem 'Tecnologia de integração com outros sistemas'. Radar Web permite lançamentos e cotações integradas via internet.
    priority: media
    source_url: https://teklamatik.com.br/solucoes/software-gestao-wkradar
  - [INFERENCIA]     description: Infraestrutura de TI / Data Center como extensão dos serviços atuais
    alignment: Médio — Teklamatik já oferece Infraestrutura/Cabeamento Estruturado e Gerenciamento da Internet como serviços.
    evidence: Soluções de consultoria incluem: Suporte Técnico, Infraestrutura/Cabeamento Estruturado, Projetos de TI, Help Desk/Service Desk e Gerenciamento da Internet.
    priority: baixa
    source_url: https://teklamatik.com.br/servicos/consultoria
  - [INFERENCIA]     description: Suporte a estações de trabalho / manutenção de hardware
    alignment: Baixo — Já fazem parte do portfólio atual. Menor potencial de novidade comercial.
    evidence: Empresa oferece suporte remoto e presencial com profissionais especializados e certificados.
    priority: baixa
    source_url: https://teklamatik.com.br/servicos/consultoria

5. RAPPORT E ESTRATEGIA COMERCIAL
  Pontos de rapport:
  - Parceria de 30 anos com WK Sistemas: A parceria de 30 anos com a WK é impressionante. Como vocês avaliam a evolução dessa relação ao longo das décadas e o que garante essa fidelidade?
  - Metodologia TECSAD: Como a metodologia TECSAD evoluiu desde a sua criação? Vocês sentem que ela é um diferencial competitivo real no mercado?
  - Reforma Tributária e preparação do WK Radar: A preparação do WK Radar para a Reforma Tributária gerou muito trabalho interno? Como vocês estão comunicando isso aos clientes?
  - Contratação de consultores de implantação: Vi que vocês estão contratando consultores de implantação. Isso reflete crescimento da demanda ou uma estratégia de renovação da equipe?
  - Parceria com Cohab-SP: Como foi a experiência com a Cohab-SP? Vocês buscam mais projetos com órgãos públicos ou prefere o mercado privado?

  Perguntas de descoberta:
  - Qual é o perfil predominante dos seus 1000+ clientes em termos de porte e segmento?
  - Como vocês organizam a equipe de suporte e implantação para atender essa base de clientes?
  - Vocês utilizam o WK Radar internamente para a gestão da Teklamatik ou usam outro sistema?
  - Quais são os principais desafios que seus clientes enfrentam na implantação e uso do ERP?
  - Como está a demanda por novas implantações versus manutenção/expansão de contratos existentes?
  - VocêsConsideram expandir a carteira de produtos além do WK Radar ou prefere concentração?
  - Como funciona o processo de decisão quando um cliente precisa adquirir novos módulos ou funcionalidades?

  Riscos comerciais:
  - Risco de concentração de receita: empresa é revenda exclusiva de um único produto (WK Radar) — dependência total do ecossistema WK Sistemas
  - Risco de porte: 10-20 funcionários em declínio (-2-3% YoY) — empresa pequena com capacidade limitada de investimento em novas tecnologias
  - Risco de obsolescência: WK Radar é um ERP de longa data (desde 1984) — pode enfrentar pressão de ERPs modernos, cloud-native e SaaS
  - Risco de canibalização: soluções de IA/automação podem reduzir a necessidade de consultoria humana de implantação e suporte, que é o core da receita
  - Dependência geográfica: atuação focada em SP (com presença menor no RJ) — mercado limitado comparado a players nacionais

  Proximas acoes sugeridas:
  - Realizar busca específica na JUCESP com query site: para identificar quadro societário
  - Pesquisar faturamento em bases de dados financeiras com CNPJ da empresa
  - Analisar cases publicados no site para mapear segmentos de clientes atendidos
  - Agendar discovery call focada em: (1) identificar decisor econômico, (2) entender cadeia de aprovação, (3) mapear dores de suporte e implantação que possam ser endereçadas por IA/automação
  - Verificar se existem Reviews/Reclamações da empresa no Reclame Aqui ou Google para entender percepção de mercado
  - Avaliar se a queda de funcionários (-2-3% YoY) é sinal de problema ou reestruturação estratégica

6. GAP ANALYSIS
  -     description: Decisor econômico (sócio, diretor ou presidente) não identificado — a query anterior sobre decisores não retornou resultados
    criticality: alta
    discovery_action: Consulta direta à JUCESP via portal oficial (não genérica), busca por CNPJ específico em bases de dados, ou abordagem via LinkedIn buscando perfis com cargo de diretor/sócio na empresa
    priority_for_next_interaction: 1
  -     description: Faturamento/Receita da empresa não estimado — porte financeiro desconhecido, impossível classificar capacidade de investimento
    criticality: alta
    discovery_action: Consulta a bases de dados de intelligence comercial com CNPJ específico (Serasa Empresas, Economática, QSA) ou estimativa via número de funcionários e ticket médio de mercado
    priority_for_next_interaction: 2
  -     description: Cadeia de aprovação para decisão de compra de novas soluções/tecnologia internamente desconhecida
    criticality: alta
    discovery_action: Identificar se empresa participou de licitações públicas como licitante (não como fornecedor) para entender processo decisório; ou directly pergunta em discovery call
    priority_for_next_interaction: 2
  -     description: Segmentos de clientes atendidos não detalhados — quais vertical markets predominam na carteira de 1000+ clientes?
    criticality: media
    discovery_action: Análise de cases publicados no site, depoimentos de clientes ou perfis de clientes mencionados em redes sociais
    priority_for_next_interaction: 3
  -     description: Reputação e satisfação de clientes não avaliada — não há dados de reclamações, reviews ou NPS
    criticality: media
    discovery_action: Consulta ao Reclame Aqui, Google Reviews, ou plataformas de avaliação de empresas
    priority_for_next_interaction: 3
  -     description: Estrutura interna de TI da própria Teklamatik — qual ERP usam para gestão administrativa/financeira interna?
    criticality: baixa
    discovery_action: Pergunta direta em call ou análise de evidências indiretas
    priority_for_next_interaction: 4
  -     description: Ticket médio de implantação e receita por cliente — não há dados financeiros por contrato
    criticality: baixa
    discovery_action: Estimativa via mercado de ERP WK Radar ou pergunta direta em call
    priority_for_next_interaction: 4

7. FONTES E RASTREABILIDADE
  Fontes consultadas: 14
    - https://teklamatik.com.br/solucoes/software-gestao-wkradar
    - https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
    - https://linkedin.com/company/teklamatik
    - https://teklamatik.com.br/sobre-a-empresa
    - https://canais.wk.com.br/validacao/40167
    - https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
    - https://teklamatik.com.br/servicos
    - https://teklamatik.com.br/servicos/consultoria
    - https://empresas.serasaexperian.com.br/
    - https://cnpja.com/
    - https://www.jucesponline.sp.gov.br/BuscaAvancada.aspx
    - https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/novo-pregao-eletronico/perguntas-e-respostas
    - https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
    - https://www.catho.com.br/vagas/analista-de-implantacao-de-erp/36181296/?entrada_apply=direto&origem_apply=vagas-similares

  Requisicoes de busca realizadas: 6
  Custo estimado das buscas: $0.0420

  Chamadas de LLM realizadas: 6

  Evidencias coletadas: 36
    - Fatos confirmados: 36
    - Inferencias: 0
    - Hipoteses: 0
    - Gaps de informacao: 0

  Fatos confirmados:
    * [stack] A WK desenvolveu o WK Radar, um ERP completo que integra áreas como Vendas, Finanças, Materiais, Produção, Custos, Serviços, Controladoria, RH, GED, BI e Qualidade
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar
    * [perfil] O WK Radar atende indústria, comércio e prestadores de serviços
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar
    * [stack] Diferenciais incluem comunicação integrada entre filiais, integração total, interface amigável, tecnologia de integração com outros sistemas, gerenciamento web, integração com Excel e atendimento à legislação fiscal
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar
    * [perfil] A empresa possui escritórios em SP e RJ com contatos distintos
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar
    * [perfil] A linha Radar Empresarial atende empresas de pequeno a grande porte, incluindo comércio, indústria, prestadoras de serviços, escritórios contábeis, escolas e empresas do ramo da saúde
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
    * [stack] A WK Sistemas opera com modelo de ofertas verticais (pré-definidas por segmento) e ofertas modulares (personalizadas)
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
    * [perfil] Três segmentos de mercado atendidos por ofertas verticais: Indústrias de Transformação, Comércio Varejista e Atacadista e Empresas Contábeis
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
    * [stack] A implantação utiliza metodologia exclusiva com pré-configurações de bases populadas para reduzir tempo e custos
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
    * [perfil] Teklamatik é revenda dos produtos WK-Radar para o estado de São Paulo, com parceria de 30 anos com a WK-Sistemas
      Fonte: https://linkedin.com/company/teklamatik
    * [perfil] Empresa fundada em 1984, com 17 funcionários (redução de 1 pessoa YoY)
      Fonte: https://linkedin.com/company/teklamatik
    * [perfil] Mais de 28 anos atendendo empresas de diversos setores, com foco em áreas administrativas e contábeis
      Fonte: https://linkedin.com/company/teklamatik
    * [stack] Metodologia exclusiva TECSAD - Tecnologia de Implantação de Sistemas Administrativos
      Fonte: https://linkedin.com/company/teklamatik
    * [stack] Tech Stack identificada: snovio, rd station, hubspot, publica, json, linux, windows 10
      Fonte: https://linkedin.com/company/teklamatik
    * [oportunidade] Empresa está contratando Consultor(a) de Implantação de ERP com preferência por vivência com WK Radar e conhecimento em módulos de Controladoria, Fiscal e Financeiro
      Fonte: https://linkedin.com/company/teklamatik
    * [oportunidade] Parceria com Cohab-SP apresentada em 2022 para gestão integrada
      Fonte: https://linkedin.com/company/teklamatik
    * [stack] ERP WK Radar já está preparado para a Reforma Tributária (publicação de 2026)
      Fonte: https://linkedin.com/company/teklamatik
    * [perfil] Visão empresarial: 'Simplificar e solucionar as necessidades de gestão de nossos clientes'
      Fonte: https://teklamatik.com.br/sobre-a-empresa
    * [perfil] Mais de 5.000 sistemas de gestão implantados ao longo de mais de 25 anos de atuação
      Fonte: https://teklamatik.com.br/sobre-a-empresa
    * [perfil] Carteira ativa com mais de 1.000 clientes atendidos diariamente
      Fonte: https://teklamatik.com.br/sobre-a-empresa
    * [stack] WK Sistemas exige certificação anual dos técnicos dos canais parceiros, com revalidação obrigatória
      Fonte: https://teklamatik.com.br/sobre-a-empresa
    * [perfil] Filosofia: 'Sempre trabalhar com ética e comprometimento junto aos nossos clientes'
      Fonte: https://teklamatik.com.br/sobre-a-empresa
    * [perfil] Teklamatik é canal certificado da WK Sistemas com razão social TEKLAMATIK SISTEMAS DE GESTAO EMPRESARIAL LTDA, município São Paulo/SP
      Fonte: https://canais.wk.com.br/validacao/40167
    * [perfil] WK Sistemas é empresa de Blumenau (SC), desde 1984, com mais de 100 mil cópias comercializadas, 60+ canais ativos e 7 mil+ empresas usuárias
      Fonte: https://canais.wk.com.br/validacao/40167
    * [stack] Radar Web permite lançamentos contábeis, financeiros, estoque e MTFiscal via internet, com acesso à base de dados remota
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
    * [stack] Representantes podem cadastrar pedidos via web on-line diretamente na base de dados, sem necessidade de notebooks ou palms
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
    * [stack] Sistema permite cotações de preços pela Internet com fornecedores via link seguro por e-mail
      Fonte: https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
    * [perfil] Canal de contato via WhatsApp disponível: (11) 2206-7051
      Fonte: https://teklamatik.com.br/servicos
    * [perfil] Endereço: Alameda Santos, 1165 - Jardim Paulista, São Paulo - SP, 01419-002
      Fonte: https://teklamatik.com.br/servicos
    * [stack] Soluções de consultoria incluem: Suporte Técnico, Infraestrutura/Cabeamento Estruturado, Projetos de TI, Help Desk/Service Desk e Gerenciamento da Internet
      Fonte: https://teklamatik.com.br/servicos/consultoria
    * [perfil] Horário de atendimento: segunda a sexta, 8:30h às 18:00h
      Fonte: https://teklamatik.com.br/servicos/consultoria
    * [stack] Empresa oferece suporte remoto e presencial com profissionais especializados e certificados
      Fonte: https://teklamatik.com.br/servicos/consultoria
    * [perfil] Teklamatik tem entre 10-20 funcionários, com declínio de 2-3% YoY
      Fonte: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
    * [oportunidade] Vaga publicada em abril de 2026 para Consultor(a) de Implantação de ERP — CLT efetivo
      Fonte: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
    * [oportunidade] Requisitos: experiência com implantação de ERP, vivência preferencial com WK Radar, conhecimento em Controladoria, Fiscal e Financeiro
      Fonte: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
    * [oportunidade] Atividades incluem: conduzir implantações ponta a ponta, levantar e mapear processos, parametrizar sistemas, treinar usuários e atuar como parceiro estratégico
      Fonte: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
    * [oportunidade] Perfil consultivo e analítico, capacidade de entender negócio do cliente
      Fonte: https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e

  Nota: Fontes devem ser validadas pelo vendedor antes de uso comercial.
  Distincao entre fato, inferencia e hipotese indicada em cada item.

============================================================
FIM DO BRIEFING
============================================================
```

---

## URLs Consultadas

- https://teklamatik.com.br/solucoes/software-gestao-wkradar
- https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-empresarial
- https://linkedin.com/company/teklamatik
- https://teklamatik.com.br/sobre-a-empresa
- https://canais.wk.com.br/validacao/40167
- https://teklamatik.com.br/solucoes/software-gestao-wkradar/por-modulo/radar-empresarial/radar-web
- https://teklamatik.com.br/servicos
- https://teklamatik.com.br/servicos/consultoria
- https://empresas.serasaexperian.com.br/
- https://cnpja.com/
- https://www.jucesponline.sp.gov.br/BuscaAvancada.aspx
- https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/novo-pregao-eletronico/perguntas-e-respostas
- https://pt.linkedin.com/posts/teklamatik_vagas-erp-consultoria-activity-7448089509604290560-8R-e
- https://www.catho.com.br/vagas/analista-de-implantacao-de-erp/36181296/?entrada_apply=direto&origem_apply=vagas-similares