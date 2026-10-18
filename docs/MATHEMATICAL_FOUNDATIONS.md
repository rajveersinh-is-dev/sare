# Mathematical Foundations

Project: adaptive elimination ordering for sparse fill-in reduction (candidate C1).
Status: Stage 5 — formal development. Contains definitions, correctness theorems and
proofs, termination proof, and counterexample analysis.

Proven results are marked **[PROVED]**. Conjectures/empirical claims are marked
**[CONJECTURE]** or **[EMPIRICAL]**. Nothing is presented as proved unless a proof is
given below.

---

## 1. Definitions and notation

**Graph.** A finite simple undirected graph G = (V, E), n = |V|, m = |E|. Adjacency is
symmetric; no self-loops; no parallel edges.

**Elimination.** Eliminating a vertex v from a graph H means: add an edge between every
pair of distinct vertices in N_H(v) that are not already adjacent in H (make N_H(v) a
clique), then delete v and its incident edges. The added edges are *fill edges*.

**Elimination ordering.** A permutation π = (v₁, …, vₙ) of V. Applying π means
eliminating v₁, then v₂, …, vₙ successively, where each elimination is performed on the
graph resulting from all previous eliminations (with fill edges included).

**Fill-in of π.** F(π) = set of all fill edges added during the elimination of π. The
filled graph H(π) = (V, E ∪ F(π)). fill-count(π) = |F(π)| − |E|.

**Elimination width.** w(π) = maxᵢ |N_{G_{i−1}}(vᵢ)|, the maximum number of later
neighbors of any vertex at the moment it is eliminated. w(π) − 1 ≥ tw(G) (treewidth of G).

**Perfect elimination ordering (PEO) of a chordal graph.** An ordering π of a chordal
graph H such that, for every vertex v, its later neighbors in H form a clique.

**Degree-0/1 vertex.** A vertex v with |N(v)| ≤ 1. Eliminating it adds fill(v) =
C(|N(v)|, 2) − e(N(v)) = 0 fill edges (C(0,2)=C(1,2)=0, e(∅)=e({u})=0).

**Simplicial vertex.** A vertex v such that N(v) is a clique in the current graph.
Eliminating a simplicial vertex adds 0 fill edges. (Used as an optional zero-fill-now
candidate; NOT claimed to be optimality-safe in general.)

**Safe reduction.** Eliminating a vertex now that cannot increase the minimum achievable
fill-in over all completions of the ordering. Degree-0/1 elimination is safe (proved
below as zero fill now; removal of an isolated or leaf vertex cannot force future fill
because it participates in no triangle).

---

## 2. The algorithm (SARE) restated formally

SARE(G, α, β):
1. H ← G; live[v] ← N_G(v); eliminated[v] ← false; π ← ().
2. **Phase A:** repeatedly dequeue and eliminate any live vertex with |live[v]| ≤ 1
   (degree 0 or 1), updating neighbor degrees and enqueuing any neighbor whose degree
   drops to 1. Each such elimination adds 0 fill.
3. **Phase B:** while any live vertex remains, choose live v minimizing
   score(v) = d(v) + α·fill(v) + β·look(v), append v to π, eliminate v (adding fill
   edges among live[v]), update affected degrees/fill.
4. Return π.

α, β ≥ 0. Default α = 1, β = 0.

---

## 3. Correctness theorems

### Theorem 1 (SARE returns a valid elimination ordering)

**[PROVED]** SARE(G, α, β) terminates and returns a permutation π of V: every vertex of
V appears in π exactly once.

*Proof.*
We show (i) every appended vertex is distinct, and (ii) every vertex is eventually
appended.

(i) In Phase A and Phase B, a vertex v is appended to π immediately before calling
ELIMINATE(v), which sets eliminated[v] = true and removes v from live[u] for every
neighbor u, and sets live[v] = ∅. The selection steps explicitly skip eliminated
vertices (Phase A skips eliminated[v]; Phase B chooses only among live vertices, i.e.
not eliminated). Hence no vertex is appended twice.

(ii) Phase A eliminates all vertices it dequeues that still have degree ≤ 1; it may leave
vertices with degree ≥ 2. Phase B then eliminates one live vertex per iteration until
none remain. Since each iteration of either phase eliminates exactly one not-yet-
eliminated vertex and there are finitely many (n), all vertices are eliminated and hence
all are appended. π contains each vertex exactly once ⇒ π is a permutation of V. ∎

### Theorem 2 (Reported fill/width equals the elimination's fill/width)

**[PROVED]** The fill-in count and width computed for π equal the fill-in count and
elimination width obtained by eliminating V in the order π.

*Proof.* ELIMINATE(v) adds exactly the edges {x, y} with x, y ∈ live[v] at elimination
time and {x, y} ∉ E(H), i.e. exactly the fill edges created by eliminating v on the
current graph. These are accumulated into H and counted. Since the sequence of
eliminations is exactly π, the accumulated fill edges are exactly F(π), and the maximum
neighborhood size seen is exactly w(π). ∎

### Theorem 3 (Phase A safe reductions add zero fill)

**[PROVED]** Every vertex eliminated in Phase A creates fill(v) = 0.

*Proof.* A vertex is enqueued/eliminated in Phase A only when |live[v]| ≤ 1.
fill(v) = C(|live[v]|, 2) − e(live[v]). If |live[v]| = 0: C(0,2) = 0, e(∅) = 0 ⇒ fill = 0.
If |live[v]| = 1, say live[v] = {u}: C(1,2) = 0, e({u}) = 0 (no self-loop) ⇒ fill = 0.
Thus Phase A adds no fill edges. ∎

### Theorem 4 (Filled graph is chordal; π is a PEO of it)

**[PROVED]** Let H(π) = (V, E ∪ F(π)) be the filled graph produced by eliminating in
order π. Then H(π) is chordal and π is a perfect elimination ordering of H(π).

*Proof.* Standard elimination-game theorem: eliminating vertices and filling each
neighborhood into a clique produces a chordal graph (a triangulation), and the elimination
order is a perfect elimination ordering of the triangulation. By construction, when vᵢ is
eliminated, all its remaining neighbors (in H(π), these are vⱼ with j > i that are
adjacent to vᵢ) have been made a clique. Hence for every vᵢ, its later neighbors in
H(π) form a clique ⇒ π is a PEO of H(π) ⇒ H(π) is chordal. ∎

### Theorem 5 (Termination)

**[PROVED]** SARE halts on every finite input graph.

*Proof.* Phase A: each processed dequeue eliminates one vertex (or skips an already-
eliminated/degree-changed one); the queue is finite and each vertex is enqueued finitely
many times (degree changes finitely). Phase B: exactly one live vertex eliminated per
iteration, n vertices total ⇒ at most n iterations. Both phases finite ⇒ SARE halts. ∎

---

## 4. What is NOT claimed (boundary of the contribution)

- **[NOT CLAIMED]** SARE minimizes fill-in or width. Minimum fill-in is NP-hard; SARE is
  a heuristic.
- **[NOT CLAIMED]** Degree-0/1 elimination is *optimality-safe* for minimum fill-in in the
  sense of belonging to *every* optimal ordering. We only claim it adds zero fill now and
  cannot force fill (an isolated/leaf vertex is in no triangle). Whether every minimum-fill
  ordering eliminates all degree-1 vertices first is an open question for this project and
  is treated as empirical.
- **[NOT CLAIMED]** Any constant-factor approximation ratio for fill-in or width. No such
  ratio is proved; none is known for simple greedy elimination orderings in general.
- **[NOT CLAIMED]** Asymptotic time improvement over AMD's O(n·m).
- **[NOT CLAIMED]** Superiority on every graph class; advantage is empirical and
  regime-dependent (see benchmark report).

---

## 5. Complexity assumptions

- The working graph H is stored with adjacency hash sets (or sorted arrays) so that
  neighbor insertion/deletion/membership are O(1) expected / O(log deg).
- fill(v) is computed by scanning pairs of live[v], cost O(d(v)²) per evaluation unless
  maintained incrementally.
- look(v) (β > 0) requires simulating one elimination; cost depends on variant.

These drive the bounds in docs/COMPLEXITY_ANALYSIS.md.

---

## 6. Counterexample search (boundary conditions)

The following were explicitly considered as potential invalidators; none invalidates
Theorems 1–5:

- **Disconnected graph:** each component eliminated independently; Theorems 1–5 hold per
  component and collectively.
- **Complete graph Kₙ:** fill(v) = 0 for all v at every step (neighborhood already a
  clique); any ordering, fill = 0, width = n−1. SARE correct; optimal width = n−1.
- **Tree:** leaves have degree 1 ⇒ eliminated in Phase A with zero fill; width 1 = tw.
  Optimal.
- **Empty / single-vertex / edgeless:** Theorems hold trivially.
- **Vertex whose degree drops below 1 mid-Phase-A:** guarded by the
  `if |live[v]| > 1: continue` re-check; correctness preserved (Theorem 1(i)).
- **Dense graph:** fill(v) computation O(d²) may be expensive but remains correct;
  performance (not correctness) degrades — documented as a limitation.

**Open counterexample question:** Does there exist a graph where eliminating all degree-1
vertices first (Phase A) strictly increases the minimum achievable fill compared to an
optimal ordering that does not? This is NOT assumed safe for optimality; it is treated as
an empirical/open question and is not part of the proved claims. If such a graph exists,
it only affects *quality*, not *correctness* (Theorems 1–5 still hold).
