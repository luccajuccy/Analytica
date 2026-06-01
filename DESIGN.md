# Analytica - Guia de Design do Website

Este documento descreve o tema visual atual do projeto Analytica e os padrões que novas telas, componentes e fluxos devem seguir. O projeto usa Flask/Jinja no frontend, Font Awesome para icones, fonte Inter, fundo escuro animado com particles.js e uma linguagem visual de painel operacional para edificios, CAG, BMS, clima, busca e contatos.

## Identidade visual

Analytica deve parecer uma plataforma operacional de monitoramento predial: escura, tecnica, precisa e orientada a dados. A interface combina azul profundo, vidro fosco, cards de informacao, indicadores de status, graficos e tabelas densas. O tom visual nao e de landing page; e de ferramenta de controle, consulta e acompanhamento.

Principios principais:

- Priorizar legibilidade e acao rapida em ambientes de monitoramento.
- Usar superficies escuras translúcidas com bordas azuladas discretas.
- Manter consistencia entre paginas com sidebar, widgets superiores, cards e formularios.
- Usar icones Font Awesome junto de rotulos para acelerar reconhecimento.
- Diferenciar estados operacionais por cor: verde para normal/online/acionamento, vermelho para falha/desligamento/erro, amarelo para alerta, azul/ciano para informacao e acao.
- Evitar layouts promocionais, banners grandes sem funcao ou elementos decorativos que tirem foco dos dados.

## Paleta de cores

Tema principal em `static/css/main.css`:

| Token | Cor | Uso |
| --- | --- | --- |
| `--dark-blue-1` | `#0a192f` | fundo principal, profundidade |
| `--dark-blue-2` | `#112240` | sidebar, cards, paineis |
| `--dark-blue-3` | `#1a3a63` | cabecalhos de tabela, contraste |
| `--medium-blue` | `#2a4a7f` | bordas, fundos hover, elementos secundarios |
| `--light-blue` | `#4a8fe7` | botoes primarios, links fortes |
| `--accent-blue` | `#64b5f6` | destaque, foco, estado ativo |
| `--hover-blue` | `#82c4ff` | hover de links e controles |
| `--text-primary` | `#e6f1ff` | titulos e texto principal |
| `--text-secondary` | `#ccd6f6` | descricoes e texto de apoio |
| `--text-muted` | `#8892b0` | metadados, labels, placeholders |
| `--success` | `#66bb6a` | online, sucesso, acionamento |
| `--warning` | `#ffa726` | alerta, pendencia |
| `--error` | `#ef5350` | erro, falha, desligamento |
| `--info` | `#42a5f5` | informacao |

Tema alternativo/demo em `static/css/style.css` usa tokens equivalentes: `--bg #0b1220`, `--panel #111c2f`, `--line #263955`, `--accent #5cc8ff`, `--accent-2 #7ce7b2`, `--danger #ff6b7a`, `--ok #72e0a8`. Quando criar novas telas, prefira os tokens de `main.css`; use os tokens de `style.css` apenas em telas demo ou legadas que ja dependem deles.

Gradientes padrao:

- Fundo: `linear-gradient(135deg, #0a192f 0%, #112240 100%)`.
- Acao principal: `linear-gradient(135deg, #4a8fe7 0%, #64b5f6 100%)`.
- Destaque operacional/demo: `linear-gradient(135deg, #64b5f6, #7ce7b2)`.
- Barras e progresso: `linear-gradient(90deg, var(--accent-blue), #7ce7b2)`.

## Tipografia

Fonte padrao: `Inter`, com fallback para `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `sans-serif`.

Escala principal:

- `h1`: `2.5rem` no desktop; reduz para `2rem` em tablet e `1.75rem` em mobile.
- `h2`: `2rem` no desktop; reduz para `1.75rem` e `1.5rem`.
- `h3`: `1.5rem` no desktop; reduz para `1.35rem` e `1.25rem`.
- Texto base: `1rem`.
- Texto pequeno: `0.875rem`.
- Metadados, badges e labels auxiliares: `0.75rem` a `0.86rem`.

Regras:

- Titulos usam peso `600` ou `700`.
- Numeros de KPI usam peso `800` e tamanho grande (`2rem` a `2.5rem`).
- Labels, metadados e cabecalhos de tabela podem usar uppercase discreto.
- `letter-spacing` deve permanecer `0` por padrao; use apenas em labels muito pequenos quando o padrao existente ja usar.

## Layout global

O layout principal vem de `templates/base.html` e `static/css/main.css`.

Estrutura:

- `body`: fundo em gradiente azul escuro, texto claro, altura total.
- `#particles-js`: canvas fixo no fundo com particulas azuis conectadas.
- `.app-container`: flex horizontal, ocupa `100vh`, contem sidebar e conteudo.
- `.sidebar`: largura `280px`, altura `100vh`, fundo translúcido, blur e borda direita.
- `.main-content`: area rolavel, padding `5rem 2rem 2rem`, conteudo principal.
- `.header-widgets`: widgets fixos no topo direito dentro do conteudo.
- `.notification-stack`: toasts fixos no topo direito.

Responsividade:

- Abaixo de `900px`, a sidebar pode encolher para `80px` e expandir no hover.
- Abaixo de `600px`, a sidebar vira drawer lateral fixo, acionado por `.mobile-menu-toggle`.
- Em mobile, `main-content` usa padding menor (`5rem 1rem 1rem`).
- Grids de 2, 3 e 4 colunas devem quebrar para 1 coluna em telas pequenas.

## Navegacao lateral

Sidebar:

- Fundo: `rgba(17, 34, 64, 0.85)` com `backdrop-filter: blur(12px)`.
- Logo textual: `Analytica`, branco, peso `700`, altura minima `44px`.
- Links: flex com icone e texto, padding `0.9rem 1.5rem`, gap `1rem`.
- Icones: Font Awesome, classe `.nav-icon`, largura fixa `24px`.
- Hover: fundo azul translúcido, texto `--accent-blue`, leve deslocamento de padding.
- Selecionado: gradiente horizontal sutil, borda esquerda `3px` em `--accent-blue`.

Itens atuais:

- CAG Partidas: `fa-building`.
- Dashboards: `fa-chart-line`.
- Pesquisar: `fa-search`.
- Edificios: `fa-city`.
- Clima: `fa-cloud-sun`.
- Plano de Chamados: `fa-clipboard-list`.
- Ajuda: `fa-question-circle`.

Padrao para novos itens:

- Sempre usar icone + texto.
- Manter borda esquerda apenas para estado ativo.
- Evitar itens muito longos; se necessario, abreviar com termos operacionais claros.

## Header widgets

Widgets superiores aparecem como links pequenos em uma pilula translúcida:

- Container `.widgets-list`: flex, gap `1rem`, fundo `rgba(10, 25, 47, 0.6)`, blur, borda arredondada full.
- Link `.widget-link`: texto secundario, icone Font Awesome, tamanho `0.85rem`, peso `500`.
- Hover: cor `--accent-blue`.

Widgets atuais:

- JIRA: `fa-tasks`.
- Portal PHP: `fa-portal-enter` no template, mas esse icone pode nao existir no Font Awesome; preferir `fa-right-to-bracket`, `fa-door-open` ou `fa-globe`.
- Relatorios: `fa-chart-bar`.

## Fundo e movimento

O site usa particles.js no fundo:

- 120 particulas.
- Cores entre `#112240`, `#1a3a63`, `#2a4a7f`, `#4a8fe7`, `#64b5f6`.
- Linhas conectadas azuis.
- Interacoes: hover com `grab`, clique com `push`.

Padroes de animacao:

- Entrada: `fadeIn`, `slideInRight`, `slideInLeft`.
- Loading: spinner circular via `.loading::after`.
- Pulso: indicadores online/status.
- Hover de cards: `translateY(-2px)` a `translateY(-5px)`.
- Evitar animacoes grandes ou constantes em areas com muito dado; use movimento apenas para feedback e status.

## Botoes

Sistema principal:

- `.btn`: inline-flex, centro, gap `0.5rem`, padding `0.5rem 1.5rem`, radius `8px`, peso `500`, transicao global.
- `.btn-primary`: fundo `--light-blue`, texto branco.
- `.btn-primary:hover`: fundo `--accent-blue`, sobe `-2px`, sombra media.
- `.btn-secondary`: fundo azul translúcido, borda azul, texto secundario.
- `.btn-secondary:hover`: fundo mais claro, texto `--accent-blue`, borda `--accent-blue`.
- `.btn-icon`: quadrado `40px`, padding reduzido.

Sistema demo/operacional:

- `.button`: gradiente ciano/verde, texto escuro `#06111f`, peso `800`, padding `10px 14px`, radius `8px`.
- `.button.secondary`: fundo escuro, texto claro, borda azulada.

Padrões de uso:

- Acao principal: `.btn-primary` ou `.button`.
- Acao secundaria: `.btn-secondary` ou `.button.secondary`.
- Icon-only: quadrado, tooltip/title obrigatorio quando o significado nao for obvio.
- Acao destrutiva ou falha: usar vermelho somente quando realmente indicar erro/desligamento/exclusao.
- Botoes em tabelas devem ser compactos e alinhados ao centro da celula.
- Evitar criar botoes com radius diferente de `8px`, exceto botoes circulares como chatbot, busca e close.

Botoes existentes importantes:

- Busca: `.search-button`, circular `48px`, icone lupa.
- Filtros de busca: `.filter-pill`, pilula com icone e contador.
- Alternancia de visualizacao: `.view-btn`, quadrado `36px`, icones grade/lista.
- Card de resultado: `.btn-icon` para util/download e `.btn-primary-sm` para detalhes.
- Contatos: `.contacts-btn-success` para novo contato, `.contacts-btn-qr` e `.contacts-btn-edit` para acoes de linha.
- CAG: `.button` para gerar e-mail e `.button.secondary` para detalhes/fechar/salvar.
- Chatbot: `.chatbot-toggle` circular `60px`, `.chatbot-send-btn`, `.chatbot-action-btn`.

## Cards e paineis

Card base:

- Fundo: `rgba(17, 34, 64, 0.7)`.
- Blur: `backdrop-filter: blur(10px)`.
- Borda: `1px solid rgba(42, 74, 127, 0.2)`.
- Radius: `8px`.
- Padding: `1.5rem` ou `18px`.
- Hover: sobe levemente, sombra e borda azul mais visivel.

Usos:

- `.card`: componente reutilizavel.
- `.dashboard-card`: graficos, tabelas e blocos de dashboard.
- `.metric-card`: KPIs pequenos.
- `.welcome-card`: card central de boas-vindas.
- `.feature-card`: recursos da home.
- `.glass-card`: clima, graficos e noticias.
- `.edificio-card`: edificio/status.
- `.result-card`: resultado de busca.
- `.contacts-table-container`: tabela em painel.
- `.glass-panel`: paineis das telas operacionais B20/VCZ2/TSUL.

Padrões:

- Cards devem conter apenas um grupo claro de informacao.
- Cards repetidos devem ter mesma altura visual quando em grid.
- Cards operacionais podem usar borda colorida lateral para indicar modo/status.
- Evitar cards dentro de cards, exceto modais e subpainel tecnico realmente necessario.

## Formularios e inputs

Input padrao:

- `.input`, `.select`, `.textarea`: fundo escuro translúcido, borda azul discreta, radius `8px`, texto claro.
- Focus: borda `--accent-blue`, sombra `0 0 0 3px rgba(100, 181, 246, 0.1)`.
- Placeholder: `--text-muted`.

Campos existentes:

- Busca global: input transparente dentro de `.search-form` arredondado.
- Filtros de edificios: `.filter-input`, `.filter-select`.
- Contatos: `.contacts-search-input`, dropdown customizado por predio/funcao/categoria.
- CAG: textareas de destinatarios, mensagem, observacoes; input de horario; select simples e multiple.
- Add/Edit contato: formulario em grid, selects obrigatorios, validacao visual e mensagens de erro.
- Chatbot: textarea auto-resize ate `100px`.

Padrões:

- Labels sempre acima do campo em formularios densos.
- Campos obrigatorios devem ter validacao visual e mensagem proxima ao campo.
- Em formularios longos, usar grid de duas colunas no desktop e uma coluna no mobile.
- Selects devem manter fundo escuro tambem nas opcoes quando possivel.
- Textareas devem permitir resize controlado ou usar altura fixa/auto-resize conforme contexto.

## Badges, estados e indicadores

Badge base:

- Inline-flex, radius full, padding compacto, fonte pequena, peso `600`, uppercase quando for status.

Variantes:

- `.badge-primary`: azul informativo.
- `.badge-success`, `.badge.ok`: verde, sucesso/online/acionamento.
- `.badge-warning`, `.badge.warn`: amarelo, alerta.
- `.badge-error`, `.badge.danger`: vermelho, erro/falha/desligamento.
- `.status-dot.online`: ponto verde com brilho.
- `.status-dot`: ponto vermelho por padrao.

Indicadores grandes de edificio:

- `.status-indicator-large`: circulo `60px`.
- `.status-online`: verde com pulso.
- `.status-offline`: vermelho com pulso/alerta.
- Sem monitoramento: cinza `#475569`, sem animacao.

CAG:

- Modo acionamento: verde, borda esquerda `--success`, badge `.ok`.
- Modo desligamento: vermelho, borda esquerda `--error`, badge `.danger`.

## Tabelas

Tabelas sao fundamentais no projeto e devem ser densas, rolaveis e legiveis.

Padrao visual:

- `border-collapse: collapse`.
- `th`: texto muted, uppercase, fonte pequena, peso `600`.
- `td`: texto secundario, borda inferior azul translúcida.
- Hover de linha: fundo azul translúcido e texto mais claro.
- Containers com `overflow-x: auto` para mobile.

Tabelas atuais:

- Dashboard: chamados recentes.
- Dashboard BMS: outliers de temperatura.
- Plano de Chamados: tabela grande de contatos com cabecalho sticky.
- CAG: edificios, destinatarios, modo e acoes.
- Historico CAG: edificio, equipamento, tipo, status, horario, origem.
- B20/VCZ2/TSUL: telemetria e tabelas internas de CAG/equipamentos.

Padrões:

- Tabelas grandes devem ter `min-width` e wrapper horizontal.
- Cabecalho sticky quando a tabela passa de uma tela.
- Acoes de linha devem ficar na ultima coluna.
- Agrupamentos podem usar linhas com fundo azul translúcido e peso maior.

## Modais

Dois estilos aparecem:

Busca:

- `.modal-overlay`: fundo escuro translúcido.
- `.modal-container`: painel central com detalhes do arquivo.
- `.modal-close`: botao iconico de fechar.

CAG:

- `.modal`: fixed inset, fundo `rgba(3, 8, 18, 0.78)`, z-index alto.
- `.modal-card`: card largo, max-height `92vh`, rolagem vertical.
- Conteudo em grid de duas colunas no desktop.

Contatos/QR:

- Fundo `rgba(10, 25, 47, 0.85)` com blur.
- Conteudo central de `400px`, QR em caixa branca, close no canto.

Padrões:

- Modal deve fechar pelo botao e, quando fizer sentido, por clique fora/ESC.
- Usar z-index acima de sidebar/chat quando necessario.
- Conteudo deve caber em mobile com scroll.
- Fechar sempre com icone claro (`fa-times` ou `&times;`).

## Toasts e notificacoes

`.notification-stack` fixa no topo direito.

`.toast`:

- Fundo `#122038`.
- Borda azulada e borda esquerda colorida.
- Padding `12px`, radius `8px`, sombra forte.
- `.toast.critical`: borda esquerda vermelha.
- `.toast.warning`: borda esquerda amarela.
- `.toast-close`: botao circular `24px`.

Padrão:

- Use toast para eventos temporarios, nao para erros que exigem decisao.
- Titulo em `strong`, detalhes em texto pequeno.
- Nao sobrepor modais ou chatbot.

## Paginas e componentes existentes

### Home

Arquivo: `templates/index.html`.

Elementos:

- `.welcome-card`: card central glass, max-width `800px`, padding `2.5rem`, texto centralizado.
- H1 com icone `fa-building` e texto Analytica.
- `.features-grid`: cards de recurso responsivos.
- `.feature-card`: cards menores com icones grandes.

Padrao:

- Home deve apresentar entrada objetiva para a plataforma, sem hero promocional.
- Cards devem remeter aos modulos reais: dashboards, edificios, clima, chamados.

### Dashboards

Arquivos: `templates/dashboard.html` e `templates/dashboard_bms.html`.

Elementos:

- Header central com H1 + icone.
- Grid de metricas.
- Cards de graficos/tabelas.
- Barras horizontais customizadas no dashboard simples.
- Plotly no Dashboard BMS com fundo transparente, fontes claras e cores ciano/verde/vermelho/amarelo.

Padrões:

- KPIs sempre no topo.
- Graficos dentro de `.dashboard-card`.
- Usar fundo transparente nos graficos.
- Cores de dados devem respeitar semantica: ciano/azul para volume, verde para normal, vermelho para falha, amarelo para correlacao/alerta.

### Busca Inteligente

Arquivo: `templates/search.html`.

Elementos:

- `.search-hero`: titulo central e texto explicativo.
- `.search-form`: barra arredondada, translúcida, com foco elevado.
- `.suggestion-tag`: sugestoes clicaveis.
- `.directory-scan-animation`: overlay de varredura com pastas e linha animada.
- `.filters-bar`: filtros e opcoes de visualizacao.
- `.filter-pill`: filtros por tipo de arquivo.
- `.view-btn`: grade/lista.
- `.result-card`: cards de arquivo com thumbnail ou icone grande.
- `.file-badge`: badge de tipo de arquivo.
- Modal de detalhes.
- Grafo com vis-network.

Padrões:

- Busca deve ter feedback visual ao pesquisar.
- Resultados devem poder alternar grade/lista.
- Cards devem mostrar tipo, titulo, tamanho, data, snippet e acoes.
- Filtros devem atualizar contagem e estado ativo.

Observacao tecnica: a pagina usa `var(--accent-primary)` e `var(--border-light)`, que nao existem em `main.css`. Para novas implementacoes, usar `--accent-blue` e bordas `rgba(42, 74, 127, 0.2/0.4)`, ou declarar aliases se a pagina for mantida.

### Edificios

Arquivo: `templates/edf.html`.

Elementos:

- Header com titulo em gradiente.
- Filtros por texto e categoria.
- Grid responsivo de cards.
- Card de edificio com painel de status, IPs/latencia e categoria.
- Indicador CAG com temperatura quando disponivel.

Categorias:

- Torre: verde.
- Atrium: rosa.
- B: amarelo.
- Corporate: roxo.
- Outros: azul.

Padrões:

- Cada edificio deve mostrar status operacional antes de detalhes textuais.
- Status online/offline deve ser visual, nao apenas texto.
- Categoria sempre em badge no rodape do card.
- Filtro deve esconder cards sem mudar layout dos demais.

### Clima

Arquivo: `templates/clima.html`.

Elementos:

- `.weather-dashboard`: grid principal.
- `.glass-card`: paineis de clima.
- Metricas atuais: temperatura, minima, maxima, umidade, vento.
- Grafico Chart.js de historico 24h.
- News cards com imagem filtrada em azul/blur e revelacao no hover.

Padrões:

- Metricas climaticas usam icones coloridos por tipo.
- Graficos devem manter labels em cinza claro e grid discreto.
- Noticias devem ser secundarias; cards com titulo, data, resumo e link.

### Plano de Chamados / Contatos BMS

Arquivo: `templates/plano_de_chamados.html`.

Elementos:

- Header simples "Analytica / Interlinked Ecosystem".
- Filtros em painel glass: predio, funcao, categoria e busca full-text.
- Dropdowns customizados.
- Botao "Novo Contato" verde.
- Tabela grande com agrupamento por funcao.
- Botoes de QR e editar por linha.
- Modal de QR Code para WhatsApp.

Padrões:

- Fluxos administrativos podem ser mais densos.
- Dropdowns devem ficar acima da tabela com z-index suficiente.
- Tabela deve ter cabecalho sticky.
- Acoes devem ser compactas e iconicas.
- QR deve aparecer em modal central com fundo escuro e QR em area branca.

### Add/Edit Contato

Arquivos: `templates/add_contato.html` e `templates/edit_contato.html`.

Elementos:

- Card de formulario.
- Campos: predio, empresa, funcao, categoria, acao, nome, telefones, email, observacao.
- Validacao com mensagens de erro.
- Mascara de telefone.
- Botoes salvar/limpar.

Padrões:

- Formularios devem ocupar card unico.
- Agrupar campos em grid.
- Campos invalidos devem destacar borda e mostrar erro abaixo.
- Acao primaria com icone de envio/salvar.

### CAG Partidas

Arquivo: `templates/cag.html`.

Elementos:

- Topbar com titulo e botao "Gerenciar e-mails".
- Duas secoes: Posto BI e Posto AC.
- Switch de modo Acionamento/Desligamento.
- Painel de modo com descricao.
- Tabela de edificios por posto.
- Historico CAG.
- Modal de edificio para gerar e-mail.
- Drop zones para imagens inline: Foto CAG, Foto FC, Clima, Adicionais.

Padrões:

- Modo operacional deve ser imediatamente visivel por cor e badge.
- Switch deve ser binario e claro.
- Modal deve separar dados do e-mail e evidencias.
- Drop zone deve aceitar arrastar/colar imagens e mudar visual quando tiver imagem.
- Botoes finais alinhados a direita: salvar destinatarios e gerar e-mail.

### Ajuda

Arquivo: `templates/help.html`.

Elementos:

- Header central com icone.
- Embed Canva em painel com radius e sombra.
- FAQ accordion.

Padrões:

- Ajuda deve ser limpa e focada.
- Accordion abre uma resposta por vez.
- Perguntas usam hover azul translúcido e chevron rotacionado.

### Chatbot

Arquivos: `components/chatbot.html` e `static/js/chatbot.js`.

Elementos:

- Botao flutuante circular no canto inferior direito.
- Badge vermelho de notificacao.
- Janela `380px x 550px`, fundo escuro com blur, borda azul.
- Header com status online/offline, titulo, limpar e fechar.
- Mensagens com avatar, bolha e alinhamento usuario/bot.
- Indicador de digitacao com tres pontos.
- Suporte basico a Markdown: negrito, italico, code e quebras de linha.
- Documentos recomendados como `doc-badge`.
- Textarea auto-resize e botao de envio.

Padrões:

- Chatbot deve permanecer acima do conteudo (`z-index --z-chatbot`) e abaixo de modais criticos.
- Mensagem do usuario usa bolha azul; mensagem do bot usa fundo azul translúcido.
- Avatar do usuario usa `fa-user`; bot usa `fa-robot`.
- Status verde pulsante quando pronto; cinza quando offline/indexando.
- Em mobile, janela ocupa quase toda largura e altura disponivel.

### Telas operacionais B20/VCZ2/TSUL

Arquivos: `templates/B20.html`, `templates/VCZ2.html`, `templates/TSUL.html`.

Essas telas usam um estilo mais "live operations", com classes utilitarias tipo Tailwind e paineis `glass-panel`.

Elementos:

- Header com icone de edificio em gradiente.
- KPIs: equipamentos, andares com falha, status de conexao, modo de operacao.
- Sidebar interna de andares.
- Painel principal com cards de fancoils/CAG.
- Badges de status: sucesso, falha, neutro.
- Indicadores de pulso, animacao de fan/spin e controles de refresh.
- Cards internos para temperatura, setpoint, parametros e falhas.

Padrões:

- Manter linguagem de centro de comando.
- Cards internos podem usar `rounded-xl` nessas telas, pois ja seguem padrao proprio.
- Falhas devem sempre ter vermelho visivel e icone de alerta.
- Itens online/normal devem usar verde ou ciano.
- Sidebars internas devem ser rolaveis e compactas.

## Iconografia

Biblioteca: Font Awesome 6.4.

Icones recorrentes:

- Edificios: `fa-building`, `fa-city`.
- Dashboards/graficos: `fa-chart-line`, `fa-chart-bar`, `fa-chart-area`.
- Busca: `fa-search`, `fa-th-large`, `fa-list`.
- Clima: `fa-cloud-sun`, `fa-temperature-high`, `fa-wind`, `fa-tint`.
- Chamados/contatos: `fa-clipboard-list`, `fa-address-book`, `fa-qrcode`, `fa-edit`.
- CAG/HVAC: `fa-snowflake`, `fa-fan`, `fa-water`.
- Status: `fa-check-circle`, `fa-exclamation-triangle`, `fa-wifi`.
- Acoes: `fa-plus`, `fa-download`, `fa-external-link-alt`, `fa-paper-plane`, `fa-times`, `fa-trash`, `fa-sync-alt`.

Padrões:

- Usar icone antes do texto em titulos de secao e botoes importantes.
- Icon-only precisa de `title` ou `aria-label`.
- Nao misturar bibliotecas de icones.

## Espacamento, bordas e sombras

Tokens:

- `--spacing-xs`: `0.25rem`.
- `--spacing-sm`: `0.5rem`.
- `--spacing-md`: `1rem`.
- `--spacing-lg`: `1.5rem`.
- `--spacing-xl`: `2rem`.
- `--spacing-2xl`: `3rem`.

Radius:

- Padrao: `8px`.
- Pequeno: `4px`.
- Grande: `12px`.
- Full: `9999px`.

Sombras:

- Pequena: `0 2px 8px rgba(0,0,0,0.1)`.
- Media: `0 4px 16px rgba(0,0,0,0.15)`.
- Grande: `0 8px 24px rgba(0,0,0,0.2)`.
- Extra: `0 12px 32px rgba(0,0,0,0.3)`.

Padrões:

- Cards e modais usam sombras grandes.
- Botoes usam sombra apenas em hover ou quando sao flutuantes.
- Bordas devem ser sutis e azuladas.

## Responsividade

Breakpoints conceituais:

- Mobile: ate `600px`.
- Tablet: ate `900px`.
- Desktop largo: acima de `1200px`.

Regras:

- Sidebar vira drawer em mobile.
- Widgets superiores escondem texto em mobile.
- Grids de cards/tabelas viram coluna unica.
- Tabelas usam scroll horizontal.
- Modais devem ocupar `min(1040px, 100%)` e rolar verticalmente.
- Chatbot em mobile usa `width: calc(100vw - 2rem)` e altura adaptada.

## Acessibilidade e interacao

Padrões ja presentes:

- `*:focus-visible` com outline azul.
- Botoes e links com transicoes suaves.
- Inputs com foco claro.
- Sidebar mobile com overlay clicavel.

Padrões recomendados:

- Todo botao iconico deve ter `aria-label` ou `title`.
- Nao depender apenas de cor para estados criticos; usar texto, icone ou badge.
- Manter contraste alto entre texto e fundo.
- Evitar texto pequeno demais em tabelas densas; minimo pratico `0.78rem`.
- Modais devem fechar com ESC quando forem interativos.

## Padrões para novas telas

Ao criar uma nova pagina:

1. Extender `base.html`.
2. Usar `main-content` automaticamente pelo bloco `content`.
3. Comecar com header curto: titulo + icone + descricao opcional.
4. Colocar filtros/toolbar logo abaixo do header, em painel glass se houver multiplos controles.
5. Usar cards para KPIs, graficos ou grupos de informacao.
6. Usar tabelas com `.table-wrap` quando houver dados tabulares.
7. Usar `.btn`, `.button`, `.input`, `.select`, `.textarea`, `.badge` antes de criar novas classes.
8. Manter cores semanticas de status.
9. Garantir layout mobile com grids quebrando para uma coluna.
10. Evitar estilos inline, exceto ajustes pontuais ja comuns em templates legados.

## Coisas a evitar

- Criar um tema claro paralelo sem necessidade.
- Usar roxo/bege/laranja como paleta dominante.
- Criar cards arredondados demais fora das telas operacionais ja existentes.
- Usar textos explicativos grandes dentro da interface operacional.
- Colocar elementos decorativos que parecam marketing.
- Criar botoes sem hover/focus.
- Usar verde/vermelho fora de contexto de status.
- Criar novas variaveis (`--accent-primary`, `--border-light`) sem declarar no `:root`.
- Duplicar o include do chatbot dentro de paginas que ja extendem `base.html`, pois `base.html` ja inclui `components/chatbot.html`.

## Observacoes tecnicas de consistencia

- `main.css` e o tema principal e deve ser a fonte de verdade.
- `style.css` contem um shell alternativo/demo; nao deve substituir `main.css` sem migracao planejada.
- Algumas paginas possuem CSS inline extenso. Para evolucao, mover estilos recorrentes para `main.css` quando forem reutilizados.
- Algumas strings aparecem com problemas de encoding em templates antigos. Novas paginas devem salvar arquivos em UTF-8 e manter `meta charset="UTF-8"`.
- A busca usa tokens nao declarados (`--accent-primary`, `--border-light`). O padrao correto e `--accent-blue` e bordas azuladas baseadas em `rgba(42, 74, 127, ...)`.
- O arquivo `base.html` inclui `main.js`, `demo.js` e o chatbot global. Evite reincluir scripts/componentes globais em paginas filhas.

