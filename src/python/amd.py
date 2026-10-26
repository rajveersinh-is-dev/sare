from typing import Dict, List, Set, Any
from .sare_reference import Graph

class QuotientGraph:
    """Quotient Graph representation for Exact Minimum Degree and Approximate Minimum Degree."""
    def __init__(self, g: Graph):
        self.n: int = g.n
        self.is_eliminated: List[bool] = [False] * self.n
        # direct live neighbors
        self.live_neighbors: List[Set[int]] = [set(g.adj[u]) for u in range(self.n)]
        # adjacent Enodes
        self.elements: List[Set[int]] = [set() for _ in range(self.n)]
        # for an Enode: live members
        self.members: List[Set[int]] = [set() for _ in range(self.n)]
        self.degree_bound: List[int] = [len(self.live_neighbors[u]) for u in range(self.n)]

    def eliminate(self, v: int, g: Graph) -> int:
        self.is_eliminated[v] = True

        # Exact live neighborhood L_v in quotient graph
        l_v = set(self.live_neighbors[v])
        for e in self.elements[v]:
            for u in self.members[e]:
                if u != v and not self.is_eliminated[u]:
                    l_v.add(u)

        # Explicily add fill edges to `g` to match `fill_count` semantics exactly
        fill_added = 0
        l_v_list = list(l_v)
        for i in range(len(l_v_list)):
            for j in range(i + 1, len(l_v_list)):
                a, b = l_v_list[i], l_v_list[j]
                if b not in g.adj[a]:
                    g.add_edge(a, b)
                    fill_added += 1

        for u in l_v_list:
            g.adj[u].remove(v)
        g.adj[v].clear()
        g.eliminated[v] = True

        # update quotient graph
        self.members[v] = set(l_v_list)
        elements_v = list(self.elements[v])

        for u in l_v_list:
            self.live_neighbors[u].discard(v)
            self.elements[u].add(v)
            for e in elements_v:
                self.elements[u].discard(e)

        return fill_added

    def exact_degree(self, u: int) -> int:
        l_u = set(self.live_neighbors[u])
        for e in self.elements[u]:
            for w in self.members[e]:
                if w != u and not self.is_eliminated[w]:
                    l_u.add(w)
        return len(l_u)

    def approx_degree(self, u: int) -> int:
        d = len(self.live_neighbors[u])
        for e in self.elements[u]:
            if len(self.members[e]) > 0:
                d += len(self.members[e]) - 1
        return d


def qmd(graph: Graph) -> Dict[str, Any]:
    """Quotient-graph based Exact Minimum Degree (QMD)."""
    g = graph.copy()
    n = g.n
    qg = QuotientGraph(g)
    order: List[int] = []
    fill_count = 0
    width = 0

    for _ in range(n):
        best_v = -1
        min_deg = float('inf')

        for v in range(n):
            if not qg.is_eliminated[v]:
                deg = qg.exact_degree(v)
                # Tie-breaker: lower ID
                if deg < min_deg or (deg == min_deg and v < best_v):
                    min_deg = deg
                    best_v = v

        if best_v == -1:
            break

        width = max(width, min_deg)
        fill_count += qg.eliminate(best_v, g)
        order.append(best_v)

    return {"order": order, "fill_count": fill_count, "width": width, "fill_edges_added": fill_count}


def approximate_minimum_degree(graph: Graph) -> Dict[str, Any]:
    """Approximate Minimum Degree (AMD) using quotient graph bounds."""
    g = graph.copy()
    n = g.n
    qg = QuotientGraph(g)
    order: List[int] = []
    fill_count = 0
    width = 0

    for _ in range(n):
        best_v = -1
        min_deg = float('inf')

        for v in range(n):
            if not qg.is_eliminated[v]:
                deg = qg.approx_degree(v)
                # Tie-breaker: lower ID
                if deg < min_deg or (deg == min_deg and v < best_v):
                    min_deg = deg
                    best_v = v

        if best_v == -1:
            break

        true_deg = qg.exact_degree(best_v)
        width = max(width, true_deg)

        fill_count += qg.eliminate(best_v, g)
        order.append(best_v)

    return {"order": order, "fill_count": fill_count, "width": width, "fill_edges_added": fill_count}

def look_ahead_qmd(qg: QuotientGraph, v: int) -> float:
    """1-step lookahead estimate (look-A) for quotient graph:
    sum of exact degrees of live neighbors after eliminating v."""
    return sum(max(qg.exact_degree(u) - 1, 0) for u in qg.live_neighbors[v])

def qmd_lookahead(graph: Graph, beta: float = 1.0) -> Dict[str, Any]:
    """Quotient-graph based Exact Minimum Degree with lookahead (QMD-lookahead)."""
    g = graph.copy()
    n = g.n
    qg = QuotientGraph(g)
    order: List[int] = []
    fill_count = 0
    width = 0

    for _ in range(n):
        best_v = -1
        min_score = float('inf')

        for v in range(n):
            if not qg.is_eliminated[v]:
                deg = qg.exact_degree(v)
                lookahead_val = look_ahead_qmd(qg, v)
                score = deg + beta * lookahead_val

                if score < min_score or (score == min_score and v < best_v):
                    min_score = score
                    best_v = v

        if best_v == -1:
            break

        true_deg = qg.exact_degree(best_v)
        width = max(width, true_deg)
        fill_count += qg.eliminate(best_v, g)
        order.append(best_v)

    return {"order": order, "fill_count": fill_count, "width": width, "fill_edges_added": fill_count}
