import json
import networkx as nx
import matplotlib.pyplot as plt
import os

def generate_topology_json():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    topology = {
        "roteadores": [
            {"id": "R1", "conexoes": [{"destino": "R2", "custo": 1}, {"destino": "R5", "custo": 5}]},
            {"id": "R2", "conexoes": [{"destino": "R4", "custo": 3}, {"destino": "R3", "custo": 3}]},
            {"id": "R3", "conexoes": [{"destino": "R2", "custo": 2}, {"destino": "R5", "custo": 2}]},
            {"id": "R4", "conexoes": [{"destino": "R2", "custo": 3}]},
            {"id": "R5", "conexoes": [{"destino": "R1", "custo": 2}, {"destino": "R3", "custo": 2}]},
        ]
    }

    json_path = os.path.join(script_dir, 'topologia_rede_simples.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(topology, f, indent=4, ensure_ascii=False)

    return topology, script_dir

def create_and_draw_network(topology, script_dir):
    G = nx.Graph()
    edge_labels = {}

    for router in topology["roteadores"]:
        origem = router["id"]
        for conexao in router["conexoes"]:
            destino = conexao["destino"]
            custo = conexao["custo"]

            if not G.has_edge(origem, destino):
                G.add_edge(origem, destino, peso=custo)
                edge_labels[(origem, destino)] = custo

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color='lightgray', node_size=1000, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    plt.title("Topologia de Rede com Custos")
    plt.axis('off')

    image_path = os.path.join(script_dir, "topologia_rede_simples.png")
    plt.savefig(image_path)
    plt.show()

if __name__ == "__main__":
    topo, path = generate_topology_json()
    create_and_draw_network(topo, path)
