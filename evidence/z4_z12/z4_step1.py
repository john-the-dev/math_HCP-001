#!/usr/bin/env python3
"""HCP-001 Z4 step 1 — independent reconstruction of the cycle-free
monochromatic-5-set witness hypergraph.

Written from the compact template (N=43, S) only; does not import or reuse the
repository's verifier code. Records are keyed by VERTEX PAIRS, not by the
repo's chord-index ordering, so the fingerprint is implementation-independent.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
import platform
import sys
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)


def cyc_dist(u, v):
    d = (v - u) % N
    return min(d, N - d)


def base_color(e):
    """1 if the edge is present in the cyclic base template, else 0."""
    return 1 if (e[1] - e[0]) % N in DIFFS else 0


def is_cycle_edge(e):
    return cyc_dist(e[0], e[1]) == 1


t0 = time.perf_counter()

# --- combinatorial cross-check of the cycle-free 5-set count ----------------
from math import comb
K = 5
identity = N * comb(N - K, K) // (N - K)          # n/(n-k) * C(n-k, k)

cycle_free = 0
hist = {0: Counter(), 1: Counter()}
records = []            # (c, W, R, F) with |R| <= 4
both_colors_le4 = 0

for W in combinations(range(N), 5):
    pairs = list(combinations(W, 2))
    if any(is_cycle_edge(e) for e in pairs):
        continue
    cycle_free += 1
    colors = [(e, base_color(e)) for e in pairs]
    n_le4 = 0
    for c in (0, 1):
        R = tuple(e for e, b in colors if b != c)
        F = tuple(e for e, b in colors if b == c)
        hist[c][len(R)] += 1
        if len(R) <= 4:
            n_le4 += 1
            records.append((c, W, R, F))
    if n_le4 == 2:
        both_colors_le4 += 1

elapsed = time.perf_counter() - t0

# --- canonical serialization ------------------------------------------------
def canon(rec):
    c, W, R, F = rec
    return json.dumps(
        {"c": c,
         "W": list(W),
         "R": [list(e) for e in sorted(R)],
         "F": [list(e) for e in sorted(F)]},
        separators=(",", ":"), sort_keys=True)


records.sort(key=lambda r: (r[0], r[1], sorted(r[2])))
blob_le4 = "\n".join(canon(r) for r in records).encode()
sha_le4 = hashlib.sha256(blob_le4).hexdigest()

# full record set (both colors, every cycle-free 5-set) for an unambiguous
# second fingerprint — the spec did not say which set to hash.
t1 = time.perf_counter()
all_recs = []
for W in combinations(range(N), 5):
    pairs = list(combinations(W, 2))
    if any(is_cycle_edge(e) for e in pairs):
        continue
    colors = [(e, base_color(e)) for e in pairs]
    for c in (0, 1):
        R = tuple(e for e, b in colors if b != c)
        F = tuple(e for e, b in colors if b == c)
        all_recs.append((c, W, R, F))
all_recs.sort(key=lambda r: (r[0], r[1], sorted(r[2])))
sha_all = hashlib.sha256("\n".join(canon(r) for r in all_recs).encode()).hexdigest()
elapsed_all = time.perf_counter() - t1

chords = [e for e in combinations(range(N), 2) if not is_cycle_edge(e)]

print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"N={N} S={sorted(S)}")
print(f"non_cycle_chords={len(chords)}")
print(f"cycle_free_5sets={cycle_free}")
print(f"identity_43_over_38_times_C38_5={identity}  match={cycle_free == identity}")
print(f"records_with_R_le_4={len(records)}")
print(f"5sets_with_both_colors_le4={both_colors_le4}  (must be 0: |R_0|+|R_1|=10)")
for c in (0, 1):
    print(f"hist_|R_{c}|=" + json.dumps(dict(sorted(hist[c].items()))))
print(f"witness_sha256_R_le_4={sha_le4}")
print(f"witness_sha256_all_records={sha_all}")
print(f"runtime_seconds_main={elapsed:.6f} runtime_seconds_full_serialize={elapsed_all:.6f}")
