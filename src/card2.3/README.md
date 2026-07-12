# Card 2.3: Módulo de Explicabilidade (XAI)

Este diretório contém a implementação do **Módulo de Inteligência Artificial Explicável (XAI)** do Sistema de Recomendação de Filmes. 

O objetivo principal deste módulo é mitigar o problema de "caixa-preta" inerente aos sistemas tradicionais. Ao explorar a topologia de um Grafo Heterogêneo de Conhecimento construído com `NetworkX`, o algoritmo rastreia o caminho estrutural entre o nó do usuário e o nó do filme recomendado, convertendo essas conexões matemáticas em justificativas textuais legíveis em linguagem natural.

## 🏗️ Estrutura do Módulo

O diretório é composto pelos seguintes artefatos:

*   `modulo_xai.py`: Núcleo do motor de explicabilidade. Contém a classe `MotorExplicabilidadeXAI`, responsável por executar os algoritmos de *Shortest Path* e aplicar o mapeamento de templates de verbalização.
*   `teste_integracao_xai.py`: Script de teste *End-to-End* (E2E). Acopla a leitura do grafo (Card 2.1), o motor de recomendação (Card 2.2) e a geração de justificativas textuais (Card 2.3). Inclui a rotina de **Teste de Ablação Estrutural**.

*(Nota: O script de geração do grafo foi centralizado no Card 2.1 para manter a coesão da arquitetura).*

## ⚙️ Como Funciona (Lógica de Tradução)

O módulo XAI busca rotas de tamanho exato igual a 4 nós (Usuário $\rightarrow$ Filme Assistido $\rightarrow$ Entidade de Conexão $\rightarrow$ Filme Recomendado). Uma vez encontrado o caminho mínimo, o sistema extrai o tipo da aresta (`tipo`) e aciona um dicionário de templates estáticos para montar a frase.

### Templates de Relação Suportados

| Relação no Grafo | Domínio | Template de Verbalização (Output) |
| :--- | :--- | :--- |
| `DIRECTED_BY` | Semântico | *"que também foi dirigido por {diretor}"* |
| `HAS_ACTOR` | Semântico | *"que também estrelou {ator}"* |
| `HAS_GENRE` | Semântico | *"que pertence ao gênero {gênero}"* (Inclui aviso de generalidade) |
| `HAS_KEYWORD` | Semântico | *"que compartilha o tema '{entidade}"* |
| `PRODUCED_BY` | Semântico | *"que também foi produzido por {produtor}"* |
| `BELONGS_TO_COLLECTION` | Semântico | *"que faz parte da mesma franquia/coleção"* |
| `RATED` | Colaborativo | *"que também é muito bem avaliado por outros usuários (ex: Usuário {id}), que tem perfil similar ao seu"* |

*Caso o algoritmo identifique uma nova relação não mapeada, um mecanismo de **fallback dinâmico** imprimirá o tipo estrutural bruto da aresta para fins de auditoria técnica.*

## 🚀 Como Executar os Testes

Para garantir que a integração entre os Cards esteja funcional e as rotas estejam sendo devidamente verbalizadas, execute o script de integração a partir da raiz do repositório (`src/`):

### 1. Teste de Integração Completo
O teste padrão varre o grafo inteiro, mesclando Filtragem Colaborativa (usuários similares) e Filtragem Baseada em Conteúdo (atributos).

```bash
python3 card2.3/teste_integracao_xai.py
```

### 2. Teste de Ablação Estrutural (Isolamento Semântico)
Dentro do arquivo `teste_integracao_xai.py`, há um bloco documentado focado em **Ablação Estrutural**. Esse teste utiliza a função `nx.subgraph()` para amputar temporariamente nós de *Gêneros* e *Outros Usuários*, forçando o motor a encontrar justificativas puramente baseadas no elenco e na direção.

**Exemplo de Output Esperado no Teste de Ablação:**
> 🎬 [#1] Ocean's Thirteen (Score: 12.740000)  
> 💡 Recomendado porque você assistiu 'Scarface', que também estrelou Al Pacino.

## 📦 Dependências

*   `networkx` (>= 3.0)
*   `pandas` (>= 2.0)

As dependências já devem estar satisfeitas caso o ambiente virtual (venv) da raiz do projeto esteja ativado.
