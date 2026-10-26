import pytest
from src.python.sare_reference import Graph, min_degree
from src.python.nd import spectral_nested_dissection
from src.python.verification import is_peo, build_filled_graph

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

def cycle_graph(n: int) -> Graph:
    g = Graph(n)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g

@pytest.mark.parametrize("n", [5, 10, 15])
def test_nd_valid_permutation(n):
    g = cycle_graph(n)
    res = spectral_nested_dissection(g)
    order = res["order"]
    assert len(order) == n
    assert sorted(order) == list(range(n))

@pytest.mark.parametrize("n", [10, 20])
def test_nd_is_peo_on_filled_graph(n):
    g = cycle_graph(n)
    res = spectral_nested_dissection(g)
    order = res["order"]
    H, fill = build_filled_graph(g, order)
    assert is_peo(H, order)
    assert res["fill_count"] == fill

def test_nd_runs_successfully_grid():
    g = grid_graph(5, 5)
    res_nd = spectral_nested_dissection(g)
    assert res_nd["fill_count"] >= 0
    assert len(res_nd["order"]) == g.n
