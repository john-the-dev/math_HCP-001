#!/usr/bin/env python3
"""HCP-001 Zk — generalized exact exclusion search, cardinalities k >= 4.

Independent implementation. Search: anchor at a cyclic-distance representative
t0, then branch on the members of a currently-unmet constraint (classic
hitting-set branching, factor <= 9). A witness (c,W) becomes an obligation only
once R_c(W) is a subset of T, so obligations GROW as T grows; a currently-unmet
obligation must still be met by some future toggle, which is what makes the
lower bounds below valid.

Pruning bounds (the claims under test):
  coverage      ceil(unmet / m) future toggles required, m = max unmet
                constraints any single eligible toggle hits
  disjointness  a pairwise-disjoint unmet subfamily needs one future toggle
                each (a chord lies in at most one member of a disjoint family)

Both are LOWER bounds on remaining toggles, so they may prune but must never
change the survivor set. That is tested differentially: --bounds on/off must
agree on survivors exactly, not merely on counts.
"""
from collections import defaultdict
from itertools import combinations
import argparse
import platform
import random
import sys
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
cdist = lambda u, v: min((v - u) % N, (u - v) % N)
bcol = lambda e: 1 if (e[1] - e[0]) % N in DIFFS else 0

chords = [e for e in combinations(range(N), 2) if cdist(*e) != 1]
idx = {e: i for i, e in enumerate(chords)}
M = len(chords)
cls = [cdist(*e) for e in chords]

byR = defaultdict(list)
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
        byR[frozenset(R)].append(Fm)

reps = {}
for t in range(M):
    reps.setdefault(cls[t], t)


def new_obligations(T, x):
    """Records whose R is a subset of T|{x} and contains x."""
    out = []
    rest = [c for c in T if c != x]
    for k in range(0, 4):
        for sub in combinations(rest, k):
            out.extend(byR.get(frozenset(sub + (x,)), ()))
    return out


def lower_bound(unmet, use_bounds):
    if not use_bounds or not unmet:
        return 0
    # coverage: m = max number of unmet constraints a single chord hits
    cnt = defaultdict(int)
    for Fm in unmet:
        m = Fm
        while m:
            b = m & -m
            cnt[b.bit_length() - 1] += 1
            m ^= b
    m_max = max(cnt.values()) if cnt else 1
    cov = -(-len(unmet) // m_max)
    # disjointness: greedy pairwise-disjoint subfamily
    used = 0
    dis = 0
    for Fm in sorted(unmet, key=lambda v: bin(v).count("1")):
        if not (Fm & used):
            dis += 1
            used |= Fm
    return max(cov, dis)


def search(k, use_bounds, use_memo=False):
    """Return (under_target, target_hits, states). Anchored per representative.

    Memoization (sound): unmet is a pure function of T and the record set, and
    the remaining budget is k - |T|, so within a fixed (k, anchor) run the
    selected-toggle set alone determines the subtree. Reaching the same T by a
    different branch cannot change what lies below it. Survivors accumulate in
    shared sets, so skipping a repeat loses nothing.
    """
    under_target, target_hits, states = set(), set(), 0
    memo = set()

    def rec(T, unmet):
        nonlocal states
        if use_memo:
            key = frozenset(T)
            if key in memo:
                return
            memo.add(key)
        states += 1
        if len(T) == k:
            if not unmet:
                target_hits.add(tuple(sorted(T)))
            return
        if not unmet:
            under_target.add(tuple(sorted(T)))
            return
        if lower_bound(unmet, use_bounds) > k - len(T):
            return
        pivot = min(unmet, key=lambda v: bin(v).count("1"))
        m = pivot
        while m:
            b = m & -m
            x = b.bit_length() - 1
            m ^= b
            if x in T:
                continue
            T2 = T + (x,)
            bit = 1 << x
            mT2 = 0
            for c in T2:
                mT2 |= 1 << c
            u2 = [Fm for Fm in unmet if not (Fm & bit)]
            for Fm in new_obligations(T2, x):
                if not (Fm & mT2):
                    u2.append(Fm)
            rec(T2, u2)

    for d in sorted(reps):
        t0 = reps[d]
        memo.clear()                      # memo is per (k, anchor)
        base = [Fm for Fm in byR.get(frozenset((t0,)), ())]
        rec((t0,), list(base))
    return under_target, target_hits, states


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--bounds", choices=["on", "off"], default="on")
    ap.add_argument("--memo", choices=["on", "off"], default="off")
    a = ap.parse_args()
    t0 = time.perf_counter()
    ut, th, states = search(a.k, a.bounds == "on", a.memo == "on")
    print(f"python={platform.python_version()} bounds={a.bounds} memo={a.memo}")
    print("mode=up_to_k")
    print(f"target_k={a.k}")
    print(f"under_target_hits={len(ut)}")
    print(f"target_size_hits={len(th)}")
    print(f"total_survivors={len(ut) + len(th)}")
    print(f"unique_states={states}")
    if ut:
        print(f"example_under_target_survivor={sorted(ut)[0]}")
    print(f"runtime_seconds={time.perf_counter()-t0:.2f}")
