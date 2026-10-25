import itertools
from typing import List, Tuple, Dict, Set

def refine_colors(adj_list: List[List[int]], initial_colors: List[int]) -> List[int]:
    n = len(adj_list)
    colors = initial_colors
    while True:
        new_colors_info = []
        for i in range(n):
            neighbor_colors = sorted([colors[j] for j in adj_list[i]])
            new_colors_info.append((colors[i], tuple(neighbor_colors)))
        unique = sorted(list(set(new_colors_info)))
        color_map = {val: idx for idx, val in enumerate(unique)}
        new_colors = [color_map[info] for info in new_colors_info]
        if len(set(new_colors)) == len(set(colors)):
            break
        colors = new_colors
    return colors

def get_canonical_permutations(adj_list: List[List[int]], current_colors: List[int]) -> List[List[int]]:
    n = len(adj_list)
    if len(set(current_colors)) == n:
        perm = [x for _, x in sorted(zip(current_colors, range(n)))]
        return [perm]
    color_counts: Dict[int, int] = {}
    for c in current_colors:
        color_counts[c] = color_counts.get(c, 0) + 1
    target_color = next(c for c, count in color_counts.items() if count > 1)
    vertices_in_class = [v for v in range(n) if current_colors[v] == target_color]
    all_perms = []
    max_c = max(current_colors)
    for v in vertices_in_class:
        new_colors = list(current_colors)
        new_colors[v] = max_c + 1
        refined_colors = refine_colors(adj_list, new_colors)
        all_perms.extend(get_canonical_permutations(adj_list, refined_colors))
    return all_perms

def get_canonical_form(n: int, edges: List[Tuple[int, int]]) -> Tuple[Tuple[int, ...], ...]:
    adj_list: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        adj_list[u].append(v)
        adj_list[v].append(u)
    initial_colors = refine_colors(adj_list, [0]*n)
    perms = get_canonical_permutations(adj_list, initial_colors)
    best_adj_matrix = None
    for p in perms:
        # p[i] is the original vertex index that maps to new index i
        matrix = tuple(
            tuple(1 if p[j] in adj_list[p[i]] else 0 for j in range(n))
            for i in range(n)
        )
        if best_adj_matrix is None or matrix > best_adj_matrix:
            best_adj_matrix = matrix
    return best_adj_matrix

def generate_non_isomorphic_graphs(n: int) -> List[List[Tuple[int, int]]]:
    """Generates all non-isomorphic graphs of size n."""
    if n == 0:
        return [[]]
    edges = list(itertools.combinations(range(n), 2))
    unique_forms: Set[Tuple[Tuple[int, ...], ...]] = set()
    unique_graphs: List[List[Tuple[int, int]]] = []

    for subset_len in range(len(edges) + 1):
        for subset in itertools.combinations(edges, subset_len):
            form = get_canonical_form(n, list(subset))
            if form not in unique_forms:
                unique_forms.add(form)

                # Reconstruct edges from canonical matrix
                canonical_edges = []
                for i in range(n):
                    for j in range(i + 1, n):
                        if form[i][j] == 1:
                            canonical_edges.append((i, j))
                unique_graphs.append(canonical_edges)

    return unique_graphs
