#!/usr/bin/env python3
"""Build and decode exact SAT searches in a Hamming ball around the F=2 seed."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


N = 43
SEED_STEPS = frozenset((1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21))
DELETED_CYCLE_EDGES = frozenset(
    (3, 4, 5, 6, 11, 12, 13, 14, 20, 21, 22, 23, 29, 30, 31, 37, 38, 39, 40)
)


def all_edges(n: int = N) -> list[tuple[int, int]]:
    return list(itertools.combinations(range(n), 2))


def seed_value(edge: tuple[int, int]) -> bool:
    u, v = edge
    diff = (v - u) % N
    value = diff in SEED_STEPS or (-diff) % N in SEED_STEPS
    cycle = u if diff == 1 else v if diff == N - 1 else None
    return value and cycle not in DELETED_CYCLE_EDGES


def seed_graph_text() -> str:
    lines = [f"n {N}"]
    lines.extend(f"e {u} {v}" for u, v in all_edges() if seed_value((u, v)))
    return "\n".join(lines) + "\n"


def negate(literal: int) -> int:
    return -literal


def counter_variable(first_aux: int, bound: int, i: int, j: int) -> int:
    return first_aux + (i - 1) * bound + (j - 1)


def at_most_clauses(literals: list[int], bound: int, first_aux: int):
    """Yield a one-way sequential counter enforcing sum(literals) <= bound."""
    if bound < 0:
        yield []
        return
    if bound >= len(literals):
        return
    if bound == 0:
        for literal in literals:
            yield [negate(literal)]
        return

    for i, literal in enumerate(literals, start=1):
        yield [negate(literal), counter_variable(first_aux, bound, i, 1)]
        if i > 1:
            for j in range(1, min(bound, i - 1) + 1):
                yield [
                    -counter_variable(first_aux, bound, i - 1, j),
                    counter_variable(first_aux, bound, i, j),
                ]
            for j in range(2, min(bound, i) + 1):
                yield [
                    negate(literal),
                    -counter_variable(first_aux, bound, i - 1, j - 1),
                    counter_variable(first_aux, bound, i, j),
                ]
            if i > bound:
                yield [
                    negate(literal),
                    -counter_variable(first_aux, bound, i - 1, bound),
                ]


def exactly_clauses(literals: list[int], bound: int, first_aux: int):
    """Yield a sequential-counter encoding of sum(literals) == bound."""
    if bound < 0 or bound > len(literals):
        yield []
        return
    if bound == 0:
        yield from at_most_clauses(literals, bound, first_aux)
        return
    if bound == len(literals):
        for literal in literals:
            yield [literal]
        return

    yield from at_most_clauses(literals, bound, first_aux)
    for i, literal in enumerate(literals, start=1):
        maximum_j = min(bound, i)
        for j in range(1, maximum_j + 1):
            state = counter_variable(first_aux, bound, i, j)
            if i == 1:
                yield [-state, literal]
            elif j == 1:
                yield [
                    -state,
                    counter_variable(first_aux, bound, i - 1, 1),
                    literal,
                ]
            elif j == i:
                yield [-state, literal]
                yield [
                    -state,
                    counter_variable(first_aux, bound, i - 1, j - 1),
                ]
            else:
                previous_same = counter_variable(
                    first_aux, bound, i - 1, j)
                yield [-state, previous_same, literal]
                yield [
                    -state,
                    previous_same,
                    counter_variable(first_aux, bound, i - 1, j - 1),
                ]
    yield [counter_variable(first_aux, bound, len(literals), bound)]


def local_model(radius: int, distance_mode: str = "at-most"):
    edges = all_edges()
    edge_var = {edge: i + 1 for i, edge in enumerate(edges)}
    for vertices in itertools.combinations(range(N), 5):
        variables = [edge_var[edge] for edge in itertools.combinations(vertices, 2)]
        yield [-variable for variable in variables]
        yield variables
    flips = [(-edge_var[edge] if seed_value(edge) else edge_var[edge]) for edge in edges]
    counter = exactly_clauses if distance_mode == "exact" else at_most_clauses
    yield from counter(flips, radius, len(edges) + 1)


def write_cnf(path: Path, radius: int, metadata_path: Path | None,
              distance_mode: str = "at-most") -> None:
    edge_variables = len(all_edges())
    flips = [
        (-i if seed_value(edge) else i)
        for i, edge in enumerate(all_edges(), start=1)
    ]
    counter = exactly_clauses if distance_mode == "exact" else at_most_clauses
    clauses = 2 * math.comb(N, 5) + sum(
        1 for _ in counter(flips, radius, edge_variables + 1))
    auxiliary_variables = edge_variables * radius if 0 < radius < edge_variables else 0
    variables = edge_variables + auxiliary_variables
    with path.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {variables} {clauses}\n")
        for clause in local_model(radius, distance_mode):
            handle.write(" ".join(map(str, clause)) + " 0\n")
    if distance_mode == "exact":
        scope = ("graphs on labeled vertices 0..42 at Hamming distance "
                 f"exactly {radius} from seed")
        distance_minimum = radius
    else:
        scope = ("graphs on labeled vertices 0..42 at Hamming distance at "
                 f"most {radius} from seed")
        distance_minimum = 0
    metadata = {
        "scope": scope,
        "radius": radius,
        "distance_mode": distance_mode,
        "distance_min": distance_minimum,
        "distance_max": radius,
        "edge_variables": edge_variables,
        "auxiliary_variables": auxiliary_variables,
        "variables": variables,
        "clauses": clauses,
        "five_sets": math.comb(N, 5),
        "seed_edges": sum(seed_value(edge) for edge in all_edges()),
        "seed_sha256": hashlib.sha256(seed_graph_text().encode()).hexdigest(),
        "cnf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    if metadata_path:
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metadata, sort_keys=True))


def decode_model(model_path: Path, graph_path: Path,
                 expected_distance: int | None = None) -> None:
    values: dict[int, bool] = {}
    status = None
    for line in model_path.read_text().splitlines():
        if line.startswith("s "):
            status = line
        elif line.startswith("v "):
            for literal in map(int, line[2:].split()):
                if literal:
                    values[abs(literal)] = literal > 0
    if status != "s SATISFIABLE":
        raise SystemExit(f"model is not SATISFIABLE: {status!r}")
    missing = [i for i in range(1, len(all_edges()) + 1) if i not in values]
    if missing:
        raise SystemExit(f"model omits edge variables, first missing: {missing[0]}")
    lines = [f"n {N}"]
    lines.extend(
        f"e {u} {v}" for i, (u, v) in enumerate(all_edges(), start=1) if values[i]
    )
    distance = sum(values[i] != seed_value(edge) for i, edge in enumerate(all_edges(), start=1))
    if expected_distance is not None and distance != expected_distance:
        raise SystemExit(
            f"decoded distance {distance}, expected {expected_distance}")
    graph_path.write_text("\n".join(lines) + "\n")
    print(f"decoded_edges={sum(values[i] for i in range(1, len(all_edges()) + 1))}")
    print(f"distance_from_seed={distance}")
    print(f"graph_sha256={hashlib.sha256(graph_path.read_bytes()).hexdigest()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--radius", required=True, type=int)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--metadata", type=Path)
    build.add_argument("--distance-mode", choices=("at-most", "exact"),
                       default="at-most")
    decode = subparsers.add_parser("decode")
    decode.add_argument("--model", required=True, type=Path)
    decode.add_argument("--output", required=True, type=Path)
    decode.add_argument("--expected-distance", type=int)
    seed = subparsers.add_parser("seed")
    seed.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if not 0 <= args.radius <= len(all_edges()):
            parser.error("radius must be between 0 and 903")
        write_cnf(args.output, args.radius, args.metadata, args.distance_mode)
    elif args.command == "decode":
        decode_model(args.model, args.output, args.expected_distance)
    else:
        args.output.write_text(seed_graph_text())
        print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
