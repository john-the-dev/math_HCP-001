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


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge_var(u, v):
    return EDGE_VAR[(u, v) if u < v else (v, u)]


def edge_bounds(degree):
    return (41 * degree + 1) // 2, 451 - degree


def a_internal_bounds(degree):
    return max(0, degree - 18), 13


def degree_leq_clauses(u, w, pool):
    """Encode deg_H(u) <= deg_H(w); their shared edge cancels."""
    left = [edge_var(u, x) for x in range(N) if x not in (u, w)]
    right = [edge_var(w, x) for x in range(N) if x not in (u, w)]
    return CardEnc.atmost(
        left + [-var for var in right], bound=N - 2,
        vpool=pool, encoding=EncType.seqcounter).clauses


def conditional_conjunction_atmost(clauses, pool, conjunctions, bound, guard):
    """Add guard => AtMost(bound, conjunctions), exact after projection."""
    disabled = [-literal for literal in guard]
    indicators = []
    for conjunction in conjunctions:
        indicator = pool.id()
        indicators.append(indicator)
        clauses.append(
            [indicator] + [-literal for literal in conjunction] + disabled)
    encoding = CardEnc.atmost(
        indicators, bound=bound, vpool=pool, encoding=EncType.seqcounter)
    clauses.extend(clause + disabled for clause in encoding.clauses)


def propagation_cut_clauses(clauses, pool, mode):
    require(mode in ("none", "pair", "triple", "all"),
            "propagation cuts must be none, pair, triple, or all")
    if mode in ("pair", "all"):
        for u, v in PAIRS:
            others = [w for w in range(N) if w not in (u, v)]
            conditional_conjunction_atmost(
                clauses, pool,
                ((edge_var(u, w), edge_var(v, w)) for w in others),
                13, (edge_var(u, v),))
            conditional_conjunction_atmost(
                clauses, pool,
                ((-edge_var(u, w), -edge_var(v, w)) for w in others),
                13, (-edge_var(u, v),))
    if mode in ("triple", "all"):
        for u, v, w in combinations(range(N), 3):
            others = [z for z in range(N) if z not in (u, v, w)]
            triangle = (edge_var(u, v), edge_var(u, w), edge_var(v, w))
            conditional_conjunction_atmost(
                clauses, pool,
                ((edge_var(u, z), edge_var(v, z), edge_var(w, z))
                 for z in others),
                4, triangle)
            conditional_conjunction_atmost(
                clauses, pool,
                ((-edge_var(u, z), -edge_var(v, z), -edge_var(w, z))
                 for z in others),
                4, tuple(-literal for literal in triangle))


def core_clauses(degree, edge_count=None, a_internal_degree=None,
                 propagation_cuts="none"):
    require(degree in (18, 19, 20), "degree must be 18, 19, or 20")
    minimum, maximum = edge_bounds(degree)
    if edge_count is not None:
        require(minimum <= edge_count <= maximum,
                f"edge count must be in {minimum}..{maximum}")
    if a_internal_degree is not None:
        lower_j, upper_j = a_internal_bounds(degree)
        require(lower_j <= a_internal_degree <= upper_j,
                f"A-internal degree must be in {lower_j}..{upper_j}")

    pool = IDPool(start_from=len(PAIRS) + 1)
    clauses = []
    block_a = range(degree)
    block_b = range(degree, N)

    for vertices in combinations(block_a, 4):
        clauses.append([-edge_var(u, v) for u, v in combinations(vertices, 2)])
    for vertices in combinations(block_b, 4):
        clauses.append([edge_var(u, v) for u, v in combinations(vertices, 2)])

    for u in range(N):
        incident = [edge_var(u, v) for v in range(N) if v != u]
        lower = degree - 1 if u < degree else degree
        upper = 23 if u < degree else 24
        clauses.extend(CardEnc.atleast(
            incident, bound=lower, vpool=pool, encoding=EncType.seqcounter).clauses)
        clauses.extend(CardEnc.atmost(
            incident, bound=upper, vpool=pool, encoding=EncType.seqcounter).clauses)

    if a_internal_degree is None:
        symmetry_blocks = (list(block_a), list(block_b))
    else:
        j = a_internal_degree
        for vertex in range(1, degree):
            clauses.append([edge_var(0, vertex) if vertex <= j
                            else -edge_var(0, vertex)])

        # Choose vertex 0 to have minimum degree in A, then sort only within
        # the residual symmetry blocks preserved by its fixed neighborhood.
        for vertex in range(1, degree):
            clauses.extend(degree_leq_clauses(0, vertex, pool))
        symmetry_blocks = (
            list(range(1, j + 1)),
            list(range(j + 1, degree)),
            list(block_b),
        )

    for block in symmetry_blocks:
        for u, w in zip(block, block[1:]):
            clauses.extend(degree_leq_clauses(u, w, pool))

    edges = list(EDGE_VAR.values())
    if edge_count is None:
        clauses.extend(CardEnc.atmost(
            edges, bound=maximum, vpool=pool, encoding=EncType.seqcounter).clauses)
    else:
        clauses.extend(CardEnc.equals(
            edges, bound=edge_count, vpool=pool, encoding=EncType.seqcounter).clauses)
    propagation_cut_clauses(clauses, pool, propagation_cuts)
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


def verify_model(adjacency, degree, edge_count=None, a_internal_degree=None):
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

    degrees = [row.bit_count() for row in adjacency]
    for u, value in enumerate(degrees):
        lower = degree - 1 if u < degree else degree
        upper = 23 if u < degree else 24
        require(lower <= value <= upper, "degree bound violated")
    if a_internal_degree is None:
        require(degrees[:degree] == sorted(degrees[:degree]), "A degrees unsorted")
    else:
        j = a_internal_degree
        require(sum((adjacency[0] >> vertex) & 1
                    for vertex in range(1, degree)) == j,
                "distinguished A-internal degree violated")
        for vertex in range(1, degree):
            require(bool((adjacency[0] >> vertex) & 1) == (vertex <= j),
                    "fixed distinguished neighborhood violated")
        require(all(degrees[0] <= degrees[vertex]
                    for vertex in range(1, degree)),
                "distinguished vertex is not minimum-degree in A")
        for block in (degrees[1:j + 1], degrees[j + 1:degree]):
            require(block == sorted(block), "residual A block is unsorted")
    require(degrees[degree:] == sorted(degrees[degree:]), "B degrees unsorted")

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
    return {"edges": actual_edges, "degrees": degrees}


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
        args.degree, args.edges, args.a_internal_degree, args.propagation_cuts)
    expected_clauses = len(clauses) + 2 * comb(N, 5)
    if args.cnf:
        written = write_dimacs(Path(args.cnf), clauses, top)
        require(written == expected_clauses, "DIMACS clause-count mismatch")

    started = time.perf_counter()
    print(f"degree={args.degree} edge_partition={args.edges} "
          f"a_internal_degree={args.a_internal_degree} "
          f"propagation_cuts={args.propagation_cuts}")
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
            "propagation_cuts": args.propagation_cuts,
            "solver": args.solver,
            "result": result,
            "vars": top,
            "clauses": expected_clauses,
            "stats": solver.accum_stats(),
            "runtime_seconds": round(time.perf_counter() - started, 2),
        }
        if sat:
            adjacency = model_adjacency(solver.get_model())
            record["verification"] = verify_model(
                adjacency, args.degree, args.edges, args.a_internal_degree)
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
        else:
            axes = ((None, j) for j in range(minimum_j, maximum_j + 1))
        for edge_count, j in axes:
            edge_part = f"-e{edge_count}" if edge_count is not None else ""
            key = f"d{degree}{edge_part}-j{j}"
            partitions.append({
                "id": key,
                "degree": degree,
                "edges": edge_count,
                "a_internal_degree": j,
                "cnf": f"{key}.cnf",
                "proof": f"{key}.drat",
                "result": f"{key}.json",
            })
    manifest = {
        "schema": 1,
        "vertex_count": 43,
        "mode": mode,
        "coverage": (
            "d in {18,19,20}; j is the A-internal degree of a chosen "
            "minimum-degree vertex of A; "
            + ("every admissible H edge count is fixed"
               if mode == "edge-j" else
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
    parser.add_argument("--a-internal-degree", type=int)
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--propagation-cuts",
                        choices=("none", "pair", "triple", "all"),
                        default="none")
    parser.add_argument("--cnf")
    parser.add_argument("--proof")
    parser.add_argument("--json")
    parser.add_argument("--list-partitions", action="store_true")
    parser.add_argument("--write-manifest")
    parser.add_argument("--manifest-mode", choices=("edge-j", "j-only"),
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
