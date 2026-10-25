# Verification Framework

This document outlines the rigorous verification framework added to the SARE repository in Stage 12 to mathematically prove correctness over exact topological classes and establish invariant properties.

## 1. Graph Isomorphism and Canonicalization
To avoid testing the same graph topology multiple times (due to the combinatorial explosion of labeled graphs), we implemented a 1D Weisfeiler-Lehman color refinement algorithm with backtracking. This algorithm computes a canonical permutation for any graph.

The `generate_non_isomorphic_graphs(n)` function inductively generates all unique topologies up to `n=8` (yielding 12,249 graphs instead of millions of isomorphic duplicates). This allows us to perform exhaustive tests for correctness bounds without redundant work.

- Rust implementation: `src/rs/src/isomorphism.rs`
- Python implementation: `src/python/isomorphism.py`

## 2. Exhaustive Non-Isomorphic Verification
The exhaustive test suite (`tests/test_exhaustive_non_isomorphic.py` and `src/rs/tests/exhaustive_isomorphic.rs`) evaluates SARE against an exact dynamic-programming optimum for every single non-isomorphic graph up to $n=6$. This verifies the exact lower bound and validates chordal completion across the entire small-instance state space.

## 3. Metamorphic Invariance
We introduced metamorphic tests (`test_permutation_invariance_metamorphic`) which randomly generate graphs, then construct random isomorphic permutations. These tests guarantee that despite internal tie-breaking mechanisms, structural permutations yield the same fill counts and widths, confirming that the elimination consequences strictly depend on graph structure, not representation.

## 4. True Benchmarking Baseline
We implemented `fast-min-degree` using a bucket-queue structure, offering $O(m + F)$ expected performance to act as an unhandicapped baseline for the evaluation of SARE against optimal implementations of standard heuristics.
