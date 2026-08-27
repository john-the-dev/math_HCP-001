#!/usr/bin/env python3
"""Emit/check compact DPLL certificates for the two 42-core extension CNFs."""
from itertools import combinations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
N = 43
S = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
DIFFS = S | {(-d) % N for d in S}
DELETED = {3, 4, 5, 6, 11, 12, 13, 14, 20, 21, 22, 23,
           29, 30, 31, 37, 38, 39, 40}
SOURCE_COMMIT = "5c1b2c2898271cd7fdc882fb6dce0518debdcc40"
EXPECTED_I5 = {(3, 6, 7, 11, 12), (6, 7, 11, 12, 15)}
EXPECTED_COUNTS = {
    6: (1133, 1185), 12: (1133, 1185),
    7: (1131, 1200), 11: (1131, 1200),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_candidate():
    adj = [0] * N
    for u, v in combinations(range(N), 2):
        if (v-u) % N in DIFFS:
            adj[u] |= 1 << v
            adj[v] |= 1 << u
    for u in DELETED:
        v = (u+1) % N
        adj[u] ^= 1 << v
        adj[v] ^= 1 << u
    return adj


def clauses_for(removed):
    adj = build_candidate()
    vertices = [v for v in range(N) if v != removed]
    clauses = []
    for q in combinations(vertices, 4):
        edges = sum((adj[u] >> v) & 1 for u, v in combinations(q, 2))
        if edges == 6:
            clauses.append({"kind": "K4", "vertices": list(q),
                            "positive": [], "negative": list(q)})
        elif edges == 0:
            clauses.append({"kind": "I4", "vertices": list(q),
                            "positive": list(q), "negative": []})
    return clauses


def validate_model():
    adj = build_candidate()
    edges = sum((adj[u] >> v) & 1 for u, v in combinations(range(N), 2))
    require(edges == 454, f"candidate edge count {edges} != 454")
    k5, i5 = [], []
    for q in combinations(range(N), 5):
        count = sum((adj[u] >> v) & 1 for u, v in combinations(q, 2))
        if count == 10:
            k5.append(q)
        elif count == 0:
            i5.append(q)
    require(not k5, f"candidate unexpectedly has K5 {k5[:1]}")
    require(set(i5) == EXPECTED_I5, f"candidate I5 set differs: {i5}")


def status(clause, assignment):
    for v in clause["positive"]:
        if assignment.get(v) is True:
            return "satisfied", None
    for v in clause["negative"]:
        if assignment.get(v) is False:
            return "satisfied", None
    free = [(v, True) for v in clause["positive"] if v not in assignment]
    free += [(v, False) for v in clause["negative"] if v not in assignment]
    if not free:
        return "conflict", None
    if len(free) == 1:
        return "unit", free[0]
    return "open", free


def prove(clauses, assignment=None):
    assignment = dict(assignment or {})
    while True:
        unit = None
        scores = {}
        for ci, clause in enumerate(clauses):
            state, detail = status(clause, assignment)
            if state == "conflict":
                return {"conflict": ci}
            if state == "unit" and unit is None:
                unit = (ci, detail)
            if state == "open":
                for v, _ in detail:
                    scores[v] = scores.get(v, 0) + 1
        if unit is None:
            break
        ci, (var, value) = unit
        assignment[var] = value
        return {"unit": [var, value], "reason": ci,
                "next": prove(clauses, assignment)}
    if not scores:
        raise ValueError("formula unexpectedly satisfiable")
    var = max(scores, key=scores.get)
    left = dict(assignment); left[var] = False
    right = dict(assignment); right[var] = True
    return {"branch": var,
            "false": prove(clauses, left),
            "true": prove(clauses, right)}


def check_node(clauses, node, assignment=None):
    assignment = dict(assignment or {})
    if "conflict" in node:
        require(status(clauses[node["conflict"]], assignment)[0] == "conflict",
                "cited conflict clause is not falsified")
        return
    if "unit" in node:
        var, value = node["unit"]
        state, detail = status(clauses[node["reason"]], assignment)
        require(state == "unit" and detail == (var, value),
                "cited unit reason does not force the asserted literal")
        require(var not in assignment, "unit reassigns an assigned variable")
        assignment[var] = value
        check_node(clauses, node["next"], assignment)
        return
    var = node["branch"]
    require(var not in assignment, "branch variable is already assigned")
    require("false" in node and "true" in node,
            "branch must contain both Boolean subtrees")
    left = dict(assignment); left[var] = False
    right = dict(assignment); right[var] = True
    check_node(clauses, node["false"], left)
    check_node(clauses, node["true"], right)


def count_nodes(node):
    if "conflict" in node:
        return 1
    if "unit" in node:
        return 1 + count_nodes(node["next"])
    return 1 + count_nodes(node["false"]) + count_nodes(node["true"])


def emit(path):
    validate_model()
    payload = {"source_commit": SOURCE_COMMIT,
               "cases": []}
    for removed in sorted(EXPECTED_COUNTS):
        clauses = clauses_for(removed)
        kinds = tuple(sum(c["kind"] == kind for c in clauses)
                      for kind in ("K4", "I4"))
        require(kinds == EXPECTED_COUNTS[removed],
                f"remove={removed} clause counts {kinds} differ")
        proof = prove(clauses)
        check_node(clauses, proof)
        payload["cases"].append({"removed": removed,
                                 "clause_count": len(clauses),
                                 "clauses": clauses,
                                 "proof": proof,
                                 "proof_nodes": count_nodes(proof)})
    path.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"wrote={path}")
    print(f"sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")
    for case in payload["cases"]:
        print(f"remove={case['removed']} clauses={case['clause_count']} proof_nodes={case['proof_nodes']}")


def check(path):
    validate_model()
    payload = json.loads(path.read_text())
    require(payload.get("source_commit") == SOURCE_COMMIT,
            "certificate source commit differs")
    cases = payload.get("cases")
    require(isinstance(cases, list) and len(cases) == len(EXPECTED_COUNTS),
            "certificate must contain exactly four cases")
    require({case.get("removed") for case in cases} == set(EXPECTED_COUNTS),
            "certificate cases must be exactly removals 6, 7, 11, and 12")
    for case in cases:
        clauses = clauses_for(case["removed"])
        kinds = tuple(sum(c["kind"] == kind for c in clauses)
                      for kind in ("K4", "I4"))
        require(kinds == EXPECTED_COUNTS[case["removed"]],
                f"remove={case['removed']} model clause counts differ")
        require(clauses == case["clauses"], "stored clauses differ from model")
        require(len(clauses) == case["clause_count"], "clause count differs")
        check_node(clauses, case["proof"])
        require(count_nodes(case["proof"]) == case["proof_nodes"],
                "proof node count differs")
        print(f"PASS remove={case['removed']} clauses={len(clauses)} proof_nodes={case['proof_nodes']}")
    print(f"sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("emit", "check"))
    ap.add_argument("path", type=Path)
    args = ap.parse_args()
    emit(args.path) if args.action == "emit" else check(args.path)


if __name__ == "__main__":
    main()
