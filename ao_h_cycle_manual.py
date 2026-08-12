import networkx as nx
import time
from itertools import product

def get_acyclic_orientations(G):
    """
    Generates all valid acyclic orientations of a graph by exhaustively 
    testing all possible edge direction combinations.
    """
    edges = list(G.edges())
    acyclic_orientations = []

    for state in product([0, 1], repeat=len(edges)):
        DG = nx.DiGraph()
        DG.add_nodes_from(G.nodes())

        for i, (u, v) in enumerate(edges):
            if state[i] == 0:
                DG.add_edge(u, v)
            else:
                DG.add_edge(v, u)

        if nx.is_directed_acyclic_graph(DG):
            acyclic_orientations.append(state)

    return acyclic_orientations

def build_flip_graph(orientations):
    """
    Constructs a flip graph connecting acyclic orientations that differ 
    by exactly one edge reversal.
    """
    FG = nx.Graph()
    FG.add_nodes_from(orientations)
    for i in range(len(orientations)):
        for j in range(i + 1, len(orientations)):
            diff = sum(1 for a, b in zip(orientations[i], orientations[j]) if a != b)

            if diff == 1:
                FG.add_edge(orientations[i], orientations[j])

    return FG


def has_hamiltonian_cycle(G):
    """
    Checks for a Hamiltonian cycle in the graph using depth-first search 
    backtracking, optimized with Warnsdorff's rule.
    """
    if len(G) < 3:
        return False

    if any(deg < 2 for _, deg in G.degree()):
        print("FAILED: Graph has nodes with degree < 2 (Dead ends).")
        return False

    if not nx.is_connected(G):
        print("FAILED: Graph is disconnected. No global cycle possible.")
        return False

    if len(G) % 2 != 0:
        return False

    nodes = list(G.nodes())
    start_node = nodes[0]
    path = [start_node]
    visited = set([start_node])

    def backtrack(current_node):
        if len(path) == len(nodes):
            if G.has_edge(current_node, start_node):
                return True
            return False

        def unvisited_degree(n):
            return sum(1 for neighbor in G.neighbors(n) if neighbor not in visited)

        valid_neighbors = [n for n in G.neighbors(current_node) if n not in visited]
        valid_neighbors.sort(key=unvisited_degree)

        for neighbor in valid_neighbors:
            visited.add(neighbor)
            path.append(neighbor)

            if backtrack(neighbor):
                return True

            path.pop()
            visited.remove(neighbor)

        return False

    return backtrack(start_node)

def run(G):
    """
    Executes the full pipeline: generates orientations, builds the flip graph, 
    checks for a Hamiltonian cycle, and prints the results.
    """
    orientations = get_acyclic_orientations(G)
    print(f"Acyclic Orientations: {len(orientations)}")
    FG=build_flip_graph(orientations)
    has_cycle=has_hamiltonian_cycle(FG)
    print(f"Hamiltonian cycle: {'YES' if has_cycle else 'NO'}\n")

if __name__ == "__main__":
    G_wheel = nx.Graph()
    G_wheel.add_edges_from([
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (2, 3), (3, 4), (4,1)])
    print("Wheel")
    run(G_wheel)
