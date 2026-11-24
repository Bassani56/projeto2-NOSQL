# Relatório

Análise das três primeiras queries do TPC-H (Q1, Q2 e Q3) em Cassandra e Redis, comparadas com o MySQL.

## Cassandra

### Importação dos dados

Primeiro importei os dados do TPC-H para o Cassandra, convertendo o tipo de cada coluna com um script em Python:

| Tipo no arquivo | Tipo no Cassandra |
|---|---|
| String | TEXT |
| Int | INT |
| Decimal | DECIMAL |
| Data | DATE |

Foram criados 8 scripts, um para cada tabela do TPC-H.

Depois, como o Cassandra não faz JOIN e só busca bem pela chave da partição, criei uma tabela desnormalizada para cada query, pensando no que cada uma precisa.

### Q1

A Q1 usa só a tabela LINEITEM. Ela filtra por data, agrupa por `L_RETURNFLAG` e `L_LINESTATUS`, calcula somas, médias e contagem, e ordena pelas duas colunas do grupo. Não tem JOIN. O custo está em processar uma quantidade muito grande de linhas (cerca de 6 milhões no fator de escala 1).

Tabela `q1_lineitem`:

```
PRIMARY KEY (
    (l_returnflag, l_linestatus, l_shipyear),
    l_shipdate, l_orderkey, l_linenumber
)
```

- Partition key: `l_returnflag`, `l_linestatus` e `l_shipyear`. Cada partição guarda um grupo da consulta em um ano.
- Clustering key: `l_shipdate`, `l_orderkey` e `l_linenumber`. Elas ordenam as linhas dentro da partição e deixam cada linha única.

Na execução, o Python faz uma busca por partição (3 flags × 2 status × 7 anos, de 1992 a 1998), com `l_shipdate <= 1998-09-02`. Depois ele soma, tira as médias e conta as linhas.

### Q2

A Q2 usa cinco tabelas: PART, PARTSUPP, SUPPLIER, NATION e REGION. Ela procura, para peças de tamanho 15 e tipo terminado em BRASS, os fornecedores da região EUROPE com o menor custo de fornecimento. O resultado é ordenado por saldo da conta do fornecedor e outros critérios, e limitado a 100 linhas.

Tabela `q2_parts_supplier`:

```
PRIMARY KEY (
    (p_size, p_type, r_name),
    ps_supplycost, p_partkey, ps_suppkey
) WITH CLUSTERING ORDER BY (ps_supplycost ASC)
```

- Partition key: `p_size`, `p_type` e `r_name`, que são os filtros da query.
- Clustering key: `ps_supplycost` (crescente), `p_partkey` e `ps_suppkey`.

Na importação, os JOINs entre as cinco tabelas foram feitos em Python e cada linha de PARTSUPP virou uma linha da tabela, com os dados da peça, do fornecedor, da nação e da região. Os filtros não foram aplicados na importação. Eles são resolvidos na consulta, pela partition key.

O Cassandra não aceita `LIKE '%BRASS'`. Por isso a consulta busca uma partição para cada um dos 30 tipos de peça de tamanho 15 que terminam em BRASS. Essa lista foi gerada a partir da tabela PART. O Python escolhe o menor custo de cada peça e faz a ordenação final.

### Q3

A Q3 usa CUSTOMER, ORDERS e LINEITEM. Ela busca os pedidos do segmento BUILDING feitos antes de 15/03/1995, com itens enviados depois dessa data. A receita de cada pedido é `SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT))`. O resultado são os 10 pedidos de maior receita.

Tabela `q3_orders`:

```
PRIMARY KEY (
    (c_mktsegment, o_orderyear, o_ordermonth),
    o_orderdate, o_orderkey
)
```

- Partition key: segmento, ano e mês do pedido.
- Clustering key: data e número do pedido.

Na importação, o Python seguiu estes passos:

1. Pegou os clientes BUILDING.
2. Pegou os pedidos desses clientes com data anterior a 15/03/1995.
3. Percorreu LINEITEM, somou a receita dos itens enviados depois de 15/03/1995 e guardou um valor por pedido.

Ou seja, a tabela não guarda os itens. Ela guarda a receita de cada pedido, já calculada. Na consulta, o Cassandra lê as partições de 1992 a 1995, e o Python ordena por receita (decrescente) e data (crescente) e devolve os 10 primeiros.

Esta tabela só responde a Q3 com esses parâmetros (BUILDING e 15/03/1995). Para outro segmento ou outra data, seria preciso refazer a importação.

### Resultados no Cassandra

| Query | MySQL | Cassandra | Diferença |
|---|---|---|---|
| Q1 | 10,1407 s | 56,4174 s | Cassandra cerca de 5,6 vezes mais lento |
| Q2 | 0,3965 s | 0,4699 s | Cassandra cerca de 19% mais lento |
| Q3 | 7,4119 s | 0,8503 s | Cassandra cerca de 8,7 vezes mais rápido |

**Q1.** Os dois retornaram 4 grupos. No Cassandra, quase todas as linhas da tabela passam pelo filtro de data. Por isso as partições não ajudaram a descartar dados, e o Python precisou receber milhões de linhas e somar uma a uma. No MySQL, o próprio banco faz a agregação.

**Q2.** Foram lidas 642 linhas, de 460 peças. Os tempos ficaram próximos, com pequena vantagem do MySQL. As partições deixaram a leitura pequena, mas o Python ainda precisou achar o menor custo por peça e ordenar.

**Q3.** O Cassandra foi bem mais rápido porque os JOINs, o filtro de datas e a soma da receita foram feitos antes, na importação. Na consulta, sobrou ler os pedidos prontos, ordenar e pegar os 10 primeiros. O MySQL faz tudo isso na hora da consulta. Por isso a comparação favorece o Cassandra.

**Observação sobre os tempos.** Os tempos medem só a execução da consulta. A preparação, a desnormalização e a importação dos dados não entram. No Cassandra, o tempo inclui o processamento feito em Python.

## Redis

### Estrutura usada

Nas três queries usei **sorted sets** (ZSET). Cada ZSET tem uma chave que funciona como a partição do Cassandra. Cada membro é um JSON com os dados da linha, e o score é o valor pelo qual os membros ficam ordenados.

| Query | Chave | Membro | Score |
|---|---|---|---|
| Q1 | `q1:{returnflag}:{linestatus}:{ano}` | linha de LINEITEM (quantidade, preço, desconto, imposto) | data de envio (AAAAMMDD) |
| Q2 | `q2:15:{p_type}:EUROPE` | peça + fornecedor + nação | custo de fornecimento |
| Q3 | `q3:BUILDING:{ano}:{mês}` | pedido com receita, data e prioridade | receita |

- **Q1:** a importação guarda todas as linhas de LINEITEM. A consulta lê as chaves, ignora as linhas com data maior que 1998-09-02 e soma o resto em Python.
- **Q2:** a importação já filtra tamanho 15, tipo BRASS e região EUROPE, e faz os JOINs. Foram criadas 30 chaves, uma por tipo de peça. A consulta lê todas, acha o menor custo por peça e ordena em Python.
- **Q3:** como no Cassandra, a receita é calculada na importação, e há uma chave por mês. A consulta lê todas as chaves, ordena por receita e data, e devolve os 10 primeiros.

### Resultados no Redis

| Query | MySQL | Cassandra | Redis |
|---|---|---|---|
| Q1 | 10,1407 s | 56,4174 s | _preencher_ |
| Q2 | 0,3965 s | 0,4699 s | _preencher_ |
| Q3 | 7,4119 s | 0,8503 s | _preencher_ |

_Comentar aqui os resultados do Redis depois de rodar as consultas._

## Conclusão

O desempenho do Cassandra depende da query e de como a tabela foi desenhada:

- **Q1:** o MySQL foi melhor. A query agrega quase a tabela inteira, e o MySQL faz isso dentro do banco, sem levar os dados para o Python.
- **Q2:** os tempos foram próximos, com pequena vantagem do MySQL.
- **Q3:** o Cassandra foi muito melhor, mas porque o trabalho pesado foi feito antes, na importação.

Modelar a tabela de acordo com a query pode dar ganhos grandes. O custo é preparar os dados antes, e a tabela serve só para aquela query e aqueles parâmetros.
