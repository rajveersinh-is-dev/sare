# Problem Definition

Project: adaptive elimination ordering for sparse fill-in reduction (candidate C1).
Status: Stage 4 — problem formulation. Primary target.

---

## 1. Computational problem

**Name:** Fill-minimizing vertex elimination ordering (a.k.a. minimum fill-in / treewidth
approximation via elimination ordering).

**Input:** A finite, simple, undirected, unweighted graph G = (V, E), with n = |V| and
m = |E|. No self-loops, no parallel edges. Vertices are labeled 0..n-1.

**Elimination process (formal).** Given an elimination ordering π = (v₁, v₂, ..., vₙ),
a permutation of V, define a sequence of graphs G₀ = G, and for i = 1..n:
- Let Nᵢ₋₁(vᵢ) be the neighbors of vᵢ in Gᵢ₋₁ (only not-yet-eliminated vertices remain).
- Add a fill edge between every pair of vertices in Nᵢ₋₁(vᵢ) that is not already an edge
  of Gᵢ₋₁ (make the neighborhood a clique).
- Remove vᵢ and its incident edges to obtain Gᵢ.
The set of edges added over all n steps is the fill-in F(π) ⊇ E. The filled graph
H = (V, E ∪ F(π)) is chordal and π is a perfect elimination ordering of H.

**Output:** An elimination ordering π (a permutation of V), plus implicitly the elimination
tree / fill-in graph H. Optionally the fill-in count |F(π)| \ |E| and the elimination
width w(π) = maxᵢ |Nᵢ₋₁(vᵢ)| (maximum number of later neighbors at elimination time).
w(π) − 1 is an upper bound on the treewidth tw(G).

**Correctness condition:** π must be a permutation of V (every vertex eliminated exactly
once), and the elimination process applied to π must terminate with all vertices removed
and produce a chordal filled graph H for which π is a perfect elimination ordering. Any
permutation satisfies this by construction; the *quality* of π is measured by fill-in and
width, not by correctness. So the algorithmic problem is an *optimization* problem: find a
low-fill / low-width ordering.

**Objective function (primary):** minimize fill-in |F(π)| − |E|.
**Objective function (secondary):** minimize elimination width w(π).

## 2. Input-size and structural parameters

- n = |V|, m = |E| (size parameters).
- Δ = maximum degree, tw(G) = treewidth, pw(G) = pathwidth (structural parameters).
- Graph classes of interest: grids, sparse random graphs, chordal graphs,
  bounded-treewidth graphs, graphs from sparse-matrix collections (e.g., SuiteSparse
  University of Florida sparse matrix collection).

## 3. Constraints and assumptions

- Graph is static (no insertions/deletions during ordering) — ordering is a one-shot
  preprocessing step before a numerical factorization.
- **Fill model:** eliminating v adds one fill edge for every missing pair in its current
  neighborhood (making N(v) a clique). This matches the fill model of sparse Cholesky/LU/
  QR factorization, which is the intended application. Exact arithmetic on the ordering
  (combinatorial); no numerical tolerance is involved in the ordering itself. The ordering is
  later used by a sparse factorization whose numerical behavior is outside this algorithm's
  scope.
- Deterministic output for a given input and fixed parameter settings (no randomized choices
  unless a seed is fixed).

## 4. Degenerate and special cases

- Empty graph (n = 0): empty ordering, fill = 0, width = 0.
- Single vertex (n = 1): trivial ordering.
- edgeless graph: any ordering, fill = 0, width = 0.
- Complete graph Kₙ: any ordering, fill = 0, width = n − 1 (optimal).
- Chordal graph: a perfect elimination ordering exists with width = tw(G) (optimal);
  Maximum Cardinality Search finds one in O(n + m).
- Tree / forest: tw = 1; eliminating leaves first gives width 1.

## 5. Complexity measures

- Ordering time (time to compute π).
- Ordering space (memory beyond the input graph).
- Quality: fill-in count, elimination width (proxy for downstream factorization cost and
  memory).
- Break-even: ordering time must be small compared to the downstream sparse factorization
  it enables; otherwise the ordering is not worthwhile.

## 6. Required exactness

The ordering is exact (combinatorial): every vertex eliminated once, fill computed exactly.
No approximation of fill-in; the *quality guarantee* (how close to optimal fill) is what is
evaluated empirically, since minimum fill-in is NP-hard.

## 7. Strongest known baseline guarantees

Minimum fill-in is NP-hard (component of treewidth computation). No polynomial-time
algorithm with a constant-factor approximation for minimum fill-in is known; treewidth
approximation is also hard. Strong practical baselines:
- Minimum Degree (MD), Tinney & Walker (1967).
- Multiple Minimum Degree (MMD), Liu (1985).
- Approximate Minimum Degree (AMD), Amestoy, Davis & Duff (SIAM MAXA 1996; Algorithm 837,
  ACM TOMS 2004) — the strongest widely used practical baseline, in SuiteSparse/SciPy.
- Minimum Fill-in (MF), Bodlaender & Koster (2008).
- Nested Dissection (ND) / METIS (graph partitioning based).
These are heuristics with no worst-case quality guarantee. Exact treewidth is FPT and
exponential; optimal fill-in is NP-hard.

## 8. Distinction: mathematical assumptions vs. benchmark conditions

- Mathematical: graph is finite, simple, undirected, static. (Required.)
- Benchmark-specific: graph sizes, density, source (SuiteSparse vs. random), and the
  downstream factorization cost model are conditions of the *experimental suite*, not
  requirements of the algorithm. Advantage claims are qualified by the benchmark regime.

## 9. Why the problem matters

Elimination ordering dominates the cost (work and memory) of sparse direct solvers
(Cholesky, LU, QR) and of variable elimination in graphical models / constraint
propagation. A small fill reduction can yield large downstream savings, so the ordering is a
high-leverage preprocessing step in scientific computing, CAD/VLSI, and probabilistic
inference.

## 10. Delimitation of claims (honesty)

This project does NOT claim:
- a polynomial constant-factor approximation for minimum fill-in,
- an asymptotic improvement over AMD's O(n·m) ordering time,
- that the new ordering is optimal or near-optimal in the worst case,
- that it beats AMD on every graph class.

It claims (to be tested honestly): a deterministic adaptive ordering with a combined
degree/fill/lookahead potential and provably-safe reductions, with rigorous correctness and
complexity, empirically evaluated against AMD / min-degree / min-fill on a defined suite,
reporting both wins and losses.
