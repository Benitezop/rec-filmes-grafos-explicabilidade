import pandas as pd
import networkx as nx

# 1. Carregar as bases de dados
# O DataFrame estruturado com listas nativas que salvamos na Etapa 2
df_filmes = pd.read_pickle('dados_tratados/tmdb_grafo_limpo.pkl') 
# O arquivo do MovieLens contendo as conexões
df_conexoes = pd.read_csv('dados_tratados/conexoes_usuario_filme.csv') 

# 2. Inicializar o Grafo
# Utilizamos um grafo não-direcionado, ideal para identificar proximidade
# estrutural entre entidades em mecanismos de recomendação.
G = nx.Graph()

# 3. Modelagem de Conteúdo Semântico (Nós: Filmes, Gêneros, Diretores e Atores)
print("Construindo nós semânticos da base TMDB...")
for _, row in df_filmes.iterrows():
    movie_id = f"m_{row['id']}"
    
    # Adicionar o nó central: Filme
    G.add_node(movie_id, name=row['original_title'], type='movie')
    
    # Conexões de Gênero
    for genre in row['genres_clean']:
        genre_id = f"g_{genre}" # Transformando o texto do gênero em ID (ex: g_Action)
        G.add_node(genre_id, name=genre, type='genre')
        G.add_edge(movie_id, genre_id, relation='belongs_to_genre')
        
    # Conexões de Diretor
    for director in row['director_clean']:
        director_id = f"d_{director}"
        G.add_node(director_id, name=director, type='director')
        G.add_edge(movie_id, director_id, relation='directed_by')
        
    # Conexões de Elenco
    for actor in row['cast_clean']:
        actor_id = f"a_{actor}"
        G.add_node(actor_id, name=actor, type='actor')
        G.add_edge(movie_id, actor_id, relation='acted_in')

# 4. Modelagem de Interação Colaborativa (Nós: Usuários)
print("Integrando interações dos usuários do MovieLens...")
for _, row in df_conexoes.iterrows():
    user_id = f"u_{int(row['userId'])}"
    # Utilizamos o tmdb_movie_id mapeado no CSV para criar o gancho com o TMDB
    movie_id = f"m_{int(row['tmdb_movie_id'])}"
    rating = float(row['rating'])
    
    # Verifica se o filme avaliado realmente existe na base limpa que criamos
    # Isso é vital para evitar "nós soltos" (dead ends) no seu grafo
    if G.has_node(movie_id):
        G.add_node(user_id, type='user')
        # A nota do usuário é inserida como peso (weight) da aresta
        G.add_edge(user_id, movie_id, relation='watched_and_rated', weight=rating)

# 5. Validação da Estrutura
print("\n------------ INTEGRACAO DE DADOS ------------")
print(f"Total de Nós criados: {G.number_of_nodes()}")
print(f"Total de Arestas criadas: {G.number_of_edges()}")

# Visualizando um pequeno teste de vizinhança para confirmar a auditabilidade (XAI)
exemplo_filme = f"m_{df_filmes.iloc[0]['id']}"
print(f"\nExemplo das conexões do filme '{df_filmes.iloc[0]['original_title']}':")
for neighbor in G.neighbors(exemplo_filme):
    # Mostra o ID do nó vizinho e o tipo de relação que os conecta
    print(f" - Ligação com: {neighbor} (Relação: {G[exemplo_filme][neighbor]['relation']})")



    from pyvis.network import Network

# ID do nosso filme alvo
filme_alvo = 'm_19995' # Avatar

# 1. Filtrar a vizinhança para evitar o "Hairball"
vizinhos_filtrados = set([filme_alvo])
limite_usuarios = 3
usuarios_adicionados = 0

# Iterar sobre todos os vizinhos do filme alvo no grafo original 'G'
for vizinho in G.neighbors(filme_alvo):
    tipo_vizinho = G.nodes[vizinho].get('type')
    
    # Se for uma informação semântica (Gênero, Diretor, Ator), adicionamos sempre!
    if tipo_vizinho in ['genre', 'director', 'actor']:
        vizinhos_filtrados.add(vizinho)
        
    # Se for um usuário, adicionamos apenas se não tivermos atingido o limite
    elif tipo_vizinho == 'user' and usuarios_adicionados < limite_usuarios:
        vizinhos_filtrados.add(vizinho)
        usuarios_adicionados += 1

# Criar o subgrafo limpo apenas com os nós que passaram no filtro
subgrafo = G.subgraph(vizinhos_filtrados)

# 2. Configurar o PyVis (Mantém igual ao anterior)
net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')

cores = {
    'movie': '#E50914',   
    'user': '#1DB954',    
    'actor': '#F5C518',   
    'director': '#373B69',
    'genre': '#FFFFFF'    
}

for node, data in subgrafo.nodes(data=True):
    tipo = data.get('type', 'desconhecido')
    cor = cores.get(tipo, '#808080')
    nome = data.get('name', str(node))
    net.add_node(node, label=nome, title=f"Tipo: {tipo}", color=cor)

for source, target, data in subgrafo.edges(data=True):
    relacao = data.get('relation', '')
    net.add_edge(source, target, title=relacao)

# 3. Gerar e abrir
net.show_buttons(filter_=['physics'])
net.show('grafo_limpo_xai.html', notebook=False)