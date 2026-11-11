import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from sare_reference import Graph, sare
from fill_path import build_filled_graph_via_paths, get_fill_edges_via_paths
from verification import build_filled_graph

def test_fill_path_theorem_path_graph():
    g = Graph(4)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)

    ordering = [1, 2, 0, 3]

    H_sim, fill_sim = build_filled_graph(g, ordering)
    H_oracle, fill_oracle = build_filled_graph_via_paths(g, ordering)

    assert fill_sim == fill_oracle
    for i in range(g.n):
        assert set(H_sim.adj[i]) == set(H_oracle.adj[i])

def test_fill_path_theorem_star_graph():
    g = Graph(5)
    for i in range(1, 5):
        g.add_edge(0, i)

    ordering = [1, 2, 3, 4, 0]

    H_sim, fill_sim = build_filled_graph(g, ordering)
    H_oracle, fill_oracle = build_filled_graph_via_paths(g, ordering)

    assert fill_sim == fill_oracle
    for i in range(g.n):
        assert set(H_sim.adj[i]) == set(H_oracle.adj[i])

def test_fill_path_theorem_with_sare():
    g = Graph(6)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 4)
    g.add_edge(4, 5)
    g.add_edge(5, 0)
    g.add_edge(1, 4)

    ordering = sare(g, 1.0, 0.0)["order"]

    H_sim, fill_sim = build_filled_graph(g, ordering)
    H_oracle, fill_oracle = build_filled_graph_via_paths(g, ordering)

    assert fill_sim == fill_oracle
    for i in range(g.n):
        assert set(H_sim.adj[i]) == set(H_oracle.adj[i])
