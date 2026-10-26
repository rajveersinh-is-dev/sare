use std::fs;
use std::io;
use std::path::Path;

use sare::Graph;

#[derive(serde::Serialize)]
struct Output {
    algorithm: String,
    n: usize,
    m: usize,
    order: Vec<usize>,
    fill_count: usize,
    width: usize,
    fill_edges_added: usize,
    alpha: f64,
    beta: f64,
}

/// Read a Matrix Market coordinate file or a plain whitespace edge list (1-based).
fn read_graph(path: &Path) -> io::Result<Graph> {
    let mut is_mm = false;
    let mut n_from_header = 0usize;
    let mut data_lines: Vec<String> = Vec::new();

    for line in fs::read_to_string(path)?.lines() {
        let l = line.trim();
        if l.is_empty() {
            continue;
        }
        if l.starts_with('%') {
            if l.starts_with("%%MatrixMarket") {
                is_mm = true;
            }
            continue;
        }
        let parts: Vec<&str> = l.split_whitespace().collect();
        if parts.len() == 3 {
            // Matrix Market coordinate data line: row col value
            if let (Ok(r), Ok(c)) = (parts[0].parse::<usize>(), parts[1].parse::<usize>()) {
                n_from_header = n_from_header.max(r).max(c);
            }
            data_lines.push(l.to_string());
        } else if parts.len() == 2 && !is_mm {
            // plain edge list: u v
            if let (Ok(a), Ok(b)) = (parts[0].parse::<usize>(), parts[1].parse::<usize>()) {
                n_from_header = n_from_header.max(a).max(b);
                data_lines.push(l.to_string());
            }
        }
    }

    let n = n_from_header.max(1);
    let mut g = Graph::new(n);
    for l in data_lines {
        let parts: Vec<&str> = l.split_whitespace().collect();
        if parts.len() < 2 {
            continue;
        }
        let r: usize = parts[0].parse().unwrap_or(0);
        let c: usize = parts[1].parse().unwrap_or(0);
        if r > 0 && c > 0 && r <= n && c <= n {
            g.add_edge(r - 1, c - 1);
        }
    }
    Ok(g)
}

fn count_edges(g: &Graph) -> usize {
    let mut s = 0usize;
    for v in 0..g.n {
        s += g.adj[v].iter().filter(|&&u| u > v).count();
    }
    s
}

fn run_algorithm(g: &Graph, algo: &str, alpha: f64, beta: f64) -> Output {
    let n = g.n;
    let m = count_edges(g);
    let (order, fill_count, width, fill_edges_added) = match algo {
        "sare" => {
            let r = sare::sare(g, alpha, beta);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "sare-a0" => {
            let r = sare::sare(g, 0.0, 0.0);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "sare-a2" => {
            let r = sare::sare(g, 2.0, 0.0);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "sare-lookahead" => {
            let r = sare::sare(g, 1.0, 1.0);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "min-degree" => {
            let r = sare::min_degree(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "fast-min-degree" => {
            let r = sare::fast_min_degree(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "min-fill" => {
            let r = sare::min_fill(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "qmd" => {
            let r = sare::qmd(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "amd" => {
            let r = sare::amd(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "nd" => {
            let r = sare::nested_dissection(g);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        "qmd-lookahead" => {
            let r = sare::qmd_lookahead(g, beta);
            (r.order, r.fill_count, r.width, r.fill_edges_added)
        }
        _ => panic!("unknown algorithm: {}", algo),
    };
    Output {
        algorithm: algo.to_string(),
        n,
        m,
        order,
        fill_count,
        width,
        fill_edges_added,
        alpha,
        beta,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!(
            "Usage: sare <input.graph> <algo> [alpha] [beta]
algo: sare, sare-a0, sare-a2, sare-lookahead, min-degree, fast-min-degree, min-fill, qmd, amd, nd, qmd-lookahead
Reads Matrix Market coordinate or plain edge list (1-based). Prints JSON to stdout."
        );
        std::process::exit(2);
    }
    let path = Path::new(&args[1]);
    let algo = &args[2];
    let alpha: f64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(1.0);
    let beta: f64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(0.0);

    let g = read_graph(path).expect("failed to read graph");
    let out = run_algorithm(&g, algo, alpha, beta);
    let json = serde_json::to_string_pretty(&out).expect("serialize");
    println!("{}", json);
}
