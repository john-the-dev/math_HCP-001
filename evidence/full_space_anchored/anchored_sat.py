#!/usr/bin/env python3
"""Exact anchored SAT model for the full 43-vertex HCP-001 space."""
from itertools import combinations
from math import comb
from pathlib import Path
import argparse
import json
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

N = 42
PAIRS = list(combinations(range(N), 2))
EDGE_VAR = {edge: index + 1 for index, edge in enumerate(PAIRS)}
R45_EDGE_BOUNDS = {
    18: (50, 85),
    19: (57, 92),
    20: (68, 100),
    22: (88, 114),
    23: (101, 122),
    24: (116, 132),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge_var(u, v):
    return EDGE_VAR[(u, v) if u < v else (v, u)]


def edge_bounds(degree):
    return (41 * degree + 1) // 2, 451 - degree


def a_internal_bounds(degree):
    return max(0, degree - 18), 13


def a_total_degree_bounds(degree, a_internal_degree):
    return (max(degree - 1, a_internal_degree),
            min(23, a_internal_degree + N - degree))


def b_minimum_internal_bounds(degree):
    b_size = N - degree
    _, b_maximum_edges = block_edge_bounds(degree)[1]
    return 28 - degree, (2 * b_maximum_edges) // b_size


def block_edge_bounds(degree):
    a_minimum, a_maximum = R45_EDGE_BOUNDS[degree]
    b_size = N - degree
    complement_minimum, complement_maximum = R45_EDGE_BOUNDS[b_size]
    b_total = comb(b_size, 2)
    return ((a_minimum, a_maximum),
            (b_total - complement_maximum, b_total - complement_minimum))


def block_edges(degree):
    a_edges = [edge_var(u, v) for u, v in combinations(range(degree), 2)]
    b_edges = [edge_var(u, v)
               for u, v in combinations(range(degree, N), 2)]
    return a_edges, b_edges


def block_internal_degree_bounds(degree):
    """Return closed internal-degree bounds for vertices in A and B."""
    return ((max(0, degree - 18), 13), (28 - degree, 17))


def block_internal_degrees(degree):
    blocks = (range(degree), range(degree, N))
    return tuple([[edge_var(u, v) for v in block if v != u]
                  for u in block] for block in blocks)


def block_internal_degree_clauses(degree, pool):
    clauses = []
    for vertex_edges, (minimum, maximum) in zip(
            block_internal_degrees(degree),
            block_internal_degree_bounds(degree)):
        for edges in vertex_edges:
            clauses.extend(CardEnc.atleast(
                edges, bound=minimum, vpool=pool,
                encoding=EncType.seqcounter).clauses)
            clauses.extend(CardEnc.atmost(
                edges, bound=maximum, vpool=pool,
                encoding=EncType.seqcounter).clauses)
    return clauses


def _conditional_conjunction_atmost(conjunctions, bound, condition, pool,
                                    encoding=EncType.seqcounter):
    indicators = []
    clauses = []
    for conjunction in conjunctions:
        indicator = pool.id()
        indicators.append(indicator)
        # condition is a signed literal; -condition intentionally flips it.
        clauses.append(
            [indicator] + [-literal for literal in conjunction] + [-condition])
    encoded = CardEnc.atmost(
        indicators, bound=bound, vpool=pool,
        encoding=encoding).clauses
    clauses.extend([[-condition] + clause for clause in encoded])
    return clauses


def block_pair_common_clauses(degree, pool):
    """Encode block common-set bounds; three require solve()'s K5/I5 clauses."""
    clauses = []
    for block_name, vertices in (("A", range(degree)),
                                 ("B", range(degree, N))):
        vertices = list(vertices)
        for u, v in combinations(vertices, 2):
            edge = edge_var(u, v)
            others = [w for w in vertices if w not in (u, v)]
            neighbor_bound = 4 if block_name == "A" else 8
            nonneighbor_bound = 8 if block_name == "A" else 4
            clauses.extend(_conditional_conjunction_atmost(
                ((edge_var(u, w), edge_var(v, w)) for w in others),
                neighbor_bound, edge, pool))
            clauses.extend(_conditional_conjunction_atmost(
                ((-edge_var(u, w), -edge_var(v, w)) for w in others),
                nonneighbor_bound, -edge, pool))
    return clauses


def global_pair_common_clauses(pool):
    """Encode whole-H common-set bounds; requires global K5/I5 clauses."""
    clauses = []
    for u, v in combinations(range(N), 2):
        edge = edge_var(u, v)
        others = [w for w in range(N) if w not in (u, v)]
        clauses.extend(_conditional_conjunction_atmost(
            ((edge_var(u, w), edge_var(v, w)) for w in others),
            13, edge, pool, EncType.kmtotalizer))
        clauses.extend(_conditional_conjunction_atmost(
            ((-edge_var(u, w), -edge_var(v, w)) for w in others),
            13, -edge, pool, EncType.kmtotalizer))
    return clauses


def block_edge_clauses(degree, pool, a_edge_count=None):
    clauses = []
    for index, (edges, (minimum, maximum)) in enumerate(zip(
            block_edges(degree), block_edge_bounds(degree))):
        if index == 0 and a_edge_count is not None:
            clauses.extend(CardEnc.equals(
                edges, bound=a_edge_count, vpool=pool,
                encoding=EncType.seqcounter).clauses)
        else:
            clauses.extend(CardEnc.atleast(
                edges, bound=minimum, vpool=pool,
                encoding=EncType.seqcounter).clauses)
            clauses.extend(CardEnc.atmost(
                edges, bound=maximum, vpool=pool,
                encoding=EncType.seqcounter).clauses)
    return clauses


def degree_leq_clauses(u, w, pool):
    """Encode deg_H(u) <= deg_H(w); their shared edge cancels."""
    left = [edge_var(u, x) for x in range(N) if x not in (u, w)]
    right = [edge_var(w, x) for x in range(N) if x not in (u, w)]
    return CardEnc.atmost(
        left + [-var for var in right], bound=N - 2,
        vpool=pool, encoding=EncType.seqcounter).clauses


def internal_degree_leq_clauses(u, w, vertices, pool):
    """Encode deg_block(u) <= deg_block(w); their shared edge cancels."""
    left = [edge_var(u, x) for x in vertices if x not in (u, w)]
    right = [edge_var(w, x) for x in vertices if x not in (u, w)]
    return CardEnc.atmost(
        left + [-var for var in right], bound=len(vertices) - 2,
        vpool=pool, encoding=EncType.seqcounter).clauses


def core_clauses(degree, edge_count=None, a_internal_degree=None,
                 enforce_block_edge_bounds=True, a_edge_count=None,
                 enforce_block_degree_bounds=True,
                 enforce_block_pair_common_bounds=True,
                 b_internal_degree=None,
                 enforce_global_pair_common_bounds=True,
                 a_total_degree=None):
    require(degree in (18, 19, 20), "degree must be 18, 19, or 20")
    minimum, maximum = edge_bounds(degree)
    if edge_count is not None:
        require(minimum <= edge_count <= maximum,
                f"edge count must be in {minimum}..{maximum}")
    if a_internal_degree is not None:
        lower_j, upper_j = a_internal_bounds(degree)
        require(lower_j <= a_internal_degree <= upper_j,
                f"A-internal degree must be in {lower_j}..{upper_j}")
    if a_total_degree is not None:
        require(a_internal_degree is not None,
                "A-total degree requires A-internal degree")
        lower_t, upper_t = a_total_degree_bounds(
            degree, a_internal_degree)
        require(lower_t <= a_total_degree <= upper_t,
                f"A-total degree must be in {lower_t}..{upper_t}")
    if b_internal_degree is not None:
        lower_k, upper_k = b_minimum_internal_bounds(degree)
        require(lower_k <= b_internal_degree <= upper_k,
                f"minimum B-internal degree must be in {lower_k}..{upper_k}")
    if a_edge_count is not None:
        lower_a, upper_a = block_edge_bounds(degree)[0]
        require(lower_a <= a_edge_count <= upper_a,
                f"A edge count must be in {lower_a}..{upper_a}")

    pool = IDPool(start_from=len(PAIRS) + 1)
    clauses = []
    block_a = range(degree)
    block_b = range(degree, N)

    for vertices in combinations(block_a, 4):
        clauses.append([-edge_var(u, v) for u, v in combinations(vertices, 2)])
    for vertices in combinations(block_b, 4):
        clauses.append([edge_var(u, v) for u, v in combinations(vertices, 2)])

    if enforce_block_edge_bounds:
        clauses.extend(block_edge_clauses(degree, pool, a_edge_count))
    elif a_edge_count is not None:
        clauses.extend(CardEnc.equals(
            block_edges(degree)[0], bound=a_edge_count, vpool=pool,
            encoding=EncType.seqcounter).clauses)

    if enforce_block_degree_bounds:
        clauses.extend(block_internal_degree_clauses(degree, pool))

    if enforce_block_pair_common_bounds:
        clauses.extend(block_pair_common_clauses(degree, pool))

    if enforce_global_pair_common_bounds:
        clauses.extend(global_pair_common_clauses(pool))

    for u in range(N):
        incident = [edge_var(u, v) for v in range(N) if v != u]
        lower = degree - 1 if u < degree else degree
        upper = 23 if u < degree else 24
        clauses.extend(CardEnc.atleast(
            incident, bound=lower, vpool=pool, encoding=EncType.seqcounter).clauses)
        clauses.extend(CardEnc.atmost(
            incident, bound=upper, vpool=pool, encoding=EncType.seqcounter).clauses)

    if a_internal_degree is None:
        a_symmetry_blocks = (list(block_a),)
    else:
        j = a_internal_degree
        for vertex in range(1, degree):
            clauses.append([edge_var(0, vertex) if vertex <= j
                            else -edge_var(0, vertex)])

        # Choose vertex 0 to have minimum degree in A, then sort only within
        # the residual symmetry blocks preserved by its fixed neighborhood.
        for vertex in range(1, degree):
            clauses.extend(degree_leq_clauses(0, vertex, pool))
        if a_total_degree is not None:
            incident = [edge_var(0, vertex) for vertex in range(1, N)]
            clauses.extend(CardEnc.equals(
                incident, bound=a_total_degree, vpool=pool,
                encoding=EncType.seqcounter).clauses)
        a_symmetry_blocks = (
            list(range(1, j + 1)),
            list(range(j + 1, degree)),
        )

    if b_internal_degree is None:
        b_symmetry_blocks = (list(block_b),)
    else:
        k = b_internal_degree
        distinguished_b = degree
        neighbor_end = distinguished_b + k
        for vertex in range(distinguished_b + 1, N):
            clauses.append([
                edge_var(distinguished_b, vertex)
                if vertex <= neighbor_end
                else -edge_var(distinguished_b, vertex)
            ])
        for vertex in range(distinguished_b + 1, N):
            clauses.extend(internal_degree_leq_clauses(
                distinguished_b, vertex, block_b, pool))
        b_symmetry_blocks = (
            list(range(distinguished_b + 1, neighbor_end + 1)),
            list(range(neighbor_end + 1, N)),
        )

    for block in a_symmetry_blocks + b_symmetry_blocks:
        for u, w in zip(block, block[1:]):
            clauses.extend(degree_leq_clauses(u, w, pool))

    edges = list(EDGE_VAR.values())
    if edge_count is None:
        clauses.extend(CardEnc.atmost(
            edges, bound=maximum, vpool=pool, encoding=EncType.seqcounter).clauses)
    else:
        clauses.extend(CardEnc.equals(
            edges, bound=edge_count, vpool=pool, encoding=EncType.seqcounter).clauses)
    return clauses, pool.top


def five_set_clauses():
    for vertices in combinations(range(N), 5):
        variables = [edge_var(u, v) for u, v in combinations(vertices, 2)]
        yield variables
        yield [-var for var in variables]


def model_adjacency(model):
    positive = {literal for literal in model if literal > 0}
    adjacency = [0] * N
    for (u, v), variable in EDGE_VAR.items():
        if variable in positive:
            adjacency[u] |= 1 << v
            adjacency[v] |= 1 << u
    return adjacency


def verify_block_edge_bounds(adjacency, degree):
    counts = []
    for vertices in (range(degree), range(degree, N)):
        counts.append(sum((adjacency[u] >> v) & 1
                          for u, v in combinations(vertices, 2)))
    for name, count, (minimum, maximum) in zip(
            ("A", "B"), counts, block_edge_bounds(degree)):
        require(minimum <= count <= maximum,
                f"{name}-block edge bound violated")
    return {"a_edges": counts[0], "b_edges": counts[1]}


def verify_block_internal_degree_bounds(adjacency, degree):
    result = {}
    for name, vertices, (minimum, maximum) in zip(
            ("A", "B"), (range(degree), range(degree, N)),
            block_internal_degree_bounds(degree)):
        values = [sum((adjacency[u] >> v) & 1
                      for v in vertices if v != u)
                  for u in vertices]
        require(all(minimum <= value <= maximum for value in values),
                f"{name}-block internal degree bound violated")
        result[f"{name.lower()}_internal_degrees"] = values
    return result


def verify_block_pair_common_bounds(adjacency, degree):
    maxima = {"a_common_neighbors": 0, "a_common_nonneighbors": 0,
              "b_common_neighbors": 0, "b_common_nonneighbors": 0}
    for name, vertices in (("A", range(degree)), ("B", range(degree, N))):
        vertices = list(vertices)
        for u, v in combinations(vertices, 2):
            adjacent = bool((adjacency[u] >> v) & 1)
            if adjacent:
                count = sum(bool((adjacency[u] >> w) & 1)
                            and bool((adjacency[v] >> w) & 1)
                            for w in vertices if w not in (u, v))
                bound = 4 if name == "A" else 8
                key = f"{name.lower()}_common_neighbors"
            else:
                count = sum(not ((adjacency[u] >> w) & 1)
                            and not ((adjacency[v] >> w) & 1)
                            for w in vertices if w not in (u, v))
                bound = 8 if name == "A" else 4
                key = f"{name.lower()}_common_nonneighbors"
            require(count <= bound,
                    f"{name}-block pair common-set bound violated")
            maxima[key] = max(maxima[key], count)
    return maxima


def verify_global_pair_common_bounds(adjacency):
    maxima = {"global_common_neighbors": 0,
              "global_common_nonneighbors": 0}
    for u, v in combinations(range(N), 2):
        adjacent = bool((adjacency[u] >> v) & 1)
        if adjacent:
            count = sum(bool((adjacency[u] >> w) & 1)
                        and bool((adjacency[v] >> w) & 1)
                        for w in range(N) if w not in (u, v))
            key = "global_common_neighbors"
        else:
            count = sum(not ((adjacency[u] >> w) & 1)
                        and not ((adjacency[v] >> w) & 1)
                        for w in range(N) if w not in (u, v))
            key = "global_common_nonneighbors"
        require(count <= 13, "global pair common-set bound violated")
        maxima[key] = max(maxima[key], count)
    return maxima


def verify_distinguished_a(adjacency, degree, a_internal_degree,
                           a_total_degree=None, degrees=None):
    j = a_internal_degree
    if degrees is None:
        degrees = [row.bit_count() for row in adjacency]
    require(sum((adjacency[0] >> vertex) & 1
                for vertex in range(1, degree)) == j,
            "distinguished A-internal degree violated")
    for vertex in range(1, degree):
        require(bool((adjacency[0] >> vertex) & 1) == (vertex <= j),
                "fixed distinguished neighborhood violated")
    require(all(degrees[0] <= degrees[vertex]
                for vertex in range(1, degree)),
            "distinguished vertex is not minimum-degree in A")
    if a_total_degree is not None:
        require(degrees[0] == a_total_degree,
                "distinguished A-total degree violated")
    for block in (degrees[1:j + 1], degrees[j + 1:degree]):
        require(block == sorted(block), "residual A block is unsorted")
    return degrees[0]


def verify_distinguished_b(adjacency, degree, b_internal_degree, degrees=None):
    block_b = range(degree, N)
    distinguished_b = degree
    k = b_internal_degree
    internal_degrees = [sum((adjacency[u] >> v) & 1
                            for v in block_b if v != u)
                        for u in block_b]
    require(internal_degrees[0] == k,
            "distinguished B-internal degree violated")
    neighbor_end = distinguished_b + k
    for vertex in range(distinguished_b + 1, N):
        require(bool((adjacency[distinguished_b] >> vertex) & 1)
                == (vertex <= neighbor_end),
                "fixed distinguished B neighborhood violated")
    require(all(internal_degrees[0] <= value
                for value in internal_degrees[1:]),
            "distinguished vertex is not minimum-internal-degree in B")
    if degrees is None:
        degrees = [row.bit_count() for row in adjacency]
    for block in (degrees[distinguished_b + 1:neighbor_end + 1],
                  degrees[neighbor_end + 1:N]):
        require(block == sorted(block), "residual B block is unsorted")
    return internal_degrees


def verify_model(adjacency, degree, edge_count=None, a_internal_degree=None,
                 enforce_block_edge_bounds=True, a_edge_count=None,
                 enforce_block_degree_bounds=True,
                 enforce_block_pair_common_bounds=True,
                 b_internal_degree=None,
                 enforce_global_pair_common_bounds=True,
                 a_total_degree=None):
    require(len(adjacency) == N, "model must contain 42 adjacency rows")
    for u in range(N):
        require(not (adjacency[u] >> u) & 1, "self edge")
        for v in range(N):
            require(((adjacency[u] >> v) & 1) == ((adjacency[v] >> u) & 1),
                    "asymmetric adjacency")

    actual_edges = sum(row.bit_count() for row in adjacency) // 2
    minimum, maximum = edge_bounds(degree)
    require(minimum <= actual_edges <= maximum, "edge bound violated")
    if edge_count is not None:
        require(actual_edges == edge_count, "edge partition violated")
    block_counts = (verify_block_edge_bounds(adjacency, degree)
                    if enforce_block_edge_bounds else None)
    actual_a_edges = sum((adjacency[u] >> v) & 1
                         for u, v in combinations(range(degree), 2))
    if a_edge_count is not None:
        require(actual_a_edges == a_edge_count,
                "A edge partition violated")
    block_degrees = (verify_block_internal_degree_bounds(adjacency, degree)
                     if enforce_block_degree_bounds else None)
    pair_common = (verify_block_pair_common_bounds(adjacency, degree)
                   if enforce_block_pair_common_bounds else None)
    global_pair_common = (verify_global_pair_common_bounds(adjacency)
                          if enforce_global_pair_common_bounds else None)

    degrees = [row.bit_count() for row in adjacency]
    for u, value in enumerate(degrees):
        lower = degree - 1 if u < degree else degree
        upper = 23 if u < degree else 24
        require(lower <= value <= upper, "degree bound violated")
    if a_internal_degree is None:
        require(degrees[:degree] == sorted(degrees[:degree]), "A degrees unsorted")
    else:
        verify_distinguished_a(
            adjacency, degree, a_internal_degree, a_total_degree, degrees)
    if b_internal_degree is None:
        require(degrees[degree:] == sorted(degrees[degree:]),
                "B degrees unsorted")
    else:
        verify_distinguished_b(
            adjacency, degree, b_internal_degree, degrees)

    for vertices in combinations(range(degree), 4):
        require(not all((adjacency[u] >> v) & 1
                        for u, v in combinations(vertices, 2)), "K4 in A")
    for vertices in combinations(range(degree, N), 4):
        require(not all(not ((adjacency[u] >> v) & 1)
                        for u, v in combinations(vertices, 2)), "I4 in B")
    for vertices in combinations(range(N), 5):
        count = sum((adjacency[u] >> v) & 1
                    for u, v in combinations(vertices, 2))
        require(count not in (0, 10), "forbidden 5-set in H")
    result = {"edges": actual_edges, "degrees": degrees}
    if block_counts is not None:
        result.update(block_counts)
    elif a_edge_count is not None:
        result["a_edges"] = actual_a_edges
    if block_degrees is not None:
        result.update(block_degrees)
    if pair_common is not None:
        result.update(pair_common)
    if global_pair_common is not None:
        result.update(global_pair_common)
    return result


def write_dimacs(path, clauses, top):
    total = len(clauses) + 2 * comb(N, 5)
    with path.open("w") as stream:
        stream.write(f"p cnf {top} {total}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + " 0\n")
        for clause in five_set_clauses():
            stream.write(" ".join(map(str, clause)) + " 0\n")
    return total


def solve(args):
    clauses, top = core_clauses(
        degree=args.degree,
        edge_count=args.edges,
        a_internal_degree=args.a_internal_degree,
        enforce_block_edge_bounds=not args.no_block_edge_bounds,
        a_edge_count=args.a_edges,
        enforce_block_degree_bounds=not args.no_block_degree_bounds,
        enforce_block_pair_common_bounds=not args.no_block_pair_common_bounds,
        b_internal_degree=args.b_internal_degree,
        enforce_global_pair_common_bounds=(
            not args.no_global_pair_common_bounds),
        a_total_degree=args.a_total_degree)
    expected_clauses = len(clauses) + 2 * comb(N, 5)
    if args.cnf:
        written = write_dimacs(Path(args.cnf), clauses, top)
        require(written == expected_clauses, "DIMACS clause-count mismatch")

    started = time.perf_counter()
    partition_line = (f"degree={args.degree} edge_partition={args.edges} "
                      f"a_internal_degree={args.a_internal_degree} ")
    if args.a_total_degree is not None:
        partition_line += f"a_total_degree={args.a_total_degree} "
    if args.b_internal_degree is not None:
        partition_line += f"b_internal_degree={args.b_internal_degree} "
    print(partition_line + f"a_edge_partition={args.a_edges}")
    print(f"block_edge_bounds={'disabled' if args.no_block_edge_bounds else 'enabled'}")
    print(f"block_degree_bounds={'disabled' if args.no_block_degree_bounds else 'enabled'}")
    print("block_pair_common_bounds="
          f"{'disabled' if args.no_block_pair_common_bounds else 'enabled'}")
    print("global_pair_common_bounds="
          f"{'disabled' if args.no_global_pair_common_bounds else 'enabled'}")
    print(f"edge_vars={len(PAIRS)} vars_with_encoding={top}")
    print(f"core_clauses={len(clauses)} total_clauses={expected_clauses}", flush=True)
    with Solver(name=args.solver, bootstrap_with=clauses,
                with_proof=bool(args.proof)) as solver:
        for index, clause in enumerate(five_set_clauses(), 1):
            solver.add_clause(clause)
            if index % 200000 == 0:
                print(f"five_set_clauses_added={index}", flush=True)
        require(index == 2 * comb(N, 5), "global clause-count mismatch")
        sat = solver.solve()
        result = "SAT" if sat else "UNSAT"
        print(f"result={result}")
        record = {
            "degree": args.degree,
            "edge_partition": args.edges,
            "a_internal_degree": args.a_internal_degree,
            "a_total_degree": args.a_total_degree,
            "a_edge_partition": args.a_edges,
            "block_edge_bounds": not args.no_block_edge_bounds,
            "block_degree_bounds": not args.no_block_degree_bounds,
            "block_pair_common_bounds": not args.no_block_pair_common_bounds,
            "global_pair_common_bounds": not args.no_global_pair_common_bounds,
            "solver": args.solver,
            "result": result,
            "vars": top,
            "clauses": expected_clauses,
            "stats": solver.accum_stats(),
            "runtime_seconds": round(time.perf_counter() - started, 2),
        }
        if args.b_internal_degree is not None:
            record["b_internal_degree"] = args.b_internal_degree
        if sat:
            adjacency = model_adjacency(solver.get_model())
            record["verification"] = verify_model(
                adjacency=adjacency,
                degree=args.degree,
                edge_count=args.edges,
                a_internal_degree=args.a_internal_degree,
                enforce_block_edge_bounds=not args.no_block_edge_bounds,
                a_edge_count=args.a_edges,
                enforce_block_degree_bounds=not args.no_block_degree_bounds,
                enforce_block_pair_common_bounds=(
                    not args.no_block_pair_common_bounds),
                b_internal_degree=args.b_internal_degree,
                enforce_global_pair_common_bounds=(
                    not args.no_global_pair_common_bounds),
                a_total_degree=args.a_total_degree)
            record["adjacency_hex"] = [f"{row:011x}" for row in adjacency]
        elif args.proof:
            proof = solver.get_proof()
            require(proof is not None, "solver returned no proof object")
            Path(args.proof).write_text("\n".join(proof) + "\n")
            record["proof_lines"] = len(proof)
        if args.json:
            Path(args.json).write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, sort_keys=True))


def write_manifest(path, mode):
    partitions = []
    for degree in (18, 19, 20):
        minimum, maximum = edge_bounds(degree)
        minimum_j, maximum_j = a_internal_bounds(degree)
        if mode == "edge-j":
            axes = ((edge_count, j)
                    for edge_count in range(minimum, maximum + 1)
                    for j in range(minimum_j, maximum_j + 1))
        elif mode == "a-edge-j":
            lower_a, upper_a = block_edge_bounds(degree)[0]
            axes = ((a_edge_count, j)
                    for a_edge_count in range(lower_a, upper_a + 1)
                    for j in range(minimum_j, maximum_j + 1))
        elif mode == "j-k":
            minimum_k, maximum_k = b_minimum_internal_bounds(degree)
            axes = ((k, j)
                    for j in range(minimum_j, maximum_j + 1)
                    for k in range(minimum_k, maximum_k + 1))
        elif mode == "j-t-k":
            minimum_k, maximum_k = b_minimum_internal_bounds(degree)
            axes = (((k, t), j)
                    for j in range(minimum_j, maximum_j + 1)
                    for t in range(a_total_degree_bounds(degree, j)[0],
                                   a_total_degree_bounds(degree, j)[1] + 1)
                    for k in range(minimum_k, maximum_k + 1))
        else:
            axes = ((None, j) for j in range(minimum_j, maximum_j + 1))
        for partition_value, j in axes:
            edge_count = partition_value if mode == "edge-j" else None
            a_edge_count = partition_value if mode == "a-edge-j" else None
            b_internal_degree = partition_value if mode == "j-k" else None
            if mode == "j-t-k":
                b_internal_degree, a_total_degree = partition_value
            else:
                a_total_degree = None
            edge_part = f"-e{edge_count}" if edge_count is not None else ""
            a_edge_part = (f"-a{a_edge_count}"
                           if a_edge_count is not None else "")
            b_degree_part = (f"-k{b_internal_degree}"
                             if b_internal_degree is not None else "")
            a_total_part = (f"-t{a_total_degree}"
                            if a_total_degree is not None else "")
            key = (f"d{degree}{edge_part}{a_edge_part}-j{j}"
                   f"{a_total_part}{b_degree_part}")
            row = {
                "id": key,
                "degree": degree,
                "edges": edge_count,
                "a_internal_degree": j,
                "cnf": f"{key}.cnf",
                "proof": f"{key}.drat",
                "result": f"{key}.json",
            }
            if mode == "j-only":
                row.update(edge_min=minimum, edge_max=maximum)
            elif mode == "a-edge-j":
                lower_a, upper_a = block_edge_bounds(degree)[0]
                row.update(a_edges=a_edge_count, a_edge_min=lower_a,
                           a_edge_max=upper_a)
            elif mode == "j-k":
                minimum_k, maximum_k = b_minimum_internal_bounds(degree)
                row.update(b_internal_degree=b_internal_degree,
                           b_internal_degree_min=minimum_k,
                           b_internal_degree_max=maximum_k,
                           edge_min=minimum, edge_max=maximum)
            elif mode == "j-t-k":
                minimum_k, maximum_k = b_minimum_internal_bounds(degree)
                minimum_t, maximum_t = a_total_degree_bounds(degree, j)
                row.update(a_total_degree=a_total_degree,
                           a_total_degree_min=minimum_t,
                           a_total_degree_max=maximum_t,
                           b_internal_degree=b_internal_degree,
                           b_internal_degree_min=minimum_k,
                           b_internal_degree_max=maximum_k,
                           edge_min=minimum, edge_max=maximum)
            partitions.append(row)
    manifest = {
        "schema": 1,
        "vertex_count": 43,
        "mode": mode,
        "coverage": (
            "d in {18,19,20}; j is the A-internal degree of a chosen "
            "minimum-degree vertex of A; "
            + ("every admissible H edge count is fixed"
               if mode == "edge-j" else
               "every admissible E(A) count is fixed"
               if mode == "a-edge-j" else
               "k is the B-internal degree of a chosen minimum-internal-"
               "degree vertex of B; every admissible k is fixed"
               if mode == "j-k" else
               "t is the full H-degree of the distinguished A vertex and "
               "k is the minimum B-internal degree; every admissible "
               "(t,k) pair is fixed"
               if mode == "j-t-k" else
               "H edge count is not fixed, with the degree-implied lower "
               "bound and |E(H)| <= 451-d enforced inside each formula")
        ),
        "partition_count": len(partitions),
        "partitions": partitions,
    }
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(partitions)} partitions to {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--degree", type=int, choices=(18, 19, 20))
    parser.add_argument("--edges", type=int)
    parser.add_argument("--a-edges", type=int)
    parser.add_argument("--a-internal-degree", type=int)
    parser.add_argument("--a-total-degree", type=int)
    parser.add_argument("--b-internal-degree", type=int)
    parser.add_argument(
        "--no-block-edge-bounds", action="store_true",
        help="disable sound R(4,5,n) block-edge bounds for diagnostics")
    parser.add_argument(
        "--no-block-degree-bounds", action="store_true",
        help="disable sound per-vertex block-degree bounds for diagnostics")
    parser.add_argument(
        "--no-block-pair-common-bounds", action="store_true",
        help="disable sound within-block pair common-set bounds for diagnostics")
    parser.add_argument(
        "--no-global-pair-common-bounds", action="store_true",
        help="disable sound whole-H pair common-set bounds for diagnostics")
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--cnf")
    parser.add_argument("--proof")
    parser.add_argument("--json")
    parser.add_argument("--list-partitions", action="store_true")
    parser.add_argument("--write-manifest")
    parser.add_argument("--manifest-mode",
                        choices=("edge-j", "j-only", "a-edge-j", "j-k",
                                 "j-t-k"),
                        default="edge-j")
    args = parser.parse_args()
    if args.write_manifest:
        write_manifest(args.write_manifest, args.manifest_mode)
        return
    if args.list_partitions:
        for degree in (18, 19, 20):
            minimum, maximum = edge_bounds(degree)
            print(f"degree={degree} edges={minimum}..{maximum} partitions={maximum-minimum+1}")
        return
    require(args.degree is not None, "--degree is required")
    if args.proof:
        require(args.cnf, "--proof requires --cnf for independent checking")
        require(args.solver in ("glucose3", "glucose4", "lingeling"),
                "select a proof-producing solver")
    solve(args)


if __name__ == "__main__":
    main()
