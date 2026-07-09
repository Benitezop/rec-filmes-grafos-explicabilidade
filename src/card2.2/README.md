# Card 2.2 — Motor de recomendação

Este diretório reúne a implementação do motor de recomendação baseado em grafo, com exemplos de uso e testes simples para validar o funcionamento.

## Como executar

### 1. Verifique se o grafo foi gerado
O motor depende do arquivo do grafo em [src/card2.1/dados_tratados/grafo_filmes.pkl](../card2.1/dados_tratados/grafo_filmes.pkl).

Se ele ainda não existir, gere primeiro no diretório [src/card2.1](../card2.1).

### 2. Rode os exemplos
No diretório [src/card2.2](.) execute:

```bash
python exemplo_uso.py
```

Isso roda os exemplos de uso do motor e imprime recomendações.

Para executar apenas o exemplo 1:

```bash
python exemplo_uso.py --exemplo1
```

### 3. Rode os testes
```bash
python teste_motor_recomendacao.py
```

Esse script valida o motor com alguns usuários e verifica se as recomendações são geradas corretamente.

## Resumo dos arquivos

- [src/card2.2/motor_recomendacao.py](motor_recomendacao.py): implementação principal do motor. Responsável por extrair o histórico do usuário, encontrar filmes candidatos por vizinhança, calcular a pontuação ponderada e gerar recomendações.
- [src/card2.2/exemplo_uso.py](exemplo_uso.py): script com exemplos práticos de uso, incluindo recomendação para um usuário, comparação entre usuários, análise de um filme e geração de relatório.
- [src/card2.2/teste_motor_recomendacao.py](teste_motor_recomendacao.py): script de validação que executa testes básicos para verificar o comportamento do motor.
- [src/card2.2/config_motor.py](config_motor.py): arquivo com configurações e pesos usados pelo motor.
- [src/card2.2/recomendacoes_usuario_42.csv](recomendacoes_usuario_42.csv): exemplo de saída gerada para o usuário 42.
- [src/card2.2/relatorio_recomendacoes.csv](relatorio_recomendacoes.csv): exemplo de relatório consolidado gerado pelo exemplo 5.

## Ideia do algoritmo

O motor funciona em três etapas principais:

1. Extrai o histórico do usuário a partir dos filmes avaliados com nota igual ou maior que 4.0.
2. Busca filmes candidatos na vizinhança do grafo, em até 2 a 3 passos de distância.
3. Calcula uma pontuação baseada na soma ponderada dos caminhos entre o usuário e os filmes candidatos, usando pesos semânticos para diferentes tipos de relação.

Essa pontuação é usada para ordenar os filmes e montar o ranking final.
