import sys
from pathlib import Path
import pytest
from collections import defaultdict
import random

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from sare_reference import Graph, sare, min_degree, fast_min_degree, exact_optimum
from verification import is_chordal, build_filled_graph
from isomorphism import generate_non_isomorphic_graphs

@pytest.mark.parametrize("n", range(1, 7))
def test_exhaustive_non_isomorphic_graphs(n):
    graphs_edges = generate_non_isomorphic_graphs(n)
    for edges in graphs_edges:
        g = Graph(n)
        for u, v in edges:
            g.add_edge(u, v)

        optimum = exact_optimum(g)

        for algo in [lambda graph: sare(graph, 1.0, 0.0), min_degree, fast_min_degree]:
            result = algo(g)

            assert result["fill_count"] >= optimum["fill_count"]
            assert result["width"] >= optimum["width"]

            ordering = result["order"]
            reported_fill = result["fill_count"]

            H, actual_fill = build_filled_graph(g, ordering)
            assert reported_fill == actual_fill
            assert is_chordal(H)
