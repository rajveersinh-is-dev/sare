use proptest::prelude::*;
use sare::{sare, min_degree, min_fill, evaluate_order, Graph};
use sare::verification::is_chordal;
use std::collections::HashSet;

// Generate a random graph with `n` vertices
prop_compose! {
    fn arb_graph(max_n: usize)(n in 1..=max_n, edges in prop::collection::vec((0..max_n, 0..max_n), 0..max_n*max_n)) -> Graph {
        let mut g = Graph::new(n);
        for (u, v) in edges {
            if u < n && v < n && u != v {
                g.add_edge(u, v);
            }
        }
        g
    }
}

proptest! {
    #[test]
    fn prop_sare_valid_permutation(g in arb_graph(20)) {
        let r = sare(&g, 1.0, 0.0);
        let mut order = r.order.clone();
        order.sort();
        let expected: Vec<usize> = (0..g.n).collect();
        prop_assert_eq!(order, expected);
    }

    #[test]
    fn prop_sare_fill_matches_evaluation(g in arb_graph(20)) {
        let r = sare(&g, 1.0, 0.0);
        let ev = evaluate_order(&g, &r.order);
        prop_assert_eq!(r.fill_count, ev.fill_count);
        prop_assert_eq!(r.width, ev.width);
    }

    #[test]
    fn prop_min_degree_valid(g in arb_graph(20)) {
        let r = min_degree(&g);
        let mut order = r.order.clone();
        order.sort();
        let expected: Vec<usize> = (0..g.n).collect();
        prop_assert_eq!(order, expected);
    }

    #[test]
    fn prop_min_fill_valid(g in arb_graph(20)) {
        let r = min_fill(&g);
        let mut order = r.order.clone();
        order.sort();
        let expected: Vec<usize> = (0..g.n).collect();
        prop_assert_eq!(order, expected);
    }

    #[test]
    fn prop_sare_chordal_completion(g in arb_graph(15)) {
        let r = sare(&g, 1.0, 0.0);

        // Build the filled graph
        let mut h = Graph::new(g.n);
        // Add original edges
        for v in 0..g.n {
            for &u in &g.adj[v] {
                if u > v {
                    h.add_edge(v, u);
                }
            }
        }

        let mut g2 = g.clone();
        let mut pos = vec![0; g.n];
        for (i, &v) in r.order.iter().enumerate() {
            pos[v] = i;
        }

        for &v in &r.order {
            let later_nbrs: Vec<usize> = g2.adj[v].iter().copied().filter(|&u| pos[u] > pos[v]).collect();
            for i in 0..later_nbrs.len() {
                for j in (i + 1)..later_nbrs.len() {
                    h.add_edge(later_nbrs[i], later_nbrs[j]);
                }
            }
            g2.eliminate(v);
        }

        prop_assert!(is_chordal(&h));
    }

    #[test]
    fn prop_sare_vs_exact_dp(g in arb_graph(10)) {
        let r = sare(&g, 1.0, 0.0);
        let opt = sare::exact_dp::exact_dp(&g);

        // The SARE heuristic should produce a fill count >= optimal DP fill count
        prop_assert!(r.fill_count >= opt.fill_count);
    }
}
