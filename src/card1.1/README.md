# Card 1.1: Obtenção, Tratamento e Visualização de Dados

Este diretório compõe a base do pipeline de dados do Sistema de Recomendação de Filmes. 

O objetivo principal deste módulo é realizar a extração dos dados brutos (provenientes do Kaggle), executar o pré-processamento (limpeza de strings, desestruturação de JSONs embutidos, tratamento de valores nulos) e consolidar os arquivos que servirão de alicerce para a construção do Grafo Heterogêneo (Card 2.1).

## 🏗️ Estrutura do Módulo

O diretório é composto pelas seguintes pastas e artefatos:

*   **`dados_originais/`**: Diretório de *landing* que armazena os CSVs brutos recém-baixados (ex: `tmdb_5000_credits.csv`, `tmdb_5000_movies.csv`).
*   **`dados_tratados/`**: Diretório de saída (*output*) que armazena os dados limpos e prontos para consumo:
    *   `tmdb_grafo_limpo.pkl`: DataFrame serializado contendo os metadados dos filmes (títulos, gêneros, elenco e direção extraídos).
    *   `conexoes_usuario_filme.csv`: Tabela padronizada relacionando os usuários, os IDs dos filmes e as respectivas notas (ratings).
*   `obtencao_dados_kaggle.py`: Script de automação para download e extração dos dados diretamente da API do Kaggle.
*   `tratamento.py`: Motor principal de engenharia de dados. Responsável por realizar o *parsing* das colunas complexas, limpar caracteres inválidos e gerar os arquivos finais.
*   `visualizacao_dados.py`: Módulo de Análise Exploratória de Dados (EDA). Gera métricas, gráficos e distribuições sobre o comportamento do dataset.

## ⚙️ Como Funciona (Pipeline de Dados)

O fluxo de dados segue uma arquitetura ETL (Extract, Transform, Load) sequencial:

1.  **Extract:** O script de obtenção conecta-se à fonte e baixa o dataset TMDB 5000 e/ou MovieLens para a pasta `dados_originais`.
2.  **Transform:** O script de tratamento lê os CSVs. Colunas como `cast`, `crew` e `genres` (que originalmente vêm como strings no formato JSON) são desaninhadas com bibliotecas literais do Python (`ast.literal_eval`). Atores secundários são filtrados, mantendo apenas o elenco principal e diretores.
3.  **Load:** Os dados refinados são salvos em `dados_tratados/` em formatos otimizados (`.pkl` para preservação de listas nativas do Python e `.csv` para dados tabulares de interação).

## 🚀 Como Executar o Pipeline

Para garantir a geração dos dados limpos, os scripts devem ser executados em ordem a partir da raiz do repositório (`src/`):

### 1. Download dos Dados
Baixa os CSVs brutos para iniciar o projeto. *(Nota: Exige que as credenciais do Kaggle estejam configuradas no seu ambiente).*
```bash
python3 card1.1/obtencao_dados_kaggle.py
```

### 2. Tratamento e Limpeza (Core)
Executa a limpeza, une as bases (se necessário) e salva os arquivos finais `.pkl` e `.csv` que alimentarão o Grafo.
```bash
python3 card1.1/tratamento.py
```

### 3. Análise Exploratória (Opcional)
Gera relatórios estatísticos e gráficos sobre a densidade das avaliações e popularidade das categorias.
```bash
python3 card1.1/visualizacao_dados.py
```

## 📦 Dependências

*   `pandas` (>= 2.0)
*   `kaggle` (API configurada via `kaggle.json`)
*   `matplotlib` / `seaborn` (para visualização gráfica)
*   `ast` (built-in do Python)