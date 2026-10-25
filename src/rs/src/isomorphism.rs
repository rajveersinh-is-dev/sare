use std::collections::{HashMap, HashSet};

/// Computes a canonical permutation of the vertices of a graph.
pub fn get_canonical_permutation(n: usize, edges: &[(usize, usize)]) -> Vec<usize> {
    if n == 0 {
        return vec![];
    }

    let mut adj_list = vec![Vec::new(); n];
    for &(u, v) in edges {
        adj_list[u].push(v);
        adj_list[v].push(u);
    }

    let initial_colors = vec![0; n];
    let refined_colors = refine_colors(n, &adj_list, &initial_colors);

    let perms = get_canonical_permutations_recursive(n, &adj_list, &refined_colors);

    let mut best_matrix = None;
    let mut best_perm = vec![];

    for p in perms {
        let mut matrix = Vec::with_capacity(n);
        for i in 0..n {
            let mut row = Vec::with_capacity(n);
            let u = p[i];
            let neighbors: HashSet<usize> = adj_list[u].iter().copied().collect();
            for j in 0..n {
                let v = p[j];
                row.push(if neighbors.contains(&v) { 1 } else { 0 });
            }
            matrix.push(row);
        }

        if best_matrix.is_none() || matrix > *best_matrix.as_ref().unwrap() {
            best_matrix = Some(matrix);
            best_perm = p;
        }
    }

    best_perm
}

fn refine_colors(n: usize, adj_list: &[Vec<usize>], initial_colors: &[usize]) -> Vec<usize> {
    let mut colors = initial_colors.to_vec();
    loop {
        let mut new_colors_info = Vec::with_capacity(n);
        for i in 0..n {
            let mut neighbor_colors: Vec<usize> = adj_list[i].iter().map(|&j| colors[j]).collect();
            neighbor_colors.sort_unstable();
            new_colors_info.push((colors[i], neighbor_colors));
        }

        let mut unique = new_colors_info.clone();
        unique.sort();
        unique.dedup();

        let mut color_map = HashMap::new();
        for (idx, info) in unique.into_iter().enumerate() {
            color_map.insert(info, idx);
        }

        let new_colors: Vec<usize> = new_colors_info.into_iter().map(|info| color_map[&info]).collect();

        let distinct_old: HashSet<_> = colors.iter().collect();
        let distinct_new: HashSet<_> = new_colors.iter().collect();

        if distinct_new.len() == distinct_old.len() {
            colors = new_colors;
            break;
        }
        colors = new_colors;
    }
    colors
}

fn get_canonical_permutations_recursive(
    n: usize,
    adj_list: &[Vec<usize>],
    current_colors: &[usize],
) -> Vec<Vec<usize>> {
    let distinct_colors: HashSet<_> = current_colors.iter().copied().collect();
    if distinct_colors.len() == n {
        let mut pairs: Vec<(usize, usize)> = current_colors.iter().copied().zip(0..n).collect();
        pairs.sort_unstable_by_key(|&(c, _)| c);
        let perm: Vec<usize> = pairs.into_iter().map(|(_, v)| v).collect();
        return vec![perm];
    }

    let mut color_counts = HashMap::new();
    for &c in current_colors {
        *color_counts.entry(c).or_insert(0) += 1;
    }

    let mut target_color = 0;
    for (&c, &count) in &color_counts {
        if count > 1 {
            target_color = c;
            break;
        }
    }

    let vertices_in_class: Vec<usize> = (0..n).filter(|&v| current_colors[v] == target_color).collect();
    let max_c = current_colors.iter().copied().max().unwrap_or(0);

    let mut all_perms = Vec::new();
    for v in vertices_in_class {
        let mut new_colors = current_colors.to_vec();
        new_colors[v] = max_c + 1;
        let refined_colors = refine_colors(n, adj_list, &new_colors);
        all_perms.extend(get_canonical_permutations_recursive(n, adj_list, &refined_colors));
    }

    all_perms
}

/// Generates all unique (non-isomorphic) connected and disconnected graphs up to size `n`.
pub fn generate_non_isomorphic_graphs(n: usize) -> Vec<Vec<(usize, usize)>> {
    if n == 0 {
        return vec![vec![]];
    }
    let mut edges = Vec::new();
    for i in 0..n {
        for j in (i + 1)..n {
            edges.push((i, j));
        }
    }

    let m = edges.len();
    let num_graphs = 1 << m;
    let mut unique_forms = HashSet::new();

    for i in 0..num_graphs {
        let mut subset = Vec::new();
        for bit in 0..m {
            if (i & (1 << bit)) != 0 {
                subset.push(edges[bit]);
            }
        }

        let p = get_canonical_permutation(n, &subset);

        let mut adj_list = vec![HashSet::new(); n];
        for &(u, v) in &subset {
            adj_list[u].insert(v);
            adj_list[v].insert(u);
        }

        let mut canonical_edges = Vec::new();
        for i in 0..n {
            for j in (i + 1)..n {
                let u = p[i];
                let v = p[j];
                if adj_list[u].contains(&v) {
                    canonical_edges.push((i, j));
                }
            }
        }
        canonical_edges.sort_unstable();
        unique_forms.insert(canonical_edges);
    }

    unique_forms.into_iter().collect()
}
