//! Verification Oracles for elimination orderings and chordal graphs.
//!
//! Contains Maximum Cardinality Search (MCS) algorithm to recognize chordal graphs
//! and verify Perfect Elimination Orderings (PEO).

use crate::Graph;
use std::collections::HashSet;

/// Maximum Cardinality Search (MCS) to find a simplicial elimination ordering.
/// Returns a valid perfect elimination ordering if the graph is chordal.
///
/// Runs in O(V + E) time.
pub fn mcs(graph: &Graph) -> Vec<usize> {
    let n = graph.n;
    if n == 0 {
        return vec![];
    }

    // weights[v] is the number of already-numbered neighbors of v
    let mut weights = vec![0; n];
    let mut unnumbered = vec![true; n];
    let mut order = vec![0; n];

    // sets[w] contains all unnumbered vertices with weight w
    let mut sets = vec![HashSet::new(); n];
    for v in 0..n {
        sets[0].insert(v);
    }

    let mut max_weight = 0;

    for i in (0..n).rev() {
        // Find an unnumbered vertex with maximum weight
        while max_weight > 0 && sets[max_weight].is_empty() {
            max_weight -= 1;
        }

        let v = *sets[max_weight].iter().next().unwrap();
        sets[max_weight].remove(&v);

        order[i] = v;
        unnumbered[v] = false;

        // Update weights of unnumbered neighbors
        for &u in &graph.adj[v] {
            if unnumbered[u] {
                let w = weights[u];
                sets[w].remove(&u);
                weights[u] += 1;
                let new_w = weights[u];
                sets[new_w].insert(u);
                if new_w > max_weight {
                    max_weight = new_w;
                }
            }
        }
    }

    order
}

/// Verifies if a given ordering is a Perfect Elimination Ordering (PEO) for the graph.
/// An ordering is a PEO if, for every v, the later neighbors of v form a clique.
pub fn is_perfect_elimination_ordering(graph: &Graph, order: &[usize]) -> bool {
    let n = graph.n;
    if order.len() != n {
        return false;
    }

    let mut pos = vec![0; n];
    for (i, &v) in order.iter().enumerate() {
        pos[v] = i;
    }

    for &v in order {
        let mut later_nbrs = Vec::new();
        for &u in &graph.adj[v] {
            if pos[u] > pos[v] {
                later_nbrs.push(u);
            }
        }

        for i in 0..later_nbrs.len() {
            for j in (i + 1)..later_nbrs.len() {
                let a = later_nbrs[i];
                let b = later_nbrs[j];
                if !graph.adj[a].contains(&b) {
                    return false;
                }
            }
        }
    }

    true
}

/// Checks if a graph is chordal using MCS.
/// A graph is chordal if and only if the ordering produced by MCS is a PEO.
pub fn is_chordal(graph: &Graph) -> bool {
    let order = mcs(graph);
    is_perfect_elimination_ordering(graph, &order)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn path(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..n.saturating_sub(1) {
            g.add_edge(i, i + 1);
        }
        g
    }

    fn cycle(n: usize) -> Graph {
        let mut g = path(n);
        if n >= 3 {
            g.add_edge(0, n - 1);
        }
        g
    }

    fn clique(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..n {
            for j in (i + 1)..n {
                g.add_edge(i, j);
            }
        }
        g
    }

    #[test]
    fn test_is_chordal_path() {
        let g = path(5);
        assert!(is_chordal(&g));
    }

    #[test]
    fn test_is_chordal_cycle() {
        let g = cycle(4); // C4 is not chordal
        assert!(!is_chordal(&g));
        let g = cycle(5); // C5 is not chordal
        assert!(!is_chordal(&g));
        let g = cycle(3); // C3 is a clique, which is chordal
        assert!(is_chordal(&g));
    }

    #[test]
    fn test_is_chordal_clique() {
        let g = clique(5);
        assert!(is_chordal(&g));
    }
}
