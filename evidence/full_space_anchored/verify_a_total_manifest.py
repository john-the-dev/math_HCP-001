#!/usr/bin/env python3
"""Fail-closed verification for the distinguished-A-total-degree manifest."""
from pathlib import Path
import argparse
import importlib.util
import json


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "base_manifest_verifier", HERE / "verify_manifest.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

DEGREES = (18, 19, 20)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge_bounds(degree):
    return (41 * degree + 1) // 2, 451 - degree


def j_bounds(degree):
    return max(0, degree - 18), 13


def k_bounds(degree):
    return 28 - degree, 13


def t_bounds(degree, j):
    return max(degree - 1, j), min(23, j + 42 - degree)


def expected_cases():
    return {(degree, j, t, k)
            for degree in DEGREES
            for j in range(j_bounds(degree)[0], j_bounds(degree)[1] + 1)
            for t in range(t_bounds(degree, j)[0],
                           t_bounds(degree, j)[1] + 1)
            for k in range(k_bounds(degree)[0], k_bounds(degree)[1] + 1)}


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def verify_manifest(data):
    require(data.get("schema") == 1, "manifest schema must be 1")
    require(data.get("vertex_count") == 43, "vertex_count must be 43")
    require(data.get("mode") == "j-t-k", "manifest mode must be j-t-k")
    rows = data.get("partitions")
    require(isinstance(rows, list), "partitions must be a list")
    require(data.get("partition_count") == len(rows),
            "partition_count does not match row count")

    seen_ids = set()
    seen_cases = set()
    for row in rows:
        require(isinstance(row, dict), "partition row must be an object")
        degree = row.get("degree")
        j = row.get("a_internal_degree")
        t = row.get("a_total_degree")
        k = row.get("b_internal_degree")
        require(degree in DEGREES, f"invalid degree: {degree}")
        require(all(isinstance(value, int) for value in (j, t, k)),
                f"invalid (j,t,k) for degree {degree}")
        require(j_bounds(degree)[0] <= j <= j_bounds(degree)[1],
                f"invalid j for degree {degree}")
        require(row.get("edges") is None, f"{row.get('id')}: edges must be null")
        minimum, maximum = edge_bounds(degree)
        require(row.get("edge_min") == minimum,
                f"{row.get('id')}: edge_min must be {minimum}")
        require(row.get("edge_max") == maximum,
                f"{row.get('id')}: edge_max must be {maximum}")
        minimum_t, maximum_t = t_bounds(degree, j)
        require(row.get("a_total_degree_min") == minimum_t,
                f"{row.get('id')}: a_total_degree_min must be {minimum_t}")
        require(row.get("a_total_degree_max") == maximum_t,
                f"{row.get('id')}: a_total_degree_max must be {maximum_t}")
        minimum_k, maximum_k = k_bounds(degree)
        require(row.get("b_internal_degree_min") == minimum_k,
                f"{row.get('id')}: b_internal_degree_min must be {minimum_k}")
        require(row.get("b_internal_degree_max") == maximum_k,
                f"{row.get('id')}: b_internal_degree_max must be {maximum_k}")
        expected_id = f"d{degree}-j{j}-t{t}-k{k}"
        require(row.get("id") == expected_id,
                f"partition id must be {expected_id}")
        for kind, suffix in (("cnf", ".cnf"), ("proof", ".drat"),
                             ("result", ".json")):
            require(row.get(kind) == expected_id + suffix,
                    f"{expected_id}: invalid {kind} filename")
        require(expected_id not in seen_ids, f"duplicate id: {expected_id}")
        case = (degree, j, t, k)
        require(case not in seen_cases, f"duplicate case: {case}")
        seen_ids.add(expected_id)
        seen_cases.add(case)

    expected = expected_cases()
    require(seen_cases == expected,
            f"case cover mismatch: missing={sorted(expected - seen_cases)} "
            f"extra={sorted(seen_cases - expected)}")
    require(len(rows) == 1142, "j-t-k manifest must contain 1142 cases")
    return seen_ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--ledger")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    require(not args.require_complete or args.ledger,
            "--require-complete requires --ledger")
    valid_ids = verify_manifest(read_json(args.manifest))
    print(f"manifest=PASS cases={len(valid_ids)}")
    if args.ledger:
        claims = BASE.verify_ledger(args.ledger, valid_ids, args.require_complete)
        print(f"ledger=PASS verified_unsat={len(claims)} "
              f"complete={claims == valid_ids}")


if __name__ == "__main__":
    main()
