from typing import List, Tuple, Set
from typing import TYPE_CHECKING
from .sare_reference import Graph

if TYPE_CHECKING:
    from .cholesky import SparseMatrix


def elimination_tree(A: 'SparseMatrix') -> List[int]:
    """
    Computes the elimination tree of a symmetric matrix A.
    Returns a list `parent` where `parent[j]` is the parent of node `j` in the etree.
    If `j` is a root, `parent[j] == -1`.
    Assumes A is in CSC format and represents the lower triangular part (plus diagonal).
    Runs in almost O(|V| + |E|).
    """
    n = A.n

    # Let's just use the classic Liu algorithm:
    # A is symmetric. The standard algorithm requires accessing the lower triangular part by rows,
    # OR upper triangular part by columns.
    # Our CSC matrix A is lower triangular (row >= col). So column j contains elements i >= j.
    # We want to process column i, and look at all j < i such that A_{ij} != 0.
    # To do this efficiently, we can build a row-access representation for the strict lower part.

    row_starts = [0] * (n + 1)
    for j in range(n):
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            i = A.row_indices[p]
            if i > j:
                row_starts[i + 1] += 1

    for i in range(n):
        row_starts[i + 1] += row_starts[i]

    row_cols = [0] * row_starts[n]
    cur_starts = list(row_starts)

    for j in range(n):
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            i = A.row_indices[p]
            if i > j:
                row_cols[cur_starts[i]] = j
                cur_starts[i] += 1

    parent = [-1] * n
    ancestor = [-1] * n

    for i in range(n):
        for p in range(row_starts[i], row_starts[i+1]):
            j = row_cols[p]
            root = j
            while root != -1 and root < i:
                next_root = ancestor[root]
                if next_root != -1 and next_root < i:
                    root = next_root
                else:
                    break

            if root != -1 and root < i:
                ancestor[root] = i
                if parent[root] == -1:
                    parent[root] = i

    return parent

def post_order_etree(parent: List[int]) -> List[int]:
    """
    Computes a post-ordering of the elimination tree.
    Returns a list where the i-th element is the node index.
    """
    n = len(parent)
    first_child = [-1] * n
    next_sibling = [-1] * n

    for i in range(n):
        p = parent[i]
        if p != -1:
            next_sibling[i] = first_child[p]
            first_child[p] = i

    order = []
    stack = []

    for i in range(n):
        if parent[i] == -1:
            stack.append(i)
            while stack:
                curr = stack[-1]
                child = first_child[curr]
                if child != -1:
                    first_child[curr] = next_sibling[child]
                    stack.append(child)
                else:
                    order.append(stack.pop())

    return order

def symbolic_factorize(A: 'SparseMatrix', parent: List[int]) -> Tuple[List[int], List[int]]:
    """
    Computes the exact non-zero structure of L.
    Returns (L_col_ptrs, L_row_indices).
    Runs in O(|L|) time.
    """
    n = A.n
    L_col_ptrs = [0] * (n + 1)

    first_child = [-1] * n
    next_sibling = [-1] * n
    for i in range(n):
        p = parent[i]
        if p != -1:
            next_sibling[i] = first_child[p]
            first_child[p] = i

    L_struct: List[Set[int]] = [set() for _ in range(n)]

    # Process in topological order (bottom up)
    post_order = post_order_etree(parent)

    for j in post_order:
        struct = set()

        # Original edges
        for p in range(A.col_ptrs[j], A.col_ptrs[j+1]):
            i = A.row_indices[p]
            if i > j:
                struct.add(i)

        # Children edges
        c = first_child[j]
        while c != -1:
            for r in L_struct[c]:
                if r > j:
                    struct.add(r)
            c = next_sibling[c]

        L_struct[j] = struct

    L_row_indices = []
    for j in range(n):
        L_row_indices.append(j) # Diagonal
        sorted_struct = sorted(list(L_struct[j]))
        L_row_indices.extend(sorted_struct)
        L_col_ptrs[j+1] = len(L_row_indices)

    return L_col_ptrs, L_row_indices
