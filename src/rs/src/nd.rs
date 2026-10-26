use std::collections::{HashSet, HashMap};
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
        // pseudo-random for tests and general use
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

/// Finds a vertex separator using spectral bisection.
fn get_vertex_separator(adj: &[Vec<usize>], nodes: &[usize]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let n_local = nodes.len();
    if n_local <= 2 {
        return (vec![], vec![], nodes.to_vec());
    }

    let mut global_to_local = HashMap::new();
    for (l, &g) in nodes.iter().enumerate() {
        global_to_local.insert(g, l);
    }

    let mut local_adj = vec![Vec::new(); n_local];
    for (i, &g) in nodes.iter().enumerate() {
        for &nbr in &adj[g] {
            if let Some(&l_nbr) = global_to_local.get(&nbr) {
                local_adj[i].push(l_nbr);
            }
        }
    }

    let fiedler = get_fiedler(&local_adj, 1000, 1e-6);

    let mut sorted_f: Vec<(f64, usize)> = fiedler.into_iter().enumerate().map(|(i, f)| (f, i)).collect();
    sorted_f.sort_unstable_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

    let median_idx = n_local / 2;

    let mut L_local = HashSet::new();
    for &(_, idx) in &sorted_f[..median_idx] {
        L_local.insert(idx);
    }
    let mut R_local = HashSet::new();
    for &(_, idx) in &sorted_f[median_idx..] {
        R_local.insert(idx);
    }

    let mut V_L = HashSet::new();
    let mut V_R = HashSet::new();

    for &u in &L_local {
        for &v in &local_adj[u] {
            if R_local.contains(&v) {
                V_L.insert(u);
                V_R.insert(v);
            }
        }
    }

    let S_local;
    if V_L.len() < V_R.len() {
        S_local = V_L;
        for &u in &S_local {
            L_local.remove(&u);
        }
    } else {
        S_local = V_R;
        for &v in &S_local {
            R_local.remove(&v);
        }
    }

    let mut L = Vec::new();
    for &idx in &L_local {
        L.push(nodes[idx]);
    }
    let mut R = Vec::new();
    for &idx in &R_local {
        R.push(nodes[idx]);
    }
    let mut S = Vec::new();
    for &idx in &S_local {
        S.push(nodes[idx]);
    }

    (L, R, S)
}

/// Recursive nested dissection
fn nd_recursive(adj: &[Vec<usize>], nodes: &[usize], min_size: usize) -> Vec<usize> {
    if nodes.len() <= min_size {
        let mut local_deg = Vec::with_capacity(nodes.len());
        for &u in nodes {
            let mut deg = 0;
            for &v in &adj[u] {
                if nodes.contains(&v) {
                    deg += 1;
                }
            }
            local_deg.push((deg, u));
        }
        local_deg.sort_unstable();
        return local_deg.into_iter().map(|(_, u)| u).collect();
    }

    let (L, R, mut S) = get_vertex_separator(adj, nodes);

    if L.is_empty() || R.is_empty() {
        return nodes.to_vec();
    }

    let mut order_L = nd_recursive(adj, &L, min_size);
    let mut order_R = nd_recursive(adj, &R, min_size);

    let mut S_deg = Vec::with_capacity(S.len());
    for &u in &S {
        let mut deg = 0;
        for &v in &adj[u] {
            if S.contains(&v) {
                deg += 1;
            }
        }
        S_deg.push((deg, u));
    }
    S_deg.sort_unstable();
    let mut S_sorted: Vec<usize> = S_deg.into_iter().map(|(_, u)| u).collect();

    let mut order = Vec::with_capacity(nodes.len());
    order.append(&mut order_L);
    order.append(&mut order_R);
    order.append(&mut S_sorted);

    order
}

pub fn nested_dissection(graph: &Graph) -> OrderingResult {
    let n = graph.n;
    let mut adj = vec![Vec::new(); n];
    for i in 0..n {
        adj[i] = graph.adj[i].iter().copied().collect();
    }

    let initial_nodes: Vec<usize> = (0..n).collect();
    let order = nd_recursive(&adj, &initial_nodes, 5);

    evaluate_order(graph, &order)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fiedler_vector() {
        let n = 4;
        let mut adj = vec![Vec::new(); n];
        // Path graph
        adj[0].push(1); adj[1].push(0);
        adj[1].push(2); adj[2].push(1);
        adj[2].push(3); adj[3].push(2);

        let f = get_fiedler(&adj, 1000, 1e-6);
        assert_eq!(f.len(), 4);

        // Sum should be roughly 0
        let sum: f64 = f.iter().sum();
        assert!(sum.abs() < 1e-5);
    }

    #[test]
    fn test_nested_dissection_order() {
        let mut g = Graph::new(5);
        g.add_edge(0, 1);
        g.add_edge(1, 2);
        g.add_edge(2, 3);
        g.add_edge(3, 4);

        let res = nested_dissection(&g);
        assert_eq!(res.order.len(), 5);

        let mut sorted_order = res.order.clone();
        sorted_order.sort_unstable();
        assert_eq!(sorted_order, vec![0, 1, 2, 3, 4]);
    }
}
