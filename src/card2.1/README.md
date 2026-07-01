# Card 2.1 — Carga do grafo heterogêneo

Este diretório contém o script `carregar_grafo.py`, responsável por consumir o arquivo tratado do TMDB em `.pkl` e o CSV tratado do MovieLens para montar um grafo heterogêneo não-dirigido com `networkx.Graph()`.

## Tipos de nós

- `user`: usuários do MovieLens
- `movie`: filmes do TMDB
- `director`: diretores do TMDB
- `actor`: atores principais do TMDB
- `genre`: gêneros do TMDB

## Tipos de arestas

- `RATED`: usuário avaliou filme
- `DIRECTED_BY`: filme dirigido por diretor
- `HAS_ACTOR`: filme possui ator no elenco principal
- `HAS_GENRE`: filme possui gênero

## Como rodar com os arquivos deste repositório

Entre na pasta do tratamento e gere novamente o `.pkl` do TMDB. Isso evita erro de incompatibilidade de versão do pandas ao carregar um pickle antigo.

```bash
cd src/card1.1
python tratamento.py
```

Depois entre na pasta do Card 2.1 e rode a carga do grafo:

```bash
cd ../card2.1
python carregar_grafo.py \
  --tmdb-pkl ../card1.1/dados_tratados/tmdb_grafo_limpo.pkl \
  --movielens-csv ../card1.1/dados_tratados/conexoes_usuario_filme.csv \
  --saida-grafo dados_tratados/grafo_filmes.pkl \
  --saida-relatorio dados_tratados/relatorio_grafo.json
```

## Uso com CSV do MovieLens já tratado

O script aceita CSV tratado com uma destas colunas de identificação do filme:

- `tmdb_movie_id`
- `tmdbId`
- `movieId`, desde que também seja informado o `links.csv`

Exemplo com `ratings.csv` e `links.csv` separados:

```bash
python carregar_grafo.py \
  --tmdb-pkl ../card1.1/dados_tratados/tmdb_grafo_limpo.pkl \
  --movielens-csv dados_originais/ratings.csv \
  --links-csv dados_originais/links.csv
```

## Uso importando no Python

```python
from carregar_grafo import carregar_grafo

G, relatorio = carregar_grafo(
    tmdb_pkl="../card1.1/dados_tratados/tmdb_grafo_limpo.pkl",
    movielens_csv="../card1.1/dados_tratados/conexoes_usuario_filme.csv",
)

print(G.number_of_nodes())
print(G.number_of_edges())
print(relatorio)
```

## Filtro opcional de ratings

Por padrão, o script usa todas as avaliações do MovieLens. Caso o grupo queira usar apenas avaliações fortes, por exemplo ratings maiores ou iguais a `4.0`, use:

```bash
--min-rating 4.0
```
