# Literature Review & Evidence Ledger

## Stage 1 — Environment & Ledger

### Research environment (verified)
- OS: Windows 11 Home 64-bit (build 10.0.22631)
- CPU: 11th Gen Intel Core i5-11260H @ 2.60 GHz, 6 cores / 12 logical processors
- RAM: 16,893,382,656 bytes (~15.7 GiB)
- GPU: Intel UHD Graphics + NVIDIA GeForce RTX 3050 Laptop GPU (CUDA toolkit 12.9 present).
  Decision: keep the algorithmic core on CPU so baseline comparisons are fair and hardware
  requirements modest; GPU not required for the central contribution.
- Python 3.14.6: numpy 2.4.6, scipy 1.18.0, matplotlib 3.11.1, networkx 3.6.1,
  sympy 1.14.0, pandas 3.0.5, cvxpy 1.9.3, clarabel 0.11.1, gmpy2, duckdb
- Rust 1.98.1 + cargo
- .NET 8.0.418, Node 24.18.0
- Git + GitHub CLI (`gh`) authenticated as `daveaddams91-dev` (scopes: gist, read:org,
  repo, user, workflow; token in keyring). Default account `Raj123-0` is invalid and unused.
- Network to github.com: reachable (TCP/443 OK).
- Working directory `C:\Users\davea\Downloads\ee` is empty and not a git repo.

### Search log
Each literature search performed during candidate selection and novelty screening is
recorded below with date, query, source, and outcome.

| # | Date (UTC) | Query | Source | Outcome |
|---|------------|-------|--------|---------|
| 1 | 2026-10-18 | Approximate Minimum Degree algorithm AMD Amestoy Davis Duff sparse Cholesky elimination ordering | websearch | Established AMD (SIAM MAXA 1996, Algorithm 837 2004), MMD (Liu 1985), MD (Tinney & Walker 1967), Minimum Fill-in, Nested Dissection/METIS as baselines for elimination ordering / fill-in reduction. |
| 2 | 2026-10-18 | minimum degree minimum fill elimination ordering treewidth heuristic lookahead graph algorithm | websearch | Found BestTW/BFHT (AAAI 2007), Turbocharging Treewidth Heuristics (IPEC 2016 — GreedyDegree/GreedyFillIn + target-width search), Bodlaender & Koster "Treewidth Computations I" (2008 — composite cost functions), ReFill (2025 — ML/GNN fill-in), "Fast Minimum Degree" (arXiv 1907.12119, 2020). Confirms C1 novelty is HIGH RISK: adaptive degree/fill ordering with search is well explored. |
| 3 | 2026-10-18 | low rank incomplete Cholesky preconditioner hierarchical off-diagonal blocks conjugate gradient convergence bound | websearch | Found HSS/HODLR preconditioners (2021 arxiv 2011.07632), H-matrix preconditioners, incomplete Cholesky/CG literature (Meijerink & van der Vorst 1978, van der Vorst 1989). C4 novelty is MEDIUM risk: hierarchical low-rank preconditioners exist; simple tunable variant with rigorous bound less standard. |

### Existing algorithms and guarantees captured
*(Populated during candidate scoring.)*

### Known limitations / competing methods / novelty conflicts
*(Populated during novelty assessment.)*

### Unresolved novelty questions
*(Populated during novelty assessment — see research/NOVELTY_ASSESSMENT.md.)*

### Source-quality note
Only primary sources (peer-reviewed papers, conference proceedings, established textbooks,
official documentation, primary implementation repositories) are relied upon. Brief web
searches are not treated as proof of absence of prior work. Any source that cannot be
verified is marked "unverified" and not used as a decisive fact.
