# Revision Log — SARE project

Internal adversarial review cycles. Each cycle: reviewer findings (critical/major/minor),
consolidated defect list, fixes applied, reassessment, regression tests added, reruns.

---

## Cycle 1 — reviews completed 2026-10-19

### Reviewer A (Mathematics) — findings
- CRITICAL: none. Theorems 1–5 correct and complete; no counterexample found.
- MAJOR: none.
- MINOR: (1) state explicitly that the fill model charges one edge per missing pair in the
  eliminated neighborhood (link to sparse Cholesky/LU). (2) boundary between proved and
  conjectured already explicit (docs/MATHEMATICAL_FOUNDATIONS.md §4).
- Resolution: added explicit fill-model note to docs/PROBLEM_DEFINITION.md §3. Docs already
  bound claims. No code change.

### Reviewer B (Algorithms) — findings
- CRITICAL: none.
- MAJOR: (1) Novelty MODERATE-HIGH risk — degree/fill greedy skeleton is standard (MD 1967,
  MMD 1985, AMD 1996, MF, composite-cost Bodlaender & Koster 2008, turbocharged IPEC 2016).
  Do NOT claim first-of-its-kind. (2) No practical advantage: SARE fill ≈ min-degree/min-fill
  (within ~7%, sometimes better sometimes worse), but SARE is SLOWER (min-degree up to ~76×
  faster on chordal_250). Do NOT claim Level A/B/C; recommend Level D.
- MINOR: AMD not directly benchmarked (min-degree/min-fill are stand-ins). Qualify baseline.
- Resolution: re-frame as Level D, bounded novelty. No code change; claims softened in
  FINAL_EVALUATION/README/paper.

### Reviewer C (Systems/Benchmarks) — findings
- CRITICAL: none.
- MAJOR: (1) single run per (instance, algorithm) — no repetition/CI. (2) no peak memory.
  (3) no real-world sparse matrices (synthetic only). (4) timings include subprocess startup.
  (5) result-to-commit traceability not established. (6) AMD not directly benchmarked.
- MINOR: no warm-up/cache policy documented; `nan` fill ratios honestly present.

### Fixes applied in Cycle 1 — COMPLETED (2026-10-19)
- [x] scripts/run_benchmarks.py: N repetitions (default 5), mean + 95% percentile-bootstrap CI
  for time and memory.
- [x] Peak memory (RSS) per run via psutil thread-based sampler (Windows-safe).
- [x] run_once rewritten: thread sampler + communicate(timeout=120) (fixes a Windows polling
  hang in the original psutil loop).
- [x] Realistic workloads added: poisson_2d (5-point stencil) and sparse_random (scipy).
- [x] Baseline qualified as stand-ins for AMD/MD/MF.
- [x] Full benchmark rerun: 18 instances × 6 algorithms × 5 reps; raw + processed + figures
  regenerated with CI.
- [ ] git init + commit + result-to-commit traceability (Stage 11).

### Reassessment after Cycle 1
Project remains Level D for performance, bounded (moderate) novelty. Contribution = a rigorous,
correct, verified adaptive elimination ordering with provably-zero-fill safe reductions,
honestly evaluated against classical heuristics. It does NOT beat min-degree/AMD. No pivot to
C4 (verified work preserved; C4 carries HSS prior-art risk).

---

## Cycle 2 (planned / in progress)
Final evaluation + scorecard (research/FINAL_EVALUATION.md), manuscript (paper/), README, CV
entry, project summary; Stage 11 GitHub publication; Stage 12 final audit.
