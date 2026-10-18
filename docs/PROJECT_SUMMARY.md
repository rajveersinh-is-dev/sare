# Project summary — SARE

## One-line description
A verified adaptive elimination ordering (SARE) for reducing fill-in in sparse direct
factorization, implemented in Rust and Python, honestly benchmarked against classical
heuristics (evidence Level D: correct and reproducible, no demonstrated advantage over
minimum degree/AMD).

## Problem
Given an undirected graph G=(V,E), compute a vertex elimination ordering that reduces
fill-in for a subsequent sparse direct factorization. Minimum fill-in is NP-hard.

## Central idea
Phase A: safe degree-0/1 reductions (provably zero fill). Phase B: adaptive greedy choice
by score = degree + alpha·fill + beta·lookahead.

## What is proved
5 theorems: valid ordering; exact fill/width reporting; zero-fill safe reductions; chordal
completion (order is a PEO of the filled graph); termination.

## What is NOT claimed
Optimality, approximation ratio, asymptotic improvement over AMD (O(n·m)), or any
practical advantage.

## Benchmark result (honest)
Fill comparable to min-degree/min-fill (±7%); SARE slower (min-degree up to ~76× faster
on chordal-250). Level D.

## Reproducibility
`cargo build --release && cargo test --release` (Rust); `python -m pytest tests/` (Python);
`python scripts/run_benchmarks.py` regenerates all results. Raw CSV + processed summary +
figures in `results/`. Fixed seeds. Two independent implementations agree.

## Author
Rajve (independent research; no institutional affiliation, degree, email, or title invented).
