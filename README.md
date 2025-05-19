![image](https://github.com/user-attachments/assets/c038116d-47d5-41cf-8c50-adba903e7b65)# 🕸️ Rede de Petri - Trabalho de Redes de Computadores 2  
**Implementação de um Algoritmo de Estado de Enlace usando Docker e Python**  

## 🛠️ Pré-requisitos  
Antes de executar o projeto, certifique-se de ter instalado: 

Docker Compose 

Phyton 

## Organização do Código 

O projeto é dividido em :

Descoberta de Vizinhos (HELLO) → UDP (Broadcast/Multicast)

Divulgação de Estado de Enlace (LSA) → UDP (Unicast para vizinhos)

Banco de Dados de Estado de Enlace (LSDB) → Armazenamento local (estrutura de dados em memória)

Cálculo de Rotas (Dijkstra) → Algoritmo local (processamento interno)

Aplicação de Rotas (ip route) → Comandos do sistema (modificação da tabela de roteamento via iproute2)

## Como executar

Primeiro precisamos criar a topologia aleatória que é moldada a partir da quantidade de roteadores ao executar o arquivo gera grafo na pasta GeraTopologia, após isso serão gerados os grafo em Csv e a imagem da topologia criada em Png na pasta CsvImg. Após isso, devemos executar o geracompose na pasta GeraTopologia, dando o caminho do csv gerado na pasta CsvImg, e a partir disso o docker-compose.yml será gerado na principal do projeto.

A partir disso, crie o conteiner com o comando docker compose build

Depois disso, execute o conteiner com o docker compose up

Os conteiners estarão em execução



