# Novelty Assessment — Primary Target C1

Stage 3 of the research workflow. Candidate C1: "Adaptive elimination-ordering for treewidth /
fill-in reduction" — an elimination ordering driven by a potential function combining current
degree, current fill-in, and a lookahead estimate of future fill, with a switching rule and
safe reductions (simplicial / degree-0 / degree-1 vertices), producing a valid elimination
ordering and elimination tree.

## Screening decision
GO — proceed with C1 as primary, but with a **MODERATE-HIGH novelty risk** flagged and an
honest, bounded claim. C4 (low-rank incomplete-factorization preconditioner) remains the
documented backup and will be revisited if C1's mechanism is shown to be a routine variation
or shows no advantage.

Rationale: C1 has the highest weighted candidate-matrix score (6.7), the strongest and most
available baselines (AMD, minimum degree, minimum fill-in), and the best verifiability
(brute-force optimal fill-in on small graphs; differential vs. networkx). The core mechanism
(adaptive degree/fill ordering) overlaps with existing composite-cost greedy heuristics and
target-width turbocharged search, so I do NOT claim a novelty that the evidence does not
support. The defensible contribution, if any, is the specific combination:
(potential function + 1-step lookahead + safe reductions + rigorous correctness/complexity
+ honest empirical validation). This is assessed below.

---

## Closest prior methods — comparison table

| # | Closest prior method | Original reference | Mathematical mechanism | Complexity & assumptions | Known practical limitations | Exact proposed difference (C1) | Evidence difference not yet established | Distinguishing experiment / proof |
|---|----------------------|--------------------|------------------------|--------------------------|----------------------------|--------------------------------|----------------------------------------|-----------------------------------|
| 1 | Approximate Minimum Degree (AMD) | Amestoy, Davis, Duff, "An Approximate Minimum Degree Ordering Algorithm", SIAM J. Matrix Anal. Appl. 17(4):886–905, 1996; Algorithm 837, ACM TOMS 30(3), 2004 | Greedy elimination of a vertex with minimum *approximate external degree* (upper bound on true degree), using quotient-graph techniques; cheap degree bounds, often equal to actual degree | O(n·m) time (ARXIV 1907.12119), linear space; produces good fill in practice; no quality guarantee | Heuristic, myopic (one step), no performance guarantee; quality can vary by graph class | C1 uses a *combined potential* (degree + fill-in + 1-step lookahead) rather than degree alone, with safe reductions; not degree-only | AMD's degree-bound is itself a form of approximation; whether the combined potential + lookahead is new is unverified | Benchmark fill-in vs AMD on a diverse suite; prove C1's ordering is valid and its per-step cost; look for a graph family where C1 beats AMD consistently |
| 2 | Minimum Degree (MD) / Multiple Minimum Degree (MMD) | Tinney & Walker 1967; Liu, 1985 | Greedy elimination of minimum-degree vertex; MMD eliminates a maximal independent set of min-degree vertices per step | O(n·m) to O(n²m); widely used | Myopic; MMD O(n²m) slow; no guarantee | C1 adds fill-in and lookahead to the score; MD/MMD use degree only | Overlap is direct (degree-based greedy) | Same as above |
| 3 | Minimum Fill-in (MF) | Bodlaender & Koster, "Treewidth Computations I", UU-CS-2008-032, 2008 (and earlier) | Greedy elimination of vertex causing fewest fill edges | O(n³) naive; good fill quality | Slow; myopic; no guarantee | C1's potential includes fill but is adaptive with lookahead, not pure greedy fill | MF is the fill-in analogue; combined degree/fill greedy is discussed in Bodlaender & Koster | Same as above |
| 4 | Composite-cost greedy ordering | Bodlaender & Koster, "Treewidth Computations I", 2008 — Table 1 lists greedy orderings for criteria including a combined cost w_π·n² + Σ|N⁺_π(v)|² | Greedy ordering under a parameterized cost function combining treewidth-like and higher-neighbour terms | Heuristic; no guarantee | Explored combinations found not clearly competitive (GreedySparsestSubgraph not competitive) | C1's potential is dynamic (updated during elimination) with lookahead, not a static composite cost | Bodlaender & Koster already consider combined cost functions — direct overlap | Benchmark vs static composite; test whether dynamic lookahead adds value |
| 5 | Turbocharged Min-Degree / Min-Fill-in | "Turbocharging Treewidth Heuristics", IPEC 2016 | Target-width k search: extend a partial order while width ≤ k, else backtrack/re-order using GreedyDegree or GreedyFillIn | Exponential in k worst case; heuristic | Search can blow up; target-width framing | C1 is a *single-pass adaptive greedy* (no target-width backtracking), with a potential + lookahead | Overlap: both combine degree and fill heuristics | Benchmark vs turbocharged on target-width instances; show single-pass advantage where applicable |
| 6 | Best-First / Breadth-First Heuristic Treewidth (BestTW, BFHT) | "Best-First Search for Treewidth", AAAI 2007 | A*-style search over elimination orders with min-fill upper bound for pruning | Exponential; exact on hard graphs | Memory/time heavy; not a fast ordering heuristic | C1 is a fast single-pass heuristic, not exhaustive search | Different regime (exact vs heuristic) | Not a direct competitor; used only as small-graph optimum reference |
| 7 | ReFill (GNN+RL fill-in minimization) | "ReFill: Reinforcement Learning for Fill-In Minimization", arXiv:2501.16130, 2025 | Learned GNN policy predicts elimination orders, adapted per input | Learning-based; training overhead | ML-dependent, no guarantee, reproducibility/training cost | C1 is deterministic, no training, provably correct, with complexity bound | Different paradigm (ML vs deterministic) | Not a direct baseline; mention as related |

## Novelty risks (honest)

1. **Degree-based greedy overlap.** Minimum degree (1967), MMD (1985), and AMD (1996) already eliminate by a vertex score. C1's score differs (adds fill + lookahead) but the *greedy-elimination-by-score skeleton* is not new.
2. **Composite cost overlap.** Bodlaender & Koster (2008) already parameterize greedy orderings by combined cost functions. A dynamic potential is a variation on this theme.
3. **Target-width search overlap.** Turbocharging (IPEC 2016) already combines GreedyDegree and GreedyFillIn within a width-bounded search.
4. **No proof of absence.** The searches above are web searches of the literature; they do NOT prove that no equivalent potential-function elimination ordering exists, possibly under different vocabulary (e.g., in the graph-search, AI-planning, or VLSI literature).
5. **Guarantee is conjectural.** C1's claimed competitive/approx bound on a graph class is not yet proved; most heuristics (MD/MF/AMD) have no guarantee, and proving one is hard.

## Evidence that the difference has not (yet) been established
- No source found describes exactly: combined potential (degree + fill-in + 1-step lookahead) + safe simplicial/degree reductions + single-pass adaptive ordering + complexity analysis + empirical validation vs AMD.
- However, absence of evidence is not evidence of absence. The closest established mechanisms (AMD degree bound, composite-cost greedy, turbocharged degree/fill) cover much of the design space.

## Experiment or proof that would distinguish C1 from a routine variation
1. **Correctness proof:** C1 always returns a valid elimination ordering/elimination tree; safe reductions never increase optimal fill-in. (Provable.)
2. **Complexity:** per-step O(deg log n) with priority queues; total O((n+m) log n) plus lookahead cost. (Derivable.)
3. **Distinguishing experiment:** On a diverse benchmark suite (grids, random graphs, sparse matrices from SuiteSparse/University of Florida collection, chordal graphs, bounded-treewidth graphs), compare C1 vs AMD vs min-degree vs min-fill on: (a) fill-in count, (b) elimination-tree max clique / width, (c) ordering time. If C1 does NOT consistently beat AMD on fill-in or width, the practical-advantage claim fails and C1 is at best a routine variation — pivot to C4 or restate as Level D.
4. **Novelty claim to actually make (bounded):** "A deterministic adaptive elimination ordering with a combined degree/fill/lookahead potential and safe reductions, with rigorous correctness and complexity, empirically validated against AMD/min-degree/min-fill." Do NOT claim first-of-its-kind, do NOT claim asymptotic improvement, do NOT claim world's fastest.

## Go / No-Go
**GO (with bounded claims).** Proceed to Stage 4 (problem definition) and Stage 5 (proofs). Reassess novelty after the mechanism is fully specified: if the mechanism is shown to be a routine variation of AMD/composite-cost/turbocharged, OR if benchmarks show no advantage over AMD, then either (a) pivot to backup C4, or (b) restate C1 as Level D (correct, interesting, unconfirmed advantage) and report honestly in FINAL_EVALUATION.
