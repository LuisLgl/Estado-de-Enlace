
import time
import psutil
import socket
import threading
import json
import os
import subprocess
import ipaddress
import datetime
from collections import defaultdict
import heapq
from typing import Dict, List, Tuple, Optional

"""
Implementação de um protocolo de descoberta de vizinhos e roteamento link-state.

Este módulo implementa um protocolo distribuído para:
1. Descoberta de vizinhos através de mensagens HELLO
2. Troca de informações de topologia via LSAs (Link State Advertisements)
3. Cálculo de rotas usando o algoritmo Dijkstra
4. Aplicação de rotas no sistema operacional
"""

class LSDB:

    """Link State Database que armazena e gerencia o estado dos links da rede."""
    
    def __init__(self, router_name: str):

        """Inicializa a LSDB para um roteador específico.
        
        Args:
            router_name (str): Nome do roteador dono desta LSDB.
        """

        self.router_name = router_name
        self.db: Dict[str, Dict] = {}
        self.topology: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.last_update_time = time.time()
        self.convergence_data = []  # Lista para armazenar dados de convergência parcial
        self.start_time = time.time()
        self.quantidade_routers = 0
        
    def update(self, lsa: Dict) -> bool:

        """
        Atualiza o LSDB com um novo Link State Advertisement (LSA).
        
        Args:
            lsa (Dict): Dicionário contendo o LSA recebido.
            
        Returns:
            bool: True se o LSA foi novo e atualizou o banco, False caso contrário.
        """

        origin = lsa.get('origin') or lsa.get('router_id')
        sequence = lsa.get('sequence') or lsa.get('sequence_number')
        
        if not origin or sequence is None:
            return False
            
        current_entry = self.db.get(origin, {})
        if sequence > current_entry.get('sequence', -1):
            normalized = {
                'origin': origin,
                'sequence': sequence,
                'timestamp': lsa.get('timestamp', time.time()),
                'neighbors': self._normalize_neighbors(lsa),
                'addresses': lsa.get('addresses', [])
            }
            self.db[origin] = normalized
            self._rebuild_topology()
            quantidade_routers = len(self.db)

            if(quantidade_routers > self.quantidade_routers):
                self.quantidade_routers = quantidade_routers
                print(f"[{self.router_name}] Updated LSDB with {quantidade_routers} routers")
                current_time = time.time() - self.start_time
                num_routers = len(self.db)
                self.convergence_data.append((current_time, num_routers))
            return True
        return False
    
    def _normalize_neighbors(self, lsa: Dict) -> Dict:
        
        """
        Padroniza o formato dos vizinhos no LSA recebido.
        
        Args:
            lsa (Dict): LSA recebido com vizinhos em formato variável.
            
        Returns:
            Dict: Vizinhos no formato padronizado {'router': {'ip': str, 'cost': int}}.
        """

        neighbors = {}
        
        if 'neighbors' in lsa and isinstance(lsa['neighbors'], dict):
            if all(isinstance(v, dict) for v in lsa['neighbors'].values()):
                neighbors = {n: {'ip': d.get('ip', ''), 'cost': d.get('cost', 1)} 
                           for n, d in lsa['neighbors'].items()}
            elif all(isinstance(v, str) for v in lsa['neighbors'].values()):
                neighbors = {n: {'ip': ip, 'cost': lsa.get('links', {}).get(n, 1)} 
                           for n, ip in lsa['neighbors'].items()}
        elif 'links' in lsa:
            neighbors = {n: {'ip': '', 'cost': c} for n, c in lsa['links'].items()}
            
        return neighbors
    
    def _rebuild_topology(self):

        """Reconstrói a topologia completa da rede a partir dos LSAs armazenados."""

        self.topology = defaultdict(dict)
        for router, lsa in self.db.items():
            for neighbor, data in lsa['neighbors'].items():
                cost = data.get('cost', 1)
                self.topology[router][neighbor] = cost
                self.topology[neighbor][router] = cost  # Links são bidirecionais

    def calculate_routing_table(self, local_neighbors: Dict[str, str]) -> Dict[str, Tuple[str, int]]:
        
        """
        Calcula a tabela de roteamento usando o algoritmo de Dijkstra.
        
        Args:
            local_neighbors (Dict[str, str]): Vizinhos diretos {nome: ip}.
            
        Returns:
            Dict[str, Tuple[str, int]]: Tabela de roteamento {destino: (próximo_salto, custo)}.
        """

        if self.router_name not in self.topology:
            return {}

        distances = {r: float('inf') for r in self.topology}
        previous = {r: None for r in self.topology}
        distances[self.router_name] = 0
        heap = [(0, self.router_name)]
        
        while heap:
            current_dist, current = heapq.heappop(heap)
            if current_dist > distances[current]:
                continue
                
            for neighbor, cost in self.topology[current].items():
                new_dist = current_dist + cost
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(heap, (new_dist, neighbor))
        
        routing_table = {}
        for dest in self.topology:
            if dest == self.router_name or distances[dest] == float('inf'):
                continue
            
            # Encontra o next hop no caminho mais curto
            next_hop = dest
            while previous[next_hop] != self.router_name and previous[next_hop] is not None:
                next_hop = previous[next_hop]
            
            # Aqui removemos a restrição de que next_hop seja um vizinho direto.
            routing_table[dest] = (next_hop, distances[dest])
        
        return routing_table


    def get_router_ips(self, router_name: str) -> List[str]:
        
        """
        Obtém todos os IPs conhecidos para um roteador específico.
        
        Args:
            router_name (str): Nome do roteador a consultar.
            
        Returns:
            List[str]: Lista de endereços IP associados ao roteador.
        """

        return self.db.get(router_name, {}).get('addresses', [])

class HelloSender:

    """Responsável pelo envio periódico de mensagens HELLO"""
    
    def __init__(self, ndp: 'NeighborDiscoveryProtocol'):

        """
        Inicializa o HelloSender.
        
        Args:
            ndp (NeighborDiscoveryProtocol): Instância do protocolo principal.
        """

        self.ndp = ndp
        self.running = False
        self.thread = None

    def start(self):

        """Inicia o thread de envio periódico de mensagens HELLO."""

        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._send_hello_loop, daemon=True)
            self.thread.start()
            print(f"[{self.ndp.container_name}] HELLO sender started")

    def stop(self):

        """Para o thread de envio de mensagens HELLO."""
        
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print(f"[{self.ndp.container_name}] HELLO sender stopped")

    def _send_hello_loop(self):
        
        """Loop principal para envio periódico de mensagens HELLO."""

        while self.running:
            try:
                for ip in self.ndp.interface_ips:
                    if not self.running:
                        break
                    self._send_hello(ip)
                time.sleep(2)
            except Exception as e:
                print(f"[{self.ndp.container_name}] HELLO error: {str(e)}")
                time.sleep(1)

    def _send_hello(self, ip: str):
        
        """
        Envia uma mensagem HELLO para o endereço de broadcast.
        
        Args:
            ip (str): Endereço IP de origem para a mensagem HELLO.
        """

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                message = json.dumps({
                    'type': 'HELLO',
                    'router_id': self.ndp.container_name,
                    'timestamp': time.time(),
                    'ip_address': ip,
                    'known_neighbors': list(self.ndp.neighbors.keys())
                })
                broadcast_ip = ip.rsplit('.', 1)[0] + '.255'
                sock.sendto(message.encode(), (broadcast_ip, self.ndp.port))
        except Exception as e:
            print(f"[{self.ndp.container_name}] HELLO send error: {str(e)}")

class LSASender:

    """Responsável pelo envio e encaminhamento de LSAs"""
    
    def __init__(self, ndp: 'NeighborDiscoveryProtocol'):

        """
        Inicializa o LSASender.
        
        Args:
            ndp (NeighborDiscoveryProtocol): Instância do protocolo principal.
        """

        self.ndp = ndp
        self.running = False
        self.thread = None
        self.lsa_sequence = 0

    def start(self):

        """Inicia o thread de envio periódico de LSAs."""

        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._send_lsa_loop, daemon=True)
            self.thread.start()
            print(f"[{self.ndp.container_name}] LSA sender started")

    def stop(self):

        """Para o thread de envio de LSAs."""

        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print(f"[{self.ndp.container_name}] LSA sender stopped")

    def _get_link_cost(self, neighbor: str) -> int:
        
        """
        Obtém o custo do link para um vizinho específico.
        
        Args:
            neighbor (str): Nome do roteador vizinho.
            
        Returns:
            int: Custo do link para o vizinho.
        """

        return self.ndp.get_link_cost_between(self.ndp.container_name, neighbor)

    def _send_lsa_loop(self):

        """Loop principal para envio periódico de LSAs."""

        while self.running:
            try:
                self._send_lsa()
                time.sleep(10)
            except Exception as e:
                print(f"[{self.ndp.container_name}] LSA error: {str(e)}")
                time.sleep(1)

    def _send_lsa(self):
        
        """Constrói e envia um LSA contendo o estado atual dos links."""

        self.lsa_sequence += 1
        
        with self.ndp.lock:
            neighbors = {
                name: {'ip': ip, 'cost': self._get_link_cost(name)}
                for name, ip in self.ndp.neighbors.items()
            }
            
        lsa = {
            'type': 'LSA',
            'router_id': self.ndp.container_name,
            'sequence_number': self.lsa_sequence,
            'timestamp': time.time(),
            'addresses': self.ndp.interface_ips,
            'links': {n: data['cost'] for n, data in neighbors.items()}
        }
        
        self._send_to_all(lsa)

    def _send_to_all(self, lsa: Dict):
        
        """
        Envia um LSA para todos os vizinhos conhecidos.
        
        Args:
            lsa (Dict): LSA a ser enviado.
        """

        message = json.dumps(lsa)
        
        with self.ndp.lock:
            for neighbor_ip in self.ndp.neighbors.values():
                try:
                    self.ndp.socket.sendto(message.encode(), (neighbor_ip, self.ndp.port))
                except Exception as e:
                    print(f"[{self.ndp.container_name}] LSA send error to {neighbor_ip}: {str(e)}")

    def forward_lsa(self, lsa: Dict, sender_ip: str):
        
        """
        Encaminha um LSA recebido para outros vizinhos (exceto o remetente).
        
        Args:
            lsa (Dict): LSA recebido.
            sender_ip (str): IP do remetente original.
        """

        with self.ndp.lock:
            recipients = [ip for ip in self.ndp.neighbors.values() if ip != sender_ip]
        
        message = json.dumps(lsa)
        for ip in recipients:
            try:
                self.ndp.socket.sendto(message.encode(), (ip, self.ndp.port))
            except Exception as e:
                print(f"[{self.ndp.container_name}] LSA forward error to {ip}: {str(e)}")

class NeighborDiscoveryProtocol:
    
    """Implementação principal do protocolo de descoberta de vizinhos e construção de tabelas de roteamento."""
    
    def __init__(self, container_name: str = "router", port: int = 5000):

        """
        Inicializa o protocolo.
        
        Args:
            container_name (str): Nome do container/roteador. Default "router".
            port (int): Porta UDP para comunicação. Default 5000.
        """

        self.container_name = os.getenv("CONTAINER_NAME", container_name)
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.settimeout(1)
        self.neighbors: Dict[str, str] = {}  # {router_id: ip}
        self.interface_ips: List[str] = []
        self.lock = threading.Lock()
        self.last_seen: Dict[str, float] = {}
        self.all_neighbors_discovered = False
        self.lsdb = LSDB(self.container_name)
        self.routing_table: Dict[str, Tuple[str, int]] = {}  # {dest: (next_hop, cost)}
        self.hello_sender = HelloSender(self)
        self.lsa_sender = LSASender(self)
        self.running = False



    def get_link_cost_between(self, router1: str, router2: str) -> int:
        
        """
        Obtém o custo do link entre dois roteadores a partir de variáveis de ambiente.
        
        Args:
            router1 (str): Nome do primeiro roteador.
            router2 (str): Nome do segundo roteador.
            
        Returns:
            int: Custo do link entre os roteadores.
        """

        cost = os.getenv(f"CUSTO_{router1}_{router2}_net")
        if cost is None:
            cost = os.getenv(f"CUSTO_{router2}_{router1}_net")
        if cost is None:
            cost = os.getenv(f"CUSTO_{router1}_{router2}")
        if cost is None:
            cost = os.getenv(f"CUSTO_{router2}_{router1}")
        return int(cost) if cost is not None else 1

    def start(self):
        
        """Inicia o protocolo e todos os seus componentes."""

        self.running = True
        self.interface_ips = self._get_interfaces_and_ips()
        self.converged = False
        self.convergence_start_time = None
        self.convergence_time = None
        self.hello_sender.start()
        threading.Thread(target=self._listen_loop, daemon=True).start()
        
        try:
            # Loop principal
            while self.running:
                self._monitor_state()
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop()

    def _get_interfaces_and_ips(self) -> List[str]:
        
        """
        Obtém os IPs das interfaces de rede do container.
    
        Returns:
            List[str]: Lista de endereços IP das interfaces.
        """

        try:
            result = subprocess.run(
                ["ip", "-4", "-o", "addr", "show"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                return []
                
            ips = []
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 4 and not parts[1].startswith('lo'):
                    ip = parts[3].split('/')[0]
                    if ip.startswith("192.168"):
                    # Converte para a rede /24
                        segmentos = ip.split(".")
                        ip = f"{segmentos[0]}.{segmentos[1]}.{segmentos[2]}.0/24"
                    ips.append(ip)
            return ips
        except Exception as e:
            print(f"[{self.container_name}] Interface error: {str(e)}")
            return []

    def _listen_loop(self):

        """Loop principal para recebimento de mensagens"""

        print(f"[{self.container_name}] Listening on port {self.port}")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = data.decode()
                
                try:
                    msg = json.loads(message)
                    if msg.get('type') == 'HELLO':
                        self._process_hello(msg, addr[0])
                    elif msg.get('type') == 'LSA':
                        self._process_lsa(msg, addr[0])
                except json.JSONDecodeError:
                    continue
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[{self.container_name}] Listen error: {str(e)}")

    def _process_hello(self, hello: Dict, sender_ip: str):
        
        """
        Processa uma mensagem HELLO recebida.
        
        Args:
            hello (Dict): Mensagem HELLO recebida.
            sender_ip (str): IP do remetente.
        """

        sender_id = hello.get('router_id')
        if not sender_id or sender_id == self.container_name:
            return
            
        with self.lock:
            self.neighbors[sender_id] = sender_ip
            self.last_seen[sender_id] = time.time()
            print(f"[{self.container_name}] Updated neighbor: {sender_id} ({sender_ip})")
            
            # Verifica se todos os vizinhos esperados foram descobertos
            expected_neighbors = self._get_expected_neighbors()
            if set(self.neighbors.keys()) >= set(expected_neighbors):
                self.all_neighbors_discovered = True
                if not self.lsa_sender.running:
                    self.lsa_sender.start()

    def _get_expected_neighbors(self) -> List[str]:
        
        """
        Obtém a lista de vizinhos esperados baseada em variáveis de ambiente.
        
        Returns:
            List[str]: Nomes dos roteadores vizinhos esperados.
        """

        neighbors = []
        for key in os.environ.keys():
            if key.startswith(f"CUSTO_{self.container_name}_") and "_net" in key:
                parts = key.split('_')
                if len(parts) >= 3:
                    neighbor = parts[2]
                    neighbors.append(neighbor)
        return neighbors

    def _process_lsa(self, lsa: Dict, sender_ip: str):
        
        """
        Processa um LSA recebido.
        
        Args:
            lsa (Dict): LSA recebido.
            sender_ip (str): IP do remetente.
        """

        try:
            if self.lsdb.update(lsa):
                print(f"[{self.container_name}] Updated topology from {lsa.get('router_id')}")
                
                if self.all_neighbors_discovered:
                    self._update_routing_table()
                    self.lsa_sender.forward_lsa(lsa, sender_ip)

                self._save_convergence_data()
                    
        except Exception as e:
            print(f"[{self.container_name}] LSA processing error: {str(e)}")

    def _monitor_state(self):

        """Monitora e atualiza o estado do roteador"""

        with self.lock:
            current_neighbors = dict(self.neighbors)
            has_neighbors = len(current_neighbors) > 0
        
        # Remove vizinhos inativos
        now = time.time()
        timeout = 30  # segundos
        inactive = []
        
        with self.lock:
            for neighbor, last_time in list(self.last_seen.items()):
                if now - last_time > timeout:
                    inactive.append(neighbor)
                    del self.neighbors[neighbor]
                    del self.last_seen[neighbor]
        
        if inactive:
            print(f"[{self.container_name}] Removing inactive neighbors: {inactive}")
            self._update_routing_table()

        # Atualiza o próprio LSA periodicamente
        if has_neighbors:
            self._update_own_lsa()
            self._update_routing_table()

    def _update_own_lsa(self):

        """Atualiza o LSA próprio no LSDB"""

        with self.lock:
            neighbors = dict(self.neighbors)
        
        if neighbors:
            lsa = {
                'type': 'LSA',
                'router_id': self.container_name,
                'sequence_number': self.lsa_sender.lsa_sequence + 1,
                'timestamp': time.time(),
                'addresses': self.interface_ips,
                'links': {n: self.get_link_cost_between(self.container_name, n) for n in neighbors}
            }
            self.lsdb.update(lsa)

    def _update_routing_table(self):

        """Recalcula e aplica a tabela de roteamento"""

        print(f"[{self.container_name}] Recalculating routing table...")
        
        with self.lock:
            local_neighbors = dict(self.neighbors)
        
        # Calcula novas rotas
        new_routes = self.lsdb.calculate_routing_table(local_neighbors)
        
        # Filtra rotas válidas (com próximo salto conhecido e IPs de destino)
        valid_routes = {}
        for dest, (hop, cost) in new_routes.items():
            dest_ips = self.lsdb.get_router_ips(dest)
            if hop in local_neighbors and dest_ips:
                valid_routes[dest] = (hop, cost)
        
        # Atualiza a tabela de roteamento
        with self.lock:
            self.routing_table = valid_routes
        
        # Log da tabela atualizada
        print(f"[{self.container_name}] Current routing table:")
        for dest, (hop, cost) in sorted(self.routing_table.items()):
            print(f"  {dest:>8} -> via {hop:<8} (cost {cost:<3})")
        
        # Aplica as rotas no sistema
        self._apply_routes_to_system()

    def _apply_routes_to_system(self):

        """Aplica as rotas calculadas no sistema operacional"""

        print(f"[{self.container_name}] Applying system routes...")
        
        with self.lock:
            neighbors_ips = dict(self.neighbors)
            routing_table = dict(self.routing_table)
        
        success = 0
        for dest, (hop, cost) in routing_table.items():
            hop_ip = neighbors_ips.get(hop)
            if not hop_ip:
                continue
                
            for dest_ip in self.lsdb.get_router_ips(dest):
                try:
                    # Valida o IP de destino
                    ipaddress.ip_address(dest_ip.split('/')[0])
                    
                    # Adiciona a rota
                    subprocess.run(
                        ["ip", "route", "replace", dest_ip, "via", hop_ip],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    print(f"[{self.container_name}] Added route: {dest_ip} via {hop_ip}")
                    success += 1
                except (subprocess.CalledProcessError, ValueError) as e:
                    print(f"[{self.container_name}] Failed to add route {dest_ip}: {str(e)}")
        
        print(f"[{self.container_name}] Successfully applied {success} routes")

    def _get_current_routes(self) -> List[str]:
        
        """
        Obtém as rotas atualmente configuradas no sistema.
        
        Returns:
            List[str]: Lista de rotas no formato do comando 'ip route'.
        """

        try:
            result = subprocess.run(
                ["ip", "route", "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            print(f"[{self.container_name}] Error getting routes: {e.stderr.strip()}")
            return []

    def stop(self):

        """Para o protocolo e limpa recursos"""

        self.running = False
        self.hello_sender.stop()
        self.lsa_sender.stop()
        self.socket.close()
        print(f"[{self.container_name}] Service stopped")

    def _save_convergence_data(self):

        """Salva os dados de convergência parcial no arquivo compartilhado"""

        try:
            caminho = "/shared_data/testesConvergencia"
            os.makedirs(caminho, exist_ok=True)
            with open(f"{caminho}/convergence_data.txt", "a") as f:
                for timestamp, num_routers in self.lsdb.convergence_data:
                    f.write(f" Roteador : {self.container_name}  Tempo : {timestamp:.2f}  Roteadores Descobertos : {num_routers}\n")
            # Limpa os dados após salvar
            self.lsdb.convergence_data = []
        except Exception as e:
            print(f"[{self.container_name}] Error saving convergence data: {str(e)}")
   
    
if __name__ == "__main__":

    """
    Ponto de entrada principal para execução do protocolo.
    
    Inicializa e executa o NeighborDiscoveryProtocol até interrupção.
    """

    print("Starting Neighbor Discovery Protocol...")
    ndp = NeighborDiscoveryProtocol()
    try:
        ndp.start()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        ndp.stop()