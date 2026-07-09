"""
Arquivo de configuração para o motor de recomendação.

Permite ajustar facilmente:
- Pesos semânticos para diferentes tipos de arestas
- Parâmetros de distância do grafo
- Limites de profundidade
- Thresholds de rating

Uso:
    from config_motor import CONFIG
    motor = MotorRecomendacao(grafo, pesos=CONFIG.PESOS_SEMANTICOS)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Configuracao:
    """Configuração principal do motor de recomendação."""

    # ========== PESOS SEMÂNTICOS ==========
    # Peso de cada tipo de aresta na soma ponderada
    # Valores típicos: 0.1 a 1.0
    # Maior peso = maior relevância para recomendação
    PESOS_SEMANTICOS: Dict[str, float] = None

    # ========== PARÂMETROS DE DISTÂNCIA ==========
    # Distância mínima no grafo para considerar um filme candidato
    # Padrão: 2 (pelo menos 1 intermediário entre usuário e filme)
    DISTANCIA_MIN_PADRAO: int = 2

    # Distância máxima no grafo para busca de candidatos
    # Padrão: 3 (evita explosão combinatória)
    DISTANCIA_MAX_PADRAO: int = 3

    # ========== PARÂMETROS DE RATING ==========
    # Rating mínimo para um filme ser considerado "gostei"
    # Padrão: 4.0 em escala 0.5 a 5.0
    RATING_MIN_PADRAO: float = 4.0

    # ========== PARÂMETROS DE RECOMENDAÇÃO ==========
    # Número padrão de filmes a recomendar
    N_RECOMENDACOES_PADRAO: int = 10

    # ========== PARÂMETROS DE DFS ==========
    # Profundidade máxima para busca de caminhos
    # Padrão: 3 (evita explosão exponencial)
    MAX_PROFUNDIDADE_DFS: int = 3

    # ========== LIMITES DE PERFORMANCE ==========
    # Número máximo de caminhos a encontrar por filme
    # Proteção contra grafo muito denso
    MAX_CAMINHOS_POR_FILME: int = 10000

    # ========== FLAGS DE COMPORTAMENTO ==========
    # Se True, exclui filmes do histórico das recomendações
    EXCLUIR_HISTORICO: bool = True

    # Se True, retorna somente filmes a exatamente distancia_min
    # Se False, retorna filmes entre distancia_min e distancia_max
    APENAS_DISTANCIA_MINIMA: bool = False

    # Se True, normaliza scores por quantidade de caminhos
    # Evita favorecer filmes com muitos caminhos triviais
    NORMALIZAR_POR_CAMINHOS: bool = False

    def __post_init__(self):
        """Inicializa pesos semânticos se não fornecidos."""
        if self.PESOS_SEMANTICOS is None:
            self.PESOS_SEMANTICOS = {
                "DIRECTED_BY": 1.0,      # Diretor: peso máximo
                "HAS_ACTOR": 0.9,        # Ator: peso alto
                "RATED": 0.7,            # Rating: peso médio
                "HAS_GENRE": 0.3,        # Gênero: peso baixo
            }


# ============================================================================
# CONFIGURAÇÕES PRÉ-DEFINIDAS
# ============================================================================

CONFIG_PADRAO = Configuracao()
"""Configuração padrão: balanceada entre precisão e performance."""


CONFIG_CONSERVADOR = Configuracao(
    PESOS_SEMANTICOS={
        "DIRECTED_BY": 1.0,
        "HAS_ACTOR": 0.7,       # Reduzido
        "RATED": 0.6,           # Reduzido
        "HAS_GENRE": 0.2,       # Reduzido
    },
    DISTANCIA_MIN_PADRAO=2,
    DISTANCIA_MAX_PADRAO=2,     # Apenas recomendações muito próximas
    RATING_MIN_PADRAO=4.5,      # Histórico mais restritivo
    MAX_PROFUNDIDADE_DFS=2,
)
"""
Configuração conservadora: favorece recomendações muito similares.
Resultado: Menos recomendações, mas muito alinhadas com preferências.
"""


CONFIG_AGRESSIVO = Configuracao(
    PESOS_SEMANTICOS={
        "DIRECTED_BY": 1.0,
        "HAS_ACTOR": 1.0,        # Aumentado
        "RATED": 0.8,            # Aumentado
        "HAS_GENRE": 0.5,        # Aumentado
    },
    DISTANCIA_MIN_PADRAO=2,
    DISTANCIA_MAX_PADRAO=4,      # Recomendações mais distantes
    RATING_MIN_PADRAO=3.5,       # Histórico mais inclusivo
    MAX_PROFUNDIDADE_DFS=4,
)
"""
Configuração agressiva: favorece recomendações diversas.
Resultado: Mais recomendações variadas, maior risco de imprecisão.
"""


CONFIG_DIRETO_FOCO = Configuracao(
    PESOS_SEMANTICOS={
        "DIRECTED_BY": 1.0,      # Máximo
        "HAS_ACTOR": 0.5,        # Reduzido
        "RATED": 0.7,
        "HAS_GENRE": 0.1,        # Mínimo
    },
)
"""
Configuração focada em diretores: dá máxima relevância ao diretor.
Uso: Usuários que têm cineastas favoritos.
"""


CONFIG_ATOR_FOCO = Configuracao(
    PESOS_SEMANTICOS={
        "DIRECTED_BY": 0.7,
        "HAS_ACTOR": 1.0,        # Máximo
        "RATED": 0.7,
        "HAS_GENRE": 0.2,
    },
)
"""
Configuração focada em atores: dá máxima relevância ao elenco.
Uso: Usuários que tem atores/atrizes favoritos.
"""


CONFIG_GENERO_FOCO = Configuracao(
    PESOS_SEMANTICOS={
        "DIRECTED_BY": 0.6,
        "HAS_ACTOR": 0.6,
        "RATED": 0.8,
        "HAS_GENRE": 1.0,        # Máximo
    },
)
"""
Configuração focada em gêneros: dá máxima relevância ao gênero.
Uso: Usuários que preferem filmes do mesmo gênero.
"""


CONFIG_RAPIDO = Configuracao(
    DISTANCIA_MIN_PADRAO=2,
    DISTANCIA_MAX_PADRAO=2,      # Limita profundidade
    MAX_PROFUNDIDADE_DFS=2,
    MAX_CAMINHOS_POR_FILME=1000,  # Reduz cálculos
)
"""
Configuração otimizada para velocidade.
Use quando precisa de recomendações em tempo real.
"""


CONFIG_PRECISO = Configuracao(
    DISTANCIA_MAX_PADRAO=3,
    MAX_PROFUNDIDADE_DFS=3,
    MAX_CAMINHOS_POR_FILME=10000,  # Explora todos os caminhos
)
"""
Configuração otimizada para precisão.
Use quando quer recomendações mais bem pensadas.
"""


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def criar_config_personalizada(
    pesos_diretor: float = 1.0,
    pesos_ator: float = 0.9,
    pesos_rating: float = 0.7,
    pesos_genero: float = 0.3,
    distancia_max: int = 3,
    rating_minimo: float = 4.0,
) -> Configuracao:
    """
    Cria uma configuração personalizada facilmente.

    Args:
        pesos_diretor: Peso para DIRECTED_BY (0.0 a 1.0)
        pesos_ator: Peso para HAS_ACTOR (0.0 a 1.0)
        pesos_rating: Peso para RATED (0.0 a 1.0)
        pesos_genero: Peso para HAS_GENRE (0.0 a 1.0)
        distancia_max: Distância máxima no grafo (2-4)
        rating_minimo: Rating mínimo do histórico (0.5-5.0)

    Returns:
        Configuracao personalizada
    """
    return Configuracao(
        PESOS_SEMANTICOS={
            "DIRECTED_BY": pesos_diretor,
            "HAS_ACTOR": pesos_ator,
            "RATED": pesos_rating,
            "HAS_GENRE": pesos_genero,
        },
        DISTANCIA_MAX_PADRAO=distancia_max,
        RATING_MIN_PADRAO=rating_minimo,
    )


def listar_configs_disponiveis() -> Dict[str, Configuracao]:
    """Retorna dicionário com todas as configurações pré-definidas."""
    return {
        "padrao": CONFIG_PADRAO,
        "conservador": CONFIG_CONSERVADOR,
        "agressivo": CONFIG_AGRESSIVO,
        "diretor": CONFIG_DIRETO_FOCO,
        "ator": CONFIG_ATOR_FOCO,
        "genero": CONFIG_GENERO_FOCO,
        "rapido": CONFIG_RAPIDO,
        "preciso": CONFIG_PRECISO,
    }


# ============================================================================
# MODO DESENVOLVIMENTO
# ============================================================================

if __name__ == "__main__":
    """Exibe resumo das configurações disponíveis."""

    print("\n" + "="*70)
    print("CONFIGURAÇÕES DISPONÍVEIS DO MOTOR DE RECOMENDAÇÃO")
    print("="*70)

    configs = listar_configs_disponiveis()

    for nome, config in configs.items():
        print(f"\n{nome.upper()}")
        print("-" * 70)
        print(f"  PESOS:")
        for tipo, peso in config.PESOS_SEMANTICOS.items():
            print(f"    {tipo:15} = {peso}")
        print(f"  DISTÂNCIA: {config.DISTANCIA_MIN_PADRAO} a {config.DISTANCIA_MAX_PADRAO}")
        print(f"  RATING MIN: {config.RATING_MIN_PADRAO}")
        print(f"  DFS MAX PROFUNDIDADE: {config.MAX_PROFUNDIDADE_DFS}")

    # Exemplo de uso
    print("\n" + "="*70)
    print("EXEMPLO DE USO")
    print("="*70)

    print("\n# Usar configuração padrão")
    print("motor = MotorRecomendacao(grafo, pesos=CONFIG_PADRAO.PESOS_SEMANTICOS)")

    print("\n# Usar configuração personalizada")
    print("config = criar_config_personalizada(")
    print("    pesos_diretor=1.0,")
    print("    pesos_ator=0.8,")
    print("    distancia_max=4,")
    print("    rating_minimo=3.5,")
    print(")")
    print("motor = MotorRecomendacao(grafo, pesos=config.PESOS_SEMANTICOS)")

    print("\n" + "="*70 + "\n")
