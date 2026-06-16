import pandas as pd

caminho_arquivo = 'dados_tratados/tmdb_grafo_limpo.pkl'
df = pd.read_pickle(caminho_arquivo)

print("--- VISÃO GERAL DOS DADOS ---")
print(df)
# print(df.head())
print("\n" + "="*50 + "\n")

print("--- TESTE DE INTEGRIDADE DAS LISTAS ---")
primeiro_filme = df.iloc[0] 

print(f"Filme: {primeiro_filme['original_title']}")
print(f"Gêneros: {primeiro_filme['genres_clean']} | Tipo: {type(primeiro_filme['genres_clean'])}")
print(f"Diretor: {primeiro_filme['director_clean']} | Tipo: {type(primeiro_filme['director_clean'])}")
print(f"Elenco: {primeiro_filme['cast_clean']} | Tipo: {type(primeiro_filme['cast_clean'])}")