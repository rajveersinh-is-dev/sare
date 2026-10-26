import pytest
from src.python.sare_reference import Graph, min_degree
from src.python.amd import approximate_minimum_degree, qmd
from src.python.verification import is_peo, build_filled_graph

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

def star_graph(n: int) -> Graph:
    g = Graph(n)
    for i in range(1, n):
        g.add_edge(0, i)
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

@pytest.mark.parametrize("n", [5, 10, 15])
@pytest.mark.parametrize("algo", [qmd, approximate_minimum_degree])
def test_amd_valid_permutation(n, algo):
    g = path_graph(n)
    res = algo(g)
    order = res["order"]
    assert len(order) == n
    assert sorted(order) == list(range(n))

@pytest.mark.parametrize("n", [10, 20])
@pytest.mark.parametrize("algo", [qmd, approximate_minimum_degree])
def test_amd_is_peo_on_filled_graph(n, algo):
    g = cycle_graph(n)
    res = algo(g)
    order = res["order"]
    H, fill = build_filled_graph(g, order)
    assert is_peo(H, order)
    assert res["fill_count"] == fill

def test_qmd_matches_min_degree():
    """QMD computes exact degrees, so its ordering length and fill should
    be valid and roughly match naive exact minimum degree, although tie breaking
    may cause small differences. We assert they run and return a valid result."""
    g = grid_graph(4, 4)
    res_qmd = qmd(g)
    res_md = min_degree(g)

    assert res_qmd["fill_count"] >= 0
    assert len(res_qmd["order"]) == g.n
    assert len(res_md["order"]) == g.n

    # QMD should have identical fill to min_degree if tie-breaking is identical.
    # We just ensure it's structurally similar.
    assert res_qmd["fill_count"] == res_md["fill_count"]

def test_amd_runs_successfully():
    """AMD upper bounds degree, so it might not match exact MD, but it must be valid."""
    g = grid_graph(5, 5)
    res_amd = approximate_minimum_degree(g)
    assert res_amd["fill_count"] >= 0
    assert len(res_amd["order"]) == g.n
