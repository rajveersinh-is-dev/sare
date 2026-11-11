use crate::Graph;

/// An independent verification oracle for checking exact fill edges using the Fill Path Theorem.
/// The Fill Path Theorem states that an edge (u, v) exists in the filled graph H
/// if and only if there exists a path between u and v in the original graph G
/// such that all intermediate vertices on the path are eliminated before both u and v.
pub fn get_fill_edges_via_paths(graph: &Graph, ordering: &[usize]) -> Vec<(usize, usize)> {
    let n = graph.n;
    if n == 0 {
        return Vec::new();
    }

    // pos[v] = index of v in the ordering.
    // If v is eliminated earlier, pos[v] is smaller.
    let mut pos = vec![0; n];
    for (i, &v) in ordering.iter().enumerate() {
        pos[v] = i;
    }

    // We can use a Floyd-Warshall style DP or BFS/DFS.
    // Since we need an independent verification, let's use a BFS for each pair,
    // or just run BFS from each vertex `u` exploring only paths through vertices `w`
    // where pos[w] < min(pos[u], pos[v]).
    //
    // Actually, a simpler way is: for each node `u`, run BFS/DFS traversing only
    // vertices `w` with pos[w] < pos[u]. The boundary of this search is the set of
    // reachable vertices `v` with pos[v] > pos[u].
    // Those `v` will have an edge `(u, v)` in the filled graph.

    let mut fill_edges = Vec::new();

    for (i, &u) in ordering.iter().enumerate() {
        // Find all reachable v with pos[v] > pos[u] using only intermediate w with pos[w] < pos[u]
        let mut visited = vec![false; n];
        let mut queue = vec![u];
        visited[u] = true;

        let mut q_idx = 0;
        while q_idx < queue.len() {
            let curr = queue[q_idx];
            q_idx += 1;

            for &nbr in &graph.adj[curr] {
                if !visited[nbr] {
                    visited[nbr] = true;
                    if pos[nbr] < pos[u] {
                        queue.push(nbr);
                    }
                }
            }
        }

        // Any vertex v with pos[v] > pos[u] that was visited (except for u itself)
        // is connected to u in the filled graph.
        for v in 0..n {
            if v != u && visited[v] && pos[v] > pos[u] {
                // To be a *fill* edge, it must not be in the original graph
                if !graph.adj[u].contains(&v) {
                    let min_v = u.min(v);
                    let max_v = u.max(v);
                    fill_edges.push((min_v, max_v));
                }
            }
        }
    }

    fill_edges.sort_unstable();
    fill_edges.dedup();
    fill_edges
}

/// Computes the filled graph strictly via the Fill Path Theorem oracle.
pub fn build_filled_graph_via_paths(graph: &Graph, ordering: &[usize]) -> (Graph, usize) {
    let mut h = Graph::new(graph.n);
    for v in 0..graph.n {
        for &u in &graph.adj[v] {
            h.add_edge(u, v);
        }
    }

    let fill_edges = get_fill_edges_via_paths(graph, ordering);
    for &(u, v) in &fill_edges {
        h.add_edge(u, v);
    }

    (h, fill_edges.len())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verification::build_filled_graph;

    #[test]
    fn test_fill_path_oracle_path_graph() {
        let mut g = Graph::new(4);
        g.add_edge(0, 1);
        g.add_edge(1, 2);
        g.add_edge(2, 3);

        // order: 1, 2, 0, 3
        let order = vec![1, 2, 0, 3];
        let (h_oracle, fill_oracle) = build_filled_graph_via_paths(&g, &order);
        let (h_sim, fill_sim) = build_filled_graph(&g, &order);

        assert_eq!(fill_oracle, fill_sim);
        for i in 0..g.n {
            assert_eq!(h_oracle.adj[i], h_sim.adj[i]);
        }
    }
}
