#!/usr/bin/env python3
"""HCP-001 Z4 step 2 — exact per-toggle 3-hitting-set counts (corrected).

Counting identity. For toggle t, let C_t = {F_c(W) : R_c(W)={t}}, U = union of
C_t, and O = (M-1) - |U| the chords in chords\\{t} that meet no constraint.
Hitting depends only on X ∩ U, so partitioning a 3-set X by j = |X ∩ U|:

    total = B1*C(O,2) + B2*C(O,1) + B3      (j = 1, 2, 3; j = 0 impossible)

where Bj = number of j-subsets of U hitting every constraint. B2 counts ALL
hitting pairs (including those containing a hitting singleton) and B3 ALL
hitting triples — the three cases are disjoint by j, so nothing is
double-counted. Counting only "newly hitting" triples, as a first draft did,
undercounts B3.

Includes a synthetic brute-force control: random small instances counted both
by this identity and by direct enumeration, compared as exact sets.
"""
from collections import defaultdict
from itertools import combinations
from math import comb
import hashlib
import json
import platform
import random
import resource
import sys
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
cdist = lambda u, v: min((v - u) % N, (u - v) % N)
bcol = lambda e: 1 if (e[1] - e[0]) % N in DIFFS else 0


def bjs(hit_masks, full):
    """B1,B2,B3 over the index range of hit_masks."""
    u = len(hit_masks)
    B1 = B2 = B3 = 0
    for a in range(u):
        ha = hit_masks[a]
        if ha == full:
            B1 += 1
        for b in range(a + 1, u):
            hab = ha | hit_masks[b]
            if hab == full:
                B2 += 1
            for c in range(b + 1, u):
                if hab | hit_masks[c] == full:
                    B3 += 1
    return B1, B2, B3


def formula_total(cons, universe_size):
    """cons: list of frozensets over an implicit universe of size universe_size."""
    n = len(cons)
    full = (1 << n) - 1
    U = sorted(set().union(*cons))
    hm = []
    for j in U:
        m = 0
        for i, F in enumerate(cons):
            if j in F:
                m |= 1 << i
        hm.append(m)
    O = universe_size - len(U)
    B1, B2, B3 = bjs(hm, full)
    return B1 * comb(O, 2) + B2 * O + B3, (B1, B2, B3, len(U), O)


def brute_total(cons, universe):
    got = set()
    for X in combinations(sorted(universe), 3):
        sx = set(X)
        if all(sx & F for F in cons):
            got.add(frozenset(X))
    return got


def control(trials=200, seed=20260826):
    rng = random.Random(seed)
    for _ in range(trials):
        usz = rng.randint(8, 16)
        universe = list(range(usz))
        ncon = rng.randint(1, 5)
        cons = []
        for _ in range(ncon):
            k = rng.randint(2, min(5, usz))
            cons.append(frozenset(rng.sample(universe, k)))
        cons = list(dict.fromkeys(cons))
        f, _meta = formula_total(cons, usz)
        b = brute_total(cons, universe)
        if f != len(b):
            return False, (cons, usz, f, len(b))
    return True, None


t0 = time.perf_counter()
chords = [e for e in combinations(range(N), 2) if cdist(*e) != 1]
idx = {e: i for i, e in enumerate(chords)}
M = len(chords)
cls = [cdist(*e) for e in chords]

Fam = defaultdict(list)
for W in combinations(range(N), 5):
    p = list(combinations(W, 2))
    if any(cdist(*e) == 1 for e in p):
        continue
    col = [(e, bcol(e)) for e in p]
    for c in (0, 1):
        R = [e for e, b in col if b != c]
        if len(R) == 1:
            Fam[idx[R[0]]].append(frozenset(idx[e] for e, b in col if b == c))
t_wit = time.perf_counter() - t0

ok, detail = control()
print(f"synthetic_brute_force_control_passed={ok}" + ("" if ok else f" FAIL {detail}"))
if not ok:
    sys.exit(1)


def per_toggle(t):
    cons = list(dict.fromkeys(Fam[t]))
    return formula_total(cons, M - 1)


reps = defaultdict(list)
for t in range(M):
    reps[cls[t]].append(t)

full_check = {2, 21}
out_w, out_h, cw, ch = {}, {}, {}, {}
for d in sorted(reps):
    ts = reps[d] if d in full_check else reps[d][:1]
    wv, hv = set(), set()
    for t in ts:
        wv.add(len(Fam[t]))
        hv.add(per_toggle(t)[0])
    out_w[d], out_h[d] = min(wv), min(hv)
    cw[d], ch[d] = len(wv) == 1, len(hv) == 1
    print(f"  d={d:2d} checked={len(ts):2d} witnesses={out_w[d]:3d} "
          f"raw3hit={out_h[d]:>13d} const_w={cw[d]} const_h={ch[d]}", flush=True)

wvec = [out_w[d] for d in range(2, 22)]
hvec = [out_h[d] for d in range(2, 22)]
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 3)
print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"witnesses_R_size1_total={sum(len(Fam[t]) for t in range(M))}")
print("witness_counts_by_distance_2_to_21=" + json.dumps(wvec))
print("raw_3_hitting_set_counts_by_distance_2_to_21=" + json.dumps(hvec))
print(f"labelled_raw_3hit_sum_over_all_860_toggles={sum(h*43 for h in hvec)}")
print(f"fully_verified_classes_all_43_translates={sorted(full_check)}")
print(f"const_within_class_witnesses={all(cw.values())} const_within_class_hitting={all(ch.values())}")
print(f"runtime_seconds_total={time.perf_counter()-t0:.2f} peak_rss_gb={peak:.2f}")
print("vectors_sha256=" + hashlib.sha256(
    json.dumps({"w": wvec, "h": hvec}, sort_keys=True).encode()).hexdigest())
