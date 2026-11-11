use sare::Graph;
use sare::sare;
use sare::verification::build_filled_graph;
use sare::fill_path::build_filled_graph_via_paths;

fn cycle_graph(n: usize) -> Graph {
    let mut g = Graph::new(n);
    for i in 0..n {
        g.add_edge(i, (i + 1) % n);
    }
    g
}

fn grid_graph(rows: usize, cols: usize) -> Graph {
    let mut g = Graph::new(rows * cols);
    for r in 0..rows {
        for c in 0..cols {
            let u = r * cols + c;
            if c + 1 < cols {
                g.add_edge(u, u + 1);
            }
            if r + 1 < rows {
                g.add_edge(u, u + cols);
            }
        }
    }
    g
}

#[test]
fn test_fill_path_oracle_matches_sim_cycle() {
    for &n in &[4, 5, 10, 20] {
        let g = cycle_graph(n);
        let res = sare(&g, 1.0, 0.0);
        let (h_sim, fill_sim) = build_filled_graph(&g, &res.order);
        let (h_oracle, fill_oracle) = build_filled_graph_via_paths(&g, &res.order);

        assert_eq!(fill_sim, fill_oracle);
        for i in 0..n {
            let mut sim_adj: Vec<usize> = h_sim.adj[i].iter().copied().collect();
            let mut oracle_adj: Vec<usize> = h_oracle.adj[i].iter().copied().collect();
            sim_adj.sort_unstable();
            oracle_adj.sort_unstable();
            assert_eq!(sim_adj, oracle_adj);
        }
    }
}

#[test]
fn test_fill_path_oracle_matches_sim_grid() {
    for &(rows, cols) in &[(3, 3), (4, 4), (5, 5)] {
        let g = grid_graph(rows, cols);
        let res = sare(&g, 1.0, 0.0);
        let (h_sim, fill_sim) = build_filled_graph(&g, &res.order);
        let (h_oracle, fill_oracle) = build_filled_graph_via_paths(&g, &res.order);

        assert_eq!(fill_sim, fill_oracle);
        for i in 0..g.n {
            let mut sim_adj: Vec<usize> = h_sim.adj[i].iter().copied().collect();
            let mut oracle_adj: Vec<usize> = h_oracle.adj[i].iter().copied().collect();
            sim_adj.sort_unstable();
            oracle_adj.sort_unstable();
            assert_eq!(sim_adj, oracle_adj);
        }
    }
}
