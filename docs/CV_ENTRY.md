# CV entry (verified, honest)

SARE — Independent Algorithm Research and Development
Independent research, October 2026. Author: Rajve (no institutional affiliation).
Source: https://github.com/rajveersinh-is-dev/sare

- Developed SARE (Safe-Reduction + Adaptive elimination ordering), a deterministic
  heuristic for computing vertex elimination orderings that reduce fill-in in sparse
  direct factorization (Cholesky/LU/QR).
- Proved correctness (valid ordering, exact fill/width reporting), provably-zero-fill
  safe degree-0/1 reductions, chordal completion (order is a perfect elimination
  ordering of the filled graph), and termination; derived worst-case/expected
  complexity bounds.
- Implemented in Rust (library + CLI) with an independent Python reference; verified
  with 55 tests including cross-language differential testing, brute-force optimum
  comparison (n ≤ 8), and chordal/PEO invariant checks.
- Benchmarked against minimum-degree and minimum-fill baselines over 18 instance
  families × 5 reps with 95% bootstrap confidence intervals and peak-memory
  measurement; raw data and regeneration script released.
- Measured result (evidence Level D): fill comparable to minimum degree/minimum fill
  (within ~7%, sometimes better/sometimes worse), but SARE is slower (minimum degree
  up to ~76× faster on some instances). No practical or theoretical advantage over
  established Approximate Minimum Degree was demonstrated. Reported honestly as such.
