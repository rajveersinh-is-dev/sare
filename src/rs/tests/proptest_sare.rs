use proptest::prelude::*;
use sare::{sare, min_degree, min_fill, exact_optimum, Graph};
use sare::verification::{is_chordal, build_filled_graph};

// Generate an arbitrary simple undirected graph up to size 20
prop_compose! {
    fn arbitrary_graph(max_n: usize)(n in 1..=max_n)(
        n in Just(n),
        edges in prop::collection::vec((0..n, 0..n), 0..(n * n))
    ) -> Graph {
        let mut g = Graph::new(n);
        for (u, v) in edges {
            if u != v {
                g.add_edge(u, v);
            }
        }
        g
    }
}

// Generate an arbitrary tree
prop_compose! {
    fn arbitrary_tree(max_n: usize)(n in 1..=max_n)(
        n in Just(n),
        parents in prop::collection::vec(0usize..1usize, n.saturating_sub(1)).prop_flat_map(move |mut p| {
            // Re-map to ensure i is connected to some j < i
            for i in 1..n {
                p[i-1] = p[i-1] % i;
            }
            Just(p)
        })
    ) -> Graph {
        let mut g = Graph::new(n);
        for (i, &parent) in parents.iter().enumerate() {
            g.add_edge(i + 1, parent);
        }
        g
    }
}

proptest! {
    #[test]
    fn test_sare_properties_random_graphs(graph in arbitrary_graph(20)) {
        let sare_result = sare(&graph, 1.0, 0.0);
        let mut ord = sare_result.order.clone();
        ord.sort();
        let expected_ord: Vec<usize> = (0..graph.n).collect();
        assert_eq!(ord, expected_ord);

        let (h, actual_fill) = build_filled_graph(&graph, &sare_result.order);
        assert_eq!(actual_fill, sare_result.fill_count);
        assert!(is_chordal(&h));

        // Also check min_degree
        let md_result = min_degree(&graph);
        let (h_md, actual_fill_md) = build_filled_graph(&graph, &md_result.order);
        assert_eq!(actual_fill_md, md_result.fill_count);
        assert!(is_chordal(&h_md));

        // Also check min_fill
        let mf_result = min_fill(&graph);
        let (h_mf, actual_fill_mf) = build_filled_graph(&graph, &mf_result.order);
        assert_eq!(actual_fill_mf, mf_result.fill_count);
        assert!(is_chordal(&h_mf));
    }

    #[test]
    fn test_sare_properties_trees(tree in arbitrary_tree(20)) {
        let sare_result = sare(&tree, 1.0, 0.0);
        assert_eq!(sare_result.fill_count, 0);

        let md_result = min_degree(&tree);
        assert_eq!(md_result.fill_count, 0);

        let mf_result = min_fill(&tree);
        assert_eq!(mf_result.fill_count, 0);
    }

    #[test]
    fn test_sare_properties_random_graphs_exact_optimum(graph in arbitrary_graph(14)) {
        let opt = exact_optimum(&graph);
        let sare_result = sare(&graph, 1.0, 0.0);
        assert!(sare_result.fill_count >= opt.fill_count);
    }
}
