use crate::cholesky::SparseMatrix;
use std::collections::BTreeSet;

pub fn elimination_tree(a: &SparseMatrix) -> Vec<Option<usize>> {
    let n = a.n;

    // Create row-access representation for strict lower part
    let mut row_starts = vec![0; n + 1];
    for j in 0..n {
        for p in a.col_ptrs[j]..a.col_ptrs[j + 1] {
            let i = a.row_indices[p];
            if i > j {
                row_starts[i + 1] += 1;
            }
        }
    }

    for i in 0..n {
        row_starts[i + 1] += row_starts[i];
    }

    let mut row_cols = vec![0; row_starts[n]];
    let mut cur_starts = row_starts.clone();

    for j in 0..n {
        for p in a.col_ptrs[j]..a.col_ptrs[j + 1] {
            let i = a.row_indices[p];
            if i > j {
                row_cols[cur_starts[i]] = j;
                cur_starts[i] += 1;
            }
        }
    }

    let mut parent: Vec<Option<usize>> = vec![None; n];
    let mut ancestor: Vec<Option<usize>> = vec![None; n];

    for i in 0..n {
        for p in row_starts[i]..row_starts[i + 1] {
            let j = row_cols[p];
            let mut root = Some(j);

            while let Some(r) = root {
                if r < i {
                    if let Some(next_root) = ancestor[r] {
                        if next_root < i {
                            root = Some(next_root);
                            continue;
                        }
                    }
                }
                break;
            }

            if let Some(r) = root {
                if r < i {
                    ancestor[r] = Some(i);
                    if parent[r].is_none() {
                        parent[r] = Some(i);
                    }
                }
            }
        }
    }

    parent
}

pub fn post_order_etree(parent: &[Option<usize>]) -> Vec<usize> {
    let n = parent.len();
    let mut first_child: Vec<Option<usize>> = vec![None; n];
    let mut next_sibling: Vec<Option<usize>> = vec![None; n];

    for i in 0..n {
        if let Some(p) = parent[i] {
            next_sibling[i] = first_child[p];
            first_child[p] = Some(i);
        }
    }

    let mut order = Vec::with_capacity(n);
    let mut stack = Vec::new();

    for i in 0..n {
        if parent[i].is_none() {
            stack.push(i);
            while let Some(&curr) = stack.last() {
                if let Some(child) = first_child[curr] {
                    first_child[curr] = next_sibling[child];
                    stack.push(child);
                } else {
                    order.push(stack.pop().unwrap());
                }
            }
        }
    }

    order
}

pub fn symbolic_factorize(a: &SparseMatrix, parent: &[Option<usize>]) -> (Vec<usize>, Vec<usize>) {
    let n = a.n;
    let mut l_col_ptrs = vec![0; n + 1];

    let mut first_child: Vec<Option<usize>> = vec![None; n];
    let mut next_sibling: Vec<Option<usize>> = vec![None; n];

    for i in 0..n {
        if let Some(p) = parent[i] {
            next_sibling[i] = first_child[p];
            first_child[p] = Some(i);
        }
    }

    let mut l_struct: Vec<BTreeSet<usize>> = vec![BTreeSet::new(); n];
    let post_order = post_order_etree(parent);

    for &j in &post_order {
        let mut struct_j = BTreeSet::new();

        for p in a.col_ptrs[j]..a.col_ptrs[j + 1] {
            let i = a.row_indices[p];
            if i > j {
                struct_j.insert(i);
            }
        }

        let mut c_opt = first_child[j];
        while let Some(c) = c_opt {
            for &r in &l_struct[c] {
                if r > j {
                    struct_j.insert(r);
                }
            }
            c_opt = next_sibling[c];
        }

        l_struct[j] = struct_j;
    }

    let mut l_row_indices = Vec::new();

    for j in 0..n {
        l_row_indices.push(j); // Diagonal
        for &r in &l_struct[j] {
            l_row_indices.push(r);
        }
        l_col_ptrs[j + 1] = l_row_indices.len();
    }

    (l_col_ptrs, l_row_indices)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Graph;
    use crate::cholesky::graph_to_spd_csc;

    fn path_graph(n: usize) -> Graph {
        let mut g = Graph::new(n);
        for i in 0..(n - 1) {
            g.add_edge(i, i + 1);
        }
        g
    }

    #[test]
    fn test_elimination_tree_path() {
        let n = 5;
        let g = path_graph(n);
        // Using a natural ordering (0, 1, 2, 3, 4)
        let order: Vec<usize> = (0..n).collect();
        let a = graph_to_spd_csc(&g, &order, 2.0);

        let parent = elimination_tree(&a);

        // For a path 0-1-2-3-4 with order 0, 1, 2, 3, 4
        // Parent of 0 is 1. Parent of 1 is 2. etc.
        assert_eq!(parent[0], Some(1));
        assert_eq!(parent[1], Some(2));
        assert_eq!(parent[2], Some(3));
        assert_eq!(parent[3], Some(4));
        assert_eq!(parent[4], None);
    }

    #[test]
    fn test_symbolic_factorize_path() {
        let n = 5;
        let g = path_graph(n);
        let order: Vec<usize> = (0..n).collect();
        let a = graph_to_spd_csc(&g, &order, 2.0);
        let parent = elimination_tree(&a);

        let (l_col_ptrs, l_row_indices) = symbolic_factorize(&a, &parent);

        assert_eq!(l_col_ptrs.len(), n + 1);
        assert_eq!(l_col_ptrs[0], 0);

        // For path with natural order, no fill-in. L has same structure as lower part of A.
        assert_eq!(l_row_indices.len(), n * 2 - 1);
    }
}
