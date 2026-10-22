"""
Verification Oracles for elimination orderings and chordal graphs.

Contains Maximum Cardinality Search (MCS) algorithm to recognize chordal graphs
and verify Perfect Elimination Orderings (PEO).
"""

from typing import List, Set
from .sare_reference import Graph


def mcs(graph: Graph) -> List[int]:
    """Maximum Cardinality Search (MCS) to find a simplicial elimination ordering."""
    n = graph.n
    if n == 0:
        return []

    weights = [0] * n
    unnumbered = [True] * n
    order = [0] * n

    # sets[w] contains all unnumbered vertices with weight w
    sets: List[Set[int]] = [set() for _ in range(n)]
    for v in range(n):
        sets[0].add(v)

    max_weight = 0

    for i in range(n - 1, -1, -1):
        while max_weight > 0 and not sets[max_weight]:
            max_weight -= 1

        # Get an arbitrary element from the non-empty set
        v = next(iter(sets[max_weight]))
        sets[max_weight].remove(v)

        order[i] = v
        unnumbered[v] = False

        for u in graph.adj[v]:
            if unnumbered[u]:
                w = weights[u]
                sets[w].remove(u)
                weights[u] += 1
                new_w = weights[u]
                sets[new_w].add(u)
                if new_w > max_weight:
                    max_weight = new_w

    return order


def is_perfect_elimination_ordering(graph: Graph, order: List[int]) -> bool:
    """Verifies if a given ordering is a Perfect Elimination Ordering (PEO) for the graph."""
    n = graph.n
    if len(order) != n:
        return False

    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    for v in order:
        later_nbrs = [u for u in graph.adj[v] if pos[u] > pos[v]]
        for i in range(len(later_nbrs)):
            for j in range(i + 1, len(later_nbrs)):
                if later_nbrs[j] not in graph.adj[later_nbrs[i]]:
                    return False

    return True


def is_chordal(graph: Graph) -> bool:
    """Checks if a graph is chordal using MCS."""
    order = mcs(graph)
    return is_perfect_elimination_ordering(graph, order)
