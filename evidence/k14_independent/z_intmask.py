#!/usr/bin/env python3
"""Independent integer-mask HCP-001 generalized obligation search."""
from collections import defaultdict
from itertools import combinations
import argparse
import platform
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
cdist = lambda u, v: min((v-u) % N, (u-v) % N)
bcol = lambda e: 1 if (e[1]-e[0]) % N in DIFFS else 0
chords = [e for e in combinations(range(N), 2) if cdist(*e) != 1]
idx = {e:i for i,e in enumerate(chords)}
classes = [cdist(*e) for e in chords]

by_required = defaultdict(list)
for W in combinations(range(N), 5):
    pairs = list(combinations(W, 2))
    if any(cdist(*e) == 1 for e in pairs):
        continue
    colors = [(e, bcol(e)) for e in pairs]
    for color in (0, 1):
        required = [idx[e] for e,b in colors if b != color]
        if len(required) > 4:
            continue
        rmask = sum(1 << x for x in required)
        fmask = sum(1 << idx[e] for e,b in colors if b == color)
        by_required[rmask].append(fmask)

reps = {}
for t, d in enumerate(classes):
    reps.setdefault(d, t)


def activated(tmask, x):
    bitx = 1 << x
    rest = [b.bit_length()-1 for b in bits(tmask ^ bitx)]
    out = list(by_required.get(bitx, ()))
    for size in (1, 2, 3):
        for sub in combinations(rest, size):
            rmask = bitx
            for y in sub:
                rmask |= 1 << y
            out.extend(by_required.get(rmask, ()))
    return out


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit
        mask ^= bit


def lower_bound(unmet):
    if not unmet:
        return 0
    counts = defaultdict(int)
    for fmask in unmet:
        for bit in bits(fmask):
            counts[bit] += 1
    if not counts:
        return len(unmet) + 1
    coverage = (len(unmet) + max(counts.values()) - 1) // max(counts.values())
    used = 0
    disjoint = 0
    for fmask in sorted(unmet, key=int.bit_count):
        if not fmask & used:
            disjoint += 1
            used |= fmask
    return max(coverage, disjoint)


def run_anchor(k, distance):
    anchor = reps[distance]
    anchor_mask = 1 << anchor
    memo = set()
    under, target = set(), set()
    states = 0

    def rec(tmask, unmet):
        nonlocal states
        if tmask in memo:
            return
        memo.add(tmask)
        states += 1
        size = tmask.bit_count()
        if size == k:
            if not unmet:
                target.add(tmask)
            return
        if not unmet:
            under.add(tmask)
            return
        if lower_bound(unmet) > k-size:
            return
        pivot = min(unmet, key=int.bit_count)
        incidence = defaultdict(int)
        for fmask in unmet:
            for bit in bits(fmask & pivot):
                incidence[bit] += 1
        for bit in sorted(bits(pivot), key=lambda b: (-incidence[b], b)):
            if tmask & bit:
                continue
            x = bit.bit_length()-1
            t2 = tmask | bit
            u2 = {f for f in unmet if not f & bit}
            for fmask in activated(t2, x):
                if not fmask & t2:
                    u2.add(fmask)
            rec(t2, tuple(u2))

    rec(anchor_mask, tuple(set(by_required.get(anchor_mask, ()))))
    return under, target, states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", required=True, type=int)
    ap.add_argument("--distance", type=int)
    args = ap.parse_args()
    started = time.perf_counter()
    distances = [args.distance] if args.distance else sorted(reps)
    all_under, all_target, total_states = set(), set(), 0
    for distance in distances:
        under, target, states = run_anchor(args.k, distance)
        all_under |= under
        all_target |= target
        total_states += states
        print(f"anchor_distance={distance} under={len(under)} target={len(target)} states={states}", flush=True)
    print(f"python={platform.python_version()}")
    print("implementation=independent_intmask_dedupe_maxincidence")
    print("mode=up_to_k")
    print(f"target_k={args.k}")
    print(f"under_target_hits={len(all_under)}")
    print(f"target_size_hits={len(all_target)}")
    print(f"total_survivors={len(all_under)+len(all_target)}")
    print(f"unique_states={total_states}")
    print(f"runtime_seconds={time.perf_counter()-started:.2f}")


if __name__ == "__main__":
    main()
