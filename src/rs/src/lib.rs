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
        let mut induced = 0usize;
        for i in 0..d {
            for j in (i + 1)..d {
                if self.adj[nbrs[i]].contains(&nbrs[j]) {
                    induced += 1;
                }
            }
        }
        if d < 2 {
            0
        } else {
            d * (d - 1) / 2 - induced
        }
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

pub mod verification;

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

/// Exact optimum (minimum fill, then minimum width) by dynamic programming over subsets.
/// Feasible for n <= ~20. Used for verification.
pub fn exact_optimum(graph: &Graph) -> OrderingResult {
    let n = graph.n;
    if n == 0 {
        return OrderingResult { order: vec![], fill_count: 0, width: 0, fill_edges_added: 0 };
    }
    // We allow DP for up to n=20; beyond that we should assert!
    assert!(n <= 20, "DP exact optimum feasible only for n <= 20, got {}", n);

    let mut dp_fill = vec![usize::MAX; 1 << n];
    let mut dp_tw = vec![usize::MAX; 1 << n];
    let mut parent_fill = vec![usize::MAX; 1 << n];

    dp_fill[0] = 0;
    dp_tw[0] = 0;

    let mut adj_mask = vec![0usize; n];
    for i in 0..n {
        for &u in &graph.adj[i] {
            adj_mask[i] |= 1 << u;
        }
    }

    for mask in 1..(1 << n) {
        let mut best_fill = usize::MAX;
        let mut best_tw = usize::MAX;
        let mut best_p = usize::MAX;

        for v in 0..n {
            if (mask & (1 << v)) != 0 {
                let s = mask & !(1 << v);
                if dp_fill[s] == usize::MAX {
                    continue;
                }

                // connected components of s
                let mut unvisited = s;
                let mut comps_adj = Vec::with_capacity(n); // Can optimize slightly
                while unvisited != 0 {
                    let start = unvisited.trailing_zeros() as usize;
                    let mut comp = 1 << start;
                    let mut queue = vec![start];
                    unvisited &= !(1 << start);
                    while let Some(node) = queue.pop() {
                        let mut unvisited_nbrs = adj_mask[node] & unvisited;
                        while unvisited_nbrs != 0 {
                            let nbr = unvisited_nbrs.trailing_zeros() as usize;
                            comp |= 1 << nbr;
                            unvisited &= !(1 << nbr);
                            unvisited_nbrs &= !(1 << nbr);
                            queue.push(nbr);
                        }
                    }
                    let mut comp_adj = 0usize;
                    let mut temp: usize = comp;
                    while temp != 0 {
                        let node = temp.trailing_zeros() as usize;
                        comp_adj |= adj_mask[node];
                        temp &= !(1 << node);
                    }
                    comps_adj.push(comp_adj);
                }

                let mut u_mask = adj_mask[v] & !s;
                for comp_adj in &comps_adj {
                    if (comp_adj & (1 << v)) != 0 {
                        u_mask |= comp_adj & !s;
                    }
                }
                u_mask &= !(1 << v);

                let mut fill = 0;
                let mut degree = 0;
                let mut u_iter = u_mask;
                while u_iter != 0 {
                    degree += 1;
                    let x = u_iter.trailing_zeros() as usize;
                    u_iter &= !(1 << x);
                    let mut y_iter = u_iter;
                    while y_iter != 0 {
                        let y = y_iter.trailing_zeros() as usize;
                        y_iter &= !(1 << y);

                        let mut adj_in_gs = (adj_mask[x] & (1 << y)) != 0;
                        if !adj_in_gs {
                            for comp_adj in &comps_adj {
                                if (comp_adj & (1 << x)) != 0 && (comp_adj & (1 << y)) != 0 {
                                    adj_in_gs = true;
                                    break;
                                }
                            }
                        }
                        if !adj_in_gs {
                            fill += 1;
                        }
                    }
                }

                let new_fill = dp_fill[s] + fill;
                let new_tw = dp_tw[s].max(degree);

                // Compare by min fill, then min tw
                if new_fill < best_fill || (new_fill == best_fill && new_tw < best_tw) {
                    best_fill = new_fill;
                    best_tw = new_tw;
                    best_p = v;
                }
            }
        }
        dp_fill[mask] = best_fill;
        dp_tw[mask] = best_tw;
        parent_fill[mask] = best_p;
    }

    let mut fill_order = Vec::with_capacity(n);
    let mut curr = (1 << n) - 1;
    while curr > 0 {
        let v = parent_fill[curr];
        fill_order.push(v);
        curr &= !(1 << v);
    }
    fill_order.reverse();

    OrderingResult {
        order: fill_order,
        fill_count: dp_fill[(1 << n) - 1],
        width: dp_tw[(1 << n) - 1],
        fill_edges_added: dp_fill[(1 << n) - 1],
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
    fn exact_optimum_matches_sare_on_path_small() {
        for n in 1..=14usize {
            let g = path(n);
            let opt = exact_optimum(&g);
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
