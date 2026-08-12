import networkx as nx
from ortools.sat.python import cp_model


def get_acyclic_orientations(G):
    """
    Generates all valid acyclic orientations of a given graph using backtracking.
    """
    edges = list(G.edges())
    valid_aos = []

    n_nodes = G.number_of_nodes()
    adj = {i: [] for i in range(n_nodes)}

    def has_path(start, target):
        stack = [start]
        visited = set()

        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current not in visited:
                visited.add(current)
                stack.extend(adj[current])

        return False

    def backtrack(edge_index, current_directions):
        if edge_index == len(edges):
            valid_aos.append(tuple(current_directions))
            return

        u, v = edges[edge_index]

        if not has_path(v, u):
            adj[u].append(v) 
            current_directions.append(0)

            backtrack(edge_index + 1, current_directions)

            current_directions.pop()
            adj[u].pop() 

        if not has_path(u, v):
            adj[v].append(u) 
            current_directions.append(1)

            backtrack(edge_index + 1, current_directions)

            current_directions.pop()
            adj[v].pop() 

    backtrack(0, [])

    return valid_aos


def build_flip_graph(aos):
    """
    Constructs a flip graph where nodes are acyclic orientations and edges 
    connect orientations that differ by exactly one edge flip.
    """
    flip_graph = nx.Graph()
    flip_graph.add_nodes_from(aos)

    aos_set = set(aos)

    for ao in aos:
        for i in range(len(ao)):
            flipped_ao = list(ao)

            flipped_ao[i] = 1 - flipped_ao[i]

            flipped_ao = tuple(flipped_ao)

            if flipped_ao in aos_set:
                flip_graph.add_edge(ao, flipped_ao)

    return flip_graph


def has_hamiltonian_cycle_ortools(graph):
    """
    Determines if a Hamiltonian cycle exists in the given graph using 
    Google OR-Tools constraint programming.
    """
    for node in graph.nodes():
        if graph.degree(node) < 2:
            return False

    model = cp_model.CpModel()

    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    arcs = []

    for u, v in graph.edges():
        i = node_to_idx[u]
        j = node_to_idx[v]

        lit_forward = model.NewBoolVar(f'edge_{i}_to_{j}')
        arcs.append([i, j, lit_forward])

        lit_backward = model.NewBoolVar(f'edge_{j}_to_{i}')
        arcs.append([j, i, lit_backward])

    model.AddCircuit(arcs)

    solver = cp_model.CpSolver()

    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return True
    return False


def create_wheel_graph(n):
    """
    Creates a wheel graph with a central node connected to an outer cycle of n nodes.
    """
    Wn = nx.Graph()
    edges = []

    for i in range(1, n + 1):
        edges.append((0, i))

    for i in range(1, n):
        edges.append((i, i + 1))

    edges.append((n, 1))

    Wn.add_edges_from(edges)
    return Wn

if __name__ == "__main__":
    Wn = create_wheel_graph(3)
    print("1. Generating Acyclic Orientations...")
    aos = get_acyclic_orientations(Wn)
    print(f"   Found {len(aos)} AOs.")

    print("\n2. Building the Flip Graph...")
    flip_graph = build_flip_graph(aos)
    print(f"   Flip graph has {len(flip_graph.edges())} edges.")

    print("\n3. Searching for a Hamiltonian Cycle with OR-Tools...")
    result = has_hamiltonian_cycle_ortools(flip_graph)

    if result:
        print("\nResult: YES, a Hamiltonian cycle exists!")
    else:
        print("\nResult: NO, a Hamiltonian cycle does not exist.")