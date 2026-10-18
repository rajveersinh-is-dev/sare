# Research Progress Log

Last updated: 2026-10-19

## Current stage
Stage 9 — Three-persona adversarial reviews (written); beginning revision loop #1.

## Completed stages
Stage 1 (environment), Stage 2 (candidate matrix, 12 candidates), Stage 3 (novelty assessment: C1 = GO),
Stage 4 (problem definition + algorithm spec), Stage 5 (formal proofs: 5 theorems proved, bounds delimited),
Stage 6 (Rust lib+CLI + Python reference, 55 passing tests incl. cross-language differential + brute-force +
chordal invariant), Stage 7 (benchmark suite: 8 families x 6 algorithms, raw+processed+figures).

## Evidence established
- OS: Windows 11 Home 64-bit (10.0.22631); CPU: 11th Gen Intel i5-11260H 6c/12t @2.60GHz; RAM ~15.7 GiB;
  GPU: Intel UHD + NVIDIA RTX 3050 Laptop (core kept on CPU for fair comparison).
- Python 3.14.6 full scientific stack; Rust 1.98.1; GitHub CLI authenticated as `daveaddams91-dev`.
- C1 = SARE (Safe-Reduction + Adaptive elimination ordering). Fully implemented and verified.
- Honest benchmark finding: SARE fill ≈ min-degree/min-fill (1-4% better on some sparse random graphs,
  equal elsewhere), but SARE is SLOWER (min-degree up to ~18x faster on er_sparse_300).
  => No clear practical advantage over min-degree/AMD. Performance claim = Level D (unconfirmed).

## Decision
Complete C1 (SARE) as primary, reported honestly at its evidenced level. Do NOT pivot to C4 (would discard
verified work; C4 carries HSS/H-matrix prior-art risk). C1's defensible contribution: rigorous correctness
(5 proved theorems), provably-zero-fill safe reductions, documented adaptive decision rule; honestly evaluated.
Performance = Level D. Novelty = moderate (bounded claims, no first-of-its-kind claim).

## Next actions
1. Write three adversarial reviews (reviews/REVIEW_MATHEMATICS.md, REVIEW_ALGORITHMS.md, REVIEW_BENCHMARKS.md).
2. Revision log + fixes (reviews/REVISION_LOG.md).
3. Final evaluation + scorecard (research/FINAL_EVALUATION.md).
4. Manuscript (paper/), README, CV entry, project summary.
5. GitHub repo creation + push under daveaddams91-dev; final audit.
