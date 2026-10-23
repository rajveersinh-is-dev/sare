import sys
import itertools
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from sare_reference import Graph, sare, min_degree, brute_force_optimum
from verification import is_chordal, build_filled_graph

def generate_all_labeled_graphs(n: int):
    """Generates all 2^(n*(n-1)/2) labeled graphs on n vertices."""
    edges = list(itertools.combinations(range(n), 2))
    for subset_len in range(len(edges) + 1):
        for subset in itertools.combinations(edges, subset_len):
            g = Graph(n)
            for u, v in subset:
                g.add_edge(u, v)
            yield g

@pytest.mark.parametrize("n", range(1, 6))
def test_exhaustive_small_instances(n):
    for g in generate_all_labeled_graphs(n):
        optimum = brute_force_optimum(g)

        for algo in [lambda graph: sare(graph, 1.0, 0.0), min_degree]:
            result = algo(g)

            # 1. Fill count and width must be bounded below by optimum
            assert result["fill_count"] >= optimum["fill_count"]
            assert result["width"] >= optimum["width"]

            # 2. Correctness of ordering and exactness of fill count
            ordering = result["order"]
            reported_fill = result["fill_count"]

            H, actual_fill = build_filled_graph(g, ordering)
            assert reported_fill == actual_fill
            assert is_chordal(H)
