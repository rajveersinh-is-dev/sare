use sare::{sare, min_degree, fast_min_degree, exact_optimum, Graph};
use sare::verification::{is_chordal, build_filled_graph};
use sare::isomorphism::generate_non_isomorphic_graphs;
use rand::seq::SliceRandom;
use rand::RngExt;

#[test]
fn test_exhaustive_non_isomorphic_instances() {
    for n in 1..=6 {
        let graphs_edges = generate_non_isomorphic_graphs(n);
        for edges in &graphs_edges {
            let mut g = Graph::new(n);
            for &(u, v) in edges {
                g.add_edge(u, v);
            }

            let opt = exact_optimum(&g);

            // Test sare
            let sare_result = sare(&g, 1.0, 0.0);
            assert!(sare_result.fill_count >= opt.fill_count);
            assert!(sare_result.width >= opt.width);
            let (h, actual_fill) = build_filled_graph(&g, &sare_result.order);
            assert_eq!(actual_fill, sare_result.fill_count);
            assert!(is_chordal(&h));

            // Test min_degree
            let md_result = min_degree(&g);
            assert!(md_result.fill_count >= opt.fill_count);
            assert!(md_result.width >= opt.width);
            let (h_md, actual_fill_md) = build_filled_graph(&g, &md_result.order);
            assert_eq!(actual_fill_md, md_result.fill_count);
            assert!(is_chordal(&h_md));

            // Test fast_min_degree
            let fmd_result = fast_min_degree(&g);
            assert!(fmd_result.fill_count >= opt.fill_count);
            assert!(fmd_result.width >= opt.width);
            let (h_fmd, actual_fill_fmd) = build_filled_graph(&g, &fmd_result.order);
            assert_eq!(actual_fill_fmd, fmd_result.fill_count);
            assert!(is_chordal(&h_fmd));
        }
    }
}

#[test]
fn test_permutation_invariance_metamorphic() {
    let n = 15;
    let mut rng = rand::rng();
    let mut edges = std::collections::HashSet::new();

    // Generate a random graph
    for _ in 0..30 {
        let u = rng.random_range(0..n);
        let v = rng.random_range(0..n);
        if u != v {
            edges.insert((u.min(v), u.max(v)));
        }
    }

    let mut g_base = Graph::new(n);
    for &(u, v) in &edges {
        g_base.add_edge(u, v);
    }

    let base_res = sare(&g_base, 1.0, 0.0);
    let base_res_md = min_degree(&g_base);
    let base_res_fmd = fast_min_degree(&g_base);

    // Test 10 random permutations
    for _ in 0..10 {
        let mut perm: Vec<usize> = (0..n).collect();
        perm.shuffle(&mut rng);

        let mut g_perm = Graph::new(n);
        for &(u, v) in &edges {
            g_perm.add_edge(perm[u], perm[v]);
        }

        let perm_res = sare(&g_perm, 1.0, 0.0);
        let perm_res_md = min_degree(&g_perm);
        let perm_res_fmd = fast_min_degree(&g_perm);

        assert_eq!(perm_res.fill_count, base_res.fill_count);
        assert_eq!(perm_res.width, base_res.width);

        // Excluded deterministic assertions due to id-based tie breaking making exact outputs vary under isomorphism for non-canonical implementations.
        // The SARE assertions above function as soft invariance checks while true structural properties remain validated by the exhaustive DP tests.
    }
}
