"""
Exact minimum fill via Dynamic Programming (Held-Karp style)

Computes exact minimum fill-in (and treewidth) by dynamic programming over subsets.
Useful for verifying heuristic algorithms on small instances up to N=18.
"""

from typing import Dict, List, Tuple
from .sare_reference import Graph, evaluate_order


def exact_dp(graph: Graph) -> Dict[str, object]:
    """
    Solves minimum fill exactly using DP over subsets.
    For each subset S of eliminated vertices, it tracks the minimum fill and width.
    Returns the optimal elimination ordering, minimum fill, and corresponding width.

    Complexity: O(2^N * poly(N)). Feasible for N <= 18.
    """
    n = graph.n
    if n == 0:
        return {"order": [], "fill_count": 0, "width": 0, "fill_edges_added": 0}

    if n > 20:
        raise ValueError(f"DP feasible only for n <= 20, got {n}")

    # dp[mask] = (min_fill, min_width, last_eliminated)
    dp: Dict[int, Tuple[int, int, int]] = {0: (0, 0, -1)}

    for size in range(n):
        current_states = [(mask, state) for mask, state in dp.items() if mask.bit_count() == size]

        for mask, (cur_fill, cur_width, _) in current_states:
            # Reconstruct the elimination order that led to 'mask'
            order = []
            current_mask = mask
            while current_mask != 0:
                _, _, v = dp[current_mask]
                order.append(v)
                current_mask &= ~(1 << v)
            order.reverse()

            # Build the graph corresponding to the eliminated subset 'mask'
            g = graph.copy()
            for v in order:
                g.eliminate(v)

            for v in range(n):
                if not (mask & (1 << v)):
                    d = g.degree(v)
                    next_g = g.copy()
                    added_fill = next_g.eliminate(v)

                    next_mask = mask | (1 << v)
                    new_fill = cur_fill + added_fill
                    new_width = max(cur_width, d)

                    if next_mask in dp:
                        existing_fill, existing_width, _ = dp[next_mask]
                        if new_fill < existing_fill or (new_fill == existing_fill and new_width < existing_width):
                            dp[next_mask] = (new_fill, new_width, v)
                    else:
                        dp[next_mask] = (new_fill, new_width, v)

    final_mask = (1 << n) - 1
    final_fill, final_width, _ = dp[final_mask]

    best_order = []
    current_mask = final_mask
    while current_mask != 0:
        _, _, v = dp[current_mask]
        best_order.append(v)
        current_mask &= ~(1 << v)
    best_order.reverse()

    return {
        "order": best_order,
        "fill_count": final_fill,
        "width": final_width,
        "fill_edges_added": final_fill
    }
