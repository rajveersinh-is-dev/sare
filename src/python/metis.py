from typing import Dict, List, Set, Any, Tuple
import math
import random
from .sare_reference import Graph, evaluate_order
from .nd import get_fiedler

class WeightedGraph:
    def __init__(self, n: int):
        self.n = n
        # adj[u] = list of (v, weight)
        self.adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
        self.vwgt: List[float] = [1.0] * n

    def add_edge(self, u: int, v: int, w: float):
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))

def coarsen(graph: WeightedGraph) -> Tuple[WeightedGraph, List[int]]:
    """Performs one level of Heavy Edge Matching graph coarsening."""
    n = graph.n
    matched = [False] * n
    match = [-1] * n

    # Process nodes in random order
    rng = random.Random(42)
    nodes = list(range(n))
    rng.shuffle(nodes)

    num_coarse_nodes = 0
    for u in nodes:
        if matched[u]:
            continue

        best_v = -1
        max_w = -1.0

        for v, w in graph.adj[u]:
            if not matched[v] and w > max_w:
                max_w = w
                best_v = v

        if best_v != -1:
            match[u] = best_v
            match[best_v] = u
            matched[u] = True
            matched[best_v] = True
        else:
            match[u] = u
            matched[u] = True

    # Build coarse graph
    coarse_map = [-1] * n
    coarse_n = 0
    for i in range(n):
        if coarse_map[i] == -1:
            coarse_map[i] = coarse_n
            if match[i] != -1:
                coarse_map[match[i]] = coarse_n
            coarse_n += 1

    coarse_g = WeightedGraph(coarse_n)
    for i in range(n):
        if match[i] == i or match[i] < i:
            c_u = coarse_map[i]
            if match[i] != i:
                coarse_g.vwgt[c_u] = graph.vwgt[i] + graph.vwgt[match[i]]
            else:
                coarse_g.vwgt[c_u] = graph.vwgt[i]

    # Combine edges
    for u in range(n):
        c_u = coarse_map[u]
        for v, w in graph.adj[u]:
            c_v = coarse_map[v]
            if c_u != c_v:
                # Add to coarse_g. If it exists, sum weights.
                # To simplify, just append and we'll compact later
                coarse_g.adj[c_u].append((c_v, w))

    # Compact edges
    for i in range(coarse_n):
        edge_map = {}
        for v, w in coarse_g.adj[i]:
            edge_map[v] = edge_map.get(v, 0.0) + w
        coarse_g.adj[i] = list(edge_map.items())

    return coarse_g, coarse_map

def initial_partition(graph: WeightedGraph) -> Tuple[List[int], List[int]]:
    """Spectral bisection on the coarsest graph."""
    n = graph.n
    if n <= 1:
        return list(range(n)), []

    # Unweighted adjacency for fiedler
    adj = [[v for v, _ in graph.adj[u]] for u in range(n)]
    fiedler = get_fiedler(adj)

    sorted_f = sorted([(fiedler[i], i) for i in range(n)])

    # Try to balance weights
    total_w = sum(graph.vwgt)
    target_w = total_w / 2.0

    L = []
    R = []
    curr_w = 0.0

    for val, idx in sorted_f:
        if curr_w < target_w:
            L.append(idx)
            curr_w += graph.vwgt[idx]
        else:
            R.append(idx)

    # Just in case one is empty
    if not L and R:
        L.append(R.pop())
    elif not R and L:
        R.append(L.pop())

    return L, R

def refine_kl(graph: WeightedGraph, L: List[int], R: List[int]) -> Tuple[List[int], List[int]]:
    """Kernighan-Lin refinement."""
    # Simplified KL: Just boundary greedy swaps
    L_set = set(L)
    R_set = set(R)

    changed = True
    while changed:
        changed = False

        # Calculate gains
        gains = {}
        for u in range(graph.n):
            internal = 0.0
            external = 0.0
            is_L = u in L_set

            for v, w in graph.adj[u]:
                if (v in L_set) == is_L:
                    internal += w
                else:
                    external += w

            gains[u] = external - internal

        # Try finding a profitable swap
        best_gain = 0.0
        best_u = -1

        for u in range(graph.n):
            if gains[u] > best_gain:
                best_gain = gains[u]
                best_u = u

        if best_u != -1 and best_gain > 0:
            if best_u in L_set:
                L_set.remove(best_u)
                R_set.add(best_u)
            else:
                R_set.remove(best_u)
                L_set.add(best_u)
            changed = True

    return list(L_set), list(R_set)

def metis_bisection(graph: WeightedGraph) -> Tuple[List[int], List[int]]:
    """Multi-level bisection."""
    if graph.n <= 50:
        return initial_partition(graph)

    coarse_g, coarse_map = coarsen(graph)

    # Stop if we didn't coarsen much
    if coarse_g.n > 0.8 * graph.n:
        return initial_partition(graph)

    cL, cR = metis_bisection(coarse_g)

    # Project back
    cL_set = set(cL)
    L = []
    R = []

    for i in range(graph.n):
        if coarse_map[i] in cL_set:
            L.append(i)
        else:
            R.append(i)

    return refine_kl(graph, L, R)

def get_vertex_separator(graph: WeightedGraph, L: List[int], R: List[int]) -> Tuple[List[int], List[int], List[int]]:
    """Extracts a vertex separator from an edge separator."""
    L_set = set(L)
    R_set = set(R)

    V_L = set()
    V_R = set()

    for u in L:
        for v, _ in graph.adj[u]:
            if v in R_set:
                V_L.add(u)
                V_R.add(v)

    if len(V_L) < len(V_R):
        S = V_L
        L_final = L_set - V_L
        R_final = R_set
    else:
        S = V_R
        R_final = R_set - V_R
        L_final = L_set

    return list(L_final), list(R_final), list(S)

def metis_nd_recursive(adj_list: List[List[int]], nodes: List[int], min_size: int = 5) -> List[int]:
    n_local = len(nodes)
    if n_local <= min_size:
        local_deg = []
        nodes_set = set(nodes)
        for u in nodes:
            deg = sum(1 for v in adj_list[u] if v in nodes_set)
            local_deg.append((deg, u))
        local_deg.sort()
        return [u for _, u in local_deg]

    # Build local weighted graph
    wg = WeightedGraph(n_local)
    global_to_local = {g: l for l, g in enumerate(nodes)}

    for i, g in enumerate(nodes):
        for nbr in adj_list[g]:
            if nbr in global_to_local:
                wg.add_edge(i, global_to_local[nbr], 1.0)

    # Bisect
    L_local, R_local = metis_bisection(wg)

    # Find separator
    L_local, R_local, S_local = get_vertex_separator(wg, L_local, R_local)

    L = [nodes[i] for i in L_local]
    R = [nodes[i] for i in R_local]
    S = [nodes[i] for i in S_local]

    if not L or not R:
        return list(nodes)

    order_L = metis_nd_recursive(adj_list, L, min_size)
    order_R = metis_nd_recursive(adj_list, R, min_size)

    # Sort separator by degree
    S_deg = []
    S_set = set(S)
    for u in S:
        deg = sum(1 for v in adj_list[u] if v in S_set)
        S_deg.append((deg, u))
    S_deg.sort()
    S_sorted = [u for _, u in S_deg]

    return order_L + order_R + S_sorted

def metis_nested_dissection(graph: Graph, min_size: int = 5) -> Dict[str, Any]:
    """Computes a fill-reducing ordering using Metis Nested Dissection."""
    n = graph.n
    adj_list = [list(graph.adj[i]) for i in range(n)]

    order = metis_nd_recursive(adj_list, list(range(n)), min_size)

    return evaluate_order(graph, order)
