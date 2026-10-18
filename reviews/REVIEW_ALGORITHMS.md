# Adversarial Review B — Algorithms & Complexity Researcher

Project: SARE (Safe-Reduction + Adaptive elimination ordering), candidate C1.
Reviewer persona: algorithms and complexity researcher.
Mandate: identify closest known algorithms/results; challenge novelty; check whether the alleged
improvement is real and correctly characterized; look for stronger competitors and lower bounds;
assess behavior across input regimes; decide new contribution vs. routine combination; recommend
the strongest defensible claim.
Label: INTERNAL ADVERSARIAL REVIEW (not peer review).

---

## 1. Closest known algorithms

The literature review (research/LITERATURE_REVIEW.md) and novelty assessment identify:

- Minimum Degree (MD): Tinney & Walker, 1967.
- Multiple Minimum Degree (MMD): Liu, 1985.
- Approximate Minimum Degree (AMD): Amestoy, Davis, Duff, SIAM MAXA 1996; Algorithm 837, ACM
  TOMS 2004. The strongest widely used practical baseline (SuiteSparse, SciPy).
- Minimum Fill-in (MF): Bodlaender & Koster, "Treewidth Computations I", 2008.
- Nested Dissection / METIS.
- Turbocharging Treewidth Heuristics (GreedyDegree + GreedyFillIn, target-width search): IPEC 2016.
- BestTW / BFHT (A*-style elimination-order search): AAAI 2007.
- Composite-cost greedy orderings: Bodlaender & Koster 2008 (Table 1).
- ReFill (GNN+RL fill minimization): arXiv:2501.16130, 2025.

AMD is the appropriate strongest practical baseline. SARE is compared against min-degree and
min-fill (clean reimplementations), which are reasonable proxies for AMD/MD/MF. Note: AMD itself
was not directly benchmarked (SuiteSparse AMD not readily wired in); min-degree/min-fill are
stand-ins. This is a benchmark limitation (see Reviewer C).

## 2. Novelty challenge

SARE's mechanism: Phase A (safe degree-0/1 reductions, zero fill) + Phase B (greedy choice by
score = degree + alpha·fill + beta·lookahead).

**The degree/fill greedy skeleton is NOT new.** Minimum degree (1967), MMD (1985), AMD (1996),
minimum fill-in, and composite-cost greedy (Bodlaender & Koster 2008) all eliminate by a vertex
score. Turbocharging (IPEC 2016) already combines GreedyDegree and GreedyFillIn. The specific
combination (safe reductions up front + degree/fill/lookahead potential + alpha/beta switching)
is a variation on this established design space, not a clearly new mathematical mechanism.

**Novelty risk: MODERATE-HIGH.** It is plausible that an equivalent potential-function elimination
ordering exists under different vocabulary. The assessment honestly does not claim first-of-its-kind.

**What IS specific/documented:** the exact potential function, the safe-reduction phase, the
alpha/beta decision rule, the rigorous correctness/complexity treatment, and the honest empirical
evaluation. These are engineering/documentation contributions more than a new mathematical
primitive.

## 3. Is the alleged improvement real?

**No clear improvement is demonstrated.** The benchmarks (results/processed/relative_to_sare.csv)
show:

| Instance | baseline | fill ratio (baseline/SARE) | time ratio (baseline/SARE) |
|----------|----------|---------------------------|----------------------------|
| er_sparse_300 | min-degree | 1.073 (baseline 7% MORE fill) | 0.056 (baseline ~18x FASTER) |
| grid_256 | min-degree | 1.043 | 0.528 (baseline ~2x FASTER) |
| er_dense_80 | min-degree | 0.961 (baseline LESS fill) | 0.518 |
| chordal_250 | min-degree | 1.002 | 0.013 (min-degree ~78x FASTER) |
| most others | — | ~1.0 (equal) | <1 (min-degree faster) |

Interpretation: SARE's fill is roughly EQUAL to min-degree/min-fill, occasionally 1–4% better on
some sparse random graphs, occasionally equal or marginally worse. SARE is consistently SLOWER
than min-degree (often an order of magnitude). min-fill is sometimes slightly better than SARE in
fill (e.g., er_dense_80: baseline fill ratio 0.966).

**Conclusion: SARE does not demonstrate a practical advantage over the strongest baseline.**
min-degree (a stand-in for AMD) is faster and equal-or-better in fill on essentially all tested
instances. There is no regime in the tested suite where SARE clearly dominates on the
fill/time tradeoff.

**The empirical advantage claim is NOT supported.** At most, SARE matches min-degree in fill
quality while costing more time.

## 4. Behavior across regimes

SARE behaves consistently (not disastrously) across paths, cliques, stars, trees, grids, Erdős-
Rényi (sparse/dense), chordal. No catastrophic regime found. But no regime where it clearly wins
either. The alpha/beta ablation shows lookahead sometimes HURTS (chordal_60: sare-lookahead fill
509 vs sare 488). So the "lookahead" mechanism is not reliably beneficial.

## 5. Lower bounds / barriers

Minimum fill-in is NP-hard; treewidth is NP-hard; no constant-factor polynomial approximation is
known. SARE correctly does not attempt to surmount these. No lower bound on greedy ordering
quality is proved or claimed. Fine.

## 6. Strongest defensible claim

SARE is a correct, deterministic adaptive elimination ordering with provably-zero-fill safe
reductions and a tunable degree/fill/lookahead decision rule, with rigorous correctness and
complexity, evaluated against min-degree/min-fill. It is NOT faster and NOT clearly better in
fill than min-degree/AMD.

**Recommended scientific level: Level D** — correct and interesting, but available evidence does
NOT establish state-of-the-art performance or a major theoretical advantage. Do NOT claim Level
A, B, or C.

## 7. Verdict for this persona

The novelty claim should be bounded (no first-of-its-kind). The performance advantage claim should
be withdrawn or severely qualified: the evidence shows comparability at best, with a time
disadvantage. The strongest defensible statement is Level D.

If the project is to be presented as research, it should be framed as "a rigorously specified and
verified adaptive elimination ordering with safe reductions, empirically benchmarked against
classical heuristics," with honest reporting that it does not beat min-degree/AMD. That is a
legitimate Level D artifact, not a breakthrough.
