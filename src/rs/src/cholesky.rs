use crate::Graph;
use std::collections::BTreeSet;

/// A simple Compressed Sparse Column (CSC) format matrix representation.
#[derive(Debug, Clone)]
pub struct SparseMatrix {
    pub n: usize,
    pub col_ptrs: Vec<usize>,
    pub row_indices: Vec<usize>,
    pub values: Vec<f64>,
}

/// Converts a Graph into a symmetric positive definite (SPD) SparseMatrix in CSC format,
/// permuted according to `order`.
/// A = alpha * I + D_adj, where D_adj is the adjacency matrix with 1s.
pub fn graph_to_spd_csc(graph: &Graph, order: &[usize], alpha: f64) -> SparseMatrix {
    let n = graph.n;
    let mut inv_order = vec![0; n];
    for (i, &v) in order.iter().enumerate() {
        inv_order[v] = i;
    }

    let mut col_ptrs = vec![0; n + 1];
    let mut row_indices = Vec::new();
    let mut values = Vec::new();

    for j in 0..n {
        let orig_u = order[j];

        // Diagonal element
        row_indices.push(j);
        values.push(alpha + graph.degree(orig_u) as f64); // strictly diagonally dominant

        // Off-diagonal elements (lower triangular part in permuted matrix)
        let mut neighbors_in_permuted = BTreeSet::new();
        for &orig_v in &graph.adj[orig_u] {
            let permuted_v = inv_order[orig_v];
            if permuted_v > j {
                neighbors_in_permuted.insert(permuted_v);
            }
        }

        for &r in &neighbors_in_permuted {
            row_indices.push(r);
            values.push(-1.0);
        }

        col_ptrs[j + 1] = row_indices.len();
    }

    SparseMatrix {
        n,
        col_ptrs,
        row_indices,
        values,
    }
}

use crate::symbolic::{elimination_tree, symbolic_factorize};

/// Performs a sparse left-looking Cholesky factorization L L^T = A.
/// Returns (L, non_zero_count).
/// Assumes A is in CSC format and represents the lower triangular part of a symmetric matrix.
pub fn cholesky_factorize(a: &SparseMatrix) -> Result<(SparseMatrix, usize), String> {
    let n = a.n;

    // 1. Symbolic Factorization phase
    let parent = elimination_tree(a);
    let (l_col_ptrs, l_row_indices) = symbolic_factorize(a, &parent);
    let mut l_values = vec![0.0; l_row_indices.len()];

    let mut updates: Vec<Vec<(usize, usize)>> = vec![Vec::new(); n];
    for k in 0..n {
        if l_col_ptrs[k] + 1 < l_col_ptrs[k + 1] {
            let first_off_diag_idx = l_col_ptrs[k] + 1;
            let j = l_row_indices[first_off_diag_idx];
            updates[j].push((k, first_off_diag_idx));
        }
    }

    // Workspace
    let mut x: Vec<f64> = vec![0.0; n];

    for j in 0..n {
        // 1. Gather the j-th column of A into x
        for p in a.col_ptrs[j]..a.col_ptrs[j + 1] {
            let r = a.row_indices[p];
            x[r] = a.values[p];
        }

        // 2. Subtract L_{j,k} * L_{*,k} for k < j
        for i_update in 0..updates[j].len() {
            let (k, p_jk) = updates[j][i_update];
            let l_jk = l_values[p_jk];

            for p in p_jk..l_col_ptrs[k + 1] {
                let r = l_row_indices[p];
                x[r] -= l_jk * l_values[p];
            }

            let next_p_jk = p_jk + 1;
            if next_p_jk < l_col_ptrs[k + 1] {
                let next_j = l_row_indices[next_p_jk];
                updates[next_j].push((k, next_p_jk));
            }
        }

        // 3. Compute L[j, j]
        if x[j] <= 0.0 {
            return Err(format!("Matrix is not positive definite at column {}, diagonal element is {}", j, x[j]));
        }

        let l_jj = x[j].sqrt();

        let diag_p = l_col_ptrs[j];
        l_values[diag_p] = l_jj;
        x[j] = 0.0;

        // 4. Compute and store L[i, j] for i > j
        for p in (l_col_ptrs[j] + 1)..l_col_ptrs[j + 1] {
            let i = l_row_indices[p];
            let val = x[i] / l_jj;
            l_values[p] = val;
            x[i] = 0.0;
        }
    }

    let nnz_strict_lower = l_row_indices.len() - n;

    Ok((
        SparseMatrix {
            n,
            col_ptrs: l_col_ptrs,
            row_indices: l_row_indices,
            values: l_values,
        },
        nnz_strict_lower,
    ))
}

/// Verifies that the topological reported_fill equals the actual fill generated
/// during a numeric Cholesky factorization.
pub fn verify_fill_numerically(graph: &Graph, order: &[usize], reported_fill: usize) -> bool {
    let a = graph_to_spd_csc(graph, order, 2.0);

    let mut orig_edges_lower = 0;
    for j in 0..graph.n {
        orig_edges_lower += a.col_ptrs[j + 1] - a.col_ptrs[j] - 1;
    }

    if let Ok((_, l_nnz_strict_lower)) = cholesky_factorize(&a) {
        let calculated_fill = l_nnz_strict_lower - orig_edges_lower;
        calculated_fill == reported_fill
    } else {
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Graph, sare};

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

    fn star_graph(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 1..n {
            g.add_edge(0, i);
        }
        g
    }

    #[test]
    fn test_numeric_fill_cycle_sare() {
        for &n in &[5, 10, 20] {
            let g = cycle_graph(n);
            let res = sare(&g, 1.0, 0.0);
            assert!(verify_fill_numerically(&g, &res.order, res.fill_count));
        }
    }

    #[test]
    fn test_numeric_fill_grid_sare() {
        for &(rows, cols) in &[(3, 3), (4, 4)] {
            let g = grid_graph(rows, cols);
            let res = sare(&g, 1.0, 0.0);
            assert!(verify_fill_numerically(&g, &res.order, res.fill_count));
        }
    }

    #[test]
    fn test_numeric_fill_star_sare() {
        let g = star_graph(10);
        let res = sare(&g, 1.0, 0.0);
        assert!(verify_fill_numerically(&g, &res.order, res.fill_count));
    }

    #[test]
    fn test_cholesky_factorize_matrix_reconstruction() {
        let g = star_graph(5);
        let res = sare(&g, 1.0, 0.0);
        let order = res.order;
        let a = graph_to_spd_csc(&g, &order, 2.0);

        let (l, _) = cholesky_factorize(&a).unwrap();
        let n = g.n;

        let mut dense_a = vec![vec![0.0; n]; n];
        for j in 0..n {
            for p in a.col_ptrs[j]..a.col_ptrs[j + 1] {
                let r = a.row_indices[p];
                dense_a[r][j] = a.values[p];
                dense_a[j][r] = a.values[p];
            }
        }

        let mut dense_l = vec![vec![0.0; n]; n];
        for j in 0..n {
            for p in l.col_ptrs[j]..l.col_ptrs[j + 1] {
                let r = l.row_indices[p];
                dense_l[r][j] = l.values[p];
            }
        }

        let mut llt = vec![vec![0.0; n]; n];
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    llt[i][j] += dense_l[i][k] * dense_l[j][k];
                }
            }
        }

        for i in 0..n {
            for j in 0..n {
                assert!((dense_a[i][j] - llt[i][j]).abs() < 1e-9);
            }
        }
    }
}
