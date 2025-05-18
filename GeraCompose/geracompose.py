import yaml
import csv
from collections import defaultdict

def gerar_docker_compose(caminho_csv, caminho_saida="docker-compose.yml"):
    conexoes = []
    roteadores = set()

    # Leitura do csv
    with open(caminho_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            origem, destino, peso = row['no_origem'], row['no_destino'], int(row['peso'])
            conexoes.append((origem, destino, peso))
            roteadores.update([origem, destino])

    # Estrutura principal do docker compose
    docker_compose = {
        'version': '3.9',
        'services': {},
        'networks': {}
    }

    subnet_base = "10.10.{}.0/24"
    host_subnet_base = "192.168.{}.0/24"
    subnet_count = 1
    host_subnet_count = 6  # Começando em 6 para seguir o padrão do exemplo

    # Mapeamento de redes e custos
    network_info = {}
    for origem, destino, peso in conexoes:
        net_name = f"{origem}_{destino}_net"
        subnet = subnet_base.format(subnet_count)
        network_info[net_name] = {
            'subnet': subnet,
            'cost': peso,
            'ips': {
                origem: f"10.10.{subnet_count}.2",
                destino: f"10.10.{subnet_count}.3"
            }
        }
        subnet_count += 1

    # Criação dos serviços de roteadores
    for router in sorted(roteadores):
        # Configuração do roteador
        router_service = {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile.router'
            },
            'container_name': router,
            'volumes': [
                './scripts:/shared_data'
            ],
            'environment': {
                'CONTAINER_NAME': router
            },
            'networks': {},
            'cap_add': ['NET_ADMIN']
        }

        # Adiciona variáveis de ambiente para os custos
        for net_name, info in network_info.items():
            if router in info['ips']:
                router_service['environment'][f"CUSTO_{net_name}"] = str(info['cost'])

        # Adiciona redes de conexão entre roteadores
        for net_name, info in network_info.items():
            if router in info['ips']:
                router_service['networks'][net_name] = {
                    'ipv4_address': info['ips'][router]
                }

        # Adiciona rede de hosts
        host_net_name = f"{router}_hosts_net"
        host_subnet = host_subnet_base.format(host_subnet_count)
        router_service['networks'][host_net_name] = {
            'ipv4_address': f"192.168.{host_subnet_count}.2"
        }

        # Adiciona rede ao compose
        docker_compose['networks'][host_net_name] = {
            'driver': 'bridge',
            'ipam': {
                'config': [{'subnet': host_subnet}]
            }
        }

        docker_compose['services'][router] = router_service

        # Criação dos hosts para cada roteador
        for i in range(1, 3):
            host_name = f"{router}_h{i}"
            host_ip = f"192.168.{host_subnet_count}.{i + 2}"
            
            docker_compose['services'][host_name] = {
                'build': {
                    'context': '.',
                    'dockerfile': 'Dockerfile.host'
                },
                'container_name': host_name,
                'volumes': [
                    './scripts:/scripts'
                ],
                'networks': {
                    host_net_name: {
                        'ipv4_address': host_ip
                    }
                },
                'cap_add': ['NET_ADMIN']
            }

        host_subnet_count += 1

    # Adiciona redes de conexão entre roteadores ao compose
    for net_name, info in network_info.items():
        docker_compose['networks'][net_name] = {
            'driver': 'bridge',
            'ipam': {
                'config': [{'subnet': info['subnet']}]
            }
        }

    # Salvamento do arquivo
    with open(caminho_saida, "w") as f:
        yaml.dump(docker_compose, f, default_flow_style=False, sort_keys=False)

    print(f"Docker Compose salvo em: {caminho_saida}")

if __name__ == '__main__':
    gerar_docker_compose("CsvImg/Csv20.csv", "docker-compose.yml")