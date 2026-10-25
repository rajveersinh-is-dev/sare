# Complexity Analysis

Project: adaptive elimination ordering for sparse fill-in reduction (candidate C1).
Status: Stage 5 — formal development.

All bounds below are derived step by step. Worst-case bounds are marked [WORST-CASE];
expected/practical bounds [EXPECTED]. The reference implementation uses adjacency hash
sets; complexity is expressed in n = |V|, m = |E|, Δ = maximum degree.

---

## 1. Cost primitives

| Primitive | Cost (adjacency hash set) | Notes |
|-----------|---------------------------|-------|
| neighbor insert/delete/membership | O(1) expected | per edge |
| iterate live[v] | O(d(v)) | |
| fill(v) = C(d,2) − e(N(v)) | O(d(v)²) | scan all pairs of neighbors; count induced edges |
| ELIMINATE(v) (fill clique + removal) | O(d(v)² + d(v)) | O(d(v)²) fill pairs + O(d) removals |
| score(v) | O(d(v)²) | dominated by fill(v) unless lookahead |
| look(v) (β>0) | O(d(v)·Δ) [look-A] or O(Δ³) [look-B] | optional ablation only |

---

## 2. Phase A (safe reductions, degree ≤ 1)

Each elimination removes one vertex and touches at most one neighbor (degree ≤ 1 ⇒ at
most one live neighbor). Edge updates are O(1). Queue operations O(1). Each vertex
eliminated once; each edge examined O(1) times when its endpoint is removed.

**[WORST-CASE] Time: O(n + m). Space: O(n + m) (the working graph).**

Phase A adds zero fill (Theorem 3) and never increases the working graph's edge count
beyond what Phase B adds; it only removes vertices/edges.

---

## 3. Phase B (adaptive greedy)

There are n − |Phase A eliminations| ≤ n iterations. In iteration i, eliminating vertex
vᵢ costs O(dᵢ²) for the fill clique (dᵢ = degree of vᵢ at elimination time) plus O(dᵢ)
for removals, plus the cost of selecting vᵢ.

**Selection cost (naïve rescan):** scanning all live vertices to compute score and take the
minimum is O(Σ_{live v} d(v)²) per iteration ⇒ O(n · Σ d(v)²) total worst case, which is
O(n³) for dense graphs (d = O(n)) and O(n·m·Δ) in general terms. With a priority queue
keyed by score and lazy updates, selection is O(log n) per pop plus O(1) per affected
neighbor update; but scores change for all neighbors of vᵢ (their degree changes, and
fill edges among neighbors change fill counts of neighbors-of-neighbors), so the number of
score updates per elimination is O(dᵢ²) in the worst case (all pairs of neighbors get a
new fill edge, affecting the fill-count of vertices adjacent to both).

Let us bound the total fill-edge additions. Each fill edge {x, y} is added once (when the
first of x, y is eliminated while the other is a common neighbor of the eliminated vertex).
Total fill edges ≤ C(n, 2) − m (all possible non-edges). So total fill-edge insertions
over the run ≤ O(n²). Each fill-edge insertion touches O(1) adjacency sets but may
trigger score updates for common neighbors.

A clean upper bound: total work = O( Σᵢ dᵢ² + (total fill-edge updates) ). Since
Σᵢ dᵢ ≤ 2m + 2·(fill edges) ≤ 2m + n², and each dᵢ ≤ Δ:

- **[WORST-CASE] Time: O(n² + n·Δ²)** using naïve rescans, dominated by selection;
  equivalently O(n³) for dense graphs (Δ = O(n)). With priority queues and incremental
  score maintenance: O((m + F) · Δ + n log n) where F = total fill edges ≤ O(n²), i.e.
  O((m + n²)·Δ) worst case = O(n³) dense.
- **[EXPECTED] Time: O(n·m)** on sparse graphs where Δ and fill are modest and a priority
  queue is used; this matches AMD's O(n·m) ordering time (no asymptotic claim of
  improvement is made — see below).
- **Space: O(n + m + F)** = O(n²) worst case (filled graph can be dense), O(n + m)
  expected for sparse inputs with little fill.

---

## 4. Lookahead (optional, β > 0)

look-A(v) = Σ_{u ∈ N(v)} d(u) after eliminating v: requires simulating elimination of v
(touching O(d(v)²) fill pairs) and reading neighbor degrees ⇒ O(d(v)²) per candidate,
O(Σ d(v)²) per iteration if recomputed for all candidates ⇒ same order as Phase B but
with a larger constant. look-B (one pass of min-degree on the post-elimination graph) is
more expensive (O(Δ³)-ish per candidate) and is used only in small ablation runs.

**Conclusion:** lookahead is disabled by default (β = 0) because its asymptotic cost is
not justified without evidence of benefit. It is an ablation.

---

## 5. Comparison proposition vs. closest prior results

| Result | Time | Space | Quality guarantee |
|--------|------|-------|-------------------|
| Minimum Degree (MD), Tinney & Walker 1967 | O(n·m) | O(n + m) | none |
| Fast Minimum Degree (Bucket Queue) | O(m + F) | O(n + m) | none |
| Approximate Minimum Degree (AMD), Amestoy/Davis/Duff 1996 | O(n·m) | O(n + m) | none |
| Minimum Fill-in (MF) | O(n³) naïve | O(n + m) | none |
| SARE (this work), naïve | O(n² + n·Δ²) | O(n²) worst | none |
| SARE (this work), with priority queue | O((m + n²)·Δ) worst | O(n²) worst | none |

**[COMPARISON PROPOSITION]** SARE does NOT improve on AMD's asymptotic O(n·m) ordering
time, nor does it provide a quality guarantee that MD/MF/AMD lack. All are heuristics
without worst-case quality guarantees for minimum fill-in (NP-hard). SARE's theoretical
contribution is limited to: (a) a clean specification with rigorous correctness (Theorems
1–5), (b) provably-zero-fill safe reductions (Theorem 3), (c) an explicit, tunable,
documented decision rule (degree/fill/lookahead). Any practical advantage over AMD must be
demonstrated empirically (Level B/C at most), not claimed theoretically.

---

## 6. Assumptions required for the bounds

- Adjacency hash sets with O(1) expected operations. With sorted arrays, membership is
  O(log d) and bounds pick up log factors.
- Fill edges counted exactly; no approximation of fill.
- α, β fixed constants (do not grow with n).
- Input fits in memory; the filled graph may be denser than G (space O(n²) worst case).

---

## 7. Lower bounds / barriers

Minimum fill-in is NP-hard; treewidth computation is NP-hard. No polynomial-time
algorithm can guarantee optimal fill-in unless P = NP. No constant-factor polynomial
approximation for minimum fill-in is known in general. These are known barriers, not
results of this project; SARE does not attempt to surmount them.
