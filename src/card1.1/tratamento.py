import pandas as pd
import ast

# carregando os dados
movies = pd.read_csv('dados_originais/tmdb_5000_movies.csv')
credits = pd.read_csv('dados_originais/tmdb_5000_credits.csv')

# unindo os datasets usando o ID do filme
df = pd.merge(movies, credits, left_on='id', right_on='movie_id')

# funções de extração
def extrair_generos(x):
    try:
        return [i['name'] for i in ast.literal_eval(x)] # pegar apenas os nomes dos gêneros
    except:
        return []

def extrair_diretor(x):
    try:
        for i in ast.literal_eval(x):
            if i['job'] == 'Director':  # procurar pelo cargo de Diretor
                return [i['name']] # retornar como lista para manter o padrão
        return []
    except:
        return []

def extrair_top_atores(x, limite=5):
    try:
        cast = ast.literal_eval(x)
        return [i['name'] for i in cast[:limite]] # pegar apenas os nomes dos atores principais para não poluir o grafo
    except:
        return []

# aplicar as funções e criar um dataframe limpo
df['genres_clean'] = df['genres'].apply(extrair_generos)
df['director_clean'] = df['crew'].apply(extrair_diretor)
df['cast_clean'] = df['cast'].apply(extrair_top_atores)

# deixar apenas as colunas que importam para o NetworkX
df_grafo = df[['id', 'original_title', 'genres_clean', 'director_clean', 'cast_clean']]

# salvar o resultado final
caminho_arquivo = 'tratamento/tmdb_grafo_limpo.pkl'
df_grafo.to_pickle(caminho_arquivo) # salvar em formato .pkl para que as propriedades Python se mantenham
