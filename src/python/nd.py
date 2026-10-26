from typing import Dict, List, Set, Any, Tuple
import math
import random
from .sare_reference import Graph, evaluate_order

def get_fiedler(adj: List[List[int]], num_iters: int = 1000, tol: float = 1e-6) -> List[float]:
    """Compute the Fiedler vector (eigenvector of 2nd smallest eigenvalue) using Deflated Power Iteration."""
    n = len(adj)
    if n <= 1:
        return [0.0] * n

    degrees = [len(nbrs) for nbrs in adj]
    max_d = max(degrees) if degrees else 0
    # Shift to make matrix positive definite and reverse eigenvalue order
    c = 2.0 * max_d + 1.0

    # Initialize random vector
    rng = random.Random(42)
    v = [rng.random() - 0.5 for _ in range(n)]

    # Deflate all-ones (smallest eigenvector of Laplacian)
    s = sum(v) / n
    v = [x - s for x in v]

    norm = math.sqrt(sum(x*x for x in v))
    if norm > 0:
        v = [x / norm for x in v]

    for _ in range(num_iters):
        v_next = [0.0] * n
        for i in range(n):
            val = (c - degrees[i]) * v[i]
            for j in adj[i]:
                val += v[j]
            v_next[i] = val

        s = sum(v_next) / n
        v_next = [x - s for x in v_next]

        norm = math.sqrt(sum(x*x for x in v_next))
        if norm > 0:
            v_next = [x / norm for x in v_next]

        diff = max(abs(v_next[i] - v[i]) for i in range(n))
        diff2 = max(abs(v_next[i] + v[i]) for i in range(n))
        if diff < tol or diff2 < tol:
            v = v_next
            break

        v = v_next

    return v

def get_vertex_separator(adj: List[List[int]], nodes: List[int]) -> Tuple[List[int], List[int], List[int]]:
    """Finds a vertex separator using spectral bisection."""
    n_local = len(nodes)
    if n_local <= 2:
        return [], [], list(nodes)

    global_to_local = {g: l for l, g in enumerate(nodes)}

    local_adj = [[] for _ in range(n_local)]
    for i, g in enumerate(nodes):
        for nbr in adj[g]:
            if nbr in global_to_local:
                local_adj[i].append(global_to_local[nbr])

    fiedler = get_fiedler(local_adj)

    # Sort to find median
    sorted_f = sorted([(fiedler[i], i) for i in range(n_local)])
    median_idx = n_local // 2

    L_local = set(idx for val, idx in sorted_f[:median_idx])
    R_local = set(idx for val, idx in sorted_f[median_idx:])

    # Find boundary (edge separator)
    V_L = set()
    V_R = set()
    for u in L_local:
        for v in local_adj[u]:
            if v in R_local:
                V_L.add(u)
                V_R.add(v)

    # Promote the smaller boundary to be the vertex separator
    if len(V_L) < len(V_R):
        S_local = V_L
        L_local = L_local - V_L
    else:
        S_local = V_R
        R_local = R_local - V_R

    L = [nodes[i] for i in L_local]
    R = [nodes[i] for i in R_local]
    S = [nodes[i] for i in S_local]

    return L, R, S

def spectral_nested_dissection(graph: Graph, min_size: int = 5) -> Dict[str, Any]:
    """Computes a fill-reducing ordering using Spectral Nested Dissection."""
    n = graph.n
    adj_list = [list(graph.adj[i]) for i in range(n)]

    def nd_recursive(nodes: List[int]) -> List[int]:
        if len(nodes) <= min_size:
            # Base case: sort by local degree
            local_deg = []
            for u in nodes:
                deg = sum(1 for v in adj_list[u] if v in nodes)
                local_deg.append((deg, u))
            local_deg.sort()
            return [u for _, u in local_deg]

        L, R, S = get_vertex_separator(adj_list, nodes)

        if not L or not R:
            return list(nodes)

        order_L = nd_recursive(L)
        order_R = nd_recursive(R)

        # Sort separator by degree
        S_deg = []
        for u in S:
            deg = sum(1 for v in adj_list[u] if v in S)
            S_deg.append((deg, u))
        S_deg.sort()
        S_sorted = [u for _, u in S_deg]

        return order_L + order_R + S_sorted

    order = nd_recursive(list(range(n)))

    # Evaluate the order
    return evaluate_order(graph, order)
