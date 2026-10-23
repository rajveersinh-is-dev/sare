use sare::{sare, min_degree, min_fill, brute_force_optimum, Graph};
use sare::verification::{is_chordal, build_filled_graph};

fn generate_all_labeled_graphs(n: usize) -> Vec<Graph> {
    let mut edges = Vec::new();
    for i in 0..n {
        for j in (i + 1)..n {
            edges.push((i, j));
        }
    }

    let m = edges.len();
    let num_graphs = 1 << m;
    let mut graphs = Vec::with_capacity(num_graphs);

    for i in 0..num_graphs {
        let mut g = Graph::new(n);
        for bit in 0..m {
            if (i & (1 << bit)) != 0 {
                g.add_edge(edges[bit].0, edges[bit].1);
            }
        }
        graphs.push(g);
    }

    graphs
}

#[test]
fn test_exhaustive_small_instances() {
    for n in 1..=5 {
        let graphs = generate_all_labeled_graphs(n);
        for g in &graphs {
            let opt = brute_force_optimum(g);

            // Test sare
            let sare_result = sare(g, 1.0, 0.0);
            assert!(sare_result.fill_count >= opt.fill_count);
            assert!(sare_result.width >= opt.width);
            let (h, actual_fill) = build_filled_graph(g, &sare_result.order);
            assert_eq!(actual_fill, sare_result.fill_count);
            assert!(is_chordal(&h));

            // Test min_degree
            let md_result = min_degree(g);
            assert!(md_result.fill_count >= opt.fill_count);
            assert!(md_result.width >= opt.width);
            let (h_md, actual_fill_md) = build_filled_graph(g, &md_result.order);
            assert_eq!(actual_fill_md, md_result.fill_count);
            assert!(is_chordal(&h_md));

            // Test min_fill
            let mf_result = min_fill(g);
            assert!(mf_result.fill_count >= opt.fill_count);
            assert!(mf_result.width >= opt.width);
            let (h_mf, actual_fill_mf) = build_filled_graph(g, &mf_result.order);
            assert_eq!(actual_fill_mf, mf_result.fill_count);
            assert!(is_chordal(&h_mf));
        }
    }
}
