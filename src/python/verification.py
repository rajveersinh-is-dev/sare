import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sare_reference import Graph
from typing import List, Tuple

def maximum_cardinality_search(graph: Graph) -> List[int]:
    """
    Computes a perfect elimination ordering using Maximum Cardinality Search (MCS).
    If the graph is chordal, the reverse of this ordering is a PEO.
    Returns the ordering (vertices 0..n-1).
    """
    n = graph.n
    weights = [0] * n
    ordering = []
    unvisited = set(range(n))

    for _ in range(n):
        # find the unvisited vertex with the maximum weight
        max_v = -1
        max_w = -1
        for v in unvisited:
            if weights[v] > max_w:
                max_w = weights[v]
                max_v = v

        ordering.append(max_v)
        unvisited.remove(max_v)

        # update weights of unvisited neighbors
        for u in graph.adj[max_v]:
            if u in unvisited:
                weights[u] += 1

    return ordering[::-1] # reverse the ordering for PEO

def is_peo(graph: Graph, ordering: List[int]) -> bool:
    """
    Checks if the given ordering is a Perfect Elimination Ordering (PEO) for the graph.
    Runs in O(V + E) time.
    """
    n = graph.n
    if len(ordering) != n or set(ordering) != set(range(n)):
        return False

    pos = {v: i for i, v in enumerate(ordering)}

    for i, v in enumerate(ordering):
        # Find later neighbors of v
        later_neighbors = [u for u in graph.adj[v] if pos[u] > i]

        if not later_neighbors:
            continue

        # Find the later neighbor that comes earliest in the ordering
        first_later_neighbor = min(later_neighbors, key=lambda u: pos[u])

        # Check if all other later neighbors of v are also neighbors of first_later_neighbor
        first_ln_adj = graph.adj[first_later_neighbor]
        for w in later_neighbors:
            if w != first_later_neighbor and w not in first_ln_adj:
                return False

    return True

def build_filled_graph(graph: Graph, ordering: List[int]) -> Tuple[Graph, int]:
    """
    Simulates the elimination process and returns the filled graph H and the number of fill edges added.
    """
    g = graph.copy()
    n = g.n

    # H starts as the original graph
    H = Graph(n)
    for v in range(n):
        for u in g.adj[v]:
            H.add_edge(u, v)

    fill_count = 0
    pos = {v: i for i, v in enumerate(ordering)}

    for v in ordering:
        # Find later neighbors of v in the currently remaining graph g
        later_neighbors = [u for u in g.adj[v] if pos[u] > pos[v]]

        # Add fill edges among later neighbors
        for i in range(len(later_neighbors)):
            for j in range(i + 1, len(later_neighbors)):
                a, b = later_neighbors[i], later_neighbors[j]
                if b not in g.adj[a]:
                    g.add_edge(a, b)
                    H.add_edge(a, b)
                    fill_count += 1

        g.eliminate(v)

    return H, fill_count

def is_chordal(graph: Graph) -> bool:
    """
    Checks if a graph is chordal using MCS.
    """
    peo = maximum_cardinality_search(graph)
    return is_peo(graph, peo)
