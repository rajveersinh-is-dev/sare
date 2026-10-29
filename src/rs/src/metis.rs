use std::collections::{HashMap, HashSet};
use crate::{Graph, OrderingResult, evaluate_order};

/// Computes the Fiedler vector using Deflated Power Iteration.
fn get_fiedler(adj: &[Vec<usize>], num_iters: usize, tol: f64) -> Vec<f64> {
    let n = adj.len();
    if n <= 1 {
        return vec![0.0; n];
    }

    let mut degrees = vec![0; n];
    let mut max_d = 0;
    for i in 0..n {
        degrees[i] = adj[i].len();
        if degrees[i] > max_d {
            max_d = degrees[i];
        }
    }

    let c = 2.0 * (max_d as f64) + 1.0;

    let mut v: Vec<f64> = (0..n).map(|i| {
        // pseudo-random
        let seed = (i as f64) * 0.12345;
        seed - seed.floor() - 0.5
    }).collect();

    let s: f64 = v.iter().sum::<f64>() / (n as f64);
    for x in &mut v {
        *x -= s;
    }

    let norm = v.iter().map(|&x| x * x).sum::<f64>().sqrt();
    if norm > 0.0 {
        for x in &mut v {
            *x /= norm;
        }
    }

    let mut v_next = vec![0.0; n];
    for _ in 0..num_iters {
        for i in 0..n {
            let mut val = (c - degrees[i] as f64) * v[i];
            for &j in &adj[i] {
                val += v[j];
            }
            v_next[i] = val;
        }

        let s: f64 = v_next.iter().sum::<f64>() / (n as f64);
        for x in &mut v_next {
            *x -= s;
        }

        let norm = v_next.iter().map(|&x| x * x).sum::<f64>().sqrt();
        if norm > 0.0 {
            for x in &mut v_next {
                *x /= norm;
            }
        }

        let mut max_diff = 0.0_f64;
        let mut max_diff2 = 0.0_f64;
        for i in 0..n {
            let diff = (v_next[i] - v[i]).abs();
            if diff > max_diff {
                max_diff = diff;
            }
            let diff2 = (v_next[i] + v[i]).abs();
            if diff2 > max_diff2 {
                max_diff2 = diff2;
            }
        }

        v.copy_from_slice(&v_next);

        if max_diff < tol || max_diff2 < tol {
            break;
        }
    }

    v
}

#[derive(Clone)]
pub struct WeightedGraph {
    pub n: usize,
    pub adj: Vec<Vec<(usize, f64)>>,
    pub vwgt: Vec<f64>,
}

impl WeightedGraph {
    pub fn new(n: usize) -> Self {
        WeightedGraph {
            n,
            adj: vec![Vec::new(); n],
            vwgt: vec![1.0; n],
        }
    }

    pub fn add_edge(&mut self, u: usize, v: usize, w: f64) {
        self.adj[u].push((v, w));
        self.adj[v].push((u, w));
    }
}

pub fn coarsen(graph: &WeightedGraph) -> (WeightedGraph, Vec<usize>) {
    let n = graph.n;
    let mut matched = vec![false; n];
    let mut match_arr = vec![usize::MAX; n];

    // Simple deterministic pseudo-random order
    let mut nodes: Vec<usize> = (0..n).collect();
    // deterministic shuffle based on index
    for i in 0..n {
        let swap_idx = (i * 137 + 42) % n;
        nodes.swap(i, swap_idx);
    }

    for &u in &nodes {
        if matched[u] {
            continue;
        }

        let mut best_v = usize::MAX;
        let mut max_w = -1.0;

        for &(v, w) in &graph.adj[u] {
            if !matched[v] && w > max_w {
                max_w = w;
                best_v = v;
            }
        }

        if best_v != usize::MAX {
            match_arr[u] = best_v;
            match_arr[best_v] = u;
            matched[u] = true;
            matched[best_v] = true;
        } else {
            match_arr[u] = u;
            matched[u] = true;
        }
    }

    let mut coarse_map = vec![usize::MAX; n];
    let mut coarse_n = 0;
    for i in 0..n {
        if coarse_map[i] == usize::MAX {
            coarse_map[i] = coarse_n;
            if match_arr[i] != usize::MAX {
                coarse_map[match_arr[i]] = coarse_n;
            }
            coarse_n += 1;
        }
    }

    let mut coarse_g = WeightedGraph::new(coarse_n);
    for i in 0..n {
        if match_arr[i] == i || match_arr[i] < i {
            let c_u = coarse_map[i];
            if match_arr[i] != i {
                coarse_g.vwgt[c_u] = graph.vwgt[i] + graph.vwgt[match_arr[i]];
            } else {
                coarse_g.vwgt[c_u] = graph.vwgt[i];
            }
        }
    }

    for u in 0..n {
        let c_u = coarse_map[u];
        for &(v, w) in &graph.adj[u] {
            let c_v = coarse_map[v];
            if c_u != c_v {
                coarse_g.adj[c_u].push((c_v, w));
            }
        }
    }

    // Compact edges
    for i in 0..coarse_n {
        let mut edge_map = HashMap::new();
        for &(v, w) in &coarse_g.adj[i] {
            *edge_map.entry(v).or_insert(0.0) += w;
        }
        coarse_g.adj[i] = edge_map.into_iter().collect();
    }

    (coarse_g, coarse_map)
}

pub fn initial_partition(graph: &WeightedGraph) -> (Vec<usize>, Vec<usize>) {
    let n = graph.n;
    if n <= 1 {
        return ((0..n).collect(), Vec::new());
    }

    let mut adj = vec![Vec::new(); n];
    for u in 0..n {
        for &(v, _) in &graph.adj[u] {
            adj[u].push(v);
        }
    }

    let fiedler = get_fiedler(&adj, 1000, 1e-6);

    let mut sorted_f: Vec<(f64, usize)> = fiedler.into_iter().enumerate().map(|(i, f)| (f, i)).collect();
    sorted_f.sort_unstable_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

    let total_w: f64 = graph.vwgt.iter().sum();
    let target_w = total_w / 2.0;

    let mut L = Vec::new();
    let mut R = Vec::new();
    let mut curr_w = 0.0;

    for &(_, idx) in &sorted_f {
        if curr_w < target_w {
            L.push(idx);
            curr_w += graph.vwgt[idx];
        } else {
            R.push(idx);
        }
    }

    if L.is_empty() && !R.is_empty() {
        L.push(R.pop().unwrap());
    } else if R.is_empty() && !L.is_empty() {
        R.push(L.pop().unwrap());
    }

    (L, R)
}

pub fn refine_kl(graph: &WeightedGraph, l: &[usize], r: &[usize]) -> (Vec<usize>, Vec<usize>) {
    let mut l_set: HashSet<usize> = l.iter().copied().collect();
    let mut r_set: HashSet<usize> = r.iter().copied().collect();

    let mut changed = true;
    while changed {
        changed = false;

        let mut best_gain = 0.0;
        let mut best_u = usize::MAX;

        for u in 0..graph.n {
            let mut internal = 0.0;
            let mut external = 0.0;
            let is_l = l_set.contains(&u);

            for &(v, w) in &graph.adj[u] {
                if l_set.contains(&v) == is_l {
                    internal += w;
                } else {
                    external += w;
                }
            }

            let gain = external - internal;
            if gain > best_gain {
                best_gain = gain;
                best_u = u;
            }
        }

        if best_u != usize::MAX && best_gain > 0.0 {
            if l_set.contains(&best_u) {
                l_set.remove(&best_u);
                r_set.insert(best_u);
            } else {
                r_set.remove(&best_u);
                l_set.insert(best_u);
            }
            changed = true;
        }
    }

    let l_final: Vec<usize> = l_set.into_iter().collect();
    let r_final: Vec<usize> = r_set.into_iter().collect();

    (l_final, r_final)
}

pub fn metis_bisection(graph: &WeightedGraph) -> (Vec<usize>, Vec<usize>) {
    if graph.n <= 50 {
        return initial_partition(graph);
    }

    let (coarse_g, coarse_map) = coarsen(graph);

    if coarse_g.n > (0.8 * graph.n as f64) as usize {
        return initial_partition(graph);
    }

    let (c_l, _) = metis_bisection(&coarse_g);
    let c_l_set: HashSet<usize> = c_l.into_iter().collect();

    let mut l = Vec::new();
    let mut r = Vec::new();

    for i in 0..graph.n {
        if c_l_set.contains(&coarse_map[i]) {
            l.push(i);
        } else {
            r.push(i);
        }
    }

    refine_kl(graph, &l, &r)
}

fn get_vertex_separator(graph: &WeightedGraph, l: &[usize], r: &[usize]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let mut l_set: HashSet<usize> = l.iter().copied().collect();
    let mut r_set: HashSet<usize> = r.iter().copied().collect();

    let mut v_l = HashSet::new();
    let mut v_r = HashSet::new();

    for &u in l {
        for &(v, _) in &graph.adj[u] {
            if r_set.contains(&v) {
                v_l.insert(u);
                v_r.insert(v);
            }
        }
    }

    let s;
    if v_l.len() < v_r.len() {
        s = v_l.clone();
        for &u in &v_l {
            l_set.remove(&u);
        }
    } else {
        s = v_r.clone();
        for &v in &v_r {
            r_set.remove(&v);
        }
    }

    let l_final: Vec<usize> = l_set.into_iter().collect();
    let r_final: Vec<usize> = r_set.into_iter().collect();
    let s_final: Vec<usize> = s.into_iter().collect();

    (l_final, r_final, s_final)
}

fn metis_nd_recursive(adj: &[Vec<usize>], nodes: &[usize], min_size: usize) -> Vec<usize> {
    let n_local = nodes.len();
    if n_local <= min_size {
        let nodes_set: HashSet<usize> = nodes.iter().copied().collect();
        let mut local_deg = Vec::with_capacity(n_local);
        for &u in nodes {
            let mut deg = 0;
            for &v in &adj[u] {
                if nodes_set.contains(&v) {
                    deg += 1;
                }
            }
            local_deg.push((deg, u));
        }
        local_deg.sort_unstable();
        return local_deg.into_iter().map(|(_, u)| u).collect();
    }

    let mut wg = WeightedGraph::new(n_local);
    let mut global_to_local = HashMap::new();
    for (l, &g) in nodes.iter().enumerate() {
        global_to_local.insert(g, l);
    }

    for (i, &g) in nodes.iter().enumerate() {
        for &nbr in &adj[g] {
            if let Some(&l_nbr) = global_to_local.get(&nbr) {
                wg.add_edge(i, l_nbr, 1.0);
            }
        }
    }

    let (l_local, r_local) = metis_bisection(&wg);
    let (l_local, r_local, s_local) = get_vertex_separator(&wg, &l_local, &r_local);

    let mut l = Vec::new();
    for &idx in &l_local {
        l.push(nodes[idx]);
    }
    let mut r = Vec::new();
    for &idx in &r_local {
        r.push(nodes[idx]);
    }
    let mut s = Vec::new();
    for &idx in &s_local {
        s.push(nodes[idx]);
    }

    if l.is_empty() || r.is_empty() {
        return nodes.to_vec();
    }

    let mut order_l = metis_nd_recursive(adj, &l, min_size);
    let mut order_r = metis_nd_recursive(adj, &r, min_size);

    let s_set: HashSet<usize> = s.iter().copied().collect();
    let mut s_deg = Vec::with_capacity(s.len());
    for &u in &s {
        let mut deg = 0;
        for &v in &adj[u] {
            if s_set.contains(&v) {
                deg += 1;
            }
        }
        s_deg.push((deg, u));
    }
    s_deg.sort_unstable();
    let mut s_sorted: Vec<usize> = s_deg.into_iter().map(|(_, u)| u).collect();

    let mut order = Vec::with_capacity(n_local);
    order.append(&mut order_l);
    order.append(&mut order_r);
    order.append(&mut s_sorted);

    order
}

pub fn metis_nested_dissection(graph: &Graph) -> OrderingResult {
    let n = graph.n;
    let mut adj = vec![Vec::new(); n];
    for i in 0..n {
        adj[i] = graph.adj[i].iter().copied().collect();
    }

    let initial_nodes: Vec<usize> = (0..n).collect();
    let order = metis_nd_recursive(&adj, &initial_nodes, 5);

    evaluate_order(graph, &order)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metis_bisection() {
        let mut wg = WeightedGraph::new(4);
        wg.add_edge(0, 1, 10.0);
        wg.add_edge(1, 2, 1.0);
        wg.add_edge(2, 3, 10.0);

        let (l, r) = metis_bisection(&wg);
        assert_eq!(l.len() + r.len(), 4);

        let l_set: HashSet<usize> = l.into_iter().collect();
        let r_set: HashSet<usize> = r.into_iter().collect();

        // Edge 1-2 should be the cut
        assert!((l_set.contains(&0) && l_set.contains(&1) && r_set.contains(&2) && r_set.contains(&3)) ||
                (r_set.contains(&0) && r_set.contains(&1) && l_set.contains(&2) && l_set.contains(&3)));
    }

    #[test]
    fn test_metis_nd_recursive() {
        let mut g = Graph::new(5);
        g.add_edge(0, 1);
        g.add_edge(1, 2);
        g.add_edge(2, 3);
        g.add_edge(3, 4);

        let res = metis_nested_dissection(&g);
        assert_eq!(res.order.len(), 5);

        let mut sorted_order = res.order.clone();
        sorted_order.sort_unstable();
        assert_eq!(sorted_order, vec![0, 1, 2, 3, 4]);
    }
}
