# Consulta de avaliações por pedido

Projeto histórico de automação em Python para consultar pedidos de um CSV em uma interface web e preencher avaliação e status. A demonstração offline usa pedidos e respostas inteiramente fictícios para mostrar o formato e os estados de resultado.

## Estrutura

- `consulta.py`: entrada de linha de comando, com seleção explícita de modo.
- `processamento.py`: leitura textual de CSV, estados, simulação e exportação.
- `automacao.py`: consulta real com Selenium e Chrome, usando configuração externa.
- `pedidos.csv`: esquema histórico sem registros.
- `examples/`: entrada, respostas e resultado esperado, todos simulados.
- `config/seletores.example.json`: seletores históricos de referência; exigem adaptação.
- `outputs/`: resultados locais, ignorados pelo Git.

O fluxo consulta pedidos concluídos, extrai o texto da avaliação e reconhece cancelamentos. Não calcula uma nova avaliação, aplica limites de score ou coleta contatos. Não existe integração por API implementada. O repositório não contém arquivo de licença; não se atribui licença ao material implicitamente.

## Demonstração offline

Requisito: **Python 3.10 ou superior**. Não é necessário instalar dependências, configurar credenciais ou possuir navegador. Na raiz do projeto:

```bash
python3 -S -B consulta.py --simular \
  --entrada examples/pedidos-sinteticos.csv \
  --respostas examples/respostas-simuladas.json
```

O comando cria um novo `outputs/simulacao-<timestamp>.csv`. Há quatro registros: um verificado com avaliação textual `4,8`, um cancelado, uma ausência explícita e uma falha técnica. A coluna `Origem` identifica todos como `Simulado`. O conteúdo deve corresponder a [examples/resultado-esperado.csv](examples/resultado-esperado.csv).

Para escolher o nome, acrescente `--saida outputs/minha-demonstracao.csv`. O arquivo não pode existir: escolha outro nome para repetir. A entrada nunca é sobrescrita. Sem argumentos, ou com `--help`, o programa mostra ajuda e não abre serviços.

[Entrada fictícia](examples/pedidos-sinteticos.csv) e [respostas fictícias](examples/respostas-simuladas.json) são arquivos locais. A simulação é escolhida antes de carregar Selenium; não acessa rede, navegador, teclado/mouse ou credenciais. Resposta fictícia ausente no JSON produz falha técnica, não comprova ausência do pedido.

## Campos e resultados

CSV separado por vírgula, UTF-8 com ou sem BOM e aspas CSV padrão. Cabeçalhos são sensíveis a maiúsculas/minúsculas.

| Campo | Uso |
|---|---|
| `Pedido` | Obrigatório e preenchido; identificador preservado como texto, incluindo zeros iniciais |
| `Pessoa` | Opcional; campo informativo preservado, sem uso na consulta |
| `Score` | Preenchido com o texto extraído; ponto é substituído por vírgula, sem cálculo numérico |
| `Status` | Estado da consulta; o valor anterior não impede nova consulta |
| `Origem` | `Simulado` ou `Consulta real` |
| `Detalhe` | Descrição fixa do significado do estado, sem erros internos |

Colunas adicionais são preservadas. O leitor rejeita cabeçalho ausente/repetido, pedidos vazios, estrutura incompatível e encoding inválido. Entrada só com cabeçalho é aceita. Não há deduplicação: cada linha é processada e respostas são relacionadas pelo texto exato de `Pedido`, sem normalização.

| Status | Significado |
|---|---|
| `verificado` | Resposta de concluído e avaliação preenchida |
| `Cancelado` | Cancelamento indicado explicitamente |
| `Pedido não encontrado` | Mensagem de ausência indicada explicitamente |
| `Falha técnica` | Consulta não confirmada, incluindo timeout, seletor/navegação ou resposta ambígua |

Para os três últimos estados, `Score` recebe `N/E`; consulte `Status` para distinguir seus significados. A exportação preserva a ordem e não inclui índice adicional. Os resultados são arquivos novos dentro de `outputs/`; não há sobrescrita silenciosa.

## Configuração e modo real

O modo real depende de Chrome, chromedriver compatível e Selenium 4. A dependência identificada está em `requirements.txt`; suas versões não fixam um ambiente histórico reproduzível. Para preparar um ambiente separado:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config/seletores.example.json config/seletores.local.json
```

Configure no ambiente do processo `CONSULTA_URL`, `CONSULTA_DRIVER`, `CONSULTA_USUARIO`, `CONSULTA_SENHA` e `CONSULTA_SELETORES`. A URL deve ser HTTP(S), sem credenciais embutidas; o driver deve ser um arquivo de chromedriver. `CONSULTA_SELETORES` aponta para o JSON local adaptado. Valores não devem ser gravados no código ou em arquivos versionados. **Não há carregamento automático de `.env`.**

Exemplo de configuração no Bash, substituindo os placeholders pela configuração própria. A URL ilustrativa abaixo não é um serviço funcional:

```bash
export CONSULTA_URL='https://prestador.example.invalid/login'
export CONSULTA_DRIVER='/caminho/absoluto/para/chromedriver'
export CONSULTA_USUARIO='substitua-pelo-usuario'
read -r -s -p 'Senha: ' CONSULTA_SENHA
export CONSULTA_SENHA
export CONSULTA_SELETORES="$PWD/config/seletores.local.json"
```

Os seletores do exemplo refletem uma interface histórica específica; configurar URL e credenciais não os torna universais. Ajuste login, histórico, busca, resultado concluído, avaliação, fechamento e cancelamento à interface pretendida. `ausente` é opcional e começa vazio: preencha somente com um seletor de mensagem explícita de ausência. Sem ele, falta de resposta reconhecível produz `Falha técnica`.

Com as variáveis definidas e os seletores adaptados, a seleção real é explícita:

```bash
python consulta.py --real --entrada pedidos.csv
```

Esse modo faz login, consulta cada pedido e produz CSV separado. Inicialização e login malsucedidos encerram sem exportação. O driver é único e seu encerramento é tentado em `finally`, inclusive após erros. O programa não imprime credenciais, URLs de acesso ou mensagens internas do Selenium.

## Limitações

- A demonstração valida formato e estados com respostas fictícias; não comprova funcionamento do serviço, autenticação, navegador ou seletores reais.
- A consulta depende do HTML, de uma espera fixa após a busca e de timeouts. Não há contrato universal de resposta nem garantia de que elementos antigos da tela já foram atualizados; seletores devem identificar corretamente o pedido consultado.
- Falha técnica não demonstra pedido ausente. Uma ausência só é registrada com indicação explícita configurada; resultados ambíguos são falhas técnicas.
- Avaliação é texto extraído, com a substituição histórica de ponto por vírgula. Escala, significado e precisão dependem da interface; não são métricas calculadas pelo projeto.
- Não há deduplicação, filtro por avaliação, coleta de contatos, envio de mensagens ou retomada automática após falhas. Use apenas entradas adequadas ao acesso autorizado.
- A execução real e a compatibilidade atual das dependências/interface não são demonstradas pelo exemplo offline. Resultados simulados não representam pedidos ou desempenho operacional.
