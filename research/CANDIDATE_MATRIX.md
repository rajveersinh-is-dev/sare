# Candidate Research Targets — Scoring Matrix

Stage 2 of the research workflow. Twelve meaningfully distinct candidate problems across
graph algorithms, strings, numerical linear algebra, symbolic computation, optimization,
algebra, geometry, and streaming. Each candidate is scored 1–10 on the eight weighted
dimensions and given a weighted total.

Weights: mathematical novelty 20%, practical importance 15%, theoretical contribution 15%,
plausible performance advantage 15%, baseline strength/availability 10%, verification
feasibility 10%, implementation feasibility 10%, academic/portfolio value 5%.

A score is a research-planning judgment, not empirical proof. For each candidate I state
the evidence, uncertainty, and the main reason the score might be wrong.

---

## C1 — Adaptive elimination-ordering for treewidth / fill-in (Graph algorithms)

1. **Problem:** Given an undirected graph G=(V,E), produce a vertex elimination ordering
   minimizing fill-in / maximum clique size (equivalently, approximate treewidth and a
   tree decomposition). Input: graph with n vertices, m edges. Output: elimination ordering
   and elimination tree. Correctness: ordering is a permutation of V; the elimination
   process fills edges between later neighbors of each eliminated vertex.
2. **Why it matters:** Elimination ordering dominates cost of sparse Cholesky, variable
   elimination in graphical models, constraint propagation, and exact inference. Used in
   CAD, VLSI, scientific computing, probabilistic graphical models.
3. **Strongest known:** Minimum Degree (MD), Minimum Fill (MF), Approximate Minimum Degree
   (AMD — Amestoy/Davis/Duff, in SuiteSparse), plus PACE exact/heuristic treewidth solvers
   (branch-and-bound, reduction rules). AMD is the strong practical baseline.
4. **Bottleneck:** MD/MF/AMD are greedy, myopic, no performance guarantee; exact treewidth
   is NP-hard and PACE solvers are heavy. No widely used adaptive method with a provable
   bound plus strong practical quality.
5. **Insight:** An adaptive ordering driven by a potential function that upper-bounds the
   final clique size, with a rigorous switching rule between MD-like and MF-like choices
   and lookahead; provable competitive bound on a natural graph class (e.g., chordal or
   bounded-treewidth graphs) plus strong empirical quality.
6. **Guarantee:** Correctness (permutation, valid elimination tree) is provable; a
   competitive/approx bound on a restricted class is conjectural; space O(n+m), per-step
   O(deg) with priority queues.
7. **Advantage:** Better fill-in quality per unit time than AMD on a defined suite; clear
   break-even (preprocessing cost vs. downstream factorization savings).
8. **Baselines:** networkx (chordal/treewidth helpers), SuiteSparse AMD (via scikit-sparse
   if available or reimplement), a clean hand-written min-fill/min-degree. Strong baselines
   exist; AMD is mature.
9. **Verification:** Exhaustive small-graph comparison to brute-force optimal fill-in;
   differential test against networkx; invariant checks on elimination tree.
10. **Novelty risk:** Elimination-ordering heuristics are heavily published (AMD, multiple
    lookahead variants, "minimum fill with degree tie-break"). Risk the adaptive rule is a
    routine variation. MEDIUM-HIGH.
11. **Falsification:** If the new ordering never beats AMD on fill-in or time across a
    diverse suite, the advantage claim fails.
12. **Feasible without proprietary/inaccessible:** Yes. Pure graph algorithms, CPU.

**Rubric scores:** novelty 5, importance 8, theory 6, advantage 6, baselines 8, verification
8, implementation 8, academic 6.
**Weighted total:** 0.20·5 + 0.15·8 + 0.15·6 + 0.15·6 + 0.10·8 + 0.10·8 + 0.10·8 + 0.05·6
= 1.0 + 1.2 + 0.9 + 0.9 + 0.8 + 0.8 + 0.8 + 0.3 = **6.7/10**

**Major reason score might be wrong:** The adaptive rule could be a routine variant of
existing lookahead/degree heuristics, collapsing novelty; or AMD could be unbeatable on
practical instances, collapsing the advantage.

---

## C2 — Maximum Weight Independent Set via new measure-and-conquer branching (Graph, exact exponential)

1. **Problem:** Given an undirected graph G=(V,E) with vertex weights w(v) ≥ 0, find an
   independent set S of maximum total weight. Output: S and its weight. NP-hard.
2. **Why it matters:** Scheduling, resource allocation, coding theory, molecular
   biology, scheduling; a canonical NP-hard problem with many applications.
3. **Strongest known:** Branch-and-reduce with measure-and-conquer (best exact algorithms
   ~O(1.1996^n) for unweighted MWIS; variants for bounded degree), MaxSat/ILP solvers
   (CP-SAT, branch-and-bound), bitset-based branch and bound (Tomita-style for clique,
   dual for independent set).
4. **Bottleneck:** Exponential; best algorithms rely on intricate reduction rules.
   Implementation complexity high; little published on *weighted* MWIS with new reductions.
5. **Insight:** A new set of safe reduction rules specific to weighted graphs (e.g., handling
   weight-dominated vertices, twin vertices, degree-2 chains with weights) combined with a
   measure-and-conquer analysis giving a provably smaller recurrence base on weighted
   instances.
6. **Guarantee:** Correctness of each reduction rule provable; exponential time bound
   O(c^n) with c derived from recurrence; space polynomial.
7. **Advantage:** Smaller search tree than plain branch-and-bound on weighted instances;
   competitive with CP-SAT on a defined class (e.g., sparse random graphs).
8. **Baselines:** networkx approximation (no exact), a hand-written branch-and-bound,
   OR-Tools CP-SAT (strong, installable via pip? ortools may not be installed — check).
   Baseline strength moderate; CP-SAT is strong but may not be available.
9. **Verification:** Brute-force on n ≤ 25 exhaustive; differential vs CP-SAT and vs
   brute force on random graphs; invariant: returned set is independent and weight optimal
   on small cases.
10. **Novelty risk:** Measure-and-conquer branching is a mature technique; new reduction
    rules are published regularly (e.g., for Vertex Cover, Independent Set). Risk the
    rules already exist. MEDIUM-HIGH.
11. **Falsification:** If a reduction rule is unsafe (produces suboptimal result) caught by
    brute-force differential, the approach collapses; if search tree not smaller, no
    advantage.
12. **Feasible without proprietary/inaccessible:** Yes. CP-SAT may be unavailable; then
    baselines are hand-written (acceptable but weaker).

**Rubric scores:** novelty 5, importance 7, theory 7, advantage 5, baselines 5, verification
8, implementation 7, academic 6.
**Weighted total:** 1.0+1.05+1.05+0.75+0.5+0.8+0.7+0.3 = **6.15/10**

**Major reason score might be wrong:** Baseline weakness (no CP-SAT) makes advantage
claims soft; measure-and-conquer is saturated, so novelty is fragile.

---

## C3 — Grammar-compression index for highly repetitive texts (Strings)

1. **Problem:** Given a text T of length n that is highly repetitive (e.g., versioned
   collections, genomic databases), build a compressed index supporting count/locate
   queries for a pattern P of length m. Output: number/positions of occurrences. Exploit
   repetitiveness rather than raw length.
2. **Why it matters:** Genomics, version control, text databases, compressed data
   structures. Repetitive-text indexing is a recognized, active area (r-index, grammar
   compressors, Re-Pair).
3. **Strongest known:** r-index (Gagie et al.), grammar-based indexes (Re-Pair, LZ77-based
   indexes), BWT-based indexes. Re-Pair grammar construction is the classic practical
   method; smallest grammar is NP-hard.
4. **Bottleneck:** Existing indexes are complex; space depends on number of runs / grammar
   size; construction can be slow; query tradeoffs fixed.
5. **Insight:** A new grammar transform (a variant of Re-Pair with a global re-pairing /
   lookahead rule) producing a smaller grammar for highly repetitive texts, with a
   provable worst-case grammar-size bound and a direct index on top.
6. **Guarantee:** Correctness of index (occurrences reported exactly) provable;
   grammar-size bound conjectural; construction O(n log n) or O(n), query O(m + occ).
7. **Advantage:** Smaller space and/or faster construction/query on repetitive corpora
   vs. Re-Pair/r-index implementations.
8. **Baselines:** A hand-built Re-Pair index and a suffix-array baseline; r-index
   implementations are complex and may not be readily available. Baseline strength
   moderate-to-weak unless a reference Re-Pair implementation is carefully built.
9. **Verification:** Differential: index results vs. naive substring search on random and
   repetitive strings; exhaustive on small alphabets/lengths; invariant on grammar
   (derives exactly T).
10. **Novelty risk:** Grammar compression and Re-Pair variants are extensively published
    (Re-Pair 1999; Larroque, Navarro, etc.). Risk the transform is routine. MEDIUM.
11. **Falsification:** If grammar not smaller on a diverse repetitive corpus, or index
    incorrect vs. naive search, fails.
12. **Feasible without proprietary/inaccessible:** Yes. Pure string algorithms.

**Rubric scores:** novelty 5, importance 6, theory 5, advantage 5, baselines 5, verification
8, implementation 7, academic 5.
**Weighted total:** 1.0+0.9+0.75+0.75+0.5+0.8+0.7+0.25 = **5.65/10**

**Major reason score might be wrong:** Re-Pair variants are well-trod; novelty fragile;
baselines (r-index) hard to obtain, weakening comparison.

---

## C4 — Incomplete-factorization preconditioner with low-rank off-diagonal blocks (Numerical linear algebra)

1. **Problem:** Given a sparse symmetric positive definite (SPD) matrix A, construct a
   preconditioner M ≈ A for the Conjugate Gradient method exploiting low-rank structure
   of off-diagonal blocks (hierarchical / H-matrix style incomplete Cholesky). Output:
   preconditioner; use in CG to solve Ax=b to tolerance.
2. **Why it matters:** Sparse linear solves are ubiquitous (FEM, structural mechanics,
   optimization, machine learning). Preconditioner quality dominates CG iterations.
3. **Strongest known:** Incomplete Cholesky (IC(0), ICC), algebraic multigrid (AMG),
   H-matrix / H²-matrix preconditioners, sparse approximate inverse (SPAI).
4. **Bottleneck:** IC(0) ignores fill and can be a poor preconditioner; full Cholesky too
   expensive; AMG setup complex and parameter-heavy; H-matrix preconditioners have high
   constant and complex implementation.
5. **Insight:** A *simple, tunable* incomplete factorization that compresses off-diagonal
   blocks via low-rank approximation (randomized or deterministic SVD) with a rigorous
   bound on the preconditioned condition number κ(M^{-1}A) for a matrix class (e.g.,
   diagonally dominant / M-matrices / graph Laplacians), giving a provable CG iteration
   bound.
6. **Guarantee:** Correctness (M SPD, CG converges) provable; condition-number bound
   conjectural for the class; CG iterations ≤ O(√κ log(1/ε)) (standard CG theory).
7. **Advantage:** Fewer CG iterations than IC(0)/Jacobi on matrices with low-rank
   off-diagonal blocks, at acceptable setup cost; clear break-even vs. problem size.
8. **Baselines:** scipy.sparse.linalg (cg, spilu, jacobi), a hand-built IC(0). Strong,
   available baselines.
9. **Verification:** Check M SPD, residual ||Ax-b||, convergence vs. scipy cg/spilu on
   generated SPD matrices (2D/3D Poisson, random diagonally dominant, graph Laplacians);
   numerical stability tests.
10. **Novelty risk:** Low-rank/H-matrix preconditioners exist; a *simple tunable* variant
    with a clean bound may still be novel, but risk of duplication is MEDIUM.
11. **Falsification:** If iteration count not lower than spilu/IC(0) at comparable setup
    cost, or bound false on adversarial SPD matrices, fails.
12. **Feasible without proprietary/inaccessible:** Yes. numpy/scipy.

**Rubric scores:** novelty 5, importance 8, theory 6, advantage 6, baselines 8, verification
8, implementation 7, academic 6.
**Weighted total:** 1.0+1.2+0.9+0.9+0.8+0.8+0.7+0.3 = **6.6/10**

**Major reason score might be wrong:** H-matrix preconditioners already exist (novelty);
or the low-rank block approach doesn't beat spilu in practice (advantage).

---

## C5 — Distance oracle / approximate APSP for sparse unweighted graphs (Graph algorithms)

1. **Problem:** Given an unweighted undirected graph G=(V,E), build a data structure
   answering approximate distance queries d̂(u,v) with stretch α (d(u,v) ≤ d̂(u,v) ≤
   α·d(u,v)) using small space and fast query. Input: graph, stretch parameter.
2. **Why it matters:** Network analysis, routing, transportation, social networks —
   distance queries at scale where APSP is too expensive.
3. **Strongest known:** Thorup–Zwick distance oracle (stretch 2k−1, space O(k·n^{1+1/k}),
   query O(k)); Baswana–Sen; Pippenger. For sparse graphs, space-query tradeoffs well
   studied.
4. **Bottleneck:** Thorup–Zwick is near-optimal in the tradeoff space; improvements are
   marginal; construction O(kmn^{1/k}) can be slow.
5. **Insight:** A new construction trading a small constant-factor stretch increase for
   substantially lower construction time and space on *sparse* graphs, with a rigorous
   stretch/space bound; an adaptive sampling scheme.
6. **Guarantee:** Stretch bound provable; space/query bounds provable; construction time
   bound derivable.
7. **Advantage:** Faster construction and lower space than Thorup–Zwick on sparse graphs
   at the same stretch, with query time competitive.
8. **Baselines:** hand-built Thorup–Zwick (complex but doable), BFS-from-source baseline
   (exact, O(m) per query), networkx all-pairs for correctness on small graphs. Baseline
   strength moderate.
9. **Verification:** Differential vs. exact BFS distances on random/sparse graphs for
   stretch correctness; exhaustive on small graphs; query-time benchmarks.
10. **Novelty risk:** Distance oracles are a mature field (Thorup–Zwick 2001, many
    followups). Risk a stretch/space tradeup already exists. MEDIUM-HIGH.
11. **Falsification:** If stretch violated (verified vs BFS), or space/construction not
    better than TZ at same stretch, fails.
12. **Feasible without proprietary/inaccessible:** Yes.

**Rubric scores:** novelty 4, importance 7, theory 6, advantage 5, baselines 6, verification
8, implementation 6, academic 5.
**Weighted total:** 0.8+1.05+0.9+0.75+0.6+0.8+0.6+0.25 = **5.75/10**

**Major reason score might be wrong:** Thorup–Zwick is essentially optimal; novelty and
advantage both fragile.

---

## C6 — Output-sensitive Longest Common Subsequence for sparse match sets (Strings)

1. **Problem:** Given two strings X (length n) and Y (length m), compute LCS length. Exploit
   sparsity of the match set M = {(i,j): X[i]=Y[j]}. Output: LCS length (and optionally
   the sequence).
2. **Why it matters:** Diff tools, version control, bioinformatics, plagiarism detection,
   sequence comparison.
3. **Strongest known:** O(nm) dynamic programming; Hunt–Szymanski O((n+r) log n) where
   r = |M| (output/input-sensitive); Myers; suffix-tree methods.
4. **Bottleneck:** Hunt–Szymanski is strong when matches are sparse but has a log factor
   and can degrade when r is large; no widely used adaptive method switching between DP
   and match-sensitive methods based on measured r.
5. **Insight:** An adaptive LCS algorithm that estimates r (sampled matches) and selects
   DP vs. Hunt–Szymanski vs. a new block-based match method via a provably near-optimal
   switching rule; rigorous bound O(min(nm, (n+r) polylog n)) with better constants.
6. **Guarantee:** Correctness (exact LCS) provable for each component and for the switch;
   complexity bound derivable.
7. **Advantage:** Faster than both pure DP and pure Hunt–Szymanski across match-density
   regimes; clear break-even in r.
8. **Baselines:** O(nm) DP (trivial, correct), Hunt–Szymanski implementation, difflib
   (Python, heuristic). Strong correctness baseline; HS needs careful implementation.
9. **Verification:** Differential vs. O(nm) DP on random strings (exhaustive small,
   randomized medium); invariant: LCS length consistent.
10. **Novelty risk:** Hunt–Szymanski and adaptive LCS variants exist; the switching rule
    may be routine. MEDIUM.
11. **Falsification:** If not faster than HS across regimes, or incorrect vs DP, fails.
12. **Feasible without proprietary/inaccessible:** Yes.

**Rubric scores:** novelty 4, importance 6, theory 5, advantage 5, baselines 7, verification
9, implementation 7, academic 4.
**Weighted total:** 0.8+0.9+0.75+0.75+0.7+0.9+0.7+0.2 = **5.7/10**

**Major reason score might be wrong:** Hunt–Szymanski already covers sparse matches;
adaptive switching is engineering, not novel algorithmics.

---

## C7 — Sparse polynomial interpolation (Symbolic computation)

1. **Problem:** Given black-box evaluation of a multivariate polynomial f over a finite
   field with at most t nonzero terms but unknown support, recover f (coefficients +
   exponents). Input: evaluation oracle, t bound.
2. **Why it matters:** Computer algebra, coding theory, cryptography, symbolic
   computation; sparse interpolation is a classical problem.
3. **Strongest known:** Zippel's probabilistic algorithm; Ben-Or/Tiwari deterministic
   for known bounds; sparse FFT-based methods; recent work on sparse interpolation with
   noise/errors.
4. **Bottleneck:** Zippel needs O(t) evaluations and field operations; Ben-Or/Tiwari need
   a large field / primitive root; practical implementations limited.
5. **Insight:** A new interpolation algorithm reducing evaluation count or field-size
   requirements using a new evaluation-point design (e.g., based on a new Kronecker
   substitution or a new subgroup structure), with a rigorous bound.
6. **Guarantee:** Correct recovery provable (with high probability or deterministically);
   evaluation and operation bounds derivable.
7. **Advantage:** Fewer black-box evaluations than Zippel on a defined class (e.g.,
   polynomials over small fields).
8. **Baselines:** hand-built Zippel and Ben-Or/Tiwari; sympy has interpolation but not
   black-box sparse multivariate. Baseline strength moderate.
9. **Verification:** Recover known sparse polynomials exactly; exhaustive over small
   fields/small t; differential vs. Zippel.
10. **Novelty risk:** Sparse interpolation is classical and heavily studied (Zippel 1979,
    Ben-Or/Tiwari 1988, many followups). High risk the idea exists. HIGH.
11. **Falsification:** If recovery fails or evaluation count not better than Zippel, fails.
12. **Feasible without proprietary/inaccessible:** Yes. Finite-field arithmetic in Python.

**Rubric scores:** novelty 3, importance 5, theory 6, advantage 4, baselines 5, verification
8, implementation 6, academic 4.
**Weighted total:** 0.6+0.75+0.9+0.6+0.5+0.8+0.6+0.2 = **4.95/10**

**Major reason score might be wrong:** Field is saturated; novelty unlikely; niche
importance lowers score.

---

## C8 — Feedback Vertex Set via new FPT branching / reduction rules (Graph, parameterized)

1. **Problem:** Given an undirected graph G=(V,E) and integer k, delete at most k vertices
   to make G acyclic (a feedback vertex set of size ≤ k). Output: FVS or report none.
   Parameterized by k; FPT.
2. **Why it matters:** Deadlock detection, circuit design, program analysis, combinatorial
   optimization; canonical parameterized problem.
3. **Strongest known:** FPT algorithms O(c^k · n^{O(1)}) with c ≈ 3.619 (and
   improvements); kernelization to O(k^2) vertices; ILP/CP-SAT formulations.
4. **Bottleneck:** Exponential in k; reduction rules and branching intricate.
5. **Insight:** A new safe reduction rule (e.g., handling degree-2 vertices with weights,
   or a new crown/reduction) combined with branching giving a smaller recurrence base c,
   with rigorous analysis.
6. **Guarantee:** Correctness (FVS valid, minimal) provable; FPT time bound O(c^k poly(n))
   derivable from recurrence.
7. **Advantage:** Solves larger k instances than plain branching on a defined graph class.
8. **Baselines:** hand-written branch-and-bound FVS, ILP via scipy.optimize milp (available
   in scipy 1.18!), networkx approximation (no exact FPT). scipy MILP is a strong exact
   baseline.
9. **Verification:** Brute-force/differential vs. scipy MILP and vs. brute force on small
   graphs; invariant: deleting returned set leaves a forest; size ≤ k.
10. **Novelty risk:** FVS FPT is heavily published (Chen et al., many reduction rules).
    Risk a new rule already exists. MEDIUM-HIGH.
11. **Falsification:** If reduction rule unsafe (brute force catches), or recurrence base
    not smaller than known, fails.
12. **Feasible without proprietary/inaccessible:** Yes. scipy MILP available.

**Rubric scores:** novelty 4, importance 6, theory 6, advantage 5, baselines 7, verification
8, implementation 6, academic 5.
**Weighted total:** 0.8+0.9+0.9+0.75+0.7+0.8+0.6+0.25 = **5.7/10**

**Major reason score might be wrong:** FVS FPT saturated; scipy MILP baseline is strong,
limiting measurable advantage.

---

## C9 — Approximation for Densest k-Subgraph (Optimization)

1. **Problem:** Given a graph G=(V,E) and integer k, find k vertices inducing the maximum
   number of edges. Output: vertex set of size k. NP-hard, hard to approximate.
2. **Why it matters:** Community detection, bioinformatics, social network analysis.
3. **Strongest known:** Approximation algorithms (n^{1/4+ε}-type), LP/SDP relaxations,
   greedy heuristics; best polynomial approximation remains weak (no constant factor
   known under standard assumptions).
4. **Bottleneck:** No good polynomial approximation; exact is exponential.
5. **Insight:** A new rounding scheme or combinatorial algorithm with a better
   approximation guarantee on a restricted but important class (e.g., graphs with bounded
   degree, or power-law graphs).
6. **Guarantee:** Approximation factor provable for the class; runtime polynomial.
7. **Advantage:** Better solution quality than greedy/LP on the target class.
8. **Baselines:** greedy, LP relaxation (scipy/cvxpy), random. Baselines available but
   weak (which makes advantage claims easier but less impressive).
9. **Verification:** Verify feasibility (|S|=k) and edge count; compare vs. greedy/LP;
   brute-force optimum on small graphs to measure true approximation ratio.
10. **Novelty risk:** Densest k-Subgraph approximation is heavily studied; improving the
    factor is a major open problem. HIGH risk of no real gain; but a class-specific
    improvement is plausible. MEDIUM-HIGH.
11. **Falsification:** If approximation ratio worse than greedy on the class, or no
    provable improvement, fails.
12. **Feasible without proprietary/inaccessible:** Yes.

**Rubric scores:** novelty 4, importance 6, theory 5, advantage 4, baselines 6, verification
7, implementation 7, academic 5.
**Weighted total:** 0.8+0.9+0.75+0.6+0.6+0.7+0.7+0.25 = **5.3/10**

**Major reason score might be wrong:** Hardness of approximation means limited gain;
class-specific claims narrow importance.

---

## C10 — Block Wiedemann for matrix rank over GF(2) (Algebra / cryptography)

1. **Problem:** Compute the rank (or solve a linear system) of a large sparse matrix over
   GF(2). Output: rank (and solution). Used in index calculus, cryptanalysis, coding.
2. **Why it matters:** The linear algebra step of number-field sieve and related
   algorithms; large sparse GF(2) systems arise in cryptanalysis and coding theory.
3. **Strongest known:** Wiedemann (iterative, O(n) matvecs), Lanczos, Block Wiedemann
   (Coppersmith), implemented in CADO-NFS, msieve.
4. **Bottleneck:** Many matvecs; sequential dependencies; block Wiedemann complex.
5. **Insight:** A new block/iterative variant reducing matvec count or improving
   parallelism for a matrix class (e.g., structured/sparse GF(2) matrices), with a
   rigorous success-probability bound.
6. **Guarantee:** Rank correctness provable (with high probability); matvec and operation
   bounds derivable.
7. **Advantage:** Fewer matvecs / faster rank than Wiedemann on a defined GF(2) matrix
   class.
8. **Baselines:** hand-built Wiedemann and Lanczos over GF(2); CADO-NFS not readily
   available/reusable. Baseline strength moderate (hand-built).
9. **Verification:** Rank vs. Gaussian elimination (sympy/numpy GF(2) or custom) on small
   matrices; solve Ax=b and check; differential vs. Wiedemann.
10. **Novelty risk:** Wiedemann/Block Wiedemann are classical (1986/1990s); variants
    published. MEDIUM-HIGH risk.
11. **Falsification:** If rank wrong or matvec count not better, fails.
12. **Feasible without proprietary/inaccessible:** Yes. GF(2) arithmetic in Python/Rust.

**Rubric scores:** novelty 4, importance 5, theory 5, advantage 4, baselines 5, verification
8, implementation 6, academic 4.
**Weighted total:** 0.8+0.75+0.75+0.6+0.5+0.8+0.6+0.2 = **5.0/10**

**Major reason score might be wrong:** Wiedemann variants saturated; niche importance;
baselines weak.

---

## C11 — Euclidean nearest-neighbor graph / MST via new decomposition (Computational geometry)

1. **Problem:** Given n points in R^d (d=2 or 3), compute the Euclidean minimum spanning
   tree or the k-nearest-neighbor graph. Output: edge set.
2. **Why it matters:** Clustering, GIS, mesh generation, computer graphics, spatial
   analysis.
3. **Strongest known:** EMST via Delaunay triangulation (O(n log n) in 2D) then Kruskal;
   WSPD-based methods; k-NN via kd-trees/ball-trees (scikit-learn), cover trees.
4. **Bottleneck:** Delaunay construction is the bottleneck in higher dimensions; kd-trees
   degrade with dimension ("curse of dimensionality").
5. **Insight:** A new decomposition (e.g., a new hierarchical clustering / net-tree
   variant) giving a provable bound for EMST/k-NN in low dimension with better constants
   and simpler construction than Delaunay.
6. **Guarantee:** Correctness (EMST is correct MST) provable; time bound derivable.
7. **Advantage:** Faster / simpler than Delaunay+Kruskal on 2D/3D point sets; competitive
   with scipy.spatial.
8. **Baselines:** scipy.spatial (Delaunay, cKDTree), networkx MST. Strong, available.
9. **Verification:** MST correctness (cut property, compare to Kruskal/Delaunay) on random
   and structured point sets; edge-count checks; exhaustive small.
10. **Novelty risk:** EMST and Delaunay are classical and optimal (O(n log n) in 2D).
    Beating scipy's Delaunay (Qhull-based) is hard. HIGH risk on advantage; novelty LOW.
11. **Falsification:** If not faster than scipy Delaunay+Kruskal, or incorrect MST, fails.
12. **Feasible without proprietary/inaccessible:** Yes. scipy available.

**Rubric scores:** novelty 2, importance 6, theory 4, advantage 3, baselines 9, verification
8, implementation 6, academic 3.
**Weighted total:** 0.4+0.9+0.6+0.45+0.9+0.8+0.6+0.15 = **4.8/10**

**Major reason score might be wrong:** O(n log n) EMST is optimal; scipy's Qhull is
fast; little room for a novel, faster exact algorithm.

---

## C12 — Distribution-sensitive heavy-hitters sketch (Streaming)

1. **Problem:** Given a stream of items, identify items with frequency ≥ φ·N (heavy
   hitters) using small space, with error guarantees. Output: candidate heavy hitters +
   frequency estimates.
2. **Why it matters:** Network monitoring, databases, data mining, OLAP.
3. **Strongest known:** Count-Min sketch (frequency estimates), Count-Sketch, SpaceSave,
   Frequent (Misra-Gries), top-k sketches; theoretical bounds well understood.
4. **Bottleneck:** Worst-case bounds are distribution-blind; real streams are skewed.
5. **Insight:** A sketch that adapts to the observed frequency distribution (e.g., a
   hierarchical / multi-resolution Count-Min) with a rigorous distribution-sensitive error
   bound (error depends on the tail, not just φN).
6. **Guarantee:** Frequency-estimate error bound provable (distribution-sensitive);
   space bound derivable.
7. **Advantage:** Lower error than Count-Min on skewed/realistic streams at the same space.
8. **Baselines:** hand-built Count-Min, Count-Sketch, Misra-Gries; available and simple.
   Baseline strength good (these are the standard strong baselines).
9. **Verification:** Error vs. exact frequencies on synthetic streams (zipfian, uniform,
   adversarial); invariant: estimates ≥ true counts (for Count-Min-style) and bounded
   overestimate.
10. **Novelty risk:** Count-Min/Count-Sketch/SpaceSave are mature; distribution-sensitive
    variants exist. MEDIUM-HIGH risk.
11. **Falsification:** If error bound violated or not better than Count-Min on skewed
    streams, fails.
12. **Feasible without proprietary/inaccessible:** Yes.

**Rubric scores:** novelty 4, importance 7, theory 5, advantage 5, baselines 8, verification
8, implementation 7, academic 4.
**Weighted total:** 0.8+1.05+0.75+0.75+0.8+0.8+0.7+0.2 = **5.85/10**

**Major reason score might be wrong:** Count-Min is near-optimal worst-case;
distribution-sensitive variants may already exist; advantage modest.

---

## Summary of weighted totals

| Candidate | Weighted total | Field |
|-----------|---------------|-------|
| C1 Adaptive elimination ordering (treewidth/fill-in) | **6.7** | Graph |
| C4 Low-rank incomplete-factorization preconditioner | **6.6** | Numerical LA |
| C2 Weighted MWIS measure-and-conquer | 6.15 | Graph |
| C12 Distribution-sensitive heavy hitters | 5.85 | Streaming |
| C5 Distance oracle / approx APSP | 5.75 | Graph |
| C6 Adaptive LCS | 5.7 | Graph/Strings |
| C8 FVS FPT | 5.7 | Graph |
| C3 Grammar-compression index | 5.65 | Strings |
| C9 Densest k-Subgraph approx | 5.3 | Optimization |
| C10 Block Wiedemann GF(2) | 5.0 | Algebra |
| C7 Sparse polynomial interpolation | 4.95 | Symbolic |
| C11 Euclidean MST / k-NN | 4.8 | Geometry |

## Selection

**Primary target: C1 — Adaptive elimination-ordering for treewidth / fill-in.**
It has the highest weighted total (6.7), strong practical importance, available strong
baselines (AMD, min-degree, min-fill), good verifiability (brute-force optimal fill-in on
small graphs; differential vs. networkx), and feasible implementation in Rust + Python.
The central insight (adaptive potential-function ordering with a switching rule and a
provable bound on a graph class) offers a genuine mechanism beyond renaming an existing
heuristic.

**Backup target: C4 — Low-rank incomplete-factorization preconditioner.**
Retained if C1 fails the novelty gate (elimination ordering is a well-trod area).

## Next action
Proceed to Stage 3: novelty screening of C1 (and C4 as backup) — literature search for
closest prior methods, construct the comparison table (research/NOVELTY_ASSESSMENT.md),
then either select C1 definitively or fall back.
