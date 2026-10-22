//! Exact minimum fill via Dynamic Programming (Held-Karp style)
//!
//! Computes exact minimum fill-in (and treewidth) by dynamic programming over subsets.
//! Useful for verifying heuristic algorithms on small instances up to N=18.

use crate::Graph;
use crate::OrderingResult;
use std::collections::HashMap;

#[derive(Clone)]
struct DpState {
    fill: usize,
    width: usize,
    last_eliminated: Option<usize>, // The vertex that was eliminated to reach this state
}

/// Solves minimum fill exactly using DP over subsets.
/// For each subset S of eliminated vertices, it tracks the minimum fill and width.
/// Returns the optimal elimination ordering, minimum fill, and corresponding width.
///
/// Complexity: O(2^N * poly(N)). Feasible for N <= 18.
pub fn exact_dp(graph: &Graph) -> OrderingResult {
    let n = graph.n;
    if n == 0 {
        return OrderingResult {
            order: vec![],
            fill_count: 0,
            width: 0,
            fill_edges_added: 0,
        };
    }

    // Check feasibility
    assert!(n <= 20, "DP feasible only for n <= 20, got {}", n);

    let mut dp: HashMap<u32, DpState> = HashMap::new();
    dp.insert(0, DpState {
        fill: 0,
        width: 0,
        last_eliminated: None,
    });

    // We will build up subsets of size 1 to n
    for size in 0..n {
        let current_states: Vec<_> = dp
            .iter()
            .filter(|(&mask, _)| mask.count_ones() as usize == size)
            .map(|(&mask, state)| (mask, state.clone()))
            .collect();

        for (mask, state) in current_states {
            // Build the graph corresponding to the eliminated subset 'mask'
            let mut g = graph.clone();
            // To compute the graph efficiently, we'll just simulate elimination
            // However, simulating from the beginning for every subset is slow.
            // Let's optimize: reconstruct the elimination order that led to 'mask'
            let mut order = Vec::with_capacity(size);
            let mut current_mask = mask;
            while current_mask != 0 {
                let s = &dp[&current_mask];
                let v = s.last_eliminated.unwrap();
                order.push(v);
                current_mask &= !(1 << v);
            }
            order.reverse(); // Now it's the sequence of eliminations

            for &v in &order {
                g.eliminate(v);
            }

            // Now try eliminating any remaining vertex
            for v in 0..n {
                if (mask & (1 << v)) == 0 {
                    let mut next_g = g.clone();
                    let d = next_g.degree(v);
                    let added_fill = next_g.eliminate(v);

                    let next_mask = mask | (1 << v);
                    let new_fill = state.fill + added_fill;
                    let new_width = state.width.max(d);

                    if let Some(existing) = dp.get_mut(&next_mask) {
                        // Tie-breaking: lower fill, then lower width
                        if new_fill < existing.fill || (new_fill == existing.fill && new_width < existing.width) {
                            existing.fill = new_fill;
                            existing.width = new_width;
                            existing.last_eliminated = Some(v);
                        }
                    } else {
                        dp.insert(next_mask, DpState {
                            fill: new_fill,
                            width: new_width,
                            last_eliminated: Some(v),
                        });
                    }
                }
            }
        }
    }

    let final_mask = (1 << n) - 1;
    let final_state = &dp[&final_mask];

    // Reconstruct the best order
    let mut best_order = Vec::with_capacity(n);
    let mut current_mask = final_mask;
    while current_mask != 0 {
        let v = dp[&current_mask].last_eliminated.unwrap();
        best_order.push(v);
        current_mask &= !(1 << v);
    }
    best_order.reverse();

    OrderingResult {
        order: best_order,
        fill_count: final_state.fill,
        width: final_state.width,
        fill_edges_added: final_state.fill,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{brute_force_optimum, Graph};

    fn path(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..n.saturating_sub(1) {
            g.add_edge(i, i + 1);
        }
        g
    }

    #[test]
    fn dp_matches_brute_force() {
        for n in 1..=8 {
            let g = path(n);
            let opt_bf = brute_force_optimum(&g);
            let opt_dp = exact_dp(&g);

            assert_eq!(opt_dp.fill_count, opt_bf.fill_count);
            assert_eq!(opt_dp.width, opt_bf.width);
        }
    }
}
