"""
SARE reference implementation (Python).

Readable, correct reference for the Safe-Reduction + Adaptive elimination ordering
algorithm. Mirrors docs/ALGORITHM_SPECIFICATION.md.

This is the reference implementation; the optimized Rust library+CLI lives in src/rs/.

Problem: given an undirected graph G=(V,E), produce an elimination ordering pi that
reduces fill-in and elimination width for a subsequent sparse direct factorization.
Minimum fill-in is NP-hard; this is a heuristic with provably-valid output.

Run:
    python src/python/sare_reference.py --help
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
import sys
from typing import Dict, List, Optional, Set, Tuple


class Graph:
    """Simple undirected graph with mutable adjacency sets (supports fill edges)."""

    def __init__(self, n: int):
        self.n = n
        self.adj: List[Set[int]] = [set() for _ in range(n)]
        self.eliminated: List[bool] = [False] * n

    def add_edge(self, u: int, v: int) -> None:
        if u == v:
            return
        self.adj[u].add(v)
        self.adj[v].add(u)

    def degree(self, v: int) -> int:
        return len(self.adj[v])

    def is_live(self, v: int) -> bool:
        return not self.eliminated[v]

    def fill(self, v: int) -> int:
        """Fill edges created by eliminating v right now: C(d,2) - edges induced by N(v)."""
        nbrs = list(self.adj[v])
        d = len(nbrs)
        induced = 0
        for i in range(d):
            for j in range(i + 1, d):
                if nbrs[j] in self.adj[nbrs[i]]:
                    induced += 1
        return d * (d - 1) // 2 - induced

    def eliminate(self, v: int) -> int:
        """Eliminate v: make N(v) a clique, then remove v. Returns fill edges added."""
        assert not self.eliminated[v]
        nbrs = list(self.adj[v])
        fill_added = 0
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                a, b = nbrs[i], nbrs[j]
                if b not in self.adj[a]:
                    self.adj[a].add(b)
                    self.adj[b].add(a)
                    fill_added += 1
        for u in nbrs:
            self.adj[u].discard(v)
        self.adj[v].clear()
        self.eliminated[v] = True
        return fill_added

    def live_vertices(self) -> List[int]:
        return [v for v in range(self.n) if not self.eliminated[v]]

    def copy(self) -> "Graph":
        g = Graph(self.n)
        for v in range(self.n):
            g.adj[v] = set(self.adj[v])
        g.eliminated = list(self.eliminated)
        return g


def evaluate_order(graph: Graph, order: List[int]) -> Dict[str, object]:
    """Simulate eliminating in `order` on a fresh copy; return fill/width stats."""
    g = graph.copy()
    fill_count = 0
    width = 0
    for v in order:
        assert g.is_live(v), f"vertex {v} eliminated twice"
        width = max(width, g.degree(v))
        fill_count += g.eliminate(v)
    assert len(order) == g.n, "ordering length != n"
    return {"order": list(order), "fill_count": fill_count, "width": width,
            "fill_edges_added": fill_count}


def min_degree(graph: Graph) -> Dict[str, object]:
    """Greedy: repeatedly eliminate a live vertex of minimum degree."""
    g = graph.copy()
    order: List[int] = []
    fill_count = 0
    width = 0
    for _ in range(g.n):
        live = g.live_vertices()
        v = min(live, key=lambda x: g.degree(x))
        width = max(width, g.degree(v))
        fill_count += g.eliminate(v)
        order.append(v)
    return {"order": order, "fill_count": fill_count, "width": width,
            "fill_edges_added": fill_count}


def min_fill(graph: Graph) -> Dict[str, object]:
    """Greedy: repeatedly eliminate a live vertex creating fewest fill edges
    (ties: lower degree, then lower id)."""
    g = graph.copy()
    order: List[int] = []
    fill_count = 0
    width = 0
    for _ in range(g.n):
        live = g.live_vertices()
        v = min(live, key=lambda x: (g.fill(x), g.degree(x), x))
        width = max(width, g.degree(v))
        fill_count += g.eliminate(v)
        order.append(v)
    return {"order": order, "fill_count": fill_count, "width": width,
            "fill_edges_added": fill_count}


def look_ahead(g: Graph, v: int) -> float:
    """1-step lookahead estimate (look-A): sum of neighbor degrees after eliminating v."""
    return float(sum(max(g.degree(u) - 1, 0) for u in g.adj[v]))


def sare(graph: Graph, alpha: float = 1.0, beta: float = 0.0) -> Dict[str, object]:
    """
    SARE: Safe-Reduction + Adaptive elimination ordering.

    Phase A: eliminate degree-0/1 vertices (zero fill, provably safe).
    Phase B: repeatedly eliminate the live vertex minimizing
        score(v) = degree(v) + alpha * fill(v) + beta * look_ahead(v)
    """
    g = graph.copy()
    order: List[int] = []
    fill_count = 0
    width = 0

    # ---------- Phase A: safe reductions ----------
    queue: List[int] = [v for v in g.live_vertices() if g.degree(v) <= 1]
    qhead = 0
    while qhead < len(queue):
        v = queue[qhead]
        qhead += 1
        if g.eliminated[v]:
            continue
        if g.degree(v) > 1:
            continue  # degree changed since enqueued
        width = max(width, g.degree(v))
        fill_count += g.eliminate(v)  # zero fill by construction
        order.append(v)
        for u in list(graph.adj[v]):
            if not g.eliminated[u] and g.degree(u) == 1:
                queue.append(u)

    # ---------- Phase B: adaptive greedy ----------
    for _ in range(g.n):
        live = g.live_vertices()
        if not live:
            break
        v = min(live, key=lambda x: (
            (g.degree(x) + alpha * g.fill(x) + beta * look_ahead(g, x)) * 1e9,
            x,
        ))
        width = max(width, g.degree(v))
        fill_count += g.eliminate(v)
        order.append(v)

    return {"order": order, "fill_count": fill_count, "width": width,
            "fill_edges_added": fill_count, "alpha": alpha, "beta": beta}


def exact_optimum(graph: Graph) -> Dict[str, object]:
    """Exact optimum (min fill, then min width) by dynamic programming over subsets.
    Feasible for n <= ~20. Used for verification."""
    n = graph.n
    if n == 0:
        return {"order": [], "fill_count": 0, "width": 0, "fill_edges_added": 0}
    if n > 20:
        raise ValueError(f"DP exact optimum feasible only for n <= 20, got {n}")

    dp_fill = [float('inf')] * (1 << n)
    dp_tw = [float('inf')] * (1 << n)
    parent = [-1] * (1 << n)

    dp_fill[0] = 0
    dp_tw[0] = 0

    adj_mask = [0] * n
    for i in range(n):
        for u in graph.adj[i]:
            adj_mask[i] |= (1 << u)

    for mask in range(1, 1 << n):
        best_fill = float('inf')
        best_tw = float('inf')
        best_p = -1

        for v in range(n):
            if mask & (1 << v):
                s = mask & ~(1 << v)
                if dp_fill[s] == float('inf'):
                    continue

                unvisited = s
                comps_adj = []
                while unvisited:
                    start = (unvisited & -unvisited).bit_length() - 1
                    comp = (1 << start)
                    queue = [start]
                    unvisited &= ~(1 << start)
                    while queue:
                        node = queue.pop()
                        unvisited_nbrs = adj_mask[node] & unvisited
                        while unvisited_nbrs:
                            nbr = (unvisited_nbrs & -unvisited_nbrs).bit_length() - 1
                            comp |= (1 << nbr)
                            unvisited &= ~(1 << nbr)
                            unvisited_nbrs &= ~(1 << nbr)
                            queue.append(nbr)

                    comp_adj = 0
                    temp = comp
                    while temp:
                        node = (temp & -temp).bit_length() - 1
                        comp_adj |= adj_mask[node]
                        temp &= ~(1 << node)
                    comps_adj.append(comp_adj)

                u_mask = adj_mask[v] & ~s
                for comp_adj in comps_adj:
                    if comp_adj & (1 << v):
                        u_mask |= (comp_adj & ~s)
                u_mask &= ~(1 << v)

                fill = 0
                degree = 0
                u_iter = u_mask
                while u_iter:
                    degree += 1
                    x = (u_iter & -u_iter).bit_length() - 1
                    u_iter &= ~(1 << x)
                    y_iter = u_iter
                    while y_iter:
                        y = (y_iter & -y_iter).bit_length() - 1
                        y_iter &= ~(1 << y)

                        adj_in_gs = (adj_mask[x] & (1 << y)) != 0
                        if not adj_in_gs:
                            for comp_adj in comps_adj:
                                if (comp_adj & (1 << x)) and (comp_adj & (1 << y)):
                                    adj_in_gs = True
                                    break
                        if not adj_in_gs:
                            fill += 1

                new_fill = dp_fill[s] + fill
                new_tw = max(dp_tw[s], degree)

                if new_fill < best_fill or (new_fill == best_fill and new_tw < best_tw):
                    best_fill = new_fill
                    best_tw = new_tw
                    best_p = v

        dp_fill[mask] = best_fill
        dp_tw[mask] = best_tw
        parent[mask] = best_p

    order: List[int] = []
    curr = (1 << n) - 1
    while curr > 0:
        v = parent[curr]
        order.append(v)
        curr &= ~(1 << v)
    order.reverse()

    return {"order": order, "fill_count": int(dp_fill[(1 << n) - 1]),
            "width": int(dp_tw[(1 << n) - 1]), "fill_edges_added": int(dp_fill[(1 << n) - 1])}


def read_edge_list(text: str) -> Graph:
    n = 0
    edges: List[Tuple[int, int]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("%"):
            continue
        parts = line.split()
        if len(parts) == 2:
            a, b = int(parts[0]), int(parts[1])
            n = max(n, a, b)
            edges.append((a - 1, b - 1))  # 1-based -> 0-based
        elif len(parts) == 3:
            r, c = int(parts[0]), int(parts[1])
            n = max(n, r, c)
            edges.append((r - 1, c - 1))
    g = Graph(n)
    for u, v in edges:
        g.add_edge(u, v)
    return g


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="SARE reference (Python)")
    parser.add_argument("input", help="edge list or Matrix Market coordinate file")
    parser.add_argument("algo", choices=["sare", "sare-a0", "sare-a2",
                        "sare-lookahead", "min-degree", "fast-min-degree", "min-fill", "qmd", "amd"])
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--beta", type=float, default=0.0)
    args = parser.parse_args(argv)

    with open(args.input) as f:
        g = read_edge_list(f.read())

    if args.algo == "sare":
        res = sare(g, args.alpha, args.beta)
    elif args.algo == "sare-a0":
        res = sare(g, 0.0, 0.0)
    elif args.algo == "sare-a2":
        res = sare(g, 2.0, 0.0)
    elif args.algo == "sare-lookahead":
        res = sare(g, 1.0, 1.0)
    elif args.algo == "min-degree":
        res = min_degree(g)
    elif args.algo == "fast-min-degree":
        res = fast_min_degree(g)
    elif args.algo == "qmd":
        from .amd import qmd
        res = qmd(g)
    elif args.algo == "amd":
        from .amd import approximate_minimum_degree
        res = approximate_minimum_degree(g)
    else:
        res = min_fill(g)

    res["algorithm"] = args.algo
    res["n"] = g.n
    res["m"] = sum(len(g.adj[v]) for v in range(g.n)) // 2
    res["alpha"] = args.alpha
    res["beta"] = args.beta
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())

def fast_min_degree(graph: Graph) -> Dict[str, object]:
    """Greedy minimum degree using a bucket queue for faster selection."""
    g = graph.copy()
    n = g.n
    order: List[int] = []
    fill_count = 0
    width = 0

    buckets: List[Set[int]] = [set() for _ in range(n + 1)]
    for v in range(n):
        buckets[g.degree(v)].add(v)

    min_bucket = 0

    for _ in range(n):
        while min_bucket <= n and not buckets[min_bucket]:
            min_bucket += 1
        if min_bucket > n:
            break

        v = next(iter(buckets[min_bucket]))
        buckets[min_bucket].remove(v)

        width = max(width, g.degree(v))

        nbrs = list(g.adj[v])
        for u in nbrs:
            buckets[g.degree(u)].remove(u)

        fill_count += g.eliminate(v)
        order.append(v)

        for u in nbrs:
            new_d = g.degree(u)
            buckets[new_d].add(u)
            if new_d < min_bucket:
                min_bucket = new_d

    return {"order": order, "fill_count": fill_count, "width": width,
            "fill_edges_added": fill_count}
