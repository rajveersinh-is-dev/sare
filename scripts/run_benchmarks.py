"""
SARE benchmark runner (revised per Reviewer C, cycle 1).

Runs the Rust CLI (src/rs/target/release/sare) on generated instance families and
records fill_count, elimination width, ordering time, and peak memory for each
algorithm.

Algorithms compared (all in the SAME Rust binary -> fair same-language comparison):
  sare            : SARE default (alpha=1, beta=0)
  sare-a0         : SARE degree-driven (alpha=0, beta=0)  [ablation]
  sare-a2         : SARE fill-driven (alpha=2, beta=0)    [ablation]
  sare-lookahead  : SARE with 1-step lookahead (alpha=1, beta=1) [ablation]
  min-degree      : Minimum Degree greedy
  min-fill        : Minimum Fill-in greedy

Instance families (deterministic, fixed seeds):
  path, clique, star, tree, grid, erdos-renyi (sparse/dense), chordal,
  poisson_2d (5-point stencil, realistic sparse-direct-solver workload),
  sparse_random (symmetric, realistic-ish)

Outputs (regenerable by this script):
  results/raw/benchmarks.csv      per-rep measurements (time, memory, fill, width)
  results/processed/summary.csv   per (family, algorithm) aggregates: mean + 95% CI
  results/processed/relative_to_sare.csv  fill/width/time ratios vs SARE
  results/figures/*.png           plots

Usage:
  python scripts/run_benchmarks.py [--quick] [--reps N]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

REPO_ROOT = Path(__file__).resolve().parents[1]
RUST_BIN = REPO_ROOT / "src" / "rs" / "target" / "release" / "sare.exe"
if not RUST_BIN.exists():
    RUST_BIN = REPO_ROOT / "src" / "rs" / "target" / "release" / "sare"

RAW_DIR = REPO_ROOT / "results" / "raw"
PROC_DIR = REPO_ROOT / "results" / "processed"
FIG_DIR = REPO_ROOT / "results" / "figures"

ALGORITHMS = ["sare", "sare-a0", "sare-a2", "sare-lookahead", "min-degree", "min-fill"]
DEFAULT_REPS = 5
BOOTSTRAP_ITERS = 2000


# ---------------------------------------------------------------------------
# instance generation
# ---------------------------------------------------------------------------

def _edges_text(n, edges):
    lines = []
    for u, v in edges:
        lines.append(f"{u + 1} {v + 1}")
    return "\n".join(lines) + "\n"


def path_graph(n):
    return [(i, i + 1) for i in range(n - 1)]


def clique_graph(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def star_graph(n):
    return [(0, v) for v in range(1, n)]


def tree_graph(n, seed=0):
    import random
    rng = random.Random(seed)
    edges = []
    for v in range(1, n):
        u = rng.randrange(v)
        edges.append((u, v))
    return edges


def grid_graph(rows, cols):
    n = rows * cols
    edges = []
    for r in range(rows):
        for c in range(cols):
            v = r * cols + c
            if r + 1 < rows:
                edges.append((v, v + cols))
            if c + 1 < cols:
                edges.append((v, v + 1))
    return edges


def erdos_renyi(n, p, seed=0):
    import random
    rng = random.Random(seed)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                edges.append((i, j))
    return edges


def chordal_graph(n, seed=0):
    """Build a chordal graph: start from a clique, add simplicial vertices."""
    import random
    rng = random.Random(seed)
    edges = []
    k = max(2, n // 4)
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((i, j))
    for v in range(k, n):
        nbrs = rng.sample(range(v), min(rng.randrange(1, k + 1), v))
        for u in nbrs:
            edges.append((u, v))
    return edges


def poisson_2d(k, seed=0):
    """5-point stencil on a k x k grid (n = k^2). Realistic sparse-direct-solver workload."""
    n = k * k
    edges = []
    for r in range(k):
        for c in range(k):
            v = r * k + c
            if r + 1 < k:
                edges.append((v, v + k))
            if c + 1 < k:
                edges.append((v, v + 1))
    return edges


def sparse_random(n, density, seed=0):
    """Symmetric random sparse matrix (scipy), written as edge list."""
    import scipy.sparse as sp
    rng_seed = seed
    A = sp.random(n, n, density=density, random_state=rng_seed, format="coo", dtype=float)
    A = (A + A.T) > 0  # symmetrize
    A.setdiag(0)
    A = A.tocoo()
    edges = [(int(i), int(j)) for i, j in zip(A.row, A.col) if i < j]
    return edges


def instance_families(quick=False):
    """Yield (family, label, n, edge_list_text)."""
    if quick:
        specs = [
            ("path", "path_50", 50, path_graph(50)),
            ("clique", "clique_30", 30, clique_graph(30)),
            ("star", "star_40", 40, star_graph(40)),
            ("tree", "tree_60", 60, tree_graph(60, seed=1)),
            ("grid", "grid_64", 64, grid_graph(8, 8)),
            ("er_sparse", "er_sparse_60", 60, erdos_renyi(60, 0.03, seed=5)),
            ("er_dense", "er_dense_50", 50, erdos_renyi(50, 0.15, seed=6)),
            ("chordal", "chordal_60", 60, chordal_graph(60, seed=7)),
            ("poisson_2d", "poisson_8x8", 64, poisson_2d(8, seed=0)),
            ("sparse_random", "sr_60_d0.05", 60, sparse_random(60, 0.05, seed=8)),
        ]
    else:
        specs = [
            ("path", "path_200", 200, path_graph(200)),
            ("path", "path_500", 500, path_graph(500)),
            ("clique", "clique_40", 40, clique_graph(40)),
            ("star", "star_80", 80, star_graph(80)),
            ("tree", "tree_200", 200, tree_graph(200, seed=2)),
            ("tree", "tree_500", 500, tree_graph(500, seed=3)),
            ("grid", "grid_144", 144, grid_graph(12, 12)),
            ("grid", "grid_256", 256, grid_graph(16, 16)),
            ("er_sparse", "er_sparse_100", 100, erdos_renyi(100, 0.03, seed=10)),
            ("er_sparse", "er_sparse_300", 300, erdos_renyi(300, 0.02, seed=11)),
            ("er_dense", "er_dense_80", 80, erdos_renyi(80, 0.15, seed=12)),
            ("er_dense", "er_dense_150", 150, erdos_renyi(150, 0.10, seed=13)),
            ("chordal", "chordal_100", 100, chordal_graph(100, seed=14)),
            ("chordal", "chordal_250", 250, chordal_graph(250, seed=15)),
            ("poisson_2d", "poisson_14x14", 196, poisson_2d(14, seed=0)),
            ("poisson_2d", "poisson_20x20", 400, poisson_2d(20, seed=0)),
            ("sparse_random", "sr_100_d0.03", 100, sparse_random(100, 0.03, seed=16)),
            ("sparse_random", "sr_200_d0.02", 200, sparse_random(200, 0.02, seed=17)),
        ]
    for family, label, n, edges in specs:
        yield family, label, n, _edges_text(n, edges)


# ---------------------------------------------------------------------------
# runner (with repetition + CI + memory)
# ---------------------------------------------------------------------------

def alpha_beta(algo):
    if algo == "sare-a0":
        return 0.0, 0.0
    if algo == "sare-a2":
        return 2.0, 0.0
    if algo == "sare-lookahead":
        return 1.0, 1.0
    return 1.0, 0.0


def run_once(bin_path, text, algo, alpha, beta):
    """Run the Rust CLI once; return (result_dict, wall_s, peak_rss_bytes).

    Memory is sampled on a daemon thread while the child runs, to avoid
    blocking on pipe I/O and to work reliably on Windows (psutil cannot query
    a process after it has exited).
    """
    inp = str(REPO_ROOT / "tests" / "_bench_input.graph")
    Path(inp).write_text(text)

    stop = threading.Event()
    peak_rss = [0]
    proc_ref = {}

    def sampler():
        try:
            p = psutil.Process(proc_ref["pid"])
        except psutil.Error:
            return
        while not stop.is_set():
            try:
                peak_rss[0] = max(peak_rss[0], p.memory_info().rss)
            except psutil.Error:
                return
            time.sleep(0.0005)

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        [str(bin_path), inp, algo, str(alpha), str(beta)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    proc_ref["pid"] = proc.pid
    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    try:
        out, err = proc.communicate(timeout=120)
    finally:
        stop.set()
        th.join(timeout=5)
    wall = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"CLI failed for {algo}: {err}")
    return json.loads(out), wall, peak_rss[0]


def bootstrap_ci(values, iters=BOOTSTRAP_ITERS, seed=0):
    """95% percentile bootstrap CI for the mean of `values`."""
    import random
    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(iters):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[max(0, int(round(0.025 * (iters - 1))))]
    hi = means[min(iters - 1, int(round(0.975 * (iters - 1))))]
    return (lo, hi)


def run_benchmarks(quick=False, reps=DEFAULT_REPS):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / "benchmarks.csv"
    fields = ["family", "label", "n", "m", "algorithm", "alpha", "beta", "rep",
              "fill_count", "width", "fill_edges_added", "wall_s", "peak_rss_bytes"]

    with open(raw_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for family, label, n, text in instance_families(quick=quick):
            m = sum(1 for line in text.splitlines() if line.strip())
            for algo in ALGORITHMS:
                alpha, beta = alpha_beta(algo)
                # Deterministic algorithm: fill/width identical across reps; time/memory vary.
                fills, widths, times, rsses = [], [], [], []
                for rep in range(reps):
                    res, wall, rss = run_once(RUST_BIN, text, algo, alpha, beta)
                    fills.append(res["fill_count"])
                    widths.append(res["width"])
                    times.append(wall)
                    rsses.append(rss)
                # report the (constant) fill/width; time & memory aggregated later
                fill = fills[0]
                width = widths[0]
                for rep in range(reps):
                    writer.writerow({
                        "family": family, "label": label, "n": n, "m": m,
                        "algorithm": algo, "alpha": alpha, "beta": beta, "rep": rep,
                        "fill_count": fill, "width": width,
                        "fill_edges_added": fill,
                        "wall_s": round(times[rep], 6),
                        "peak_rss_bytes": rsses[rep],
                    })
                print(f"  {label} {algo}: fill={fill} width={width} "
                      f"time_mean={sum(times)/len(times):.4f}s "
                      f"rss_mean={sum(rsses)/len(rsses)/1e6:.1f}MB")

    print(f"\nRaw results -> {raw_path}")
    return raw_path


# ---------------------------------------------------------------------------
# processing
# ---------------------------------------------------------------------------

def process(raw_path):
    import statistics
    rows = []
    with open(raw_path) as f:
        for row in csv.DictReader(f):
            rows.append(row)

    # Group by (family, label, n, algorithm)
    groups = {}
    for r in rows:
        key = (r["family"], r["label"], int(r["n"]), r["algorithm"])
        groups.setdefault(key, []).append(r)

    summary_rows = []
    for key, recs in sorted(groups.items()):
        family, label, n, algo = key
        fill = int(recs[0]["fill_count"])
        width = int(recs[0]["width"])
        times = [float(x["wall_s"]) for x in recs]
        rsses = [int(x["peak_rss_bytes"]) for x in recs]
        t_lo, t_hi = bootstrap_ci(times)
        m_lo, m_hi = bootstrap_ci(rsses)
        summary_rows.append({
            "family": family, "label": label, "n": n, "algorithm": algo,
            "alpha": recs[0]["alpha"], "beta": recs[0]["beta"],
            "reps": len(recs),
            "fill_count": fill, "width": width,
            "time_mean_s": round(statistics.mean(times), 6),
            "time_ci_lo_s": round(t_lo, 6), "time_ci_hi_s": round(t_hi, 6),
            "rss_mean_bytes": round(statistics.mean(rsses), 1),
            "rss_ci_lo_bytes": round(m_lo, 1), "rss_ci_hi_bytes": round(m_hi, 1),
        })

    summary_path = PROC_DIR / "summary.csv"
    with open(summary_path, "w", newline="") as f:
        if summary_rows:
            w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            w.writeheader()
            w.writerows(summary_rows)
    print(f"Processed summary -> {summary_path}")

    # Relative to sare.
    by_instance = {}
    for r in summary_rows:
        by_instance.setdefault((r["family"], r["label"], r["n"]), {})[r["algorithm"]] = r
    rel_rows = []
    for inst, algs in by_instance.items():
        base = algs.get("sare")
        if not base:
            continue
        for algo in ("min-degree", "min-fill"):
            if algo not in algs:
                continue
            o = algs[algo]
            rel_rows.append({
                "family": inst[0], "label": inst[1], "n": inst[2],
                "baseline": algo,
                "fill_ratio_vs_sare": round(o["fill_count"] / base["fill_count"], 4)
                if base["fill_count"] else float("nan"),
                "width_ratio_vs_sare": round(o["width"] / base["width"], 4)
                if base["width"] else float("nan"),
                "time_ratio_vs_sare": round(o["time_mean_s"] / base["time_mean_s"], 4)
                if base["time_mean_s"] else float("nan"),
            })
    rel_path = PROC_DIR / "relative_to_sare.csv"
    with open(rel_path, "w", newline="") as f:
        if rel_rows:
            w = csv.DictWriter(f, fieldnames=list(rel_rows[0].keys()))
            w.writeheader()
            w.writerows(rel_rows)
    print(f"Relative summary -> {rel_path}")
    return summary_path, rel_path


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------

def make_figures(summary_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"matplotlib unavailable, skipping figures: {e}")
        return

    import csv
    rows = []
    with open(summary_path) as f:
        for row in csv.DictReader(f):
            rows.append(row)

    families = sorted({r["label"] for r in rows})
    algos = ["sare", "min-degree", "min-fill"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    x = range(len(families))
    width = 0.25
    for i, algo in enumerate(algos):
        vals = []
        for fam in families:
            recs = [r for r in rows if r["label"] == fam and r["algorithm"] == algo]
            vals.append(float(recs[0]["fill_count"]) if recs else 0)
        ax.bar([p + i * width for p in x], vals, width, label=algo)
    ax.set_xticks([p + width for p in x])
    ax.set_xticklabels(families, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("fill_count")
    ax.set_title("Fill-in by instance")
    ax.legend(fontsize=7)

    ax = axes[1]
    for i, algo in enumerate(algos):
        vals = []
        for fam in families:
            recs = [r for r in rows if r["label"] == fam and r["algorithm"] == algo]
            vals.append(float(recs[0]["time_mean_s"]) if recs else 0)
        ax.bar([p + i * width for p in x], vals, width, label=algo)
    ax.set_xticks([p + width for p in x])
    ax.set_xticklabels(families, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("time_mean_s")
    ax.set_title("Ordering time by instance")
    ax.legend(fontsize=7)

    fig.tight_layout()
    out = FIG_DIR / "fill_time_by_instance.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Figure -> {out}")

    # Relative fill ratio (baseline/sare): <1 means baseline uses less fill.
    fig, ax = plt.subplots(figsize=(8, 4))
    rel = []
    with open(PROC_DIR / "relative_to_sare.csv") as f:
        for row in csv.DictReader(f):
            rel.append(row)
    if rel:
        labels = [f"{r['label']}\n({r['baseline']})" for r in rel]
        ratios = [float(r["fill_ratio_vs_sare"]) if r["fill_ratio_vs_sare"] == r["fill_ratio_vs_sare"] else float("nan") for r in rel]
        ratios = [r if math.isfinite(r) else 1.0 for r in ratios]
        colors = ["green" if v < 1 else "red" for v in ratios]
        ax.bar(range(len(rel)), ratios, color=colors)
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
        ax.set_xticks(range(len(rel)))
        ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
        ax.set_ylabel("baseline fill / sare fill")
        ax.set_title("SARE fill relative to baselines (<1: baseline uses less fill)")
        fig.tight_layout()
        out = FIG_DIR / "sare_vs_baselines_fill.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"Figure -> {out}")


def main():
    parser = argparse.ArgumentParser(description="SARE benchmark runner")
    parser.add_argument("--quick", action="store_true", help="small quick benchmark set")
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS, help="repetitions per (instance, algorithm)")
    args = parser.parse_args()

    raw = run_benchmarks(quick=args.quick, reps=args.reps)
    summary_path, rel_path = process(raw)
    make_figures(summary_path)
    print("\nBenchmarking complete.")


if __name__ == "__main__":
    main()
