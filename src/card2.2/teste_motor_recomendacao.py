#!/usr/bin/env python3
"""
Script de teste do motor de recomendação.

Executa testes automatizados com 3 usuários distintos para validar
a coerência lógica do algoritmo de recomendação.

Uso:
    python teste_motor_recomendacao.py

Pré-requisitos:
    - Arquivo dados_tratados/grafo_filmes.pkl gerado pelo card2.1
"""

import sys
from pathlib import Path

# Adiciona diretório pai ao path para importar motor_recomendacao
sys.path.insert(0, str(Path(__file__).parent))

from motor_recomendacao import MotorRecomendacao
import pickle


def validar_estrutura_grafo(grafo):
    """Valida se o grafo tem a estrutura esperada."""
    print("\n" + "="*70)
    print("VALIDAÇÃO DO GRAFO")
    print("="*70)

    # Verifica tipos de nós
    tipos_nos = set()
    for node, atributos in grafo.nodes(data=True):
        tipos_nos.add(atributos.get("tipo"))

    print(f"\n✓ Total de nós: {grafo.number_of_nodes():,}")
    print(f"✓ Total de arestas: {grafo.number_of_edges():,}")
    print(f"✓ Tipos de nós encontrados: {sorted(tipos_nos)}")

    # Valida tipos de arestas
    tipos_arestas = set()
    for _, _, atributos in grafo.edges(data=True):
        tipos_arestas.add(atributos.get("tipo"))

    print(f"✓ Tipos de arestas encontrados: {sorted(tipos_arestas)}")

    # Conta usuários
    usuarios = [n for n, a in grafo.nodes(data=True) if a.get("tipo") == "user"]
    print(f"✓ Total de usuários: {len(usuarios)}")

    # Valida que tem 5 tipos de nós
    tipos_esperados = {"user", "movie", "director", "actor", "genre"}
    if tipos_esperados.issubset(tipos_nos):
        print("✓ Grafo possui todos os 5 tipos de nós esperados")
    else:
        raise ValueError(f"Faltam tipos de nós: {tipos_esperados - tipos_nos}")

    return usuarios


def teste_completo_usuario(motor, user_id, numero_teste):
    """Executa teste completo para um usuário."""
    print(f"\n{'='*70}")
    print(f"TESTE {numero_teste}: Usuário ID = {user_id}")
    print(f"{'='*70}\n")

    # Passo 1: Extrai histórico
    print("PASSO 1: Extração de histórico")
    print("-" * 70)
    historico = motor.extrair_historico_usuario(user_id, min_rating=4.0)
    print(f"✓ Filmes com rating >= 4.0: {len(historico)}")

    if not historico:
        print(f"⚠ Usuário {user_id} não tem histórico suficiente")
        return False

    # Mostra amostra
    amostra = list(historico.items())[:3]
    for filme_node, rating in amostra:
        titulo = motor.grafo.nodes[filme_node].get("titulo", "?")
        print(f"  - {titulo} (rating: {rating})")

    # Passo 2: Encontra candidatos
    print("\nPASSO 2: Busca por vizinhança")
    print("-" * 70)
    candidatos = motor.encontrar_candidatos_vizinhanca(
        user_id,
        distancia_min=2,
        distancia_max=3,
    )
    print(f"✓ Candidatos a distância 2-3: {len(candidatos)}")

    if not candidatos:
        print(f"⚠ Nenhum candidato encontrado para usuário {user_id}")
        return False

    # Passo 3: Gera recomendações
    print("\nPASSO 3: Geração de recomendações")
    print("-" * 70)
    recomendacoes = motor.gerar_recomendacoes_detalhadas(
        user_id,
        n_recomendacoes=10,
        max_profundidade=3,
    )

    if recomendacoes.empty:
        print(f"⚠ Nenhuma recomendação gerada para usuário {user_id}")
        return False

    print(f"✓ Top 10 recomendações geradas:\n")
    print(recomendacoes.to_string(index=False))

    print(f"\n✓ TESTE {numero_teste} PASSOU\n")
    return True


def main():
    """Função principal."""
    # Resolve o caminho do grafo a partir do diretório do script
    base_dir = Path(__file__).resolve().parent
    caminhos_possiveis = [
        base_dir / "dados_tratados" / "grafo_filmes.pkl",
        base_dir.parent / "card2.1" / "dados_tratados" / "grafo_filmes.pkl",
        base_dir.parent / "card2.1" / "grafo_filmes.pkl",
    ]

    caminho_grafo = None
    for caminho in caminhos_possiveis:
        if caminho.exists():
            caminho_grafo = caminho
            break

    print("\n" + "="*70)
    print("TESTE DO MOTOR DE RECOMENDAÇÃO")
    print("="*70)

    if caminho_grafo is None:
        print("\n✗ ERRO: Arquivo grafo_filmes.pkl não encontrado!")
        print("\nPrecisa gerar o grafo primeiro usando:")
        print("  cd ../card2.1")
        print("  python carregar_grafo.py \\")
        print("    --tmdb-pkl ../card1.1/dados_tratados/tmdb_grafo_limpo.pkl \\")
        print("    --movielens-csv ../card1.1/dados_tratados/conexoes_usuario_filme.csv \\")
        print("    --saida-grafo dados_tratados/grafo_filmes.pkl")
        sys.exit(1)

    # Carrega grafo
    print(f"\nCarregando grafo de {caminho_grafo}...")
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    print(f"✓ Grafo carregado com sucesso")

    # Valida grafo
    usuarios = validar_estrutura_grafo(grafo)

    # Inicializa motor
    motor = MotorRecomendacao(grafo)

    # Seleciona 3 usuários para teste
    usuarios_teste = usuarios[:3]
    print(f"\n✓ Usuários selecionados para teste: {usuarios_teste}")

    # Executa testes
    resultados = []
    try:
        for i, user_id in enumerate(usuarios_teste, 1):
            # Extrai ID do nó
            user_id_int = int(user_id.split(":")[1])
            resultado = teste_completo_usuario(motor, user_id_int, i)
            resultados.append(resultado)

        if all(resultados):
            print("\n✓ TESTES FINALIZADOS COM SUCESSO")
            sys.exit(0)
        else:
            print("\n✗ ALGUNS TESTES FALHARAM")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ ERRO DURANTE TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
