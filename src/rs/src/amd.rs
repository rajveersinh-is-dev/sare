use std::collections::HashSet;
use crate::{Graph, OrderingResult};

/// Quotient Graph representation for fast elimination algorithms like
/// Approximate Minimum Degree (AMD) or Exact Quotient Minimum Degree (QMD).
#[derive(Clone, Debug)]
pub struct QuotientGraph {
    pub n: usize,
    pub is_eliminated: Vec<bool>,
    /// For a live node: its directly connected live neighbors.
    pub live_neighbors: Vec<HashSet<usize>>,
    /// For a live node: the set of adjacent Enodes (elements).
    pub elements: Vec<HashSet<usize>>,
    /// For an Enode (element): the set of live nodes in its clique.
    pub members: Vec<HashSet<usize>>,
    /// Degree upper bound (or exact degree) for each live node.
    pub degree_bound: Vec<usize>,
}

impl QuotientGraph {
    pub fn new(g: &Graph) -> Self {
        let n = g.n;
        let mut live_neighbors = vec![HashSet::new(); n];
        let mut degree_bound = vec![0; n];

        for u in 0..n {
            live_neighbors[u] = g.adj[u].clone();
            degree_bound[u] = g.adj[u].len();
        }

        QuotientGraph {
            n,
            is_eliminated: vec![false; n],
            live_neighbors,
            elements: vec![HashSet::new(); n],
            members: vec![HashSet::new(); n],
            degree_bound,
        }
    }

    /// Eliminates a node `v`, turning it into an Enode (element).
    /// Returns the true exact degree of `v` at the time of elimination (which equals the number of new edges added minus edges already existing).
    pub fn eliminate(&mut self, v: usize, g: &mut Graph) -> usize {
        self.is_eliminated[v] = true;

        // Find all unique live neighbors of `v` in the quotient graph.
        let mut L_v: HashSet<usize> = self.live_neighbors[v].clone();
        for &e in &self.elements[v] {
            for &u in &self.members[e] {
                if u != v && !self.is_eliminated[u] {
                    L_v.insert(u);
                }
            }
        }

        let mut fill_added = 0;

        let l_v_vec: Vec<usize> = L_v.into_iter().collect();
        for i in 0..l_v_vec.len() {
            for j in (i + 1)..l_v_vec.len() {
                let a = l_v_vec[i];
                let b = l_v_vec[j];
                if !g.adj[a].contains(&b) {
                    g.add_edge(a, b);
                    fill_added += 1;
                }
            }
        }

        for &u in &l_v_vec {
            g.adj[u].remove(&v);
        }
        g.adj[v].clear();
        g.eliminated[v] = true;

        self.members[v] = l_v_vec.iter().copied().collect();

        let elements_v = self.elements[v].clone();

        for &u in &l_v_vec {
            self.live_neighbors[u].remove(&v);
            self.elements[u].insert(v);

            for &e in &elements_v {
                self.elements[u].remove(&e);
            }
        }

        fill_added
    }

    pub fn exact_degree(&self, u: usize) -> usize {
        let mut L_u: HashSet<usize> = self.live_neighbors[u].clone();
        for &e in &self.elements[u] {
            for &w in &self.members[e] {
                if w != u && !self.is_eliminated[w] {
                    L_u.insert(w);
                }
            }
        }
        L_u.len()
    }

    pub fn approx_degree(&self, u: usize) -> usize {
        let mut d = self.live_neighbors[u].len();
        for &e in &self.elements[u] {
            if self.members[e].len() > 0 {
                d += self.members[e].len() - 1;
            }
        }
        d
    }
}

pub fn qmd(graph: &Graph) -> OrderingResult {
    let mut g = graph.clone();
    let n = g.n;
    let mut qg = QuotientGraph::new(&g);
    let mut order = Vec::with_capacity(n);
    let mut fill_count = 0usize;
    let mut width = 0usize;

    for _ in 0..n {
        let mut best_v = usize::MAX;
        let mut min_deg = usize::MAX;

        for v in 0..n {
            if !qg.is_eliminated[v] {
                let deg = qg.exact_degree(v);
                if deg < min_deg {
                    min_deg = deg;
                    best_v = v;
                } else if deg == min_deg && v < best_v {
                    best_v = v;
                }
            }
        }

        if best_v == usize::MAX { break; }

        width = width.max(min_deg);
        fill_count += qg.eliminate(best_v, &mut g);
        order.push(best_v);
    }

    OrderingResult {
        order,
        fill_count,
        width,
        fill_edges_added: fill_count,
    }
}

pub fn amd(graph: &Graph) -> OrderingResult {
    let mut g = graph.clone();
    let n = g.n;
    let mut qg = QuotientGraph::new(&g);
    let mut order = Vec::with_capacity(n);
    let mut fill_count = 0usize;
    let mut width = 0usize;

    for _ in 0..n {
        let mut best_v = usize::MAX;
        let mut min_deg = usize::MAX;

        for v in 0..n {
            if !qg.is_eliminated[v] {
                let deg = qg.approx_degree(v);
                if deg < min_deg {
                    min_deg = deg;
                    best_v = v;
                } else if deg == min_deg && v < best_v {
                    best_v = v;
                }
            }
        }

        if best_v == usize::MAX { break; }

        let true_deg = qg.exact_degree(best_v);
        width = width.max(true_deg);

        fill_count += qg.eliminate(best_v, &mut g);
        order.push(best_v);
    }

    OrderingResult {
        order,
        fill_count,
        width,
        fill_edges_added: fill_count,
    }
}
