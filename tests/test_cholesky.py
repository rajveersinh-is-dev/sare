import pytest
from src.python.sare_reference import Graph, sare, min_degree
from src.python.cholesky import verify_fill_numerically, graph_to_spd_csc, cholesky_factorize

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

def star_graph(n: int) -> Graph:
    g = Graph(n)
    for i in range(1, n):
        g.add_edge(0, i)
    return g

@pytest.mark.parametrize("n", [5, 10, 20])
def test_numeric_fill_cycle_min_degree(n):
    g = cycle_graph(n)
    res = min_degree(g)
    assert verify_fill_numerically(g, res["order"], res["fill_count"])

@pytest.mark.parametrize("rows,cols", [(3, 3), (4, 4)])
def test_numeric_fill_grid_sare(rows, cols):
    g = grid_graph(rows, cols)
    res = sare(g)
    assert verify_fill_numerically(g, res["order"], res["fill_count"])

def test_numeric_fill_star_sare():
    g = star_graph(10)
    res = sare(g)
    assert verify_fill_numerically(g, res["order"], res["fill_count"])

def test_cholesky_factorize_matrix_reconstruction():
    """Verify L L^T = A for a small example."""
    g = star_graph(5)
    res = sare(g)
    order = res["order"]
    A = graph_to_spd_csc(g, order)

    L, _ = cholesky_factorize(A)

    # We construct a dense representation to easily check L L^T == A
    n = g.n
    dense_A = [[0.0 for _ in range(n)] for _ in range(n)]
    for j in range(n):
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            r = A.row_indices[p]
            dense_A[r][j] = A.values[p]
            dense_A[j][r] = A.values[p]

    dense_L = [[0.0 for _ in range(n)] for _ in range(n)]
    for j in range(n):
        for p in range(L.col_ptrs[j], L.col_ptrs[j+1]):
            r = L.row_indices[p]
            dense_L[r][j] = L.values[p]

    # Compute L L^T
    LLT = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                LLT[i][j] += dense_L[i][k] * dense_L[j][k]

    # Check max difference
    for i in range(n):
        for j in range(n):
            assert abs(dense_A[i][j] - LLT[i][j]) < 1e-9
