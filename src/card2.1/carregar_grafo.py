from __future__ import annotations

import argparse
import json
import pickle
import re
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import pandas as pd


def normalizar_texto(valor: Any) -> str:
    texto = str(valor).strip().lower()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r"[^a-z0-9_À-ÿ-]", "", texto)
    return texto


def garantir_lista(valor: Any) -> list[Any]:
    if isinstance(valor, list):
        return valor
    if isinstance(valor, tuple) or isinstance(valor, set):
        return list(valor)
    if pd.isna(valor):
        return []
    return [valor]


def no_usuario(user_id: Any) -> str:
    return f"user:{int(user_id)}"


def no_filme(tmdb_id: Any) -> str:
    return f"movie:{int(tmdb_id)}"


def no_diretor(nome: Any) -> str:
    return f"director:{normalizar_texto(nome)}"


def no_ator(nome: Any) -> str:
    return f"actor:{normalizar_texto(nome)}"


def no_genero(nome: Any) -> str:
    return f"genre:{normalizar_texto(nome)}"


def carregar_tmdb(caminho_pkl: str | Path) -> pd.DataFrame:
    caminho_pkl = Path(caminho_pkl)

    if not caminho_pkl.exists():
        raise FileNotFoundError(f"Arquivo TMDB .pkl não encontrado: {caminho_pkl}")

    try:
        df_tmdb = pd.read_pickle(caminho_pkl)
    except Exception as erro:
        raise RuntimeError(
            "Não foi possível carregar o .pkl do TMDB. "
            "Isso costuma acontecer quando o arquivo foi gerado com outra versão "
            "do pandas. Rode novamente o tratamento.py da sprint anterior ou use "
            "a mesma versão de pandas usada para gerar o .pkl.\n"
            f"Erro original: {erro}"
        ) from erro

    colunas_obrigatorias = {
        "id",
        "original_title",
        "genres_clean",
        "director_clean",
        "cast_clean",
    }
    colunas_ausentes = colunas_obrigatorias - set(df_tmdb.columns)

    if colunas_ausentes:
        raise ValueError(
            "O .pkl do TMDB não possui as colunas esperadas: "
            f"{sorted(colunas_ausentes)}"
        )

    df_tmdb = df_tmdb.copy()
    df_tmdb["id"] = pd.to_numeric(df_tmdb["id"], errors="coerce")
    df_tmdb = df_tmdb.dropna(subset=["id"])
    df_tmdb["id"] = df_tmdb["id"].astype(int)
    df_tmdb = df_tmdb.drop_duplicates(subset=["id"])

    return df_tmdb


def carregar_movielens(
    caminho_csv: str | Path,
    caminho_links_csv: str | Path | None = None,
    min_rating: float | None = None,
) -> pd.DataFrame:
    caminho_csv = Path(caminho_csv)

    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo MovieLens .csv não encontrado: {caminho_csv}")

    df_ml = pd.read_csv(caminho_csv)

    if "tmdb_movie_id" in df_ml.columns and "tmdbId" not in df_ml.columns:
        df_ml = df_ml.rename(columns={"tmdb_movie_id": "tmdbId"})

    if "movieId" not in df_ml.columns:
        if "tmdbId" in df_ml.columns:
            df_ml["movieId"] = df_ml["tmdbId"]
        else:
            raise ValueError(
                "O CSV do MovieLens precisa ter userId, rating e uma das colunas: "
                "tmdb_movie_id, tmdbId ou movieId."
            )

    colunas_minimas = {"userId", "movieId", "rating"}
    colunas_ausentes = colunas_minimas - set(df_ml.columns)
    if colunas_ausentes:
        raise ValueError(
            "O CSV do MovieLens precisa possuir pelo menos as colunas "
            f"{sorted(colunas_minimas)}. Ausentes: {sorted(colunas_ausentes)}"
        )

    if "tmdbId" not in df_ml.columns:
        if caminho_links_csv is None:
            raise ValueError(
                "O CSV do MovieLens não possui tmdbId/tmdb_movie_id. "
                "Para interligar corretamente com o TMDB, use um CSV já tratado "
                "ou informe o links.csv com o parâmetro --links-csv."
            )

        caminho_links_csv = Path(caminho_links_csv)
        if not caminho_links_csv.exists():
            raise FileNotFoundError(f"links.csv não encontrado: {caminho_links_csv}")

        df_links = pd.read_csv(caminho_links_csv)
        if not {"movieId", "tmdbId"}.issubset(df_links.columns):
            raise ValueError("O links.csv precisa possuir as colunas movieId e tmdbId.")

        df_ml = df_ml.merge(df_links[["movieId", "tmdbId"]], on="movieId", how="left")

    df_ml = df_ml.copy()
    df_ml["userId"] = pd.to_numeric(df_ml["userId"], errors="coerce")
    df_ml["movieId"] = pd.to_numeric(df_ml["movieId"], errors="coerce")
    df_ml["tmdbId"] = pd.to_numeric(df_ml["tmdbId"], errors="coerce")
    df_ml["rating"] = pd.to_numeric(df_ml["rating"], errors="coerce")

    df_ml = df_ml.dropna(subset=["userId", "movieId", "tmdbId", "rating"])

    if min_rating is not None:
        df_ml = df_ml[df_ml["rating"] >= min_rating]

    df_ml["userId"] = df_ml["userId"].astype(int)
    df_ml["movieId"] = df_ml["movieId"].astype(int)
    df_ml["tmdbId"] = df_ml["tmdbId"].astype(int)

    colunas_ordenacao = ["userId", "tmdbId"]
    if "timestamp" in df_ml.columns:
        colunas_ordenacao.append("timestamp")
    df_ml = df_ml.sort_values(colunas_ordenacao)
    df_ml = df_ml.drop_duplicates(subset=["userId", "tmdbId"], keep="last")

    return df_ml


def adicionar_no_filme(grafo: nx.Graph, linha: pd.Series, movie_id_movielens: int | None = None) -> str:
    tmdb_id = int(linha["id"])
    node_id = no_filme(tmdb_id)

    atributos = {
        "tipo": "movie",
        "tmdb_id": tmdb_id,
        "titulo": linha["original_title"],
    }

    if movie_id_movielens is not None:
        atributos["movielens_movie_id"] = int(movie_id_movielens)

    grafo.add_node(node_id, **atributos)
    return node_id


def construir_grafo(
    df_tmdb: pd.DataFrame,
    df_movielens: pd.DataFrame,
) -> tuple[nx.Graph, dict[str, Any]]:
    grafo = nx.Graph()

    tmdb_por_id = df_tmdb.set_index("id", drop=False)
    ids_tmdb_validos = set(tmdb_por_id.index.astype(int))

    arestas_metadados_esperadas: set[tuple[str, str, str]] = set()

    for _, filme in df_tmdb.iterrows():
        for genero in garantir_lista(filme["genres_clean"]):
            if not str(genero).strip():
                continue
            movie_node = adicionar_no_filme(grafo, filme)
            genre_node = no_genero(genero)
            grafo.add_node(genre_node, tipo="genre", nome=str(genero).strip())
            grafo.add_edge(movie_node, genre_node, tipo="HAS_GENRE")
            arestas_metadados_esperadas.add((movie_node, genre_node, "HAS_GENRE"))

        for diretor in garantir_lista(filme["director_clean"]):
            if not str(diretor).strip():
                continue
            movie_node = adicionar_no_filme(grafo, filme)
            director_node = no_diretor(diretor)
            grafo.add_node(director_node, tipo="director", nome=str(diretor).strip())
            grafo.add_edge(movie_node, director_node, tipo="DIRECTED_BY")
            arestas_metadados_esperadas.add((movie_node, director_node, "DIRECTED_BY"))

        for ator in garantir_lista(filme["cast_clean"]):
            if not str(ator).strip():
                continue
            movie_node = adicionar_no_filme(grafo, filme)
            actor_node = no_ator(ator)
            grafo.add_node(actor_node, tipo="actor", nome=str(ator).strip())
            grafo.add_edge(movie_node, actor_node, tipo="HAS_ACTOR")
            arestas_metadados_esperadas.add((movie_node, actor_node, "HAS_ACTOR"))

    df_avaliacoes_validas = df_movielens[df_movielens["tmdbId"].isin(ids_tmdb_validos)].copy()
    arestas_rating_esperadas: set[tuple[str, str, str]] = set()

    for _, avaliacao in df_avaliacoes_validas.iterrows():
        tmdb_id = int(avaliacao["tmdbId"])
        filme = tmdb_por_id.loc[tmdb_id]

        user_node = no_usuario(avaliacao["userId"])
        movie_node = adicionar_no_filme(
            grafo,
            filme,
            movie_id_movielens=int(avaliacao["movieId"]),
        )

        grafo.add_node(user_node, tipo="user", user_id=int(avaliacao["userId"]))

        atributos_aresta = {
            "tipo": "RATED",
            "rating": float(avaliacao["rating"]),
            "movielens_movie_id": int(avaliacao["movieId"]),
        }
        if "timestamp" in avaliacao.index and pd.notna(avaliacao["timestamp"]):
            atributos_aresta["timestamp"] = int(avaliacao["timestamp"])

        grafo.add_edge(user_node, movie_node, **atributos_aresta)
        arestas_rating_esperadas.add((user_node, movie_node, "RATED"))

    isolados = list(nx.isolates(grafo))
    contagem_tipos = {}
    for _, atributos in grafo.nodes(data=True):
        tipo = atributos.get("tipo", "sem_tipo")
        contagem_tipos[tipo] = contagem_tipos.get(tipo, 0) + 1

    relacoes = {}
    for _, _, atributos in grafo.edges(data=True):
        tipo = atributos.get("tipo", "sem_tipo")
        relacoes[tipo] = relacoes.get(tipo, 0) + 1

    arestas_esperadas = len(arestas_metadados_esperadas) + len(arestas_rating_esperadas)
    arestas_reais = grafo.number_of_edges()

    relatorio = {
        "qtd_nos": grafo.number_of_nodes(),
        "qtd_arestas": arestas_reais,
        "qtd_nos_por_tipo": dict(sorted(contagem_tipos.items())),
        "qtd_arestas_por_tipo": dict(sorted(relacoes.items())),
        "qtd_avaliacoes_movielens_entrada": int(len(df_movielens)),
        "qtd_avaliacoes_movielens_com_filme_no_tmdb": int(len(df_avaliacoes_validas)),
        "qtd_avaliacoes_movielens_ignoradas_sem_match_tmdb": int(len(df_movielens) - len(df_avaliacoes_validas)),
        "qtd_arestas_esperadas": arestas_esperadas,
        "qtd_arestas_reais": arestas_reais,
        "arestas_batem_com_esperado": arestas_reais == arestas_esperadas,
        "qtd_nos_orfaos": len(isolados),
        "nos_orfaos_amostra": isolados[:10],
        "possui_5_tipos_de_nos": {"user", "movie", "director", "actor", "genre"}.issubset(contagem_tipos),
    }

    if relatorio["qtd_nos_orfaos"] > 0:
        raise ValueError(
            "A validação encontrou nós órfãos no grafo. "
            f"Amostra: {relatorio['nos_orfaos_amostra']}"
        )

    if not relatorio["arestas_batem_com_esperado"]:
        raise ValueError(
            "A contagem de arestas reais não bate com a contagem esperada. "
            f"Esperadas: {arestas_esperadas}; reais: {arestas_reais}"
        )

    if not relatorio["possui_5_tipos_de_nos"]:
        raise ValueError(
            "O grafo não possui os 5 tipos de nós exigidos. "
            f"Tipos encontrados: {sorted(contagem_tipos)}"
        )

    return grafo, relatorio


def carregar_grafo(
    tmdb_pkl: str | Path,
    movielens_csv: str | Path,
    links_csv: str | Path | None = None,
    min_rating: float | None = None,
) -> tuple[nx.Graph, dict[str, Any]]:
    df_tmdb = carregar_tmdb(tmdb_pkl)
    df_movielens = carregar_movielens(movielens_csv, links_csv, min_rating)
    return construir_grafo(df_tmdb, df_movielens)


def salvar_grafo_pickle(grafo: nx.Graph, caminho_saida: str | Path) -> None:
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with caminho_saida.open("wb") as arquivo:
        pickle.dump(grafo, arquivo)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Carrega TMDB + MovieLens e constrói um nx.Graph() heterogêneo."
    )
    parser.add_argument("--tmdb-pkl", required=True, help="Caminho para tmdb_grafo_limpo.pkl")
    parser.add_argument("--movielens-csv", required=True, help="Caminho para o CSV tratado do MovieLens")
    parser.add_argument(
        "--links-csv",
        default=None,
        help="Opcional: caminho para links.csv, caso o CSV do MovieLens não tenha tmdbId",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=None,
        help="Opcional: mantém apenas ratings maiores ou iguais a este valor, ex.: 4.0",
    )
    parser.add_argument(
        "--saida-grafo",
        default=None,
        help="Opcional: salva o grafo montado em um .pkl",
    )
    parser.add_argument(
        "--saida-relatorio",
        default=None,
        help="Opcional: salva o relatório de validação em .json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    grafo, relatorio = carregar_grafo(
        tmdb_pkl=args.tmdb_pkl,
        movielens_csv=args.movielens_csv,
        links_csv=args.links_csv,
        min_rating=args.min_rating,
    )

    print("\nGrafo carregado com sucesso!\n")
    print(json.dumps(relatorio, indent=2, ensure_ascii=False))

    if args.saida_grafo:
        salvar_grafo_pickle(grafo, args.saida_grafo)
        print(f"\nGrafo salvo em: {args.saida_grafo}")

    if args.saida_relatorio:
        caminho_relatorio = Path(args.saida_relatorio)
        caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
        caminho_relatorio.write_text(
            json.dumps(relatorio, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Relatório salvo em: {args.saida_relatorio}")


if __name__ == "__main__":
    main()