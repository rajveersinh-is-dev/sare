# Independent Verification Framework

This document details the independent verification mechanisms added to ensure the correctness of the SARE algorithm and its foundation.

## 1. Property-Based Testing

We use property-based testing (`proptest` in Rust, `hypothesis` in Python) to subject our heuristic implementations to adversarial random graph generation. The following properties are rigorously asserted on every run:
*   **Permutation Validity:** The elimination order returned must be a complete and exact permutation of the vertices.
*   **Fill Evaluation Match:** The fill and width reported by the algorithm matching exactly with a post-hoc exact simulation on the order.
*   **Chordal Completion:** The final graph formed by merging all original edges with the fill edges specified by the order must be demonstrably chordal.

## 2. Chordal Verification Oracle (MCS)

We built an independent Maximum Cardinality Search (MCS) oracle.
*   It implements standard MCS to compute an elimination ordering.
*   It checks whether the MCS ordering is a Perfect Elimination Ordering (PEO).
*   By classical graph theory (Fulkerson and Gross, 1965), a graph is chordal if and only if MCS finds a PEO. We use this to independently verify that SARE properly triangulates the graph.

## 3. Exact DP Oracle

We implemented an exact minimum fill dynamic programming algorithm (Held-Karp style) that runs in $O(2^n \text{poly}(n))$.
*   This expands our capability to compute the exact optimal fill-in from $n \le 11$ (previous factorial brute-force) to $n \le 18$.
*   Property tests verify that SARE’s heuristic fill is strictly lower bounded by this exact optimal fill across thousands of random small-instance topologies.
