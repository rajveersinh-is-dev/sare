import math
from typing import List, Tuple, Optional
from .sare_reference import Graph

class SparseMatrix:
    """A simple Compressed Sparse Column (CSC) format matrix representation."""
    def __init__(self, n: int, col_ptrs: List[int], row_indices: List[int], values: List[float]):
        self.n = n
        self.col_ptrs = col_ptrs
        self.row_indices = row_indices
        self.values = values

def graph_to_spd_csc(graph: Graph, order: List[int], alpha: float = 2.0) -> SparseMatrix:
    """
    Converts a Graph into a symmetric positive definite (SPD) SparseMatrix in CSC format,
    permuted according to `order`.

    A = alpha * I + D_adj, where D_adj is the adjacency matrix with 1s.
    alpha must be large enough to ensure A is positive definite.
    """
    n = graph.n
    inv_order = [0] * n
    for i, v in enumerate(order):
        inv_order[v] = i

    col_ptrs = [0] * (n + 1)
    row_indices = []
    values = []

    for j in range(n):
        orig_u = order[j]

        # Diagonal element
        row_indices.append(j)
        values.append(alpha + graph.degree(orig_u)) # strictly diagonally dominant

        # Off-diagonal elements (lower triangular part in permuted matrix)
        neighbors_in_permuted = []
        for orig_v in graph.adj[orig_u]:
            permuted_v = inv_order[orig_v]
            if permuted_v > j:
                neighbors_in_permuted.append(permuted_v)

        neighbors_in_permuted.sort()
        for r in neighbors_in_permuted:
            row_indices.append(r)
            values.append(-1.0)

        col_ptrs[j + 1] = len(row_indices)

    return SparseMatrix(n, col_ptrs, row_indices, values)

from .symbolic import elimination_tree, symbolic_factorize

def cholesky_factorize(A: SparseMatrix) -> Tuple[SparseMatrix, int]:
    """
    Performs a sparse left-looking Cholesky factorization L L^T = A.
    Returns (L, non_zero_count).

    Assumes A is in CSC format and represents the lower triangular part of a symmetric matrix.
    Raises ValueError if matrix is not positive definite.
    """
    n = A.n

    # 1. Symbolic Factorization phase
    parent = elimination_tree(A)
    L_col_ptrs, L_row_indices = symbolic_factorize(A, parent)
    L_values = [0.0] * len(L_row_indices)

    # We need a quick way to find the index of L_{i, j} in L_values.
    # L_row_indices[L_col_ptrs[j]:L_col_ptrs[j+1]] contains sorted row indices for column j.
    # Since we are building L left-to-right, we can maintain the values directly.

    # We will compute the values in place.
    # L_row_indices is ordered [j, i1, i2...] with i_k > j.

    # We will need to iterate through dependencies. If parent[k] == j, then k affects j.
    # Actually, any column k that has a non-zero at row j affects column j.
    # So we can build a list of columns that update j.
    # Instead of scanning all k < j, we can just use the property that k updates j if L_{j,k} != 0.
    # We can track for each column j, the list of columns k that will update it.

    updates = [[] for _ in range(n)]
    for k in range(n):
        # The first off-diagonal non-zero in column k dictates the first column j that k updates
        # Since L_row_indices[L_col_ptrs[k]] is the diagonal (k), the next is the first off-diagonal
        if L_col_ptrs[k] + 1 < L_col_ptrs[k+1]:
            first_off_diag_idx = L_col_ptrs[k] + 1
            j = L_row_indices[first_off_diag_idx]
            updates[j].append((k, first_off_diag_idx))

    # Workspace
    x = [0.0] * n

    for j in range(n):
        # 1. Gather the j-th column of A into x
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            r = A.row_indices[p]
            x[r] = A.values[p]

        # 2. Subtract L_{j,k} * L_{*,k} for all k that affect j
        for (k, p_jk) in updates[j]:
            L_jk = L_values[p_jk]

            # Apply update from column k to column j
            for p in range(p_jk, L_col_ptrs[k+1]):
                r = L_row_indices[p]
                x[r] -= L_jk * L_values[p]

            # Column k has updated j. The next column it updates is the next non-zero in column k.
            next_p_jk = p_jk + 1
            if next_p_jk < L_col_ptrs[k+1]:
                next_j = L_row_indices[next_p_jk]
                updates[next_j].append((k, next_p_jk))

        # 3. Compute L[j, j]
        if x[j] <= 0.0:
            raise ValueError(f"Matrix is not positive definite at column {j}, diagonal element is {x[j]}")

        L_jj = math.sqrt(x[j])

        diag_p = L_col_ptrs[j]
        assert L_row_indices[diag_p] == j
        L_values[diag_p] = L_jj
        x[j] = 0.0

        # 4. Compute and store L[i, j] for i > j
        for p in range(L_col_ptrs[j] + 1, L_col_ptrs[j+1]):
            i = L_row_indices[p]
            val = x[i] / L_jj
            # In structural symbolic factorization, numerical zeros might appear if exact cancellation happens,
            # but structural non-zeros remain. We store it regardless to maintain structural integrity.
            L_values[p] = val
            x[i] = 0.0

    L = SparseMatrix(n, L_col_ptrs, L_row_indices, L_values)

    # Calculate non-zeros in strict lower triangular part
    # L_col_ptrs[-1] is total non-zeros, including n diagonal elements
    nnz_strict_lower = len(L_row_indices) - n

    return L, nnz_strict_lower

def verify_fill_numerically(graph: Graph, order: List[int], reported_fill: int) -> bool:
    """
    Verifies that the topological reported_fill equals the actual fill generated
    during a numeric Cholesky factorization.
    """
    A = graph_to_spd_csc(graph, order)

    # Calculate original number of edges in strict lower part of A
    orig_edges_lower = 0
    for j in range(graph.n):
        orig_edges_lower += (A.col_ptrs[j+1] - A.col_ptrs[j] - 1) # -1 for diagonal

    L, L_nnz_strict_lower = cholesky_factorize(A)

    calculated_fill = L_nnz_strict_lower - orig_edges_lower

    return calculated_fill == reported_fill
