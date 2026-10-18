# Adversarial Review A — Research Mathematician

Project: SARE (Safe-Reduction + Adaptive elimination ordering), candidate C1.
Reviewer persona: research mathematician.
Mandate: challenge definitions, assumptions, theorem statements; hunt for counterexamples and
hidden quantifiers; check proof completeness; judge whether the object is genuinely distinct from
standard constructions; challenge complexity calculations.
Label: INTERNAL ADVERSARIAL REVIEW (not peer review, not endorsed by any external party).

---

## 1. Definitions and assumptions

The problem definition (docs/PROBLEM_DEFINITION.md) is precise: finite simple undirected graph,
elimination ordering as a permutation, fill-in defined constructively, output = ordering +
fill/width. Good. The distinction between "mathematical assumptions" (finite, simple, static) and
"benchmark conditions" (graph sizes, sources) is honestly drawn.

One assumption worth stating explicitly: the elimination model charges exactly one fill edge per
missing pair in the eliminated neighborhood, which matches the sparse Cholesky/LU fill model. This
is standard but should be stated as an assumption linking the combinatorial problem to the
application. It is stated implicitly via the elimination process; I'd make it explicit.

## 2. Theorems and proofs

docs/MATHEMATICAL_FOUNDATIONS.md states Theorems 1–5.

- Theorem 1 (SARE returns a permutation): proof is complete and correct. Every vertex appended
  once before ELIMINATE; eliminated vertices skipped. Halts because one vertex eliminated per
  iteration. OK.
- Theorem 2 (reported fill/width equals elimination's): correct by construction of ELIMINATE.
- Theorem 3 (Phase A safe reductions add zero fill): correct — degree 0/1 => fill = C(d,2)-e =
  0. OK.
- Theorem 4 (filled graph chordal; pi is a PEO): standard elimination-game argument, stated
  correctly. OK.
- Theorem 5 (termination): trivial but stated. OK.

All five proofs are mathematically valid. No hidden quantifiers detected. The proofs do not use
"obviously"/"clearly" to conceal steps; they are short and complete.

**Assessment: the proved results are correct and the proofs are complete.** No counterexample
invalidates Theorems 1–5 (degenerate cases: empty, single, clique, tree, disconnected, edgeless —
all handled; verified by tests).

## 3. What is NOT proved (boundary of the mathematical contribution)

This is where the review is critical:

- **No optimality claim.** SARE does not minimize fill or width. Minimum fill-in is NP-hard; no
  claim of approximation ratio. Correct.
- **No claim that every optimal ordering eliminates degree-1 vertices first.** The project
  explicitly treats this as an open/empirical question (docs/MATHEMATICAL_FOUNDATIONS.md, §6).
  Good — this is an honest limitation, not a hidden assumption.
- **No constant-factor approximation.** None claimed; none known for greedy elimination. Correct.
- **No asymptotic improvement over AMD's O(n·m).** Correctly disclaimed in COMPLEXITY_ANALYSIS.md.

So the mathematical contribution is: a correct, specified algorithm with provable validity and
zero-fill safe reductions. It is NOT a new complexity bound, NOT an approximation algorithm, NOT
optimal. This is modest but honest.

## 4. Is the object genuinely distinct from standard constructions?

Partially. The elimination-by-greedy-score skeleton is standard (Minimum Degree 1967, MMD 1985,
AMD 1996, Minimum Fill-in). The specific combination (safe degree-0/1 reductions up front +
adaptive potential degree + alpha·fill + beta·lookahead + documented switching parameter) is a
specific construction. Whether it's "genuinely distinct" or a routine variation of AMD/composite-cost
greedy (Bodlaender & Koster 2008) is an algorithms-research question (Reviewer B's remit), not a
mathematical one. Mathematically, the object is well-defined and its properties are correctly
proved.

## 5. Complexity calculations

docs/COMPLEXITY_ANALYSIS.md: worst-case O(n^2 + n·Delta^2) naive selection, O((m+n^2)·Delta)
with priority queues, O(n^2) space worst case, O(n·m) expected on sparse graphs with PQ. These are
reasonably derived. The honest comparison proposition admits SARE does NOT improve on AMD's O(n·m).
Good.

## 6. Counterexample search

The counterexample section (§6) is thoughtful. The one open question (degree-1-first optimality)
is correctly flagged as not assumed. No counterexample to the proved theorems was found, and the
test suite (brute force n<=8, chordal invariant) supports correctness on small cases.

## 7. Verdict for this persona

**The mathematics is sound.** The theorems are correctly stated and proved; the boundary between
proved and conjectured is honestly drawn; no counterexample to the claims exists. 

**However, the mathematical contribution is modest:** a correct greedy elimination ordering with
safe reductions and a tunable decision rule. It does not prove a new bound, does not approximate,
and is not optimal. The mathematical novelty rests entirely on the specific combination, which is
algorithms-research terrain.

**Strongest defensible mathematical claim:** "SARE always returns a valid elimination ordering;
its Phase-A safe reductions add provably zero fill; its reported fill/width exactly match the
elimination; the filled graph is chordal and the order is a PEO; it terminates in bounded time."
Nothing stronger is justified.

Open mathematical question worth recording: whether eliminating all degree-1 vertices first is
optimality-safe for minimum fill-in (not assumed, not tested as a theorem).
