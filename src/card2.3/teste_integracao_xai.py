import sys
import os
import pickle

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # Aponta para src/card2.3/
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..')) # Volta para src/
sys.path.append(os.path.join(SRC_DIR, 'card2.2'))

# importar o motor do card 2.2
from motor_recomendacao import MotorRecomendacao

def rodar_teste_end_to_end():
    # Caminho para o grafo já gerado
    caminho_grafo = os.path.join(SRC_DIR, 'card2.1', 'dados_tratados', 'grafo_filmes.pkl')    
    
    print("\n" + "="*50)
    print("TESTE DE INTEGRAÇÃO DO SISTEMA DE RECOMENDAÇÃO XAI")
    print("="*50)
    
    print(f"\nCarregando o grafo de: {caminho_grafo}...")
    try:
        with open(caminho_grafo, "rb") as f:
            grafo = pickle.load(f)
        print(f"Grafo carregado com sucesso! ({grafo.number_of_nodes()} nós)")
    except FileNotFoundError:
        print("Erro: Arquivo do grafo não encontrado. Verifique se o Card 2.1 foi executado.")
        return
        
    print("Instanciando o Motor de Recomendação...")
    user_test = 42
    user_node_alvo = f"user:{user_test}"
    
    # --- TESTE DE ABLAÇÃO ESTRUTURAL --------------------------------- (tratando somente o conteúdo)
    # nos_permitidos = []
    
    # for n in grafo.nodes():
    #     node_str = str(n).lower()
        
    #     # ignorar os nós que geram conexões muito amplas (Gêneros), e a filtragem colaborativa (Usuários)
    #     if 'genre' in node_str:
    #         continue   
    #     if 'user' in node_str and str(n) != user_node_alvo:
    #         continue
            
    #     nos_permitidos.append(n)
            
    # # criar uma cópia do grafo contendo apenas o conteúdo
    # grafo_ablacao = grafo.subgraph(nos_permitidos)
    
    # print(f"Grafo reduzido de {grafo.number_of_nodes()} para {grafo_ablacao.number_of_nodes()} nós.")
    # print("Gêneros e outros usuários foram cortados. Foco em Diretores e Atores.")
    
    # --- FIM ABLAÇÃO ESTRUTURAL --------------------------------------------
    
    # Motor de recomendação
    # motor = MotorRecomendacao(grafo_ablacao)
    motor = MotorRecomendacao(grafo)


    
    print(f"Gerando Top 5 recomendações para o usuário {user_test}...\n")
    
    # Gera recomendações com explicação explícita
    recomendacoes = motor.gerar_recomendacoes_com_explicacao(user_id=user_test, n_recomendacoes=5)
    
    if recomendacoes.empty:
        print("Nenhuma recomendação encontrada para este usuário.")
        return

    print("="*50)
    print(f" RESULTADOS FINAIS (Usuário {user_test})")
    print("="*50 + "\n")
    
    # exibe os filmes e a trilha semântica de forma limpa e auditável
    for _, row in recomendacoes.iterrows():
        print(f"[#{row['ranking']}] {row['titulo']} (Score: {row['pontuacao']:.6f})")
        print(f"{row['justificativa_xai']}\n")

if __name__ == "__main__":
    rodar_teste_end_to_end()
