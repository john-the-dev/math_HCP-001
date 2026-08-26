#!/usr/bin/env python3
"""HCP-001 Z4 stage-3 controls. A zero result is only as good as the evidence
that the pipeline can find a survivor when one exists.

C1  survives_direct(T) agrees with an exhaustive scan of all 423,937 records,
    on random quadruples.
C2  mutual condition is NECESSARY: on random quadruples, direct-survivor
    implies mutual-pass. (Proof: t in T and R={t} gives R subset T, so T must
    meet F; t not in F, hence T\\{t} meets F. The control guards the code.)
C3  PLANTED SOLUTION: choose a quadruple T*, delete exactly the witnesses T*
    fails to kill, rerun the unmodified mutual+direct machinery, and require
    that T* is found. This is the false-negative test — it fails loudly if the
    filter rejects everything regardless of input.
"""
from collections import defaultdict
from itertools import combinations
import platform
import random
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
cdist = lambda u, v: min((v - u) % N, (u - v) % N)
bcol = lambda e: 1 if (e[1] - e[0]) % N in DIFFS else 0

t0 = time.perf_counter()
chords = [e for e in combinations(range(N), 2) if cdist(*e) != 1]
idx = {e: i for i, e in enumerate(chords)}
M = len(chords)

records = []                       # (frozenset(R), F bitmask)
Fam = defaultdict(list)
for W in combinations(range(N), 5):
    p = list(combinations(W, 2))
    if any(cdist(*e) == 1 for e in p):
        continue
    col = [(e, bcol(e)) for e in p]
    for c in (0, 1):
        R = [idx[e] for e, b in col if b != c]
        if len(R) > 4:
            continue
        Fm = 0
        for e, b in col:
            if b == c:
                Fm |= 1 << idx[e]
        records.append((frozenset(R), Fm))
        if len(R) == 1:
            Fam[R[0]].append(Fm)

byR = defaultdict(list)
for R, Fm in records:
    byR[R].append(Fm)


def direct_indexed(T, index):
    mT = 0
    for c in T:
        mT |= 1 << c
    for k in range(1, 5):
        for sub in combinations(sorted(T), k):
            for Fm in index.get(frozenset(sub), ()):
                if not (Fm & mT):
                    return False
    return True


def direct_scan(T, recs):
    Ts = set(T)
    mT = 0
    for c in T:
        mT |= 1 << c
    for R, Fm in recs:
        if R <= Ts and not (Fm & mT):
            return False
    return True


def mutual_ok(T, fam):
    mT = 0
    for c in T:
        mT |= 1 << c
    for c in T:
        rest = mT & ~(1 << c)
        for Fm in fam.get(c, ()):
            if not (Fm & rest):
                return False
    return True


rng = random.Random(20260826)
c1 = c2 = 0
TRIALS = 400
mutual_pass = direct_pass = 0
for _ in range(TRIALS):
    T = tuple(sorted(rng.sample(range(M), 4)))
    di, ds = direct_indexed(T, byR), direct_scan(T, records)
    if di == ds:
        c1 += 1
    m = mutual_ok(T, Fam)
    if ds:
        direct_pass += 1
        if m:
            c2 += 1
    else:
        c2 += 1                     # vacuous: implication holds
    if m:
        mutual_pass += 1

# --- C3: planted solution ---------------------------------------------------
Tstar = tuple(sorted(rng.sample(range(M), 4)))
mTs = 0
for c in Tstar:
    mTs |= 1 << c
kept = [(R, Fm) for (R, Fm) in records if not (R <= set(Tstar) and not (Fm & mTs))]
removed = len(records) - len(kept)
byR2 = defaultdict(list)
fam2 = defaultdict(list)
for R, Fm in kept:
    byR2[R].append(Fm)
    if len(R) == 1:
        fam2[next(iter(R))].append(Fm)
c3_mutual = mutual_ok(Tstar, fam2)
c3_direct = direct_indexed(Tstar, byR2)
c3_scan = direct_scan(Tstar, kept)

print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"records_total={len(records)}")
print(f"C1_indexed_equals_exhaustive_scan={c1}/{TRIALS}")
print(f"C2_direct_implies_mutual={c2}/{TRIALS}")
print(f"random_quadruples_passing_mutual={mutual_pass}/{TRIALS}")
print(f"random_quadruples_passing_direct={direct_pass}/{TRIALS}")
print(f"C3_planted_T={list(Tstar)} witnesses_removed={removed}")
print(f"C3_planted_found_by_mutual={c3_mutual}")
print(f"C3_planted_found_by_direct_indexed={c3_direct}")
print(f"C3_planted_found_by_direct_scan={c3_scan}")
print(f"C3_passed={c3_mutual and c3_direct and c3_scan}")
print(f"runtime_seconds={time.perf_counter()-t0:.1f}")
