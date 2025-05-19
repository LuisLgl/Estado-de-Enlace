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

## 🚀 **Como Executar**

1️⃣ - Primeiro, é necessário criar a topologia aleatória:

* Acesse a pasta `GeraTopologia`.
* Execute o arquivo `geragrafo.py`.
* Será gerado um grafo em formato CSV e uma imagem PNG representando a topologia na pasta `CsvImg`.

2️⃣ - Em seguida, gere o arquivo `docker-compose.yml`:

* Na pasta `GeraTopologia`, execute o script `geracompose.py`, informando o caminho do arquivo CSV gerado.
* O arquivo Docker Compose será criado na raiz do projeto.

3️⃣ - Construa os containers Docker:

```bash
docker compose build
```

4️⃣ - Inicie os containers:

```bash
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

Pronto! Agora sua topologia está em execução e você pode validar os roteamentos, testar comunicação e monitorar convergência de forma prática e eficiente.
""
