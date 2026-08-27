#!/usr/bin/env python3
"""Verify the 39-case SAT manifest and any separately recorded UNSAT claims."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re


DEGREES = (18, 19, 20)
SHA256 = re.compile(r"[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge_bounds(degree):
    return (41 * degree + 1) // 2, 451 - degree


def j_bounds(degree):
    return max(0, degree - 18), 13


def expected_cases():
    return {(degree, j)
            for degree in DEGREES
            for j in range(j_bounds(degree)[0], j_bounds(degree)[1] + 1)}


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def verify_manifest(data):
    require(data.get("schema") == 1, "manifest schema must be 1")
    require(data.get("vertex_count") == 43, "vertex_count must be 43")
    require(data.get("mode") == "j-only", "manifest mode must be j-only")
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
        minimum, maximum = edge_bounds(degree)
        require(row.get("edge_min") == minimum,
                f"{row.get('id')}: edge_min must be {minimum}")
        require(row.get("edge_max") == maximum,
                f"{row.get('id')}: edge_max must be {maximum}")
        expected_id = f"d{degree}-j{j}"
        require(row.get("id") == expected_id,
                f"partition id must be {expected_id}")
        require(row.get("cnf") == f"{expected_id}.cnf",
                f"{expected_id}: invalid cnf filename")
        require(row.get("proof") == f"{expected_id}.drat",
                f"{expected_id}: invalid proof filename")
        require(row.get("result") == f"{expected_id}.json",
                f"{expected_id}: invalid result filename")
        require(expected_id not in seen_ids, f"duplicate id: {expected_id}")
        require((degree, j) not in seen_cases,
                f"duplicate case: degree={degree} j={j}")
        seen_ids.add(expected_id)
        seen_cases.add((degree, j))

    expected = expected_cases()
    require(seen_cases == expected,
            f"case cover mismatch: missing={sorted(expected - seen_cases)} "
            f"extra={sorted(seen_cases - expected)}")
    require(len(rows) == 39, "j-only manifest must contain 39 cases")
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
