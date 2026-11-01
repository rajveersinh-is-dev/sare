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

def cholesky_factorize(A: SparseMatrix) -> Tuple[SparseMatrix, int]:
    """
    Performs a sparse left-looking Cholesky factorization L L^T = A.
    Returns (L, non_zero_count).

    Assumes A is in CSC format and represents the lower triangular part of a symmetric matrix.
    Raises ValueError if matrix is not positive definite.
    """
    n = A.n
    L_col_ptrs = [0] * (n + 1)
    L_row_indices = []
    L_values = []

    # Workspace
    x = [0.0] * n
    non_zero = [False] * n

    for j in range(n):
        # 1. Gather the j-th column of A into x
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            r = A.row_indices[p]
            x[r] = A.values[p]
            non_zero[r] = True

        # 2. Subtract L_{j,k} * L_{*,k} for k < j
        # Find which columns k of L affect column j.
        # A simple, albeit slightly less efficient way: check all k < j.
        # In a true left-looking sparse, we'd use a reachability search (elimination tree).
        # We'll use a simplified symbolic phase on the fly.

        # We need to find k < j such that L[j, k] != 0
        for k in range(j):
            L_jk = 0.0
            # Check if L_{j,k} is non-zero
            for p in range(L_col_ptrs[k], L_col_ptrs[k+1]):
                if L_row_indices[p] == j:
                    L_jk = L_values[p]
                    break

            if L_jk != 0.0:
                for p in range(L_col_ptrs[k], L_col_ptrs[k+1]):
                    r = L_row_indices[p]
                    if r >= j:
                        if not non_zero[r]:
                            non_zero[r] = True
                        x[r] -= L_jk * L_values[p]

        # 3. Compute L[j, j]
        if x[j] <= 0.0:
            raise ValueError(f"Matrix is not positive definite at column {j}, diagonal element is {x[j]}")

        L_jj = math.sqrt(x[j])

        # Store L_{j, j}
        L_row_indices.append(j)
        L_values.append(L_jj)

        # Reset x[j] and non_zero flag
        x[j] = 0.0
        non_zero[j] = False

        # 4. Compute and store L[i, j] for i > j
        for i in range(j + 1, n):
            if non_zero[i]:
                val = x[i] / L_jj
                if abs(val) > 1e-12: # Threshold for numerical zeros
                    L_row_indices.append(i)
                    L_values.append(val)
                x[i] = 0.0
                non_zero[i] = False

        L_col_ptrs[j + 1] = len(L_row_indices)

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
