import sys
from pathlib import Path
import pytest
from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from sare_reference import Graph, sare, min_degree, exact_optimum
from verification import is_chordal, build_filled_graph

def generate_graph_from_edges(n: int, edges: list[tuple[int, int]]) -> Graph:
    g = Graph(n)
    for u, v in edges:
        g.add_edge(u, v)
    return g

@st.composite
def graph_strategy(draw):
    n = draw(st.integers(min_value=1, max_value=20))
    # generate random edges
    edges = draw(st.lists(
        st.tuples(st.integers(min_value=0, max_value=n-1), st.integers(min_value=0, max_value=n-1)).filter(lambda e: e[0] != e[1]),
        min_size=0,
        max_size=n*(n-1)//2
    ))
    return generate_graph_from_edges(n, edges)

@st.composite
def tree_strategy(draw):
    n = draw(st.integers(min_value=1, max_value=20))
    g = Graph(n)
    for i in range(1, n):
        parent = draw(st.integers(min_value=0, max_value=i-1))
        g.add_edge(i, parent)
    return g

@st.composite
def clique_strategy(draw):
    n = draw(st.integers(min_value=1, max_value=20))
    g = Graph(n)
    for i in range(n):
        for j in range(i+1, n):
            g.add_edge(i, j)
    return g

@given(graph_strategy())
def test_sare_properties(graph):
    for algo in [lambda g: sare(g, 1.0, 0.0), min_degree]:
        result = algo(graph)
        ordering = result["order"]
        reported_fill = result["fill_count"]

        # 1. Ordering is a valid permutation
        assert sorted(ordering) == list(range(graph.n))

        # 2. Filled graph is chordal and fill count matches
        H, actual_fill = build_filled_graph(graph, ordering)
        assert actual_fill == reported_fill
        assert is_chordal(H)

@given(tree_strategy())
def test_algorithms_on_trees(tree):
    for algo in [lambda g: sare(g, 1.0, 0.0), min_degree]:
        result = algo(tree)
        assert result["fill_count"] == 0

@given(clique_strategy())
def test_algorithms_on_cliques(clique):
    for algo in [lambda g: sare(g, 1.0, 0.0), min_degree]:
        result = algo(clique)
        assert result["fill_count"] == 0

from hypothesis import settings

@settings(deadline=None)
@given(graph_strategy())
def test_sare_fill_ge_exact_optimum_on_small_graphs(graph):
    if graph.n <= 15:
        opt = exact_optimum(graph)
        result = sare(graph, 1.0, 0.0)
        assert result["fill_count"] >= opt["fill_count"]
