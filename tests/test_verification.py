import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from sare_reference import Graph
from verification import maximum_cardinality_search, is_peo, is_chordal, build_filled_graph

def test_mcs_and_peo_on_chordal_graph():
    # Tree is a chordal graph
    g = Graph(5)
    g.add_edge(0, 1)
    g.add_edge(0, 2)
    g.add_edge(1, 3)
    g.add_edge(1, 4)

    peo = maximum_cardinality_search(g)
    assert is_peo(g, peo)
    assert is_chordal(g)

def test_mcs_and_peo_on_non_chordal_graph():
    # Cycle of length 4 (C4) is not chordal
    g = Graph(4)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 0)

    peo = maximum_cardinality_search(g)
    assert not is_peo(g, peo)
    assert not is_chordal(g)

def test_is_peo_on_clique():
    g = Graph(4)
    for i in range(4):
        for j in range(i+1, 4):
            g.add_edge(i, j)

    peo = maximum_cardinality_search(g)
    assert is_peo(g, peo)
    assert is_chordal(g)

def test_build_filled_graph():
    g = Graph(4)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 0)

    ordering = [0, 1, 2, 3]
    H, fill_count = build_filled_graph(g, ordering)

    # Eliminating 0 adds edge (1, 3)
    # Eliminating 1 (neighbors 2, 3) adds edge (2, 3), but it's already there
    # Total fill: 1
    assert fill_count == 1

    # H should be chordal now
    assert is_chordal(H)
