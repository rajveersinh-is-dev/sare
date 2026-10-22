"""
Property-based tests for SARE reference implementation using hypothesis.
Checks that all orderings generated are valid permutations, that the fill
is accurately computed, and that the filled graph is chordal.
"""

from hypothesis import given, settings
import hypothesis.strategies as st
from typing import List, Tuple

from src.python.sare_reference import Graph, sare, min_degree, min_fill, evaluate_order
from src.python.verification import is_chordal
from src.python.exact_dp import exact_dp

@st.composite
def graph_strategy(draw, max_n=20) -> Graph:
    n = draw(st.integers(min_value=1, max_value=max_n))
    edges = draw(st.lists(
        st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
        min_size=0,
        max_size=n * n
    ))
    g = Graph(n)
    for u, v in edges:
        if u != v:
            g.add_edge(u, v)
    return g

@given(g=graph_strategy())
@settings(max_examples=100)
def test_sare_valid_permutation(g: Graph):
    r = sare(g, 1.0, 0.0)
    assert sorted(r["order"]) == list(range(g.n))

@given(g=graph_strategy())
@settings(max_examples=100)
def test_sare_fill_matches_evaluation(g: Graph):
    r = sare(g, 1.0, 0.0)
    ev = evaluate_order(g, r["order"])
    assert r["fill_count"] == ev["fill_count"]
    assert r["width"] == ev["width"]

@given(g=graph_strategy())
@settings(max_examples=100)
def test_min_degree_valid(g: Graph):
    r = min_degree(g)
    assert sorted(r["order"]) == list(range(g.n))

@given(g=graph_strategy())
@settings(max_examples=100)
def test_min_fill_valid(g: Graph):
    r = min_fill(g)
    assert sorted(r["order"]) == list(range(g.n))

@given(g=graph_strategy(max_n=15))
@settings(max_examples=50)
def test_sare_chordal_completion(g: Graph):
    r = sare(g, 1.0, 0.0)
    order = r["order"]

    # Build the filled graph
    h = Graph(g.n)
    for v in range(g.n):
        for u in g.adj[v]:
            if u > v:
                h.add_edge(v, u)

    g2 = g.copy()
    pos = {v: i for i, v in enumerate(order)}

    for v in order:
        later_nbrs = [u for u in g2.adj[v] if pos[u] > pos[v]]
        for i in range(len(later_nbrs)):
            for j in range(i + 1, len(later_nbrs)):
                h.add_edge(later_nbrs[i], later_nbrs[j])
        g2.eliminate(v)

    assert is_chordal(h)

@given(g=graph_strategy(max_n=10))
@settings(max_examples=50)
def test_sare_vs_exact_dp(g: Graph):
    r = sare(g, 1.0, 0.0)
    opt = exact_dp(g)

    # SARE heuristic fill must be >= exact optimal DP fill
    assert r["fill_count"] >= opt["fill_count"]
