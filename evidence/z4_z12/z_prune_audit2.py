#!/usr/bin/env python3
"""Prune audit, split by predicate so neither bound hides behind the other.

Both predicates are evaluated on every instance BEFORE any short-circuit, so a
bound that never fires alone is visible as such rather than being credited with
the union's activity.
"""
from collections import defaultdict
from itertools import combinations
import random

def coverage_lb(unmet):
    if not unmet: return 0
    cnt = defaultdict(int)
    for Fm in unmet:
        m = Fm
        while m:
            b = m & -m; cnt[b.bit_length()-1] += 1; m ^= b
    m_max = max(cnt.values()) if cnt else 1
    return -(-len(unmet) // m_max)

def disjoint_lb(unmet):
    used = 0; q = 0
    for Fm in sorted(unmet, key=lambda v: bin(v).count("1")):
        if not (Fm & used):
            q += 1; used |= Fm
    return q

def feasible(unmet, n, r):
    for sub in combinations(range(n), r):
        mask = 0
        for j in sub: mask |= 1 << j
        if all(Fm & mask for Fm in unmet): return True
    return False

rng = random.Random(20260826)
TRIALS = 4000
c_only = d_only = both = 0
c_uns = d_uns = u_uns = 0
for _ in range(TRIALS):
    n = rng.randint(6, 14); r = rng.randint(1, 3)
    unmet = []
    for _ in range(rng.randint(1, 7)):
        k = rng.randint(1, min(5, n)); m = 0
        for j in rng.sample(range(n), k): m |= 1 << j
        unmet.append(m)
    unmet = list(dict.fromkeys(unmet))
    cf = coverage_lb(unmet) > r          # both computed before short-circuit
    df = disjoint_lb(unmet) > r
    if cf and df: both += 1
    elif cf: c_only += 1
    elif df: d_only += 1
    if cf or df:
        ok = feasible(unmet, n, r)
        if ok:
            if cf: c_uns += 1
            if df: d_uns += 1
            u_uns += 1
print(f"trials={TRIALS}")
print(f"coverage_only_fired={c_only}")
print(f"disjoint_only_fired={d_only}")
print(f"both_fired={both}")
print(f"union_firing_rate={(c_only+d_only+both)/TRIALS:.3f}")
print(f"coverage_unsound={c_uns}")
print(f"disjoint_unsound={d_uns}")
print(f"union_unsound={u_uns}")
print(f"SPLIT_AUDIT_PASSED={u_uns==0 and c_only+both>0 and d_only+both>0}")
