//! SARE - Safe-Reduction + Adaptive elimination ordering for sparse fill-in reduction.
//!
//! Provides:
//!   * `sare`: adaptive elimination ordering (safe reductions + degree/fill/lookahead)
//!   * `min_degree`, `min_fill`: classical greedy baselines
//!   * `brute_force_optimum`: exact optimum fill/width for small graphs (verification)
//!   * `Graph`: mutable adjacency supporting fill-edge insertion during elimination

use std::collections::HashSet;

/// A mutable simple undirected graph supporting fill-edge insertion during elimination.
#[derive(Clone, Debug)]
pub struct Graph {
    pub n: usize,
    /// live adjacency; eliminated vertices have an empty set and are removed from neighbors
    pub adj: Vec<HashSet<usize>>,
    pub eliminated: Vec<bool>,
}

impl Graph {
    pub fn new(n: usize) -> Self {
        Graph {
            n,
            adj: vec![HashSet::new(); n],
            eliminated: vec![false; n],
        }
    }

    pub fn add_edge(&mut self, u: usize, v: usize) {
        if u == v {
            return;
        }
        self.adj[u].insert(v);
        self.adj[v].insert(u);
    }

    /// Number of live neighbors of v (not yet eliminated).
    pub fn degree(&self, v: usize) -> usize {
        self.adj[v].len()
    }

    /// True if v is still live.
    pub fn is_live(&self, v: usize) -> bool {
        !self.eliminated[v]
    }

    /// Fill edges that eliminating v would create right now:
    /// C(d,2) - (edges induced by N(v)).
    pub fn fill(&self, v: usize) -> usize {
        let nbrs: Vec<usize> = self.adj[v].iter().copied().collect();
        let d = nbrs.len();
        if d < 2 {
            return 0;
        }
        let mut induced = 0usize;
        for i in 0..d {
            for j in (i + 1)..d {
                if self.adj[nbrs[i]].contains(&nbrs[j]) {
                    induced += 1;
                }
            }
        }
        d * (d - 1) / 2 - induced
    }

    /// Eliminate v: make N(v) a clique (adding fill edges), then remove v.
    /// Returns the number of fill edges added.
    pub fn eliminate(&mut self, v: usize) -> usize {
        assert!(!self.eliminated[v]);
        let nbrs: Vec<usize> = self.adj[v].iter().copied().collect();
        let mut fill_added = 0usize;
        // make neighborhood a clique
        for i in 0..nbrs.len() {
            for j in (i + 1)..nbrs.len() {
                let a = nbrs[i];
                let b = nbrs[j];
                if !self.adj[a].contains(&b) {
                    self.adj[a].insert(b);
                    self.adj[b].insert(a);
                    fill_added += 1;
                }
            }
        }
        // remove v from neighbors' adjacency
        for u in &nbrs {
            self.adj[*u].remove(&v);
        }
        self.adj[v].clear();
        self.eliminated[v] = true;
        fill_added
    }

    pub fn live_vertices(&self) -> Vec<usize> {
        (0..self.n).filter(|&v| !self.eliminated[v]).collect()
    }
}

/// Result of running an elimination ordering algorithm.
#[derive(Clone, Debug, serde::Serialize)]
pub struct OrderingResult {
    pub order: Vec<usize>,
    pub fill_count: usize,
    pub width: usize,
    pub fill_edges_added: usize,
}

/// Compute the fill count and width of a given elimination order by simulating
/// elimination on a fresh copy of the graph.
pub mod verification;
pub mod exact_dp;

pub fn evaluate_order(graph: &Graph, order: &[usize]) -> OrderingResult {
    let mut g = graph.clone();
    let mut fill_count = 0usize;
    let mut width = 0usize;
    let mut fill_edges_added = 0usize;
    for &v in order {
        assert!(!g.eliminated[v], "ordering eliminates vertex {:?} twice", v);
        let d = g.degree(v);
        width = width.max(d);
        fill_edges_added += g.eliminate(v);
        fill_count = fill_edges_added;
    }
    // every vertex must be eliminated exactly once
    assert_eq!(order.len(), g.n, "ordering length {} != n {}", order.len(), g.n);
    OrderingResult {
        order: order.to_vec(),
        fill_count,
        width,
        fill_edges_added,
    }
}

/// Minimum Degree greedy: repeatedly eliminate a live vertex of minimum degree.
pub fn min_degree(graph: &Graph) -> OrderingResult {
    let mut g = graph.clone();
    let mut order = Vec::with_capacity(g.n);
    let mut fill_count = 0usize;
    let mut width = 0usize;
    for _ in 0..g.n {
        let v = g
            .live_vertices()
            .iter()
            .copied()
            .min_by_key(|v| g.degree(*v))
            .expect("graph not empty");
        width = width.max(g.degree(v));
        fill_count += g.eliminate(v);
        order.push(v);
    }
    OrderingResult {
        order,
        fill_count,
        width,
        fill_edges_added: fill_count,
    }
}

/// Minimum Fill-in greedy: repeatedly eliminate a live vertex creating fewest fill edges
/// (ties broken by lower degree, then lower id).
pub fn min_fill(graph: &Graph) -> OrderingResult {
    let mut g = graph.clone();
    let mut order = Vec::with_capacity(g.n);
    let mut fill_count = 0usize;
    let mut width = 0usize;
    for _ in 0..g.n {
        let v = g
            .live_vertices()
            .iter()
            .copied()
            .min_by_key(|v| {
                let fill = g.fill(*v);
                let deg = g.degree(*v);
                (fill, deg, *v)
            })
            .expect("graph not empty");
        width = width.max(g.degree(v));
        fill_count += g.eliminate(v);
        order.push(v);
    }
    OrderingResult {
        order,
        fill_count,
        width,
        fill_edges_added: fill_count,
    }
}

/// SARE: Safe-Reduction + Adaptive elimination ordering.
///
/// Phase A: eliminate degree-0/1 vertices (zero fill, provably safe).
/// Phase B: repeatedly eliminate the live vertex minimizing
///   score(v) = degree(v) + alpha * fill(v) + beta * look(v)
/// lookahead is disabled when beta == 0 (default).
pub fn sare(graph: &Graph, alpha: f64, beta: f64) -> OrderingResult {
    let mut g = graph.clone();
    let mut order = Vec::with_capacity(g.n);
    let mut fill_count = 0usize;
    let mut width = 0usize;

    // ---------- Phase A: safe reductions ----------
    let mut queue: Vec<usize> = g
        .live_vertices()
        .iter()
        .copied()
        .filter(|v| g.degree(*v) <= 1)
        .collect();
    let mut qhead = 0;
    while qhead < queue.len() {
        let v = queue[qhead];
        qhead += 1;
        if g.eliminated[v] {
            continue;
        }
        if g.degree(v) > 1 {
            continue; // degree changed since enqueued
        }
        width = width.max(g.degree(v));
        fill_count += g.eliminate(v); // zero fill by construction
        order.push(v);
        for u in graph.adj[v].iter() {
            if !g.eliminated[*u] && g.degree(*u) == 1 {
                queue.push(*u);
            }
        }
    }

    // ---------- Phase B: adaptive greedy ----------
    for _ in 0..g.n {
        if g.live_vertices().is_empty() {
            break;
        }
        let v = g
            .live_vertices()
            .iter()
            .copied()
            .min_by_key(|v| {
                let score = (g.degree(*v) as f64)
                    + alpha * (g.fill(*v) as f64)
                    + beta * look_ahead(&g, *v);
                // total order for determinism: (score, id)
                (score * 1e9) as i64
            })
            .expect("graph not empty");
        width = width.max(g.degree(v));
        fill_count += g.eliminate(v);
        order.push(v);
    }

    OrderingResult {
        order,
        fill_count,
        width,
        fill_edges_added: fill_count,
    }
}

/// 1-step lookahead estimate (look-A): sum of neighbor degrees after eliminating v.
fn look_ahead(g: &Graph, v: usize) -> f64 {
    let nbrs: Vec<usize> = g.adj[v].iter().copied().collect();
    // degrees after eliminating v: each neighbor loses v as a neighbor
    let mut sum: f64 = 0.0;
    for u in &nbrs {
        let d = if g.degree(*u) > 0 { g.degree(*u) - 1 } else { 0 };
        sum += d as f64;
    }
    sum
}

/// Exact optimum (minimum fill, then minimum width) by exhaustive search over all
/// permutations. Only feasible for n <= ~10. Used for verification.
pub fn brute_force_optimum(graph: &Graph) -> OrderingResult {
    let n = graph.n;
    assert!(n <= 11, "brute force feasible only for n <= 11, got {}", n);
    let mut best_fill = usize::MAX;
    let mut best_width = usize::MAX;
    let mut best_order: Vec<usize> = vec![];

    // Simple but exponential: clone graph at each recursion level.
    fn rec(
        g: &Graph,
        remaining: &[usize],
        current_fill: usize,
        current_width: usize,
        best_fill: &mut usize,
        best_width: &mut usize,
        best_order: &mut Vec<usize>,
        prefix: &mut Vec<usize>,
    ) {
        if remaining.is_empty() {
            if current_fill < *best_fill
                || (current_fill == *best_fill && current_width < *best_width)
            {
                *best_fill = current_fill;
                *best_width = current_width;
                *best_order = prefix.clone();
            }
            return;
        }
        if current_fill > *best_fill {
            return;
        }
        for i in 0..remaining.len() {
            let v = remaining[i];
            let mut g2 = g.clone();
            let d = g2.degree(v);
            let new_width = current_width.max(d);
            let added = g2.eliminate(v);
            let new_fill = current_fill + added;
            let mut next_remaining = remaining.to_vec();
            next_remaining.remove(i);
            prefix.push(v);
            rec(&g2, &next_remaining, new_fill, new_width, best_fill, best_width,
                best_order, prefix);
            prefix.pop();
        }
    }

    let g0 = graph.clone();
    let rem: Vec<usize> = (0..n).collect();
    let mut prefix: Vec<usize> = Vec::new();
    rec(&g0, &rem, 0, 0, &mut best_fill, &mut best_width, &mut best_order, &mut prefix);

    OrderingResult {
        order: best_order,
        fill_count: best_fill,
        width: best_width,
        fill_edges_added: best_fill,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn clique(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..n {
            for j in (i + 1)..n {
                g.add_edge(i, j);
            }
        }
        g
    }

    fn path(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..n.saturating_sub(1) {
            g.add_edge(i, i + 1);
        }
        g
    }

    fn make_empty_graph(n: usize) -> Graph {
        Graph::new(n)
    }

    #[test]
    fn order_is_permutation() {
        for n in 0..12usize {
            let g = path(n);
            let r = sare(&g, 1.0, 0.0);
            let mut ord = r.order.clone();
            ord.sort();
            assert_eq!(ord, (0..n).collect::<Vec<_>>());
        }
    }

    #[test]
    fn fill_width_match_evaluate() {
        let g = path(8);
        let r = sare(&g, 1.0, 0.0);
        let ev = evaluate_order(&g, &r.order);
        assert_eq!(ev.fill_count, r.fill_count);
        assert_eq!(ev.width, r.width);
    }

    #[test]
    fn clique_zero_fill() {
        let g = clique(5);
        let r = sare(&g, 1.0, 0.0);
        assert_eq!(r.fill_count, 0);
        assert_eq!(r.width, 4);
    }

    #[test]
    fn path_width_one() {
        // A path has treewidth 1; eliminating leaves first yields width 1.
        let g = path(10);
        let r = sare(&g, 1.0, 0.0);
        assert_eq!(r.fill_count, 0);
        assert!(r.width <= 1);
    }

    #[test]
    fn empty_graph() {
        let g = make_empty_graph(0);
        let r = sare(&g, 1.0, 0.0);
        assert!(r.order.is_empty());
        assert_eq!(r.fill_count, 0);
        assert_eq!(r.width, 0);
        let g = make_empty_graph(1);
        let r = sare(&g, 1.0, 0.0);
        assert_eq!(r.order, vec![0]);
        assert_eq!(r.fill_count, 0);
        assert_eq!(r.width, 0);
    }

    #[test]
    fn min_degree_valid() {
        let g = path(7);
        let r = min_degree(&g);
        let ev = evaluate_order(&g, &r.order);
        assert_eq!(ev.fill_count, r.fill_count);
    }

    #[test]
    fn min_fill_valid() {
        let g = path(7);
        let r = min_fill(&g);
        let ev = evaluate_order(&g, &r.order);
        assert_eq!(ev.fill_count, r.fill_count);
    }

    #[test]
    fn sare_beats_or_equals_min_degree_on_path() {
        // On a path, both should find zero fill; just check validity.
        let g = path(9);
        let rs = sare(&g, 1.0, 0.0);
        let rd = min_degree(&g);
        assert_eq!(rs.fill_count, 0);
        assert_eq!(rd.fill_count, 0);
    }

    #[test]
    fn brute_force_matches_sare_on_path_small() {
        for n in 1..=8usize {
            let g = path(n);
            let opt = brute_force_optimum(&g);
            let rs = sare(&g, 1.0, 0.0);
            // SARE on a path should find the optimum (zero fill, width 1)
            assert_eq!(rs.fill_count, opt.fill_count, "path n={}", n);
            assert_eq!(rs.width, opt.width, "path n={}", n);
        }
    }

    #[test]
    fn beta_lookahead_runs() {
        let g = path(8);
        let _ = sare(&g, 1.0, 0.5);
        let _ = sare(&g, 0.0, 0.0); // pure min degree via safe reductions + degree
    }
}
