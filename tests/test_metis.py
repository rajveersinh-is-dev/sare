import pytest
from src.python.metis import WeightedGraph, coarsen, initial_partition, refine_kl, metis_bisection, metis_nested_dissection
from src.python.sare_reference import Graph

def test_weighted_graph():
    g = WeightedGraph(4)
    g.add_edge(0, 1, 10.0)
    g.add_edge(1, 2, 1.0)

    assert g.adj[0] == [(1, 10.0)]
    assert g.adj[1] == [(0, 10.0), (2, 1.0)]
    assert g.adj[2] == [(1, 1.0)]

def test_coarsen():
    g = WeightedGraph(4)
    g.add_edge(0, 1, 10.0)
    g.add_edge(1, 2, 1.0)
    g.add_edge(2, 3, 10.0)

    coarse_g, coarse_map = coarsen(g)
    # The two heavy edges (0-1) and (2-3) should be matched.
    assert coarse_g.n <= 3
    assert len(set(coarse_map)) == coarse_g.n

def test_initial_partition():
    g = WeightedGraph(4)
    g.add_edge(0, 1, 10.0)
    g.add_edge(1, 2, 1.0)
    g.add_edge(2, 3, 10.0)

    L, R = initial_partition(g)
    assert len(L) > 0 and len(R) > 0
    assert set(L).union(set(R)) == {0, 1, 2, 3}

def test_metis_bisection():
    g = WeightedGraph(4)
    g.add_edge(0, 1, 10.0)
    g.add_edge(1, 2, 1.0)
    g.add_edge(2, 3, 10.0)

    L, R = metis_bisection(g)
    assert len(L) + len(R) == 4

    l_set = set(L)
    r_set = set(R)
    # Cut should ideally be at 1-2
    assert ({0, 1} == l_set and {2, 3} == r_set) or ({0, 1} == r_set and {2, 3} == l_set)

def test_metis_nested_dissection():
    g = Graph(5)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 4)

    res = metis_nested_dissection(g)
    assert len(res["order"]) == 5
    assert sorted(res["order"]) == [0, 1, 2, 3, 4]
