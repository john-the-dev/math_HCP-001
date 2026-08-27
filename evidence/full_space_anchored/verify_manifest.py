#!/usr/bin/env python3
"""Verify supported SAT manifests and separately recorded UNSAT claims."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re


DEGREES = (18, 19, 20)
A_EDGE_BOUNDS = {
    18: (50, 85),
    19: (57, 92),
    20: (68, 100),
}
SHA256 = re.compile(r"[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge_bounds(degree):
    return (41 * degree + 1) // 2, 451 - degree


def j_bounds(degree):
    return max(0, degree - 18), 13


def expected_cases(mode):
    if mode == "j-only":
        return {(degree, j)
                for degree in DEGREES
                for j in range(j_bounds(degree)[0], j_bounds(degree)[1] + 1)}
    return {(degree, j, a_edges)
            for degree in DEGREES
            for j in range(j_bounds(degree)[0], j_bounds(degree)[1] + 1)
            for a_edges in range(A_EDGE_BOUNDS[degree][0],
                                 A_EDGE_BOUNDS[degree][1] + 1)}


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def verify_manifest(data):
    require(data.get("schema") == 1, "manifest schema must be 1")
    require(data.get("vertex_count") == 43, "vertex_count must be 43")
    mode = data.get("mode")
    require(mode in ("j-only", "a-edge-j"),
            "manifest mode must be j-only or a-edge-j")
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
        require(degree in DEGREES, f"invalid degree: {degree}")
        require(isinstance(j, int), f"invalid j for degree {degree}")
        require(row.get("edges") is None, f"{row.get('id')}: edges must be null")
        lower_j, upper_j = j_bounds(degree)
        require(lower_j <= j <= upper_j,
                f"invalid j for degree {degree}: {j}")
        if mode == "j-only":
            minimum, maximum = edge_bounds(degree)
            require(row.get("edge_min") == minimum,
                    f"{row.get('id')}: edge_min must be {minimum}")
            require(row.get("edge_max") == maximum,
                    f"{row.get('id')}: edge_max must be {maximum}")
            case = (degree, j)
            expected_id = f"d{degree}-j{j}"
        else:
            a_edges = row.get("a_edges")
            lower_a, upper_a = A_EDGE_BOUNDS[degree]
            require(isinstance(a_edges, int),
                    f"{row.get('id')}: a_edges must be an integer")
            require(row.get("a_edge_min") == lower_a,
                    f"{row.get('id')}: a_edge_min must be {lower_a}")
            require(row.get("a_edge_max") == upper_a,
                    f"{row.get('id')}: a_edge_max must be {upper_a}")
            require(lower_a <= a_edges <= upper_a,
                    f"{row.get('id')}: a_edges must be in {lower_a}..{upper_a}")
            case = (degree, j, a_edges)
            expected_id = f"d{degree}-a{a_edges}-j{j}"
        require(row.get("id") == expected_id,
                f"partition id must be {expected_id}")
        require(row.get("cnf") == f"{expected_id}.cnf",
                f"{expected_id}: invalid cnf filename")
        require(row.get("proof") == f"{expected_id}.drat",
                f"{expected_id}: invalid proof filename")
        require(row.get("result") == f"{expected_id}.json",
                f"{expected_id}: invalid result filename")
        require(expected_id not in seen_ids, f"duplicate id: {expected_id}")
        require(case not in seen_cases, f"duplicate case: {case}")
        seen_ids.add(expected_id)
        seen_cases.add(case)

    expected = expected_cases(mode)
    require(seen_cases == expected,
            f"case cover mismatch: missing={sorted(expected - seen_cases)} "
            f"extra={sorted(seen_cases - expected)}")
    expected_count = 39 if mode == "j-only" else 1368
    require(len(rows) == expected_count,
            f"{mode} manifest must contain {expected_count} cases")
    return seen_ids


def artifact_path(root, value, case_id, kind):
    require(isinstance(value, str) and value, f"{case_id}: missing {kind} path")
    relative = Path(value)
    require(not relative.is_absolute() and ".." not in relative.parts,
            f"{case_id}: {kind} path must stay under the ledger directory")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()),
            f"{case_id}: {kind} path escapes the ledger directory")
    require(path.is_file(), f"{case_id}: missing {kind} artifact: {value}")
    return path


def verify_artifact(root, record, case_id, kind):
    require(isinstance(record, dict), f"{case_id}: missing {kind} record")
    path = artifact_path(root, record.get("path"), case_id, kind)
    expected_hash = record.get("sha256")
    require(isinstance(expected_hash, str) and SHA256.fullmatch(expected_hash),
            f"{case_id}: invalid {kind} sha256")
    actual_hash = sha256(path.read_bytes()).hexdigest()
    require(actual_hash == expected_hash,
            f"{case_id}: {kind} sha256 mismatch")
    return path


def verify_ledger(path, valid_ids, require_complete=False):
    ledger_path = Path(path).resolve()
    data = read_json(ledger_path)
    require(data.get("schema") == 1, "ledger schema must be 1")
    claims = data.get("claims")
    require(isinstance(claims, list), "ledger claims must be a list")
    seen = set()
    for claim in claims:
        require(isinstance(claim, dict), "ledger claim must be an object")
        case_id = claim.get("id")
        require(case_id in valid_ids, f"unknown ledger case: {case_id}")
        require(case_id not in seen, f"duplicate ledger case: {case_id}")
        require(claim.get("status") == "UNSAT",
                f"{case_id}: ledger records only completed UNSAT claims")
        artifacts = claim.get("artifacts")
        require(isinstance(artifacts, dict), f"{case_id}: missing artifacts")
        verify_artifact(ledger_path.parent, artifacts.get("cnf"), case_id, "cnf")
        verify_artifact(ledger_path.parent, artifacts.get("proof"), case_id, "proof")
        checker = verify_artifact(
            ledger_path.parent, artifacts.get("checker"), case_id, "checker")
        checker_lines = checker.read_text(errors="replace").splitlines()
        require(any(line.strip() == "s VERIFIED" for line in checker_lines),
                f"{case_id}: checker output lacks an exact 's VERIFIED' line")
        seen.add(case_id)
    if require_complete:
        require(seen == valid_ids,
                f"completion ledger is incomplete: missing={sorted(valid_ids - seen)}")
    return seen


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
        claims = verify_ledger(args.ledger, valid_ids, args.require_complete)
        print(f"ledger=PASS verified_unsat={len(claims)} "
              f"complete={claims == valid_ids}")


if __name__ == "__main__":
    main()
