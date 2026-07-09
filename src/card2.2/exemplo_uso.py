#!/usr/bin/env python3
"""
Exemplo de uso prático do motor de recomendação.

Este script demonstra como usar a API do motor para gerar
recomendações personalizadas para usuários específicos.

Uso:
    python exemplo_uso.py
"""

import argparse
import pickle
from pathlib import Path
import pandas as pd

from motor_recomendacao import MotorRecomendacao


def localizar_grafo() -> Path:
    """Localiza o arquivo do grafo em diferentes possíveis caminhos."""
    base_dir = Path(__file__).resolve().parent
    caminhos_possiveis = [
        base_dir / "dados_tratados" / "grafo_filmes.pkl",
        base_dir.parent / "card2.1" / "dados_tratados" / "grafo_filmes.pkl",
        base_dir.parent / "card2.1" / "grafo_filmes.pkl",
    ]

    for caminho in caminhos_possiveis:
        if caminho.exists():
            return caminho

    return caminhos_possiveis[0]


def exemplo_1_usuario_especifico():
    """Exemplo 1: Gerar recomendações para um usuário específico."""
    print("\n" + "="*70)
    print("EXEMPLO 1: Recomendações Personalizadas para Usuário Específico")
    print("="*70)

    # Carrega grafo
    caminho_grafo = localizar_grafo()
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    motor = MotorRecomendacao(grafo)

    # Gera recomendações para usuário 42
    user_id = 42
    print(f"\nGerando recomendações para usuário {user_id}...\n")

    recomendacoes = motor.gerar_recomendacoes_detalhadas(
        user_id=user_id,
        n_recomendacoes=10,
        min_rating=4.0,
        distancia_min=2,
        distancia_max=3,
        max_profundidade=3,
    )

    print("TOP 10 RECOMENDAÇÕES:")
    print(recomendacoes.to_string(index=False))

    # Salva resultado em CSV
    csv_output = f"recomendacoes_usuario_{user_id}.csv"
    recomendacoes.to_csv(csv_output, index=False)
    print(f"\n✓ Resultados salvos em {csv_output}")


def exemplo_2_comparar_usuarios():
    """Exemplo 2: Comparar recomendações de múltiplos usuários."""
    print("\n" + "="*70)
    print("EXEMPLO 2: Comparação de Recomendações Entre Usuários")
    print("="*70)

    caminho_grafo = localizar_grafo()
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    motor = MotorRecomendacao(grafo)

    usuarios = [1, 2, 5]
    print(f"\nComparando recomendações para usuários: {usuarios}\n")

    for user_id in usuarios:
        print(f"\n--- Usuário {user_id} ---")

        # Histórico
        historico = motor.extrair_historico_usuario(user_id, min_rating=4.0)
        print(f"Filmes avaliados (rating >= 4.0): {len(historico)}")

        # Recomendações
        recomendacoes = motor.gerar_recomendacoes_detalhadas(
            user_id=user_id,
            n_recomendacoes=3,
            min_rating=4.0,
            distancia_min=2,
            distancia_max=3,
            max_profundidade=3,
        )

        if not recomendacoes.empty:
            for _, row in recomendacoes.iterrows():
                print(f"  #{row['ranking']}: {row['titulo']} (score: {row['pontuacao']:.3f})")


def exemplo_3_analisar_um_filme():
    """Exemplo 3: Análise detalhada de um filme candidato."""
    print("\n" + "="*70)
    print("EXEMPLO 3: Análise Detalhada de Caminhos para um Filme")
    print("="*70)

    caminho_grafo = localizar_grafo()
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    motor = MotorRecomendacao(grafo)

    user_id = 1
    print(f"\nAnalisando caminhos para recomendações do usuário {user_id}...\n")

    # Obtém candidatos
    candidatos = motor.encontrar_candidatos_vizinhanca(user_id)
    print(f"Total de candidatos: {len(candidatos)}\n")

    # Analisa top 3 candidatos
    candidatos_analisados = []
    for filme_node in list(candidatos)[:3]:
        pontuacao = motor.calcular_pontuacao_filme(user_id, filme_node)
        caminhos = motor.calcular_caminhos_ponderados(user_id, filme_node, max_profundidade=3)
        metadados = motor.extrair_metadados_filme(filme_node)

        candidatos_analisados.append({
            "filme_node": filme_node,
            "titulo": metadados.get("titulo", "?"),
            "pontuacao": pontuacao,
            "num_caminhos": len(caminhos),
            "diretores": metadados.get("diretores"),
            "atores": metadados.get("atores"),
        })

    # Exibe análise
    for candidato in candidatos_analisados:
        print(f"Filme: {candidato['titulo']}")
        print(f"  Pontuação: {candidato['pontuacao']:.4f}")
        print(f"  Caminhos encontrados: {candidato['num_caminhos']}")
        print(f"  Diretores: {', '.join(candidato['diretores'][:2]) if candidato['diretores'] else 'N/A'}")
        print(f"  Atores: {', '.join(candidato['atores'][:2]) if candidato['atores'] else 'N/A'}")
        print()


def exemplo_4_variar_parametros():
    """Exemplo 4: Teste com diferentes parâmetros."""
    print("\n" + "="*70)
    print("EXEMPLO 4: Teste de Diferentes Parâmetros")
    print("="*70)

    caminho_grafo = localizar_grafo()
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    motor = MotorRecomendacao(grafo)
    user_id = 1

    print(f"\nTestando diferentes configurações para usuário {user_id}...\n")

    configuracoes = [
        {
            "nome": "Recomendações mais próximas (distância máx 2)",
            "params": {"user_id": user_id, "n_recomendacoes": 5, "distancia_max": 2},
        },
        {
            "nome": "Recomendações mais distantes (distância máx 4)",
            "params": {"user_id": user_id, "n_recomendacoes": 5, "distancia_max": 4},
        },
        {
            "nome": "Apenas filmes com rating muito alto (min_rating 4.5)",
            "params": {"user_id": user_id, "n_recomendacoes": 5, "min_rating": 4.5},
        },
        {
            "nome": "Top 3 recomendações",
            "params": {"user_id": user_id, "n_recomendacoes": 3},
        },
    ]

    for config in configuracoes:
        print(f"\n{config['nome']}:")
        print("-" * 60)

        params = dict(config["params"])
        params.update({
            "min_rating": 4.0,
            "distancia_min": 2,
            "distancia_max": 3,
            "max_profundidade": 3,
        })
        recomendacoes = motor.gerar_recomendacoes_detalhadas(**params)

        if recomendacoes.empty:
            print("  (nenhuma recomendação)")
        else:
            for _, row in recomendacoes.iterrows():
                print(f"  #{row['ranking']}: {row['titulo']} (score: {row['pontuacao']:.3f})")


def exemplo_5_exportar_relatorio():
    """Exemplo 5: Gerar relatório de recomendações para múltiplos usuários."""
    print("\n" + "="*70)
    print("EXEMPLO 5: Gerar Relatório de Recomendações")
    print("="*70)

    caminho_grafo = localizar_grafo()
    with open(caminho_grafo, "rb") as f:
        grafo = pickle.load(f)

    motor = MotorRecomendacao(grafo)

    # Obtém lista de usuários
    usuarios = [
        node for node, attrs in grafo.nodes(data=True)
        if attrs.get("tipo") == "user"
    ]

    print(f"\nGerando recomendações para {len(usuarios[:5])} usuários...\n")

    resultados_consolidados = []

    for user_node in usuarios[:5]:
        user_id = int(user_node.split(":")[1])

        recomendacoes = motor.gerar_recomendacoes_detalhadas(
            user_id=user_id,
            n_recomendacoes=3,
            min_rating=4.0,
            distancia_min=2,
            distancia_max=3,
            max_profundidade=3,
        )

        for _, row in recomendacoes.iterrows():
            resultados_consolidados.append({
                "usuario_id": user_id,
                "ranking": row["ranking"],
                "filme": row["titulo"],
                "pontuacao": row["pontuacao"],
            })

    df_consolidado = pd.DataFrame(resultados_consolidados)

    print("RELATÓRIO CONSOLIDADO:")
    print(df_consolidado.to_string(index=False))

    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    print(f"  Total de recomendações: {len(df_consolidado)}")
    print(f"  Pontuação média: {df_consolidado['pontuacao'].mean():.4f}")
    print(f"  Pontuação máxima: {df_consolidado['pontuacao'].max():.4f}")
    print(f"  Pontuação mínima: {df_consolidado['pontuacao'].min():.4f}")

    # Salva relatório
    df_consolidado.to_csv("relatorio_recomendacoes.csv", index=False)
    print(f"\n✓ Relatório salvo em relatorio_recomendacoes.csv")


def main():
    """Executa o exemplo principal por padrão e, opcionalmente, todos os exemplos."""
    parser = argparse.ArgumentParser(description="Exemplos de uso do motor de recomendação")
    parser.add_argument("--exemplo1", action="store_true", help="Executar apenas o exemplo 1")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("EXEMPLOS DE USO DO MOTOR DE RECOMENDAÇÃO")
    print("="*70)

    # Verifica se o grafo existe
    caminho_grafo = localizar_grafo()
    if not caminho_grafo.exists():
        print("\n✗ ERRO: Arquivo grafo_filmes.pkl não encontrado!")
        print("\nGere o grafo primeiro usando:")
        print("  cd ../card2.1")
        print("  python carregar_grafo.py \\")
        print("    --tmdb-pkl ../card1.1/dados_tratados/tmdb_grafo_limpo.pkl \\")
        print("    --movielens-csv ../card1.1/dados_tratados/conexoes_usuario_filme.csv \\")
        print("    --saida-grafo dados_tratados/grafo_filmes.pkl")
        return

    try:
        if args.exemplo1:
            exemplo_1_usuario_especifico()
            print("\n" + "="*70)
            print("✓ EXEMPLO 1 EXECUTADO COM SUCESSO!")
            print("="*70 + "\n")
        else:
            exemplo_1_usuario_especifico()
            exemplo_2_comparar_usuarios()
            exemplo_3_analisar_um_filme()
            exemplo_4_variar_parametros()
            exemplo_5_exportar_relatorio()
            print("\n" + "="*70)
            print("✓ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
            print("="*70 + "\n")

    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
