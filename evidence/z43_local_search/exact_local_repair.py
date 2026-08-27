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

    def counter(i: int, j: int) -> int:
        return first_aux + (i - 1) * bound + (j - 1)

    for i, literal in enumerate(literals, start=1):
        yield [negate(literal), counter(i, 1)]
        if i > 1:
            for j in range(1, min(bound, i - 1) + 1):
                yield [-counter(i - 1, j), counter(i, j)]
            for j in range(2, min(bound, i) + 1):
                yield [negate(literal), -counter(i - 1, j - 1), counter(i, j)]
            if i > bound:
                yield [negate(literal), -counter(i - 1, bound)]


def local_model(radius: int):
    edges = all_edges()
    edge_var = {edge: i + 1 for i, edge in enumerate(edges)}
    for vertices in itertools.combinations(range(N), 5):
        variables = [edge_var[edge] for edge in itertools.combinations(vertices, 2)]
        yield [-variable for variable in variables]
        yield variables
    flips = [(-edge_var[edge] if seed_value(edge) else edge_var[edge]) for edge in edges]
    yield from at_most_clauses(flips, radius, len(edges) + 1)


def write_cnf(path: Path, radius: int, metadata_path: Path | None) -> None:
    edge_variables = len(all_edges())
    flips = [
        (-i if seed_value(edge) else i)
        for i, edge in enumerate(all_edges(), start=1)
    ]
    clauses = 2 * math.comb(N, 5) + sum(
        1 for _ in at_most_clauses(flips, radius, edge_variables + 1)
    )
    auxiliary_variables = edge_variables * radius if 0 < radius < edge_variables else 0
    variables = edge_variables + auxiliary_variables
    with path.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {variables} {clauses}\n")
        for clause in local_model(radius):
            handle.write(" ".join(map(str, clause)) + " 0\n")
    metadata = {
        "scope": f"graphs on labeled vertices 0..42 at Hamming distance at most {radius} from seed",
        "radius": radius,
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


def decode_model(model_path: Path, graph_path: Path) -> None:
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
    graph_path.write_text("\n".join(lines) + "\n")
    distance = sum(values[i] != seed_value(edge) for i, edge in enumerate(all_edges(), start=1))
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
    decode = subparsers.add_parser("decode")
    decode.add_argument("--model", required=True, type=Path)
    decode.add_argument("--output", required=True, type=Path)
    seed = subparsers.add_parser("seed")
    seed.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if not 0 <= args.radius <= len(all_edges()):
            parser.error("radius must be between 0 and 903")
        write_cnf(args.output, args.radius, args.metadata)
    elif args.command == "decode":
        decode_model(args.model, args.output)
    else:
        args.output.write_text(seed_graph_text())
        print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
