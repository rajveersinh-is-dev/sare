import sys
from pathlib import Path
import pytest
from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from src.python.sare_reference import Graph, min_degree
from src.python.cholesky import graph_to_spd_csc, cholesky_factorize
from src.python.symbolic import elimination_tree, symbolic_factorize

def path_graph(n: int) -> Graph:
    g = Graph(n)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g

def cycle_graph(n: int) -> Graph:
    g = Graph(n)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g

def grid_graph(rows: int, cols: int) -> Graph:
    g = Graph(rows * cols)
    for r in range(rows):
        for c in range(cols):
            u = r * cols + c
            if c + 1 < cols:
                g.add_edge(u, u + 1)
            if r + 1 < rows:
                g.add_edge(u, u + cols)
    return g

@pytest.mark.parametrize("n", [5, 10, 20])
def test_symbolic_factorize_path(n):
    g = path_graph(n)
    # Using min_degree for order
    order = min_degree(g)["order"]
    A = graph_to_spd_csc(g, order)

    parent = elimination_tree(A)
    L_col_ptrs, L_row_indices = symbolic_factorize(A, parent)

    L, _ = cholesky_factorize(A)

    assert L_col_ptrs == L.col_ptrs
    assert L_row_indices == L.row_indices

@pytest.mark.parametrize("n", [5, 10, 20])
def test_symbolic_factorize_cycle(n):
    g = cycle_graph(n)
    order = min_degree(g)["order"]
    A = graph_to_spd_csc(g, order)

    parent = elimination_tree(A)
    L_col_ptrs, L_row_indices = symbolic_factorize(A, parent)

    L, _ = cholesky_factorize(A)

    assert L_col_ptrs == L.col_ptrs
    assert L_row_indices == L.row_indices

@pytest.mark.parametrize("rows, cols", [(2, 2), (3, 3), (4, 4)])
def test_symbolic_factorize_grid(rows, cols):
    g = grid_graph(rows, cols)
    order = min_degree(g)["order"]
    A = graph_to_spd_csc(g, order)

    parent = elimination_tree(A)
    L_col_ptrs, L_row_indices = symbolic_factorize(A, parent)

    L, _ = cholesky_factorize(A)

    assert L_col_ptrs == L.col_ptrs
    assert L_row_indices == L.row_indices

def generate_graph_from_edges(n: int, edges: list[tuple[int, int]]) -> Graph:
    g = Graph(n)
    for u, v in edges:
        g.add_edge(u, v)
    return g

@st.composite
def graph_strategy(draw):
    n = draw(st.integers(min_value=2, max_value=20))
    edges = draw(st.lists(
        st.tuples(st.integers(min_value=0, max_value=n-1), st.integers(min_value=0, max_value=n-1)).filter(lambda e: e[0] != e[1]),
        min_size=1,
        max_size=n*(n-1)//2
    ))
    return generate_graph_from_edges(n, edges)

@given(graph_strategy())
def test_symbolic_structure_matches_numeric(graph):
    # Try random natural ordering
    order = list(range(graph.n))
    A = graph_to_spd_csc(graph, order, alpha=2.0)

    parent = elimination_tree(A)
    L_col_ptrs, L_row_indices = symbolic_factorize(A, parent)

    L, _ = cholesky_factorize(A)

    assert L_col_ptrs == L.col_ptrs
    assert L_row_indices == L.row_indices
