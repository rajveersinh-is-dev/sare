# Symbolic Factorization and Elimination Trees

The SARE repository relies on a robust verification framework that constructs left-looking numerical Cholesky factorizations $LL^T = A$ to rigorously confirm that topological elimination orders result in identical fill-in sizes.

Previously, `cholesky.py` and `cholesky.rs` utilized a naive $\mathcal{O}(n^2)$ approach to numeric factorization, explicitly scanning all past columns to find reachability for subtraction updates. For large scale evaluations or larger graph benchmarks, this is unscalable.

Modern sparse factorization pipelines utilize a **Symbolic Factorization** phase prior to the numeric phase to achieve true scalability.

## Elimination Trees (Etrees)

The elimination tree (etree) defines the dependencies among the columns of a Cholesky factor $L$.
For a symmetric positive definite matrix $A$ and its lower-triangular Cholesky factor $L$, the parent of column $j$ in the etree is defined as:
$parent(j) = \min \{ i > j : L_{ij} \neq 0 \}$

If column $j$ has no non-zeros below the diagonal, it is a root.
The etree has the fundamental property that if $L_{ij} \neq 0$ for $i > j$, then node $i$ is an ancestor of node $j$ in the etree.

### Construction
The etree can be built in $\mathcal{O}(|V| + |E|\alpha(|V|))$ time using a disjoint-set data structure, where $\alpha$ is the inverse Ackermann function, working directly from the original graph adjacency structure without simulating the fill-in process.

## Symbolic Factorization

Symbolic factorization determines the precise non-zero structure of $L$ (the row indices of the non-zeros in each column) in optimal $\mathcal{O}(|L|)$ time, avoiding $\mathcal{O}(n^2)$ density checks.

It achieves this by traversing the elimination tree. The non-zero structure of column $j$, denoted $\mathcal{L}_j = \{ i > j : L_{ij} \neq 0 \}$, is computed recursively from its children in the etree and its neighbors in $A$:

$\mathcal{L}_j = \mathcal{A}_j \cup \bigcup_{c \text{ is child of } j} ( \mathcal{L}_c \setminus \{j\} )$

where $\mathcal{A}_j = \{ i > j : A_{ij} \neq 0 \}$ are the original graph edges for vertex $j$.

### Fast Numeric Factorization

With the non-zero structure of $L$ pre-computed via Symbolic Factorization, the left-looking numerical factorization is accelerated because the exact dependencies (which columns $k$ affect column $j$) are known.
Instead of scanning $k < j$, we can dynamically traverse the dependency graph or simply use the established sparsity structure $L$ as a skeleton to safely apply the required multiply-adds.