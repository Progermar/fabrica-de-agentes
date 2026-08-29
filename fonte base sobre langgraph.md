Introdução: Como criar um assistente de Deep Research grátis!
Fala, fala pessoal, tudo bem com vocês? Seja muito bem-vindo ao meu canal. Na aula de hoje, eu gostaria de apresentar
para vocês um exemplo que eu vim estudando esses dias, que é o desenvolvimento de um fluxo que vai
trabalhar fazendo uma pesquisa profunda na internet a partir de um tópico. O que vocês estão vendo na tela é o fluxo que
eu implementei a partir do tópico de entrada. O nosso fluxo utiliza uma ferramenta de busca web, pesquisa sobre
diversos assuntos relacionados a este tópico de entrada e nos fornece um
relatório muito bem detalhado sobre este tópico. Então pessoal, no vídeo de hoje
eu gostaria de compartilhar com vocês como que funciona o LRAPF, os principais componentes, como funciona a arquitetura
deste framework e através deste exemplo você vai conseguir entender e
implementar sua própria solução de busca profunda, sem depender de ferramentas privadas, como é o chat GPT.
[Música] Vamos começar aqui entendendo sobre a
arquitetura do Lengraph e depois nós colocaremos a mão na massa. Então vamos
lá. Antes de eu começar comentando sobre como funciona o Lengraph e a arquitetura
deste framework, eu gostaria de deixar avisado que todo o código e exemplo que eu apresentar aqui na tela, inclusive
este diagrama, vai estar lá dentro do nosso GitHub. Então, no link da descrição deste vídeo, tem um lugar onde
eu estou deixando os meus códigos compartilhados com vocês. Então, pessoal, para que nós possamos entender
como funciona a construção de um fluxo dentro do Lengraph, você precisa entender primeiro o que que é o
Lengraph. O Lengraph, ele é um framework de agentes de AI projetados para
construir, implementar e gerenciar fluxos de trabalhos complexos de agentes de A generativo, criada pela empresa
Langchain. O LF ele trabalha com a principal teoria que é a teoria dos grafos. Então, pessoal, um grafo ele é
construído a partir de nós e arestas e a partir de um sentido, né, uma direção
por onde percorre todas as informações. No caso do Lengraph, nós temos os nós, onde ali estão todas as ações que são
realizadas dentro do seu workflow e as arestas que dizem para o nosso sistema
para onde vai a minha informação, de um nó de origem até um nó destino. Então, a
aresta vai direcionar dentro do L graph o estado do nosso gráfico. Perfeito. E
aí eu vou te mostrar o que que é este estado. No caso do Lraph, ele trabalha com estados de trabalho. O que que seria
isso? O estado compartilhado é ao longo de todo o fluxo, cada nó recebe um
estado que seria um conjunto de variáveis no estado inicial, ou seja,
inicializada com uma determinada informação, que representa, né, uma etapa de execução de trabalho. Cada nó
tem a capacidade de atualizar informações neste estado compartilhado.
Uma vez que o nó realizou esta atualização dentro de uma determinada variável no meu estado, este estado
através da aresta, é transferido para outro nó realizar suas próprias ações.
Para isso, o nó retorna um estado novo para os próximos nós ligados por arestas. Ah, ficou confuso, Gustavo?
Perfeito. Então eu vou trazer aqui este diagraminha bem simplificado para te mostrar como que é o Lraph. No L graph,
para que você comece a construir o seu workflow, é necessário você inicializar
um state graph, que vai dizer para o nosso framework, eu estou inicializando o meu graf. O state graph, ele vai
permitir você adicionar nós e arestas dentro do seu grafo para construir seu
workflow, seu fluxo de trabalho. Vol graph sempre existem os nós de start,
que é aquele que inicializa o nosso grafo, para que o nosso sistema entenda aonde começa o meu grafo e um nó end que
vai dizer para o nosso fluxo, ó, quando chegar neste nó finalizador, meu fluxo terminou e o meu estado final já está
todo atualizado, conforme o que eu realizei em cada um dos nós do meu gráfico. E além disso, né, você pode
adicionar nodes, que são os nós dentro de um grafo de LPF. E para você unir
cada um dos nós, para fazer com que o seu estado percorra todo o seu grafo,
você adiciona as arestas. E é importante sempre ter um determinado caminho
fechado entre o nó inicializador e o nó finalizador. E o que que vai passar em
cada um desses nós para que eu possa salvar informações, atualizar informações? nós chamamos de state.
Muitas vezes esse state ele é do tipo dicionário. Então esse type dictão ver
no exemplo que eu vou apresentar na aula de hoje contém diversas variáveis onde
os meus nós podem escrever informações dentro dessa classe que vai representar
o meu estado do gráfico. Então esse state ele vai percorrer todos os meus
nós. Então ele entra no nó start, passa por nó 1, 2, 3, nó
n finalizador, ele vai se encontrar numa situação que é o que você deseja que o
seu fluxo tenha trabalhado no seu estado para você poder imprimir na tela alguma informação. Quais são os outros
componentes que nós normalmente utilizamos dentro dos nós do Lengraph? Principalmente nós utilizamos os chat
models, os nossos LLMs, que vão ser responsáveis por ou tomar decisões ou
criar informações, atualizar informações que serão registradas dentro do nosso
state, certo? Também existem as tools. As tools nós já apresentamos em vídeos
anteriores que são ferramentas. Essas ferramentas realizam algum trabalho com
meio externo, como por exemplo, chamada de APIs, acesso a diretórios do seu computador, são
ns trabalhamos com as messages, ou seja, mensagens. Por que nós trabalhamos com
isso? Porque os chat models, eles recebem como entrada um conjunto de
mensagens do tipo sistema, do tipo humana e respondem com o tipo AI. Então,
esses são alguns componentes que vocês também vão ver aliado aos componentes principais do grafo de Lraph. Para que
você possa entender como que ocorre essa união entre nós e arestas, como que nós
construímos o nosso state graph completo, incluindo o nosso state personalizado. Eu trouxe um exemplo na
aula de hoje, que é o estudo de caso, onde nós vamos desenvolver um deep research bem simplificado, ou seja, nós
vamos desenvolver um fluxo de automação que vai ter LLMs integrados em alguns
nós para que nós possamos construir uma pesquisa profunda sobre um determinado
tópico de entrada que nós vamos fornecer para o nosso sistema. Então, o que que é esse estudo de caso? O que que é esse
depois search que eu comentei? Bom, o nosso conceito é o Deep Research. É um fluxo que realiza uma pesquisa de
informações sobre um determinado tópico solicitado pelo usuário e, como resultado, cria um documento detalhado
sobre o tema, utilizando diferentes fontes de informação. No nosso caso, nós vamos utilizar uma ferramenta de busca
web, mas você também pode adicionar ferramentas, por exemplo, de leituras de PDF. O que nós vamos utilizar no nosso
estudo de caso, o próprio Lraph, API do Duck Duck Go Search, ou seja, nós vamos
utilizar uma API aberta que realiza pesquisa na web. Nós vamos utilizar como
modelo o chat openi, ou seja, nós estamos utilizando uma API privada, mas você pode utilizar APIs locais
utilizando o chat OLAMA ou também você pode utilizar APIs gratuitas, como é o chat Grock, que eu já também apresentei
em alguns vídeos anteriores no canal. e uma outra biblioteca chamada Markdown Fine. O que que esta biblioteca faz?
Esta biblioteca, quando recebe um HTML, converte este HTML em um arquivo estruturado do tipo MarkD. E nós sabemos
que o arquivo Markdow é muito bem interpretado pelos modelos de linguagem natural. Então nós vamos utilizar esta
biblioteca que quando nós acessamos um determinado site, nós extraímos o HTML e passamos este HTML para a nossa
biblioteca que vai converter o conteúdo da página em estrutura markdown. Atenção, como o objetivo aqui é entender
como criar fluxos orientados dentro do LRAPF, nós não vamos utilizar aqui um
fluxo agêntico, ou seja, nós não vamos utilizar o LLM aqui como um tomador de
decisão. Nós vamos utilizar o LLM como um especialista que realiza a leitura
que nós vamos entregar a partir das páginas e das n fontes que nós pesquisamos para realizar este tipo de
pesquisa, para entregar para nós no final um laudo muito bem estruturado da nossa pesquisa profunda. No nosso caso
aqui, nós vamos diretamente criar as arestas e o sentido dentro do nosso
fluxo de Lengraph. Então pessoal, como nos outros vídeos eu já te apresentei como funciona alguns tipos de agente,
como por exemplo o agente React, no vídeo de hoje eu gostaria de apresentar como nós realmente construímos um fluxo
orientado unindo nós e arestas num sentido que nós mesmos vamos definir.
Então como que vai funcionar? A nossa aplicação tem o usuário que vai entregar um tópico que ele deseja conhecer. A
partir daí, nós disparamos uma função que vai realizar a pesquisa na web. A
partir das pesquisas web, nós vamos colher três fontes URLs e extrair as
informações das páginas destes sites. Com a extração destas páginas, nós
enviamos para um LLM que vai realizar um resumo de cada uma dessas três páginas.
Muito bem detalhado com este resumo, né? Ou seja, ele reúne e sumariza os tópicos
relevantes. O conteúdo é enviado para um nó que vai ser responsável único e
exclusivamente para construir a nossa pesquisa profunda, que também é um outro LLM. No caso do sumizador, nós vamos
utilizar um modelo maior e também no caso da pesquisa profunda, nós também vamos utilizar um modelo maior. Porém
aqui ele está responsável a partir do prom prompt que nós vamos entregar única
e exclusivamente em construir a nossa pesquisa profunda muito bem detalhada, a partir dos resumos que ele recebe. Uma
vez que eu tenho essa pesquisa estruturada, inicialmente criada, nós temos um terceiro LLM que vai julgar se
eu preciso encontrar novas informações para contribuir e complementar a minha
pesquisa profunda, ou se eu atingir o número de requisições neste loop de, sei
lá, mais ou menos três, nós finalizamos a nossa pesquisa profunda e devolvemos ela para o nosso usuário. Então, em
resumo, a partir de um tópico, é realizar é realizada a busca na web,
extrai as informações das páginas da web. O LM vai reunir os principais
tópicos destas páginas, vai passar para o nó, que vai ser um outro LLM, que vai
realizar a estruturação da nossa pesquisa profunda. Tem um terceiro LLM que vai julgar as informações e colher o
que que eu precisaria pesquisar mais para complementar esta minha pesquisa profunda. E se este loop atingir n
iterações que nós vamos definir, eu paro e devolvo ao meu usuário a pesquisa
profunda final. Então vocês vão ver que quando nós construirmos os nossos nós,
ele terá esta cara aqui. Ou seja, a partir de um tópico de pesquisa que vai
estar lá dentro do nosso state, eu tenho o gerador de consulta web. Então, a
partir de um tópico, eu tenho um ll para fazer a pesquisa na web. Eu
mando esta query para o meu pesquisador que é a P do Duck Duck Go Search. A
partir desta pesquisa, eu mando para o nó que vai organizar e resumir as três fontes. Mando o resultado para o
escritor da pesquisa profunda. Com o resultado desta pesquisa profunda, eu tenho um analista de gaps, ou seja, eu
preciso ter mais informações para complementar muito mais a minha pesquisa profunda que eu estou construindo no nó
anterior. Se sim, eu volto com uma nova query para o meu pesquisador. Ou seja,
este analista, ele vai construir uma quer secundária, uma consulta secundária para pesquisar lá na web. E este loop,
atingindo um número máximo de interações, eu passo aqui para um nó que
eu vou inserir todas as fontes que eu pesquisei na web e entregar o meu
relatório final ao usuário, que é o documento com a pesquisa profunda, incluindo as minhas URLs, de maneira
finalizada para o usuário. Então vamos lá no código para ficar muito mais fácil para você entender como que nós
construímos isso utilizando o Lengraph. Agora que a gente está aqui no P charm, eu queria informar para vocês que no
Entendendo LangGraph na prática
repositório vocês vão encontrar alguns arquivos Python que são amin.p,
interface.p, state.p, funções auxiliadoras.pow.p.
Vou começar aqui te explicando como que é o nosso state. Lembrando, o nosso state é aquele, aquela classe que vai
armazenar as variáveis que cada nó vai poder registrar informações dentro desta
variável. No LPH existem diversas formas de você criar este state. No caso mais
comum se usa o typed dict, ou seja, eu estou criando uma classe que estende um
tipo dicionário. Então, cada uma dessas variáveis, elas serão acessadas da mesma
forma que você acessa um dicionário, utilizando uma chave e atribuindo um valor. Então, o nosso fluxo principal,
que eu nomeei aqui de estado fluxo principal, tem alguns parâmetros que eu vou utilizar. Primeiro, o tópico de
pesquisa, que eu vou preencher com a entrada do usuário. Consulta da pesquisa web, que é a resposta que o LLM vai
gerar para que eu possa incluir aqui qual que deve ser a querer, que pesquisando na web eu consiga retornar
diversas fontes sobre um determinado tópico de pesquisa que o usuário me passou. Então, uma vez que eu faço uma
pesquisa na web, eu preciso armazenar as informações. Lembrando, nós vamos consultar as três primeiras fontes.
Então, eu vou adicionar dentro de resultados web o resultado de cada uma
dessas páginas web. Então estou criando aqui uma lista com um reducer, né, que é
um operador de adição. Então toda vez que eu retornar no meu state, né, no meu
nó, eu retornar para esta chave aqui uma um determinado valor, este valor ele é
adicionado num formato de lista. Também eu preciso registrar quais são as minhas fontes. Então, se eu tenho três sites
visitados, eu tenho que registrar as minhas três fontes. Então, eu estou utilizando também um state, né, uma
variável do tipo lista. E cada vez que eu mandar esta lista, ela é adicionada a uma lista maior. Eu tenho uma variável
chamada contador loop pesquisa, porque como eu falei para vocês, eu não vou deixar o meu loop infinito e rodando
para gerar minha pesquisa profunda. Eu vou me limitar ali a no máximo duas, três iterações só para apresentar para
vocês. Então eu vou fazer com que esse controle de loop seja um iterador. Então
no primeiro loop ele começa como zero, no segundo loop ele começa com um e assim por diante. até o meu max loop
pesquisa. Então eu vou definir aqui, sei lá, três no máximo, que o meu loop de pesquisa pode executar uma ação. Então
eu vou fazer o meu contador chegar até esta variável. Sumalizador de pesquisa. Aqui eu estou adicionando todos os
sumários realizados a partir de cada loop, quando eu vou lá e pesquiso as
minhas páginas web. Então, se eu tenho todos os resumos sendo criados por LLM, eu estou aqui armazenando todos esses
resultados numa lista apenas para meu controle e o meu e a minha pesquisa
profunda final, o meu relatório final, vou registrar dentro do resultado final,
que vai ser um texto bem grandão com o resultado obtido pelo construído pelo
LLM a partir das diversas fontes que o meu fluxo foi lá e pesquisou e entregou
para ele, tá? Então esta é a classe que define o meu state, ou seja, nós
preenchemos desta primeira caixinha aqui em azul. Agora eu gostaria de, antes de
Construindo o State (etapa essencial!)
iniciarmos para a construção do meu grafo, eu gostaria de mostrar para vocês como que é a função que eu estou
utilizando para pesquisar na web, que é utilizando a API da Duck Duck Go Search.
Então eu vou apenas apresentar esta funcionalidade aqui, mas você encontra
muito mais informações dentro do repositório da Duck Duck Go Search, tá? Então vocês vão conseguir entender
melhor lá e eu partir do exemplo que está lá dentro do repositório deles. E a
minha função que vai realizar a pesquisa no web se chama Duck Duck Go pesquisa,
onde ela recebe uma consulta e eu estou pedindo para que o máximo de resultados
que retorne minha API seja quatro três sites. Então você inicializa um
contexto, né, com esse Duck Duck Go search que eu nomei aqui, tá? E a partir
daí você tem um contexto aberto. Neste contexto eu vou utilizar a API do Duck
Duck Go para fazer a pesquisa, né, a partir de uma determinada consulta com o
número máximo de resultados que são três. E eu quero que retorne no formato de texto. Isso tudo dentro da lista.
Cada um dos três links, ele retorna isso dentro de uma lista. A partir daí, eu vou obter qual que é a URL, o título da
página e o conteúdo resumido, que que é bem semelhante ao Google. Quando você faz uma pesquisa, tem um mini sumário
para cada um dos sites que vão são retornados na pesquisa. Uma vez que eu tenho a URL, eu consigo realizar uma
busca completa do conteúdo do site. Então, eu tenho aquela outra biblioteca
que é o Markfy, se eu não me engano, fala desse jeito, onde eu vou abrir uma
API, né? Vou abrir uma requisição e vou abrir este site que eu estou enviando
como parâmetro de entrada. Como eu tenho a resposta, que a resposta é um arquivo HTML, né? Este HTML, o texto é enviado
por pro paraa minha biblioteca que vai converter esta HTML num arquivo MarkD
estruturado. Então eu retorno este arquivo Markdown estruturado e eu
armazeno numa variável chamada conteúdo completo. Então o retorno da minha
função Duck Ducky Go pesquisa será uma lista, tá? Porque resultados é uma
lista. Eu estou fazendo um append para cada pesquisando com um dicionário que
contém título, URL, o conteúdo resumido e o conteúdo completo. Então eu vou ter
todas estas informações para cada minha API do Duck Duck Go search
retorna para mim a partir de uma determinada consulta, a partir de um determinado tópico. Então, esta é a
minha função principal que vai realizar a pesquisa das diferentes fontes a
partir da do tópico de entrada do usuário. Então essa é a mais importante aqui que eu gostaria que vocês entendessem e as outras eu vou deixar
para que vocês possam debugar utilizando o próprio chattigal que elas vão conseguir te
explicar de forma forma bem detalhada como que funciona cada uma dessas funções. E eu gostaria de levar agora
vocês na para a construção do nosso workflow. E o workflow parte da
Implementação completa da API DuckDuckGo Search
construção utilizando os nós. Então como que nós construímos nós dentro do Lraph?
Os nós eles são criados a partir de funções Python. Então cada função Python
no Lraph ela é um nó. Porém, para você dizer para o Lraph que aquilo ali é
realmente um nó, você precisa adicionar este nó, esta função ao seu state graph.
Mas aí eu vou te mostrar lá na frente. Outra coisa, pessoal, no Lraph, para que você possa receber as informações do
estado e utilizar dentro deste seu desta função, você precisa colocar
obrigatoriamente como primeiro parâmetro o state. Então, todo nó do L graph
recebe o seu state principal, que é o que a gente construiu aqui, e ele
retorna alguma variável que ele deseja atualizar e que esteja lá dentro do
state. Tá vendo que consulta de pesquisa web, eu estou retornando aqui um dicionário cuja chave consulta de
pesquisa web é atualizada para resultado pconsulta. Então, eu estou pegando este
parâmetro do meu state, que é consulta pesquisa web, estou retornando um dicionário para dizer que o state, o
estado fluxo principal será atualizado na variável consulta de pesquisa web com
este valor aqui. Então, veja que um nó do Lengraph, ele retorna um dicionário,
que no caso é o seu state, e recebe um dicionário que é o seu state também. Então, um state no estado inicial e no
final deste nó é um state atualizado. Então vamos construir os nossos nós.
Como que vai funcionar os nossos nós? Então eu preciso primeiro construir um nó que vai gerar uma query que eu possa
utilizar para pesquisar na web, que é aquela que eu vou enviar lá para aquela função que eu mostrei agora para vocês.
Então nó gerador de consulta web. Eu escrevi aqui um prompt, né, dizendo que
o Ll deve agir como um pesquisador experiente, com habilidades de realizar pesquisa sobre diferentes temas. Qual é
o objetivo contexto atual, que é a data atual, né, que eu coloquei aqui pro LLM
não ficar perdido. Eu disse algumas informações necessárias para ele conhecer qual que é o tópico de pesquisa
que o usuário enviou para que ele possa criar a consulta web baseada neste
tópico e qual deve ser a tarefa deste LLM. Então, eu estou criando aqui um system. Pronto. Eh, a partir daí eu
estarei criando uma saída estruturada, porque eu quero criar, eu quero que o
meu LLM responda da seguinte forma: eu quero que ele crie uma consulta e eu
gostaria que ele criasse também qual que é o racional, qual que é o pensamento que ele utilizou para criar este esta
query de pesquisa web. Então eu estou agora formatando o meu prompt para preencher as variáveis que eu coloquei
aqui, né, data atual e tópico de pesquisa, com os valores que está lá dentro do meu state, tópico de pesquisa,
porque isso daqui sempre vai tá preenchido, porque é a primeira coisa que o usuário manda. Estou mandando qual
que é a data atual para preencher aqui. E aí eu tenho o meu prompt formatado.
Como eu tenho o meu prompt formatado, eu posso enviar para o meu LLM. Qual que é o
Ll? O GPT4O Mini, que é o mais baratinho. Eu vou exigir que o meu LLM
tenha uma saída estruturada. E qual que é o formato da minha saída estruturada? Consulta pesquisa, que eu criei aqui
utilizando uma classe PID. Se tiver um pouco nebuloso sobre isso, é, você pode assistir as aulas de Lengchain, que eu
mostrei como que é a criação de saídas estruturadas utilizando essa classe Pent. É, retornando aqui, eu vou fazer a
invocação do meu Ll, que tem uma saída estruturada utilizando uma lista de
mensagens. E a minha lista de mensagens contém só o system message com o meu
system prompt configurado. Quando eu tenho isso aqui e eu faço o invoke do
meu modelo, em resultado eu tenho uma instância da consulta pesquisa. Então eu posso acessar diretamente qual que foi a
consulta e qual que foi o racional que o meu modelo utilizou para criar o tópico de pesquisa. Então o consulta de
pesquisa web, eu vou utilizar o resultado ponto consulta. Eu vou pegar o
que que o LLM utilizou como frase para ser pesquisada e colocar aqui no meu
state dentro da variável consulta de pesquisa web. Então este é o meu primeiro nó. O meu segundo nó vou
realizar a pesquisa. Então, no meu segundo nó, eu vou realizar a pesquisa. Como que eu vou realizar a pesquisa? Eu
Desenvolvimento do nó de consulta WEB
recebo o meu state porque o meu tópico tá lá dentro do meu state. Eu pego o tópico que eu criei no no nó anterior,
que é consulta de pesquisa web, mando pra minha função de pesquisa, que vai utilizar o Duck Duck Ghost Search. Pego
o resultado, que vai ser aquela lista de dicionários com três sites lá dentro.
formato esta lista em um único texto para ficar mais fácil para eu mandar pro LLM, né? Depois vou formatar também qual
que será as referências. Lembrando que o resultado disso daqui contém também as
minhas referências, que é as minhas URLs. Então eu vou acessar essa URL lá e
vou pegar qual que é o título e a URL. Então vou pegar o título e a URL e organizar de uma forma que fique igual
ao que o GPT mostra no finalzinho, referências bibliográficas com o título
e a URL. Então para isso, eu vou organizar estas referências e vou armazenar dentro de dentro de fontes.
Então eu estou lá em fontes mandando uma lista de referência. O meu contador loop
pesquisa vai adicionar um, ou seja, eu estou realizando uma primeira pesquisa.
Toda vez que voltar neste nó, eu vou atualizar este contador para que eu não fique num loop infinito e quando eu
atingir um loop máximo eu pare de executar. E quais são os resultados? Web
pesquisado é o resultado obtido lá da minha pesquisa web e de um jeito mais formatado que eu utilizei aqui uma
função formata texta texto pesquisado que vocês podem encontrar aqui em funções auxiliadoras. Então vamos voltar
aqui pro nosso fold. Então eu tenho aqui o meu segundo nó que é o nó de realiza
pesquisa. A partir do momento que eu tenho o nó de pesquisa realizada, eu preciso criar aqui um nó que lê todas
Criação do nó que resume páginas
essas fontes e também cria um resumo bem estruturado pro meu agente especialista
em criar a pesquisa profunda. Então eu estou seguindo para o meu terceiro nó, que é o organizador e resumidor
resumidor das três fontes web. Por aqui eu tô com um texto puro. Aqui eu vou
organizar a partir de uma interpretação do LLM utilizando estas fontes pesquisadas. Tanto que se você verificar
aqui o meu prompt de sistema é: haja como um especialista em processamento de linguagem natural com 15 anos de
experiência em resumos automáticos de textos técnicos. E aí eu dei o objetivo,
os requisitos, as instruções que devem seguir, o que que ele deve ter como atenção. E aí eu criei também um prompt
humano para simular qual que é o resumo que eu estou passando para o meu LLM criar este resumo. Então eu tô falando
assim, ó, o contexto pesquisado está aqui dentro, dentro de resultados web, que é o que eu retornei aqui em cima.
Resultados web. Sempre pegue o último, porque a cada iteração eu estou adicionando informação nessa lista.
Então, sempre pegue o último. A sua tarefa é com base no contexto crie um novo sumário a partir do tópico de
pesquisa, que é o tópico de pesquisa que o o usuário mandou para nós. E aí eu criei aqui uma chamada ao LLM, né? Então
o meu LLM aqui ele vai executar a minha chamada a API da Openi. E a partir daí
tá aqui, né? A partir daí utilizando o GPT4O. E a partir daí ele vai entregar uma resposta. Lembrando que a resposta é
de um tipo AI message. Então eu preciso acessar o conteúdo. E o conteúdo eu vou
colocar dentro de sumário da pesquisa. Então o meu LLM leu todas as minhas
fontes e tirou os tópicos mais importantes de forma bem organizada e eu
estou colocando dentro de sumário da pesquisa. Perfeito. Agora deixa eu pular esse e vou mostrar qual que é o meu
Desenvolvendo o escritor automático de pesquisas profundas
especialista em criar a pesquisa profunda. O meu especialista em criar pesquisa profunda é um outro nó que é
este nó aqui, escritor de pesquisa profunda, que tem um LLM e ele vai
inicializar ou atualizar um documento de pesquisa profunda. Então, eu tenho também um LLM que vai realizar a minha
construção do relatório de pesquisa profunda. Eu tenho aqui é o Llando GPT4O
com uma temperatura de 03. Eu vou verificar se o meu state contém um resultado pesquisa final, ou seja, se eu
já iniciei o meu Deeps, o search, a minha o meu relatório. Se eu não iniciei, eu vou retornar aqui, né? Eu
vou colocar dentro de pesquisa profunda um aviso, pesquisa profunda não iniciada. Mas se eu já tô numa iteração
dois, quer dizer que eu já iniciei a minha pesquisa profunda. Então eu vou utilizar o próprio resultado que tá
dentro da minha variável, o resultado final, que é o minha pesquisa profunda. E aí eu tenho o prompt aqui, que vai ser
o responsável por criar essa pesquisa profunda. Então, qual que é o papel que eu dei para ele? Aja como um pesquisador
acadêmico altamente qualificado e experiente. Você tem mais de 20 anos de experiência na elaboração de pesquisas
profundas a partir de múltiplas fontes. Sua especialidade é coletar, interpretar, organizar informações
dispersas e etc. Dei um objetivo, dei as instruções que ele deve seguir, quais
são os requisitos. Se tiver uma pesquisa profunda já iniciada, qual deve ser o
caminho que ele deve seguir? Disse qual que deve ser o formato de saída para minha pesquisa profunda, pontos
importantes e pontos de atenção. Coloquei aqui o sumário da última pesquisa realizada. E aqui em pesquisa
profunda, eu estou colocando duas situações. Se eu tô numa interação zero, quer dizer que pesquisa profunda não
está iniciada. Então eu vou colocar aqui um aviso que não foi iniciada e ele vai seguir estes requisitos aqui caso não
existe uma pesquisa profunda. Ah, mas e se ele tá numa interação dois? Na segunda interação eu já tenho um
resultado final que é uma pesquisa deep research no caso, né? Já iniciada. Então eu vou colocar o que ele já escreveu
aqui dentro para ele apenas atualizar e realizar algumas modificações nessa
pesquisa profunda com as novas informações que eu estou recebendo dos resumos dos sites que eu estou
pesquisando. Então, eu tenho um prompt que vai realizar aqui uma chamada ao
Llosta e a resposta aqui vai ser a minha pesquisa profunda puramente dita. Então estou colocando o conteúdo, né, de um AI
message aqui dentro do resultado final. Então eu fico nesse loop, pesquiso, faço um resumo bem organizado e crio minha
pesquisa profunda, tá? Mas aí eu tenho o resultado aqui e eu vou mandar para um
Construção do nó Analista
especialista de gaps. O que que seria especialista de gap? Preciso pesquisar informações complementares? Este é o
questionamento que o LLM que tá aqui dentro vai se perguntar. Se sim, qual que é a querer que se eu fizer uma
pesquisa na web, eu consigo resolver o que está faltando aqui neste relatório.
Então ele vai gerar uma query, vai voltar para este nó e vai fazer o mesmo caminho. Lembrando que aqui já vai ter
uma pesquisa profunda, então ele vai atualizar as novas informações aqui dentro dessa pesquisa profunda. Então, é
por isso que nós construímos aqui um analista de resultado de relatório, onde eu vou pedir para ele gerar uma query
nova e qual foi o raciocínio dele por trás para descobrir o que tá faltando no
meu relatório final. E aí eu dei também um promp sistema, qual é o objetivo que
ele teve tomar com atenção, as tarefas, o resumo já existente, né, que é a minha pesquisa já iniciada para ele pensar o
que que tá faltando e criar uma nova query pra gente realizar a pesquisa na web. Uma vez que ele realizou a pesquisa
na criou essa query, eu tenho dentro de consulta de pesquisa que é necessário
atualizar a informação, ou seja, eu estou criando aqui, né? Fale-me mais
sobre o que ele imaginou aqui que deveria ser a consulta nova. E aí eu pego este resultado aqui e mando lá pro
meu nó que realiza a pesquisa. Então eu tenho aqui um nó fechado, um ciclo fechado. Perfeito. Ah, Gustavo, mas isso
Configurando decisões inteligentes (arestas condicionais)
vai ficar de forma infinita? Não, eu tenho uma aresta condicional. O que que é essa aresta condicional dentro do
Lraph? A aresta condicional é isso aqui. Ou eu vou aqui para baixo ou eu vou aqui para cima. Eu atingi um número máximo de
interações desse ciclo aqui, tá? Se eu atingir um número máximo, vai para baixo
e finaliza o meu gráfico. Ah, não atingi o número máximo, então retorna aqui, vai lá pro meu pesquisador, cria a nova
pesquisa e realiza a pesquisa aprofunda novamente. Então, eu tenho aqui um nó de rota, onde eu tenho como retorno o nome
dos meus nós para onde eu quero que vai o meu fluxo. Então aqui eu estou observando o quê? Bom, contador de loop
pesquisa já atingiu o máximo do loop de pesquisa que eu desejo? Se ele não
atingiu, realiza a nova pesquisa com a com a consulta que o meu analista de
resultados de relatório criou para mim. Ah, não, Gustavo, já chegou. Se aqui era
três, já chegou no três, né? Já chegou, já tá no quarto loop. Ah, você tá no
quarto loop, então finaliza. Vai para o nó que apenas inclui as fontes no final
do meu relatório, tá? Então, o nó que inclui as fontes finais do meu relatório é uma simples função, onde eu vou pegar
Adicionando o nó de referências e fontes
todas as fontes que eu armazenei lá no meu state, na variável fontes, vou criar uma lista, vou tirar as fontes repetidas
e uma vez que eu tenho as fontes todas organizadas e de maneira única, eu vou
concatenar no meu relatório final as minhas fontes. Ou seja, o meu relatório final é formado pelo state, tópico de
pesquisa, state, resultado final e referências bibliográficas, que são
todas as minhas fontes que eu estou organizando aqui acima neste nó. e vou
retornar de novo pro meu resultado final, porque o meu resultado final, eu sempre quero que esteja o a minha
pesquisa profunda final, organizada, sempre ali naquela variável para que
quando chega no nó end o nó finalizador, eu consigo acessar esta variável e eu
sei que nesta variável vai ser o meu estado final do da minha pesquisa profunda, tá? Ah, beleza, Gustavo. Agora
a gente já construiu todos os nossos nós. Então, vamos construir agora o nosso fluxo mesmo, o nosso grafo. Vamos
Montagem completa do grafo inteligente
inicializar o nosso grafo de Lraph. Então, você precisa fazer a importação do state graph e enviar qual que é o
estado customizado que você criou, que é esse aqui que a gente fez, né? Então você pega e inicializa o seu construtor,
seu construtor de gráfico. Vamos adicionar os nossos nós. Para adicionar no nosso state graph os nós, você
utiliza a função ede. Beleza? Node. Nome do nó, função que representa o nó. Nome
do nó, função que representa o nó. Lembrando que todas as funções que representam os nós, a gente construiu
aqui em cima. Aqui no nome você pode pôr o nome que você quiser. Beleza? Mas como que eu vou unir os nós? Porque até agora
eu só tenho as caixinhas. Eu ainda não tenho as arestas, tá? Então vamos construir as nossas arestas. Como que
deve ser o nosso fluxo? Aí eu aconselho vocês a desenharem para que vocês não se percam na hora de construir cada uma
dessas arestas. Perfeito? Então vamos construir. Eu gostaria que o meu nó
start tivesse ligado no primeiro nó que é o nó gerador de consulta web. Então o
nó start ligado ao meu gerador de consulta web. Meu gerador de consulta web tem que ir para o realiza pesquisa.
O meu Node realiza pesquisa tem que ir para o nome, o meu Node que realiza o resumo do texto da pesquisa. Lembrando,
para eu adicionar uma aresta, eu tenho que utilizar a função
add o nó de início e o nó de fim, origem, destino, sempre assim para você
criar uma aresta. Então vocês vão verificar aqui que eu sempre segui um caminho direcionado. Start nó gerador de
querer nó gerador de consulta pro realiza pesquisa. Realize a pesquisa pro resumo. Resumo para o deep e search.
Deep research pro analista. O analista vai seguir para a rota. A rota vai tomar
decisão. Qual decisão? Dependendo do meu state, vai para o meu nó de realiza
pesquisa ou para o meu nó que inclui fontes de resposta. Então eu criei
utilizando rota, utilizando additional eds. Estas duas arestas aqui,
esta e essa. Uma vez que ele chegou no limite máximo de interações, eu tenho
que o nó que eu incluo as fontes precisa ir para o nó final. Então eu tenho esta
última aresta aqui, end. Perfeito. Então, uma vez que você construiu os seus nós e as suas arestas, você dá um
compile do seu gráfico, você compila ele e aí você consegue visualizar se está
tudo corretamente organizado utilizando um plot da imagem do seu gráfo. E eu vou
mostrar aqui para vocês na tela como que vai ficar o nosso gráfo. Veja que o LFTH criou os nós e as arestas conforme o que
a gente colocou aqui no nosso desenho, quando a gente pensou qual deveria ser a
arquitetura do nosso grafo. E agora nós podemos fazer a invocação do nosso
Testando o fluxo em tempo real (funciona MESMO!)
grafo. E aí eu deixei aqui no arquivo main.p como que você realiza a chamada
pro seu grafo, né, a invocação do seu grafo de lengra. Como o state ele é o
estado inicial que você precisa enviar para o seu grafo, você precisa
inicializar o seu state graph utilizando as mesmas variáveis que você colocou
aqui dentro de state com um determinado valor. E aí a gente vai colocar tudo vazio, né? Então meu contador do loop de
pesquisa vai ser zero, a consulta da pesquisa web vai est vazio e o meu máximo loop de pesquisa vai ser dois. No
caso, eu decidi colocar dois aqui. Beleza? Eu coloquei dois e eu posso
executar o meu grafo. E aí vocês vão poder verificar que ao executar o meu
grafo, meu workflow, dando o meu invoke no meu graph, você vai obter dentro da
resposta, na variável resultado final, a pesquisa profunda realizada. E aí eu vou
executar aqui para vocês verem qual que é o resultado final. Vai demorar um pouquinho, então eu vou pausar o vídeo
aqui e eu vou mostrar para vocês o resultado final. Lembrando pessoal que o meu tópico de pesquisa vai ser: Me dê
uma pesquisa profunda sobre o novo Papa eleito hoje. Pronto pessoal, finalizou a
nossa pesquisa profunda e eu vou mostrar para vocês tudo que aconteceu. Bom, ele passou pelo gerador de consulta web,
realizou as pesquisas em três sites, realizou a primeira pesquisa profunda, né? Criou o nosso arquivo da primeira
pesquisa profunda e seguiu que precisaria realizar uma nova pesquisa. E aí ele fez isso três vezes. Você pode
ver aqui todos os sites que eu ele pesquisou. E no final, né, ele incluiu
as fontes no nosso relatório de pesquisa profunda final. E veja aqui, ó, que a pesquisa profunda finalizada sobre o
tópico me deu uma pesquisa profunda sobre o novo Papa eleito hoje. A ascensão do Papa, um novo capítulo da
Igreja Católica, introdução, contexto da eleição, o perfil do papa, discurso
inaugural, desafios e oportunidades, implicações globais, conclusão e referências bibliográficas, como é o
deep research ali do chat GPT. Veja que bacana, pessoal, que você criou o mesmo
fluxo que o Chat GPT tem. Obviamente o Chat GPT tem um deep research muito mais
robusto que isso. Então eu gostaria de trazer só um exemplo simplificado para você aprender como conectar os nós e
arestas no fluxo de Lraph. E agora, pessoal, é, eu queria apresentar para vocês só uma integração com Chainlit,
Criando interface profissional com Chainlit
porque isso daqui é muito feio de você apresentar ou utilizar. Então, eu deixei um outro arquivo chamado interface.p, do
pai, onde a gente utiliza o Chainlit. E se você não conhece o Chainlit, ele é
uma biblioteca também baseada ali no smitada na construção de uma interface
de chat. E aí eu vou mostrar para vocês aqui como que ficaria este nosso fluxo
de Lraph sendo executado pelo chalit. Então você inicializa o chainlit, então
você precisa fazer um pip install chainlit e aí você consegue acessar qual é o seu chat. Então veja aqui que você
já tem o mini chat GPT e utilizando Lraph e que realiza a sua pesquisa
profunda. A pesquisa profunda do Papa atual eu coloquei aqui e eu deixei uma segunda pesquisa profunda que é para
pesquisar sobre um determinado tópico de tecnologia. Mas se você quiser escrever aqui qual que é o tópico, sem problemas
também. Então eu vou aproveitar isso que eu deixei aqui, esse cardzinho, pra gente pesquisar sobre os desafios sobre
inteligência artificial. Então, qual que é o tópico que eu solicitei para ele? É sabido que hoje hoje que a inteligência
artificial está sendo bastante divulgada. Poderia me entregar uma pesquisa focando nos desafios encontrados pelas empresas, na adoção de
AI em seus processos? Seja detalhada e forneça dados quantitativos também. Eu
mandei a requisição, se vocês verificarem aqui, já está realizando a pesquisa profunda. E aí eu vou dar um
pause também no vídeo e vou mostrar para vocês qual que foi o resultado lá na tela do Chainlit. Pronto, pessoal, agora
que finalizou eu vou mostrar para vocês como ficou lá no Chainlit. E aí vocês podem ver aqui que a nossa pesquisa
profunda sobre o tópico solicitado finalizou. Então, título da pesquisa, desafios na adoção de inteligência
artificial pelas empresas, introdução, desafios técnicos, falta de talento
especializado, custos de implementação, questões éticas e privacidade, mudança cultural e resistência interna, dados de
qualidade, medição de retorno sobre investimento ou ROY, conclusão e as nossas referências bibliográficas. Para
ir mais rápido, eu coloquei para fazer apenas um loop, mas você pode colocar n loops que você quiser. Lembrando que eh
app do Duck Duck Go Search tem possibilidades de limite. Então ele pode
limitar a taxa de requisição e você pode utilizar qualquer ferramenta de busc. Existem algumas ferramentas pagas para
isso que também compensa a utilizar para construir o seu fluxo do Lraph. No caso, este exemplo que a gente está mostrando
aqui, nós utilizamos uma API aberto, mas você pode também solicitar lá dentro das
requisições do prompt de criação da pesquisa profunda, a expansão de não apenas um parágrafo, você pode pedir
para ele sempre construir mais de um parágrafo sobre cada tópico e aí você consegue construir e resultados muito
mais robustos. O que eu gostaria de apresentar era algo muito mais simplificado para te ensinar a trabalhar
com este framework que é o Lraph. E agora que chegamos no final do vídeo, pessoal, espero que vocês tenham
Conclusão e próximos passos
entendido através deste exemplo que não é complicado trabalhar com Lraph. Basta
você entender como cada componente funciona e como cada componente se conecta. Para conseguir construir
diversas soluções bem mais robustas, você pode partir de exemplos simples
como este que eu apresentei na aula de hoje. Se você acompanhou junto comigo e
implementou também junto comigo, compartilhe suas experiências aí no comentário, que eu vou ficar muito feliz
em saber que meus vídeos estão ajudando pessoas como você a entender como
trabalhar com modelos de inteligência artificial integrados dentro do seu sistema, dentro das suas soluções.
Lembrando, pessoal, todo o código que eu mostrei aqui, inclusive o diagrama, já tá lá dentro do GitHub. Se você quiser,
pode ir lá acessar, baixar e executar na sua máquina. Qualquer problema, deixe
nos comentários. Se você gostou do vídeo, te peço, aproveite, curta, compartilhe, se inscreva no canal, ative
o sininho para que fazer com que o YouTube compartilhe meus vídeos para outras pessoas que desejam aprender
também sobre inteligência artificial e construções de sistemas mais robustos utilizando os LLMs. Então, nos vemos no
próximo vídeo. Um forte abraço e tchau tchau. เฮ
[Música]

Todos

De Gustavo Sacchi
