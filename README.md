🕸️ Rede de Petri - Trabalho de Redes de Computadores 2
Implementação de uma Rede de Petri usando Docker e Python

Este repositório contém o trabalho da primeira avaliação de Redes de Computadores 2, simulando o comportamento de uma Rede de Petri em um ambiente conteinerizado.

🛠️ Pré-requisitos
Antes de executar o projeto, certifique-se de ter instalado:

Ferramenta	Link de Download
Docker Desktop	https://www.docker.com/products/docker-desktop
Python 3.6+	https://www.python.org/downloads/
� Configuração do Ambiente
1. Clone o repositório
bash
git clone https://github.com/seu-usuario/rede-de-petri.git
cd rede-de-petri
2. Construa a imagem Docker
bash
docker build -t rede-petri .
3. Execute o container
bash
docker run -it --name rede-petri-container rede-petri
🧪 Testando a Implementação
Para validar o funcionamento, execute o script de testes:

bash
./pinlalla.sh
📌 Observações
Certifique-se de que o Docker está em execução antes de iniciar o container.

O script pinlalla.sh deve ter permissões de execução (chmod +x pinlalla.sh).
