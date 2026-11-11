import sys
from pathlib import Path
from typing import List, Tuple, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sare_reference import Graph

def get_fill_edges_via_paths(graph: Graph, ordering: List[int]) -> List[Tuple[int, int]]:
    """
    An independent verification oracle for checking exact fill edges using the Fill Path Theorem.
    The Fill Path Theorem states that an edge (u, v) exists in the filled graph H
    if and only if there exists a path between u and v in the original graph G
    such that all intermediate vertices on the path are eliminated before both u and v.
    """
    n = graph.n
    if n == 0:
        return []

    pos = {v: i for i, v in enumerate(ordering)}
    fill_edges = set()

    for u in ordering:
        visited = [False] * n
        queue = [u]
        visited[u] = True

        q_idx = 0
        while q_idx < len(queue):
            curr = queue[q_idx]
            q_idx += 1

            for nbr in graph.adj[curr]:
                if not visited[nbr]:
                    visited[nbr] = True
                    if pos[nbr] < pos[u]:
                        queue.append(nbr)

        for v in range(n):
            if v != u and visited[v] and pos[v] > pos[u]:
                if v not in graph.adj[u]:
                    min_v = min(u, v)
                    max_v = max(u, v)
                    fill_edges.add((min_v, max_v))

    return sorted(list(fill_edges))

def build_filled_graph_via_paths(graph: Graph, ordering: List[int]) -> Tuple[Graph, int]:
    """
    Computes the filled graph strictly via the Fill Path Theorem oracle.
    """
    H = Graph(graph.n)
    for v in range(graph.n):
        for u in graph.adj[v]:
            H.add_edge(u, v)

    fill_edges = get_fill_edges_via_paths(graph, ordering)
    for u, v in fill_edges:
        H.add_edge(u, v)

    return H, len(fill_edges)
