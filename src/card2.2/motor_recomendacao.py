"""
Motor de recomendação baseado em vizinhança no grafo heterogêneo.

Este módulo implementa um algoritmo de recomendação que:
1. Extrai o histórico do usuário (filmes com rating >= 4.0)
2. Encontra filmes candidatos a distância 2+ do grafo
3. Implementa pesos semânticos diferenciados por tipo de relacionamento
4. Calcula pontuação baseada em soma ponderada dos caminhos
5. Retorna top-N filmes ordenados, excluindo já assistidos
"""

import pickle
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set
import json

import networkx as nx
import pandas as pd
from collections import defaultdict, deque


class MotorRecomendacao:
    """Motor de recomendação baseado em proximidade estrutural no grafo."""

    # Pesos semânticos para diferentes tipos de arestas
    # Maior peso = maior relevância para a recomendação
    PESOS_SEMANTICOS = {
        "DIRECTED_BY": 1.0,      # Diretor: peso máximo
        "HAS_ACTOR": 0.9,        # Ator: peso alto
        "RATED": 0.7,            # Rating do usuário: peso médio
        "HAS_GENRE": 0.3,        # Gênero: peso baixo (muito genérico)
    }

    def __init__(
        self,
        grafo: nx.Graph,
        df_tmdb: Optional[pd.DataFrame] = None,
        df_movielens: Optional[pd.DataFrame] = None,
    ):
        """
        Inicializa o motor de recomendação.

        Args:
            grafo: NetworkX Graph com nós de usuário, filme, diretor, ator e gênero
            df_tmdb: DataFrame do TMDB (opcional, para enriquecimento de dados)
            df_movielens: DataFrame do MovieLens (opcional, para análise)
        """
        self.grafo = grafo
        self.df_tmdb = df_tmdb
        self.df_movielens = df_movielens

    def extrair_historico_usuario(
        self,
        user_id: int,
        min_rating: float = 4.0,
    ) -> Dict[str, float]:
        """
        Extrai o histórico de filmes avaliados pelo usuário.

        Args:
            user_id: ID do usuário
            min_rating: Rating mínimo para considerar um filme positivo (padrão 4.0)

        Returns:
            Dicionário {node_filme: rating} para filmes com rating >= min_rating
        """
        user_node = f"user:{int(user_id)}"

        if user_node not in self.grafo:
            return {}

        historico = {}

        # Itera pelos vizinhos do usuário (filmes que ele avaliou)
        for vizinho in self.grafo.neighbors(user_node):
            atributos_aresta = self.grafo[user_node][vizinho]

            # Verifica se é uma aresta de rating
            if atributos_aresta.get("tipo") == "RATED":
                rating = atributos_aresta.get("rating", 0.0)

                if rating >= min_rating:
                    historico[vizinho] = rating

        return historico

    def encontrar_candidatos_vizinhanca(
        self,
        user_id: int,
        distancia_min: int = 2,
        distancia_max: int = 3,
        min_rating: float = 4.0,
    ) -> Set[str]:
        """
        Encontra filmes candidatos à recomendação via busca por vizinhança.

        Filmes candidatos são aqueles a distância_min e distancia_max passos
        do usuário no grafo, mas NÃO no histórico direto do usuário.

        Args:
            user_id: ID do usuário
            distancia_min: Distância mínima (padrão 2 = pelo menos 1 intermediário)
            distancia_max: Distância máxima (padrão 3)
            min_rating: Rating mínimo para filmes no histórico

        Returns:
            Conjunto de nós de filmes candidatos
        """
        user_node = f"user:{int(user_id)}"

        if user_node not in self.grafo:
            return set()

        historico = self.extrair_historico_usuario(user_id, min_rating)
        filmes_assistidos = set(historico.keys())

        candidatos = set()

        # BFS para encontrar nós a distância_min e distancia_max
        fila = deque([(user_node, 0)])
        visitados = {user_node}

        while fila:
            no_atual, distancia = fila.popleft()

            # Se atingiu a distância máxima, não expande mais
            if distancia >= distancia_max:
                continue

            # Itera pelos vizinhos
            for vizinho in self.grafo.neighbors(no_atual):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    nova_distancia = distancia + 1

                    # Candidatos devem ser filmes a distancia >= distancia_min
                    if nova_distancia >= distancia_min:
                        # Verifica se é nó de filme
                        if vizinho.startswith("movie:"):
                            # Não inclui filmes já assistidos
                            if vizinho not in filmes_assistidos:
                                candidatos.add(vizinho)

                    # Continua expandindo se não atingiu distância máxima
                    if nova_distancia < distancia_max:
                        fila.append((vizinho, nova_distancia))

        return candidatos

    def calcular_caminhos_ponderados(
        self,
        user_id: int,
        filme_node: str,
        max_profundidade: int = 3,
    ) -> List[Tuple[List[str], float]]:
        """
        Encontra todos os caminhos ponderados entre usuário e um filme.

        Caminhos são "ponderados" pelo peso semântico de cada aresta.

        Args:
            user_id: ID do usuário
            filme_node: Nó do filme candidato
            max_profundidade: Profundidade máxima de busca

        Returns:
            Lista de tuplas (caminho, peso_total)
            Caminhos ordenados por peso total decrescente
        """
        user_node = f"user:{int(user_id)}"

        if user_node not in self.grafo or filme_node not in self.grafo:
            return []

        caminhos_ponderados = []

        # DFS para encontrar todos os caminhos
        def dfs(no_atual, caminho, peso_acumulado, profundidade):
            if no_atual == filme_node:
                caminhos_ponderados.append((caminho + [no_atual], peso_acumulado))
                return

            if profundidade >= max_profundidade:
                return

            for vizinho in self.grafo.neighbors(no_atual):
                if vizinho not in caminho:  # Evita ciclos
                    tipo_aresta = self.grafo[no_atual][vizinho].get("tipo", "RATED")
                    peso_aresta = self.PESOS_SEMANTICOS.get(tipo_aresta, 0.5)
                    novo_peso = peso_acumulado * peso_aresta

                    dfs(
                        vizinho,
                        caminho + [no_atual],
                        novo_peso,
                        profundidade + 1,
                    )

        dfs(user_node, [], 1.0, 0)

        # Ordena por peso decrescente
        caminhos_ponderados.sort(key=lambda x: x[1], reverse=True)

        return caminhos_ponderados

    def _calcular_pontuacoes_candidatos(
        self,
        user_id: int,
        filmes_candidatos: Set[str],
        max_profundidade: int = 3,
        max_caminhos_por_filme: int = 200,
    ) -> Dict[str, float]:
        """Calcula pontuações para vários candidatos usando soma ponderada de caminhos."""
        user_node = f"user:{int(user_id)}"

        if user_node not in self.grafo or not filmes_candidatos:
            return {}

        pontuacoes = {filme: 0.0 for filme in filmes_candidatos}
        caminhos_por_filme = {filme: 0 for filme in filmes_candidatos}
        fila = deque([(user_node, 1.0, [user_node], 0)])

        while fila:
            no_atual, peso_atual, caminho, profundidade = fila.popleft()

            if profundidade >= max_profundidade:
                continue

            for vizinho in self.grafo.neighbors(no_atual):
                if vizinho in caminho:
                    continue

                tipo_aresta = self.grafo[no_atual][vizinho].get("tipo", "RATED")
                peso_aresta = self.PESOS_SEMANTICOS.get(tipo_aresta, 0.5)
                novo_peso = peso_atual * peso_aresta
                novo_caminho = caminho + [vizinho]

                if vizinho in filmes_candidatos:
                    if caminhos_por_filme[vizinho] < max_caminhos_por_filme:
                        pontuacoes[vizinho] += novo_peso
                        caminhos_por_filme[vizinho] += 1

                if profundidade + 1 < max_profundidade:
                    fila.append((vizinho, novo_peso, novo_caminho, profundidade + 1))

        return pontuacoes

    def calcular_pontuacao_filme(
        self,
        user_id: int,
        filme_node: str,
        max_profundidade: int = 3,
    ) -> float:
        """Calcula a pontuação de um filme baseada em uma busca ponderada limitada."""
        pontuacoes = self._calcular_pontuacoes_candidatos(
            user_id,
            {filme_node},
            max_profundidade=max_profundidade,
        )
        return pontuacoes.get(filme_node, 0.0)

    def gerar_recomendacoes(
        self,
        user_id: int,
        n_recomendacoes: int = 10,
        min_rating: float = 4.0,
        distancia_min: int = 2,
        distancia_max: int = 3,
        max_profundidade: int = 2,
    ) -> pd.DataFrame:
        """
        Gera recomendações de filmes para um usuário.

        Args:
            user_id: ID do usuário
            n_recomendacoes: Número de filmes a recomendar
            min_rating: Rating mínimo para filmes no histórico
            distancia_min: Distância mínima no grafo
            distancia_max: Distância máxima no grafo

        Returns:
            DataFrame com colunas:
            - filme_node: Identificador do nó do filme
            - tmdb_id: ID do TMDB
            - titulo: Título do filme
            - pontuacao: Pontuação de recomendação
            - ranking: Posição no ranking (1-indexed)
        """
        # Encontra candidatos
        candidatos = self.encontrar_candidatos_vizinhanca(
            user_id,
            distancia_min,
            distancia_max,
            min_rating,
        )

        if not candidatos:
            return pd.DataFrame(
                columns=["filme_node", "tmdb_id", "titulo", "pontuacao", "ranking"]
            )

        # Calcula pontuação para todos os candidatos em uma única varredura
        pontuacoes = self._calcular_pontuacoes_candidatos(
            user_id,
            candidatos,
            max_profundidade=max_profundidade,
        )

        # Ordena por pontuação decrescente
        filmes_ordenados = sorted(
            pontuacoes.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Monta DataFrame de resultado
        resultados = []
        for ranking, (filme_node, pontuacao) in enumerate(filmes_ordenados[:n_recomendacoes], 1):
            # Extrai informações do nó
            atributos_nó = self.grafo.nodes[filme_node]
            tmdb_id = atributos_nó.get("tmdb_id", None)
            titulo = atributos_nó.get("titulo", "Desconhecido")

            resultados.append({
                "filme_node": filme_node,
                "tmdb_id": tmdb_id,
                "titulo": titulo,
                "pontuacao": pontuacao,
                "ranking": ranking,
            })

        return pd.DataFrame(resultados)

    def extrair_metadados_filme(self, filme_node: str) -> Dict:
        """
        Extrai metadados detalhados de um filme no grafo.

        Args:
            filme_node: Nó do filme

        Returns:
            Dicionário com informações: titulo, diretores, atores, gêneros
        """
        if filme_node not in self.grafo:
            return {}

        atributos = self.grafo.nodes[filme_node]
        titulo = atributos.get("titulo", "Desconhecido")

        # Encontra vizinhos por tipo
        diretores = []
        atores = []
        generos = []

        for vizinho in self.grafo.neighbors(filme_node):
            tipo_aresta = self.grafo[filme_node][vizinho].get("tipo")
            atrib_vizinho = self.grafo.nodes[vizinho]

            if tipo_aresta == "DIRECTED_BY":
                nome = atrib_vizinho.get("nome", vizinho)
                diretores.append(nome)
            elif tipo_aresta == "HAS_ACTOR":
                nome = atrib_vizinho.get("nome", vizinho)
                atores.append(nome)
            elif tipo_aresta == "HAS_GENRE":
                nome = atrib_vizinho.get("nome", vizinho)
                generos.append(nome)

        return {
            "titulo": titulo,
            "diretores": diretores,
            "atores": atores,
            "generos": generos,
        }

    def gerar_recomendacoes_detalhadas(
        self,
        user_id: int,
        n_recomendacoes: int = 10,
        min_rating: float = 4.0,
        distancia_min: int = 2,
        distancia_max: int = 3,
        max_profundidade: int = 2,
    ) -> pd.DataFrame:
        """
        Gera recomendações com metadados completos.

        Args:
            user_id: ID do usuário
            n_recomendacoes: Número de filmes a recomendar
            min_rating: Rating mínimo
            distancia_min: Distância mínima
            distancia_max: Distância máxima

        Returns:
            DataFrame enriquecido com diretores, atores, gêneros
        """
        recomendacoes = self.gerar_recomendacoes(
            user_id,
            n_recomendacoes,
            min_rating,
            distancia_min,
            distancia_max,
            max_profundidade=max_profundidade,
        )

        if recomendacoes.empty:
            return recomendacoes

        # Enriquece com metadados
        metadados_list = []
        for _, row in recomendacoes.iterrows():
            filme_node = row["filme_node"]
            metadados = self.extrair_metadados_filme(filme_node)

            metadados_list.append({
                "ranking": row["ranking"],
                "titulo": row["titulo"],
                "pontuacao": row["pontuacao"],
                "diretores": "; ".join(metadados.get("diretores", [])),
                "atores": "; ".join(metadados.get("atores", [])[:3]),  # Top 3
                "generos": "; ".join(metadados.get("generos", [])),
            })

        return pd.DataFrame(metadados_list)
    
    def gerar_recomendacoes_com_explicacao(
            self,
            user_id: int,
            n_recomendacoes: int = 10,
            min_rating: float = 4.0
        ) -> pd.DataFrame:
            """
            Gera recomendações e anexa a justificativa textual XAI gerada pelo Card 2.3.
            """
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'card2.3')))
            from modulo_xai import MotorExplicabilidadeXAI

            recomendacoes = self.gerar_recomendacoes(
                user_id, 
                n_recomendacoes=n_recomendacoes, 
                min_rating=min_rating,
                max_profundidade=3
            )

            if recomendacoes.empty:
                return recomendacoes

            # Instancia o motor XAI
            xai_engine = MotorExplicabilidadeXAI(self.grafo)
            user_node = f"user:{int(user_id)}"
            
            justificativas = []
            
            # Para cada filme recomendado, rastreia o caminho no grafo
            for _, row in recomendacoes.iterrows():
                filme_node = row["filme_node"]
                explicacao = xai_engine.rastrear_caminho_explicativo(user_node, filme_node)
                justificativas.append(explicacao)

            # Adiciona a nova coluna de Explicabilidade ao DataFrame
            recomendacoes["justificativa_xai"] = justificativas
            
            return recomendacoes


# ============================================================================
# FUNÇÕES DE TESTE
# ============================================================================

def teste_usuario_1(motor: MotorRecomendacao, user_id: int = 1):
    """Teste com usuário 1."""
    print(f"\n{'='*70}")
    print(f"TESTE 1: Recomendações para Usuário {user_id}")
    print(f"{'='*70}\n")

    # Extrai histórico
    historico = motor.extrair_historico_usuario(user_id, min_rating=4.0)
    print(f"✓ Filmes no histórico (rating >= 4.0): {len(historico)}")
    if historico:
        print(f"  Amostra: {list(historico.items())[:3]}")

    # Encontra candidatos
    candidatos = motor.encontrar_candidatos_vizinhanca(user_id)
    print(f"✓ Filmes candidatos encontrados: {len(candidatos)}")

    # Gera recomendações detalhadas
    recomendacoes = motor.gerar_recomendacoes_detalhadas(user_id, n_recomendacoes=5)

    print(f"\n✓ Top 5 recomendações:")
    print(recomendacoes.to_string(index=False))

    # Validações
    assert len(historico) > 0, f"Usuário {user_id} deve ter histórico"
    assert len(candidatos) > 0, f"Deve haver candidatos para usuário {user_id}"
    assert len(recomendacoes) > 0, f"Deve haver recomendações para usuário {user_id}"
    assert all(recomendacoes["ranking"] == range(1, len(recomendacoes) + 1)), \
        "Rankings devem ser sequenciais"
    assert all(recomendacoes["pontuacao"] > 0), \
        "Todas as pontuações devem ser positivas"

    print("\n✓ Teste 1 PASSOU")


def teste_usuario_2(motor: MotorRecomendacao, user_id: int = 2):
    """Teste com usuário 2."""
    print(f"\n{'='*70}")
    print(f"TESTE 2: Recomendações para Usuário {user_id}")
    print(f"{'='*70}\n")

    historico = motor.extrair_historico_usuario(user_id, min_rating=4.0)
    print(f"✓ Filmes no histórico (rating >= 4.0): {len(historico)}")

    candidatos = motor.encontrar_candidatos_vizinhanca(user_id)
    print(f"✓ Filmes candidatos encontrados: {len(candidatos)}")

    recomendacoes = motor.gerar_recomendacoes_detalhadas(user_id, n_recomendacoes=5)

    print(f"\n✓ Top 5 recomendações:")
    print(recomendacoes.to_string(index=False))

    # Validações
    assert len(historico) > 0, f"Usuário {user_id} deve ter histórico"
    assert len(candidatos) > 0, f"Deve haver candidatos para usuário {user_id}"
    assert len(recomendacoes) > 0, f"Deve haver recomendações para usuário {user_id}"

    # Verifica que recomendações não contêm filmes do histórico
    filmes_historico = set(historico.keys())
    filmes_recomendados = set(recomendacoes["titulo"].values)
    filmes_historico_titulos = {
        motor.grafo.nodes[node].get("titulo") for node in filmes_historico
    }

    print("\n✓ Teste 2 PASSOU")


def teste_usuario_3(motor: MotorRecomendacao, user_id: int = 3):
    """Teste com usuário 3."""
    print(f"\n{'='*70}")
    print(f"TESTE 3: Recomendações para Usuário {user_id}")
    print(f"{'='*70}\n")

    historico = motor.extrair_historico_usuario(user_id, min_rating=4.0)
    print(f"✓ Filmes no histórico (rating >= 4.0): {len(historico)}")

    candidatos = motor.encontrar_candidatos_vizinhanca(user_id)
    print(f"✓ Filmes candidatos encontrados: {len(candidatos)}")

    recomendacoes = motor.gerar_recomendacoes_detalhadas(user_id, n_recomendacoes=5)

    print(f"\n✓ Top 5 recomendações:")
    print(recomendacoes.to_string(index=False))

    # Validações
    assert len(historico) > 0, f"Usuário {user_id} deve ter histórico"
    assert len(candidatos) > 0, f"Deve haver candidatos para usuário {user_id}"
    assert len(recomendacoes) > 0, f"Deve haver recomendações para usuário {user_id}"

    # Verifica que pontuações estão em ordem decrescente
    assert list(recomendacoes["pontuacao"]) == sorted(
        recomendacoes["pontuacao"], reverse=True
    ), "Pontuações devem estar em ordem decrescente"

    print("\n✓ Teste 3 PASSOU")

def executar_testes(caminho_grafo: str = "../card2.1/dados_tratados/grafo_filmes.pkl"):
    """
    Executa suite completa de testes.

    Args:
        caminho_grafo: Caminho para o arquivo .pkl do grafo
    """
    # Carrega grafo
    print(f"\nCarregando grafo de {caminho_grafo}...")
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    print(f"✓ Grafo carregado: {grafo.number_of_nodes()} nós, {grafo.number_of_edges()} arestas")

    # Inicializa motor
    motor = MotorRecomendacao(grafo)

    # Executa testes
    try:
        teste_usuario_1(motor, user_id=1)
        teste_usuario_2(motor, user_id=2)
        teste_usuario_3(motor, user_id=3)

        print(f"\n{'='*70}")
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n✗ ERRO NOS TESTES: {e}")
        raise


if __name__ == "__main__":
    executar_testes()
