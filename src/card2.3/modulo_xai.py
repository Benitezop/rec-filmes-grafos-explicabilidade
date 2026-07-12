import networkx as nx

class MotorExplicabilidadeXAI:
    """
    Módulo de Inteligência Artificial Explicável (XAI) para o Sistema de Recomendação.
    Gera justificativas em linguagem natural baseadas nos caminhos estruturais do grafo heterogêneo.
    """
    def __init__(self, grafo: nx.Graph):
        self.grafo = grafo
        
        self.templates = {
            'DIRECTED_BY': "que também foi dirigido por {entidade}",
            'HAS_ACTOR': "que também estrelou {entidade}",
            'HAS_GENRE': "que pertence ao gênero {entidade}"
        }

    def rastrear_caminho_explicativo(self, user_node: str, recommended_movie_node: str) -> str:
            """
            Mapeia a conexão lógica entre o usuário e o filme recomendado e converte em texto legível.
            """
            try: # encontra os menores caminhos entre o usuário e o filme alvo
                caminhos = list(nx.all_shortest_paths(self.grafo, source=user_node, target=recommended_movie_node))
                
                if not caminhos:
                    return "Recomendação gerada com base na proximidade estrutural global."

                # o caminho precisa de no mínimo 4 nós para ter sentido lógico. [Usuário -> Filme Base -> Elo Semântico -> Filme Recomendado]
                caminho_xai = None
                for c in caminhos:
                    if len(c) == 4:
                        caminho_xai = c
                        break
                
                if caminho_xai:
                    filme_assistido_id = caminho_xai[1]
                    entidade_id = caminho_xai[2]

                    nome_filme_assistido = self.grafo.nodes[filme_assistido_id].get('titulo', 'um filme do seu histórico')
                    tipo_entidade = self.grafo.nodes[entidade_id].get('type', '')
                    if 'user' in str(entidade_id) or tipo_entidade == 'user':
                        numero_usuario = str(entidade_id).split(':')[-1].replace('u_', '') # retornar ID de usuário formatado
                        nome_entidade = f"outros usuários (ex: Usuário {numero_usuario})"
                    else:
                        nome_entidade = self.grafo.nodes[entidade_id].get('nome', f"Entidade ID [{str(entidade_id).split(':')[-1]}]")

                    aresta_dados = self.grafo.get_edge_data(filme_assistido_id, entidade_id)
                    if not aresta_dados:
                        aresta_dados = self.grafo.get_edge_data(entidade_id, filme_assistido_id)
                        
                    tipo_aresta = aresta_dados.get('tipo', 'DESCONHECIDO') if aresta_dados else 'DESCONHECIDO'

                    # Expandindo os templates estruturados
                    self.templates = {
                        'DIRECTED_BY': "que também foi dirigido por {entidade}",
                        'HAS_ACTOR': "que também estrelou {entidade}",
                        'HAS_GENRE': "que pertence ao gênero {entidade}",
                        'HAS_KEYWORD': "que compartilha o tema '{entidade}'",
                        'PRODUCED_BY': "que também foi produzido por {entidade}",
                        'BELONGS_TO_COLLECTION': "que faz parte da mesma franquia/coleção",
                        'RATED': "que também é muito bem avaliado por {entidade}, que tem perfil similar ao seu"
                    }

                    # Retornando um texto explicativo com base no tipo de aresta, para gerar a frase de relação
                    if tipo_aresta in self.templates:
                        frase_relacao = self.templates[tipo_aresta].format(entidade=nome_entidade)
                    else:
                        frase_relacao = f"que compartilha a conexão estrutural '{tipo_aresta}' com {nome_entidade}"

                    aviso_amplo = ""
                    if tipo_aresta == 'HAS_GENRE':
                        aviso_amplo = " (Nota: Sugestão baseada em categoria ampla de gênero)"

                    return f"Recomendado porque você assistiu '{nome_filme_assistido}', {frase_relacao}.{aviso_amplo}"

                grau_separacao = len(caminhos[0]) - 1
                return f"Recomendado por grau de separação profundo (Distância semântica: {grau_separacao})."

            except nx.NetworkXNoPath:
                return "Caminho não encontrado no grafo."
            except Exception as e:
                return f"Erro interno no módulo XAI: {str(e)}"