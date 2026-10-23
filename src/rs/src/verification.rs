use crate::Graph;
use std::collections::HashSet;

/// Computes a perfect elimination ordering using Maximum Cardinality Search (MCS).
/// If the graph is chordal, the reverse of this ordering is a PEO.
pub fn maximum_cardinality_search(graph: &Graph) -> Vec<usize> {
    let n = graph.n;
    let mut weights = vec![0; n];
    let mut ordering = Vec::with_capacity(n);
    let mut unvisited: HashSet<usize> = (0..n).collect();

    for _ in 0..n {
        let mut max_v = 0;
        let mut max_w = -1;

        for &v in &unvisited {
            if weights[v] > max_w {
                max_w = weights[v];
                max_v = v;
            }
        }

        ordering.push(max_v);
        unvisited.remove(&max_v);

        for &u in &graph.adj[max_v] {
            if unvisited.contains(&u) {
                weights[u] += 1;
            }
        }
    }

    ordering.reverse();
    ordering
}

/// Checks if the given ordering is a Perfect Elimination Ordering (PEO) for the graph.
pub fn is_peo(graph: &Graph, ordering: &[usize]) -> bool {
    let n = graph.n;
    if ordering.len() != n {
        return false;
    }

    let mut pos = vec![0; n];
    for (i, &v) in ordering.iter().enumerate() {
        pos[v] = i;
    }

    for (i, &v) in ordering.iter().enumerate() {
        let mut later_neighbors = Vec::new();
        for &u in &graph.adj[v] {
            if pos[u] > i {
                later_neighbors.push(u);
            }
        }

        if later_neighbors.is_empty() {
            continue;
        }

        // Find the later neighbor that comes earliest in the ordering
        let mut first_ln = later_neighbors[0];
        let mut min_pos = pos[first_ln];
        for &u in later_neighbors.iter().skip(1) {
            if pos[u] < min_pos {
                min_pos = pos[u];
                first_ln = u;
            }
        }

        for &w in &later_neighbors {
            if w != first_ln && !graph.adj[first_ln].contains(&w) {
                return false;
            }
        }
    }

    true
}

/// Simulates the elimination process and returns the filled graph H and the number of fill edges added.
pub fn build_filled_graph(graph: &Graph, ordering: &[usize]) -> (Graph, usize) {
    let mut g = graph.clone();
    let n = graph.n;

    let mut h = Graph::new(n);
    for v in 0..n {
        for &u in &g.adj[v] {
            h.add_edge(u, v);
        }
    }

    let mut fill_count = 0;
    let mut pos = vec![0; n];
    for (i, &v) in ordering.iter().enumerate() {
        pos[v] = i;
    }

    for &v in ordering {
        let mut later_neighbors = Vec::new();
        for &u in &g.adj[v] {
            if pos[u] > pos[v] {
                later_neighbors.push(u);
            }
        }

        for i in 0..later_neighbors.len() {
            for j in (i + 1)..later_neighbors.len() {
                let a = later_neighbors[i];
                let b = later_neighbors[j];
                if !g.adj[a].contains(&b) {
                    g.add_edge(a, b);
                    h.add_edge(a, b);
                    fill_count += 1;
                }
            }
        }

        g.eliminate(v);
    }

    (h, fill_count)
}

/// Checks if a graph is chordal using MCS.
pub fn is_chordal(graph: &Graph) -> bool {
    let peo = maximum_cardinality_search(graph);
    is_peo(graph, &peo)
}
