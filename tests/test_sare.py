"""
Tests for SARE (Safe-Reduction + Adaptive elimination ordering).

Covers:
  * reference-implementation correctness (Python)
  * cross-language differential: Rust CLI vs Python reference
  * brute-force differential on small graphs (optimum lower bound)
  * invariants: valid permutation, exact fill/width, chordal completion
  * adversarial / degenerate inputs

Run:  pytest tests/  (from repo root)
"""

import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUST_BIN = REPO_ROOT / "src" / "rs" / "target" / "release" / "sare.exe"
if not RUST_BIN.exists():
    RUST_BIN = REPO_ROOT / "src" / "rs" / "target" / "release" / "sare"

# ---- load the Python reference as a module ----
spec = importlib.util.spec_from_file_location(
    "sare_reference", REPO_ROOT / "src" / "python" / "sare_reference.py"
)
sare_ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sare_ref)
Graph = sare_ref.Graph
sare = sare_ref.sare
min_degree = sare_ref.min_degree
min_fill = sare_ref.min_fill
brute_force_optimum = sare_ref.brute_force_optimum
evaluate_order = sare_ref.evaluate_order
read_edge_list = sare_ref.read_edge_list


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def rand_graph(n, m, seed=0, p=None):
    """Random undirected simple graph: either m random edges or Erdos-Renyi p."""
    rng = random.Random(seed)
    g = Graph(n)
    max_edges = n * (n - 1) // 2
    m = min(m, max_edges)
    edges = set()
    if p is None:
        # m random edges
        while len(edges) < m:
            u, v = rng.randrange(n), rng.randrange(n)
            if u == v:
                continue
            e = (min(u, v), max(u, v))
            if e in edges:
                continue
            edges.add(e)
            g.add_edge(u, v)
    else:
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < p:
                    g.add_edge(u, v)
    return g


def grid_graph(rows, cols):
    g = Graph(rows * cols)
    for r in range(rows):
        for c in range(cols):
            v = r * cols + c
            if r + 1 < rows:
                g.add_edge(v, v + cols)
            if c + 1 < cols:
                g.add_edge(v, v + 1)
    return g


def run_rust_cli(graph_text, algo, alpha=1.0, beta=0.0):
    """Run the Rust CLI on graph text; return parsed JSON."""
    inp = str(Path(__file__).resolve().parents[1] / "tests" / "_tmp_input.graph")
    Path(inp).write_text(graph_text)
    cmd = [str(RUST_BIN), inp, algo, str(alpha), str(beta)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    assert out.returncode == 0, f"Rust CLI failed: {out.stderr}"
    return json.loads(out.stdout)


def text_of(g):
    lines = []
    for v in range(g.n):
        for u in sorted(g.adj[v]):
            if u > v:
                lines.append(f"{v+1} {u+1}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# reference correctness (Python)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", list(range(0, 13)))
def test_order_is_permutation(n):
    g = rand_graph(n, n * 2, seed=n)
    r = sare(g, 1.0, 0.0)
    assert sorted(r["order"]) == list(range(n))


def test_fill_width_match_evaluate():
    g = rand_graph(9, 20, seed=3)
    r = sare(g, 1.0, 0.0)
    ev = evaluate_order(g, r["order"])
    assert ev["fill_count"] == r["fill_count"]
    assert ev["width"] == r["width"]


def test_clique_zero_fill():
    g = Graph(6)
    for i in range(6):
        for j in range(i + 1, 6):
            g.add_edge(i, j)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] == 0
    assert r["width"] == 5  # max later neighbors


def test_path_width_one():
    # path: leaves first -> width 1, zero fill
    g = Graph(10)
    for i in range(9):
        g.add_edge(i, i + 1)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] == 0
    assert r["width"] <= 1


def test_empty_and_single():
    for n in (0, 1):
        g = Graph(n)
        r = sare(g, 1.0, 0.0)
        assert r["order"] == list(range(n))
        assert r["fill_count"] == 0
        assert r["width"] == 0


def test_complete_graph_optimal_width():
    # clique K_n: any order, fill 0, width n-1 (optimal since tw = n-1)
    for n in (2, 4, 7):
        g = Graph(n)
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        r = sare(g, 1.0, 0.0)
        assert r["fill_count"] == 0
        assert r["width"] == n - 1


def test_star():
    # star K_{1,k}: center last -> width 1, zero fill; center first -> fill C(k,2)
    g = Graph(6)
    for v in range(1, 6):
        g.add_edge(0, v)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] == 0
    assert r["width"] <= 1


# ---------------------------------------------------------------------------
# cross-language differential: Rust CLI vs Python reference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("algo", ["sare", "sare-a0", "sare-a2", "min-degree", "min-fill"])
def test_rust_matches_python(algo):
    rng = random.Random(42)
    for trial in range(8):
        n = rng.randrange(2, 15)
        m = rng.randrange(1, min(n * (n - 1) // 2, 25) + 1)
        g = rand_graph(n, m, seed=1000 + trial)
        # Ensure no isolated vertices: a plain edge list cannot encode isolated
        # vertices, so Rust would read a smaller n. Matrix Market headers carry n
        # for real benchmarks (see docs/MATHEMATICAL_FOUNDATIONS / benchmark docs).
        # Both sides see the same modified g.
        for v in range(g.n):
            if g.degree(v) == 0:
                u = 0 if v != 0 else 1
                g.add_edge(u, v)
        if algo == "sare":
            py = sare(g, 1.0, 0.0)
        elif algo == "sare-a0":
            py = sare(g, 0.0, 0.0)
        elif algo == "sare-a2":
            py = sare(g, 2.0, 0.0)
        elif algo == "min-degree":
            py = min_degree(g)
        else:
            py = min_fill(g)
        rust = run_rust_cli(text_of(g), algo)
        assert rust["fill_count"] == py["fill_count"], (algo, g.n, text_of(g))
        assert rust["width"] == py["width"], (algo, g.n, text_of(g))
        assert sorted(rust["order"]) == sorted(py["order"]) == list(range(g.n))


def test_rust_matches_python_with_lookahead():
    rng = random.Random(7)
    for trial in range(4):
        n = rng.randrange(2, 12)
        g = rand_graph(n, n * 2, seed=2000 + trial)
        for v in range(g.n):
            if g.degree(v) == 0:
                u = 0 if v != 0 else 1
                g.add_edge(u, v)
        py = sare(g, 1.0, 1.0)
        rust = run_rust_cli(text_of(g), "sare-lookahead")
        assert rust["fill_count"] == py["fill_count"]
        assert rust["width"] == py["width"]


# ---------------------------------------------------------------------------
# brute-force differential (small graphs): SARE fill >= optimum fill
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 9))
def test_sare_fill_ge_optimum(n):
    g = rand_graph(n, n, seed=500 + n)
    opt = brute_force_optimum(g)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] >= opt["fill_count"], (
        f"SARE fill {r['fill_count']} < optimum {opt['fill_count']} (impossible)")
    assert r["width"] >= opt["width"], (
        f"SARE width {r['width']} < optimum {opt['width']} (impossible)")


@pytest.mark.parametrize("n", range(1, 9))
def test_sare_optimal_on_paths(n):
    g = Graph(n)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    opt = brute_force_optimum(g)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] == opt["fill_count"] == 0
    assert r["width"] == opt["width"]


@pytest.mark.parametrize("n", range(1, 9))
def test_sare_optimal_on_cliques(n):
    g = Graph(n)
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(i, j)
    opt = brute_force_optimum(g)
    r = sare(g, 1.0, 0.0)
    assert r["fill_count"] == opt["fill_count"] == 0
    assert r["width"] == opt["width"]


# ---------------------------------------------------------------------------
# invariants
# ---------------------------------------------------------------------------

def test_eliminated_graph_is_chordal_peo():
    """pi is a perfect elimination ordering of the final filled graph H = G + fill edges."""
    rng = random.Random(99)
    for trial in range(8):
        n = rng.randrange(2, 14)
        g = rand_graph(n, n * 2, seed=trial)
        r = sare(g, 1.0, 0.0)
        order = r["order"]
        pos = {v: i for i, v in enumerate(order)}
        # Build the final filled graph H = original edges + all fill edges.
        g2 = g.copy()
        H = Graph(n)
        for v in range(n):
            for u in g.adj[v]:
                if u > v:
                    H.add_edge(v, u)
        for v in order:
            later_nbrs = [u for u in g2.adj[v] if pos[u] > pos[v]]
            # add fill edges among later neighbors into H
            for i in range(len(later_nbrs)):
                for j in range(i + 1, len(later_nbrs)):
                    H.add_edge(later_nbrs[i], later_nbrs[j])
            g2.eliminate(v)
        # PEO check: for each vertex, its later neighbors in H form a clique in H.
        for v in order:
            later_nbrs = [u for u in H.adj[v] if pos[u] > pos[v]]
            for i in range(len(later_nbrs)):
                for j in range(i + 1, len(later_nbrs)):
                    assert later_nbrs[j] in H.adj[later_nbrs[i]], \
                        "filled graph H not chordal / pi not a PEO"


def test_min_fill_never_worse_fill_than_min_degree_on_trees():
    # On trees, both find zero fill; sanity that both are valid.
    rng = random.Random(3)
    for trial in range(5):
        n = rng.randrange(3, 15)
        g = Graph(n)
        # random tree via attachment
        for v in range(1, n):
            u = rng.randrange(v)
            g.add_edge(u, v)
        rd = min_degree(g)
        rf = min_fill(g)
        rs = sare(g, 1.0, 0.0)
        for r in (rd, rf, rs):
            assert r["fill_count"] == 0, (r, text_of(g))
            assert r["width"] <= 1


# ---------------------------------------------------------------------------
# adversarial / degenerate
# ---------------------------------------------------------------------------

def test_disconnected_graph():
    g = Graph(8)
    g.add_edge(0, 1); g.add_edge(2, 3); g.add_edge(4, 5); g.add_edge(6, 7)
    r = sare(g, 1.0, 0.0)
    assert sorted(r["order"]) == list(range(8))
    assert r["fill_count"] == 0
    assert r["width"] <= 1


def test_isolated_vertices():
    g = Graph(5)
    g.add_edge(0, 1)
    r = sare(g, 1.0, 0.0)
    assert sorted(r["order"]) == list(range(5))
    assert r["fill_count"] == 0


def test_determinism():
    g = rand_graph(12, 30, seed=123)
    r1 = sare(g, 1.0, 0.0)
    r2 = sare(g.copy(), 1.0, 0.0)
    assert r1 == r2


def test_alpha_variants_run():
    g = rand_graph(15, 40, seed=5)
    for a in (0.0, 0.5, 1.0, 2.0, 5.0):
        r = sare(g, a, 0.0)
        assert sorted(r["order"]) == list(range(g.n))
        ev = evaluate_order(g, r["order"])
        assert ev["fill_count"] == r["fill_count"]
