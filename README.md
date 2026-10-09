# Consulta de avaliações por pedido

Consultar pedidos um a um para registrar avaliações e status exige trabalho manual repetitivo. Criado para apoiar uma rotina de delivery, este projeto automatiza as consultas por identificador e consolida os resultados em um CSV para análise.

A demonstração usa uma base local inteiramente fictícia: **CSV de pedidos → consulta por identificador no JSON → tratamento da avaliação e do status → CSV consolidado**.

## Experimente a demonstração

Na raiz do projeto, com **Python 3.10 ou superior**:

```bash
python3 -S -B consulta.py --simular \
  --entrada examples/pedidos-sinteticos.csv \
  --respostas examples/respostas-simuladas.json
```

A simulação usa apenas a biblioteca padrão e arquivos locais, sem rede, navegador ou credenciais. O comando gera `outputs/simulacao-<timestamp>.csv`, preservando a entrada, a ordem dos pedidos e os zeros iniciais dos identificadores.

Prévia dos quatro registros de [resultado-esperado.csv](examples/resultado-esperado.csv), todos fictícios. O CSV completo inclui também `Pessoa` e `Detalhe`:

| Pedido | Score | Status | Origem |
|---|---|---|---|
| `000101` | `4,8` | verificado | Simulado |
| `000102` | N/E | Cancelado | Simulado |
| `000103` | N/E | Pedido não encontrado | Simulado |
| `000104` | N/E | Falha técnica | Simulado |

Para escolher o nome da saída, acrescente `--saida outputs/minha-demonstracao.csv`. O programa aceita somente um arquivo novo dentro de `outputs/`; para repetir, escolha outro nome. Sem argumentos, ou com `--help`, mostra a ajuda.

## Experimente outros casos

Crie cópias locais da [entrada fictícia](examples/pedidos-sinteticos.csv) e das [respostas fictícias](examples/respostas-simuladas.json):

```bash
mkdir -p outputs
cp examples/pedidos-sinteticos.csv outputs/pedidos-experimento.csv
cp examples/respostas-simuladas.json outputs/respostas-experimento.json
```

Edite o CSV para acrescentar ou trocar pedidos. No JSON, mantenha `"simulado": true` e a lista `respostas`; cada item relaciona o mesmo `Pedido` textual a um `Estado`. Use um dos estados abaixo. Para `verificado`, informe `Score` como texto preenchido, por exemplo `"4.8"`. Os demais estados dispensam esse campo.

| Estado no JSON | Status no CSV | Significado |
|---|---|---|
| `verificado` | verificado | Pedido concluído com avaliação preenchida |
| `cancelado` | Cancelado | Cancelamento indicado na resposta |
| `ausente` | Pedido não encontrado | Ausência indicada explicitamente na resposta |
| `erro_tecnico` | Falha técnica | Consulta sem confirmação, como erro de navegação, timeout ou resposta ambígua |

Um pedido sem resposta no JSON recebe `Falha técnica`. Para representar uma ausência, use `ausente` explicitamente. Cada identificador pode aparecer uma única vez na lista de respostas; a correspondência usa o texto exato de `Pedido`.

Execute com os arquivos editados:

```bash
python3 -S -B consulta.py --simular \
  --entrada outputs/pedidos-experimento.csv \
  --respostas outputs/respostas-experimento.json
```

## Entrada e saída

O CSV usa vírgula como separador, UTF-8 com ou sem BOM e aspas CSV padrão. Os cabeçalhos são sensíveis a maiúsculas/minúsculas.

| Campo | Uso |
|---|---|
| `Pedido` | Obrigatório e preenchido; preservado como texto, incluindo zeros iniciais |
| `Pessoa` | Opcional; informação preservada, sem uso na consulta |
| `Score` | Texto da avaliação, com ponto substituído por vírgula; `N/E` nos demais estados |
| `Status` | Estado do processamento, conforme a tabela acima |
| `Origem` | `Simulado` na demonstração ou `Consulta real` no modo Selenium |
| `Detalhe` | Descrição do estado do processamento |

Colunas adicionais são preservadas. `Score`, `Status`, `Origem` e `Detalhe` são preenchidos pelo processamento, substituindo valores anteriores dessas colunas. O CSV de saída não inclui índice adicional.

Pedidos repetidos na entrada são processados linha a linha, sem deduplicação. Cabeçalhos ausentes ou repetidos, pedidos vazios e estruturas incompatíveis são rejeitados; uma entrada só com cabeçalho gera uma saída sem registros. A avaliação permanece textual: a substituição de ponto por vírgula não calcula nem normaliza uma métrica.

## Estrutura

- `consulta.py`: CLI e seleção explícita entre simulação e consulta real.
- `processamento.py`: leitura de CSV, estados, simulação e exportação.
- `automacao.py`: consulta da interface web com Selenium e Chrome.
- `examples/`: pedidos, respostas e resultado esperado fictícios.
- `pedidos.csv`: cabeçalho do formato original, sem registros.
- `config/seletores.example.json`: referência para configurar os seletores da interface.
- `outputs/`: resultados locais, ignorados pelo Git.

## Configuração Selenium

O modo real consulta a interface web configurada, faz login e preenche avaliação/status para cada pedido. Requer **Python 3.10+, Chrome, ChromeDriver compatível e Selenium 4**, declarado em [requirements.txt](requirements.txt):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config/seletores.example.json config/seletores.local.json
```

Configure `CONSULTA_URL` (HTTP(S), sem credenciais embutidas), `CONSULTA_DRIVER` (arquivo do ChromeDriver), `CONSULTA_USUARIO`, `CONSULTA_SENHA` e `CONSULTA_SELETORES` (JSON local com os seletores adaptados). Os valores são lidos do ambiente do processo; **não há carregamento automático de `.env`**.

Exemplo no Bash; substitua os placeholders. A URL é ilustrativa:

```bash
export CONSULTA_URL='https://sistema.example.invalid/login'
export CONSULTA_DRIVER='/caminho/absoluto/para/chromedriver'
export CONSULTA_USUARIO='substitua-pelo-usuario'
read -r -s -p 'Senha: ' CONSULTA_SENHA
export CONSULTA_SENHA
export CONSULTA_SELETORES="$PWD/config/seletores.local.json"
```

Adapte os seletores de login, histórico, busca, resultado concluído, avaliação, fechamento e cancelamento à interface usada. O seletor `ausente` é opcional e começa vazio: configure-o somente para uma mensagem explícita de ausência. Uma resposta sem estado reconhecível recebe `Falha técnica`.

A consulta depende do HTML, de uma espera fixa após a busca e de timeouts. Os seletores precisam identificar o pedido consultado e distinguir resultados atualizados de elementos antigos da tela. URL e credenciais externas não tornam os seletores universais.

Preencha seu CSV e escolha o modo real explicitamente:

```bash
python consulta.py --real --entrada pedidos.csv
```

O resultado fica em um novo `outputs/consulta-<timestamp>.csv`, com `Origem` igual a `Consulta real`. Erros de inicialização ou login encerram o processamento sem exportação. O modo usa um único driver e tenta encerrá-lo em `finally`, inclusive após erros.
