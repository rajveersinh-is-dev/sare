# Algorithm Specification

Project: adaptive elimination ordering for sparse fill-in reduction (candidate C1).
Algorithm name: **SARE** — Safe-Reduction + Adaptive Elimination ordering.
Status: Stage 4 — specification (reference form, before optimization).

---

## 1. Purpose

Given a finite simple undirected graph G = (V, E), produce an elimination ordering π
that (hopefully) reduces fill-in and elimination width for a subsequent sparse direct
factorization (Cholesky/QR/LU). SARE is a deterministic heuristic; it does not solve
minimum fill-in optimally (NP-hard). Its claims are: (a) it always returns a valid
elimination ordering with exactly-computed fill/width; (b) its safe-reduction phase adds
zero fill; (c) its running time and space are bounded as analyzed.

---

## 2. Notation

- G = (V, E), n = |V|, m = |E|.
- For the working graph H and a live vertex v:
  - N_H(v) = neighbors of v in H (live vertices only).
  - d(v) = |N_H(v)|.
  - fill(v) = C(d(v), 2) − e(N_H(v)), where e(S) = number of edges of H induced by S.
    fill(v) = number of new fill edges created by eliminating v *now*.
  - score(v) = d(v) + α·fill(v) + β·look(v), α, β ≥ 0 tunable parameters.
- look(v) (optional, β = 0 disables): a cheap 1-step lookahead estimate of the fill
  consequences of eliminating v next. Defined precisely in §5.

---

## 3. Pseudocode (reference implementation)

```
SARE(G, α = 1.0, β = 0.0):
  # G = (V, E), undirected, simple
  H ← copy of G            # mutable adjacency: live[v] = set of live neighbors
  live[v] ← true for all v ∈ V
  π ← empty list           # elimination ordering
  eliminated[v] ← false for all v ∈ V

  # ---------- Phase A: safe reductions (degree 0 or 1 -> zero fill) ----------
  Q ← FIFO queue
  for v ∈ V:
    if |live[v]| ≤ 1: Q.push(v)

  while Q not empty:
    v ← Q.pop()
    if eliminated[v]: continue
    if |live[v]| > 1: continue   # degree changed since enqueued
    append v to π
    ELIMINATE(v)                 # adds 0 fill because |live[v]| ≤ 1
    for u ∈ live[v] (at most one neighbor):
      live[u].remove(v)
      d(u) decreases by 1
      if d(u) == 1: Q.push(u)

  # ---------- Phase B: adaptive greedy elimination ----------
  while ∃ live vertex:
    choose live v minimizing score(v) = d(v) + α·fill(v) + β·look(v)
    append v to π
    ELIMINATE(v)

  return π


ELIMINATE(v):
  eliminated[v] ← true
  Nv ← live[v]                   # snapshot of neighbors
  # add fill edges: make Nv a clique
  for each unordered pair {x, y} ⊆ Nv with {x, y} ∉ E(H):
    add edge {x, y} to H
    live[x].add(y); live[y].add(x)
    d(x) += 1; d(y) += 1
  # remove v
  for u ∈ Nv:
    live[u].remove(v)
    d(u) -= 1
  live[v] ← ∅
  d(v) ← 0


fill(v):
  d ← |live[v]|
  e ← number of edges of H induced by live[v]  # count pairs {x,y}⊆live[v] that are edges
  return C(d, 2) − e


look(v)  # 1-step lookahead estimate (β > 0 only)
  # Estimate fill created by eliminating v, then each neighbor u immediately after.
  # Computed by simulating elimination of v on a copy and summing fill(u) for u ∈ N(v).
  # Cheap approximation: sum over u ∈ N(v) of (d(u) after eliminating v).
  return Σ_{u ∈ live[v]} d_after_eliminating_v(u)
```

**Tie-breaking:** lower vertex id first (deterministic).
**Parameters:** α weights fill vs. degree; α = 1 ≈ "min-fill with degree bias"; α = 0 is pure minimum degree; β = 0 disables lookahead (default).
**Termination:** each loop iteration eliminates exactly one vertex; at most n iterations; Phase A also eliminates at least one vertex per pop that is processed. Halts on every finite input.

---

## 4. Correctness argument (proof sketch; full proofs in docs/MATHEMATICAL_FOUNDATIONS.md)

**Theorem 1 (Valid ordering).** SARE returns a permutation π of V: every vertex is
appended to π exactly once and no vertex is appended twice.
*Reason:* ELIMINATE marks v eliminated and removes it from all neighbor sets; a vertex
is only appended right before ELIMINATE, and eliminated vertices are skipped.

**Theorem 2 (Exact fill/width).** The fill-in and width reported for π equal the fill-in
and width produced by eliminating vertices in the order π (by construction: fill edges
are added exactly when their eliminating vertex is processed).

**Theorem 3 (Safe reductions add zero fill).** Any vertex eliminated in Phase A has
|live[v]| ≤ 1 at elimination time, hence fill(v) = C(≤1, 2) − e(...) = 0, so Phase A
adds no fill edges.

**Theorem 4 (Chordal completion).** Eliminating in any order π and adding clique edges
among each vertex's later neighbors yields a chordal filled graph H for which π is a
perfect elimination ordering. Standard; π is a PEO of H.

---

## 5. Lookahead (optional ablation)

look(v) estimates the downstream fill effect of eliminating v now. Two variants are
implemented as an ablation study:
- look-A(v) = Σ_{u ∈ N(v)} d(u) after eliminating v (sum of neighbor degrees post-elimination).
- look-B(v) = greedy fill of the graph obtained after eliminating v, computed by one pass of minimum degree (expensive; used only in ablation, β small).

The core claim (correctness, complexity, safe reductions) does not depend on lookahead;
β = 0 is the default configuration. lookahead is evaluated as an ablation to see whether
it improves fill at acceptable cost.

---

## 6. Input validation and edge cases

- n = 0: return empty ordering.
- n = 1: return [v₀].
- Self-loops / parallel edges: rejected (input must be simple); adjacency stored as sets.
- Disconnected graph: each connected component processed independently by the same loop.
- α, β: validated ≥ 0; β = 0 default.

---

## 7. Failure behavior

SARE never fails on a valid input (deterministic, always terminates, always returns a
permutation). Memory failure (out of memory on very large dense graphs) is an
implementation/environment limit, not an algorithmic failure; it is documented and not
claimed to be handled.

---

## 8. Role of each step (for the reader)

- Phase A: remove vertices that provably create no fill (degree ≤ 1), cheaply, before
  the more expensive greedy phase. Reduces graph size for Phase B.
- Phase B: greedy adaptive choice balancing current degree (keeps the graph small) and
  current fill (avoids creating many edges), with optional lookahead.
- ELIMINATE: applies the graph transformation (clique on neighborhood, then removal),
  exactly modeling what a sparse direct solver does.
- score: the single decision rule; α and β select the regime (degree-driven vs.
  fill-driven vs. lookahead-driven).
