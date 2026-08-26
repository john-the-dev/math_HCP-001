#!/usr/bin/env python3
"""HCP-001 Z4 — replay of the synthetic control from the committed payload.

Reads z4_control_instances.jsonl (200 canonical instances), asserts its
SHA-256, then runs both control assertions. Requires no RNG: the payload is
the authority, the seeded generator is provenance only.

NOTE ON BYTES: standard JSONL — exactly one LF after the final record. Blank
lines are ignored when parsing, but the hash covers the exact bytes, so adding
or removing any newline invalidates it.

Usage:
    python3 z4_control_replay.py [path/to/z4_control_instances.jsonl]
"""
from itertools import combinations
from math import comb
import hashlib
import json
import platform
import sys
import time

EXPECTED_SHA = "2a0c9ac9e60731c35dacac7d5c156ace8058c42add51e0f6c90414be9a049aad"
EXPECTED_BYTES = 13318
EXPECTED_N = 200


def partition_generate(cons, universe):
    U = sorted(set().union(*cons))
    Us = set(U)
    O = [x for x in universe if x not in Us]
    full = (1 << len(cons)) - 1
    hit = {j: sum(1 << i for i, F in enumerate(cons) if j in F) for j in U}
    fam = set()
    for a in U:
        if hit[a] == full:
            for extra in combinations(O, 2):
                fam.add(frozenset((a,) + extra))
    for a, b in combinations(U, 2):
        if hit[a] | hit[b] == full:
            for extra in O:
                fam.add(frozenset((a, b, extra)))
    for a, b, c in combinations(U, 3):
        if hit[a] | hit[b] | hit[c] == full:
            fam.add(frozenset((a, b, c)))
    return fam


def partition_count(cons, universe):
    U = sorted(set().union(*cons))
    O = len(universe) - len(U)
    full = (1 << len(cons)) - 1
    hm = [sum(1 << i for i, F in enumerate(cons) if j in F) for j in U]
    u = len(hm)
    B1 = B2 = B3 = 0
    for a in range(u):
        ha = hm[a]
        if ha == full:
            B1 += 1
        for b in range(a + 1, u):
            hab = ha | hm[b]
            if hab == full:
                B2 += 1
            for c in range(b + 1, u):
                if hab | hm[c] == full:
                    B3 += 1
    return B1 * comb(O, 2) + B2 * O + B3


def brute(cons, universe):
    return {frozenset(X) for X in combinations(sorted(universe), 3)
            if all(set(X) & F for F in cons)}


path = sys.argv[1] if len(sys.argv) > 1 else "z4_control_instances.jsonl"
raw = open(path, "rb").read()
sha = hashlib.sha256(raw).hexdigest()
t0 = time.perf_counter()

print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"payload={path} bytes={len(raw)} sha256={sha}")
print(f"payload_bytes_match={len(raw) == EXPECTED_BYTES}")
print(f"payload_sha256_match={sha == EXPECTED_SHA}")
print(f"trailing_newline_present={raw.endswith(bytes([10]))} (expected True)")
if sha != EXPECTED_SHA:
    sys.exit("payload hash mismatch — refusing to report a control result")

# Structural contract, asserted independently of the hash: the hash proves
# "these exact bytes", the structure check states what the file must BE, so a
# mismatch says which property broke rather than only that something did.
text = raw.decode("utf-8")
physical = text.split("\n")
terminal_lf = raw.endswith(bytes([10])) and not raw.endswith(bytes([10, 10]))
records = physical[:-1] if physical and physical[-1] == "" else physical
blank_inside = sum(1 for ln in records if not ln.strip())
struct_ok = terminal_lf and len(records) == EXPECTED_N and blank_inside == 0
print(f"structure_exactly_one_terminal_lf={terminal_lf}")
print(f"structure_physical_json_records={len(records)} expected={EXPECTED_N}")
print(f"structure_blank_records_inside={blank_inside} expected=0")
print(f"structure_ok={struct_ok}")
if not struct_ok:
    sys.exit("payload structure contract violated")
instances = [json.loads(ln) for ln in records]
a1 = a2 = 0
for inst in instances:
    universe = list(range(inst["universe_size"]))
    cons = [frozenset(F) for F in inst["constraints"]]
    fam = partition_generate(cons, universe)
    if fam == brute(cons, universe):
        a1 += 1
    if partition_count(cons, universe) == len(fam):
        a2 += 1

print(f"instances_parsed={len(instances)} expected={EXPECTED_N} "
      f"match={len(instances) == EXPECTED_N}")
print(f"A1_family_equality_passed={a1}/{len(instances)}")
print(f"A2_scalar_equals_family_cardinality_passed={a2}/{len(instances)}")
print(f"replay_ok={a1 == a2 == len(instances) == EXPECTED_N}")
print(f"runtime_seconds={time.perf_counter()-t0:.3f}")
