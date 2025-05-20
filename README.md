""# 🕸️ Rede de Petri - Trabalho de Redes de Computadores 2
**Implementação de um Algoritmo de Estado de Enlace usando Docker e Python**

---

## 🛠️ **Pré-requisitos**

Antes de executar o projeto, certifique-se de ter os seguintes itens instalados:

* Docker Compose
* Python
* Git Bash

---

## 📂 **Organização do Projeto**

O projeto está estruturado nos seguintes componentes:

1. **Descoberta de Vizinhos (HELLO)**

   * Comunicação via **UDP (Broadcast/Multicast)** para identificar roteadores vizinhos.

2. **Divulgação de Estado de Enlace (LSA)**

   * Envio de informações de enlaces através de **UDP (Unicast para vizinhos)**.

3. **Banco de Dados de Estado de Enlace (LSDB)**

   * Armazenamento local das informações de enlace em uma estrutura de dados em memória.

4. **Cálculo de Rotas (Dijkstra)**

   * Processamento interno para cálculo das melhores rotas.

5. **Aplicação de Rotas (ip route)**

   * Modificação da tabela de roteamento local utilizando comandos do sistema com `iproute2`.

---


## 🚀 Como Executar

### 1️⃣ Geração da Topologia Aleatória

#### 🔹 Opção 1: Instalação global (direto no sistema)

```bash
pip install -r requirements.txt
```
- Execute manualmente o ``geragrafo.py``.

- Um grafo em formato CSV e uma imagem PNG serão gerados na pasta `CsvImg`.

- Execute manualmente o ``geracompose.py``.

- O arquivo `docker-compose.yml` será criado na raiz do projeto.

#### 🔹 Opção 2: Usando ambiente virtual


```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
python GeraTopologia\geragrafo.py
```

- Um grafo em formato CSV e uma imagem PNG serão gerados na pasta `CsvImg`.

```bash
python GeraTopologia\geracompose.py
```

- O arquivo `docker-compose.yml` será criado na raiz do projeto.
---

### 2️⃣ Construção e Execução dos Containers

```bash
docker compose build
docker compose up
```

---

## ✅ **Testes Disponíveis**

Com os containers em execução, é possível realizar os seguintes testes:

* **Ping entre roteadores e hosts:**

  * Acesse o Git Bash (no Windows).

  ```bash
  ./pinghost.sh
  ./pingrouter.sh
  ```

---

## 📈 **Testes de Convergência**

Os tempos de convergência da rede são calculados automaticamente ao iniciar os containers.
Esses dados são armazenados em relatórios dentro da pasta `Scripts/TesteConvergencia`, sendo baseados na descoberta de roteadores na topologia.

---

## 🔎 **Escolha dos Protocolos**

Para a implementação da rede de Petri simulando o protocolo de estado de enlace (Link-State), foram selecionados os seguintes protocolos: **UDP**, **IP** e o método de cálculo de rotas com **Dijkstra**. A escolha se deu pelos seguintes motivos:

1. **UDP (User Datagram Protocol)**:

   * Utilizado para comunicação entre os roteadores no processo de descoberta de vizinhos (HELLO) e na troca de informações de estado de enlace (LSA).
   * O UDP foi escolhido por ser um protocolo de transporte leve, sem estabelecimento de conexão, o que o torna ideal para transmissões rápidas e com baixo overhead, características importantes para atualizações frequentes de tabelas de roteamento.
   * Permite o uso de **Broadcast** e **Multicast**, facilitando a disseminação de mensagens para múltiplos roteadores ao mesmo tempo.

2. **IP (Internet Protocol)**:

   * Responsável por endereçar e rotear os pacotes entre os roteadores.
   * A escolha do protocolo IP se justifica pela necessidade de endereçamento único para cada roteador, permitindo a identificação clara de origem e destino das mensagens de estado de enlace.
   * Além disso, as rotas geradas pelo algoritmo de Dijkstra são aplicadas diretamente nas tabelas de roteamento, que utilizam o IP como referência.

3. **Algoritmo de Dijkstra**:

   * Utilizado para calcular os menores caminhos (rotas mais curtas) entre os roteadores com base nos custos de enlace divulgados nos pacotes LSA.
   * É um algoritmo eficiente e bem consolidado para esse tipo de aplicação, garantindo a seleção da rota de menor custo para cada destino.

---

## 🌐 **Geração da Topologia de Rede**

A topologia da rede é gerada de forma **aleatória e parcialmente conectada** através do script `geragrafo.py`. Esse script utiliza a biblioteca **NetworkX** para modelar os nós e as conexões (arestas) entre eles. O processo ocorre em algumas etapas principais:

---

### 🔹 **1️⃣ Geração dos Nós (Roteadores)**

Os roteadores são representados por nós no grafo. Eles são nomeados sequencialmente como `r1`, `r2`, `r3`, etc. O número total de roteadores é definido pela variável `quant_roteadores`.

---

### 🔹 **2️⃣ Criação das Conexões (Enlaces)**

As conexões entre os roteadores são estabelecidas com uma probabilidade definida por `prob_conexao`. Para cada par de nós `(i, j)`, um valor aleatório é gerado. Se esse valor for menor que a probabilidade definida, é criada uma aresta entre esses nós, representando um enlace com um peso (custo) aleatório entre `peso_min` e `peso_max`.

---

### 🔹 **3️⃣ Verificação de Conectividade**

Após a criação das arestas, é feita uma verificação para garantir que o grafo é **conexo** — ou seja, todos os roteadores conseguem se comunicar de alguma forma, direta ou indiretamente.
Caso o grafo não seja conexo, novas arestas são criadas aleatoriamente até que todos os nós estejam acessíveis uns aos outros.

---

### 🔹 **4️⃣ Salvamento da Topologia**

Ao final, o grafo é salvo de duas maneiras:

1. **Imagem PNG** representando a topologia gráfica dos roteadores e suas conexões.
2. **Arquivo CSV** contendo a lista de enlaces (origem, destino e peso), utilizado para gerar o arquivo `docker-compose.yml` com a configuração dos containers.

---

Pronto! Agora sua topologia está em execução e você pode validar os roteamentos, testar comunicação e monitorar convergência de forma prática e eficiente.
""
