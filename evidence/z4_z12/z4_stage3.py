#!/usr/bin/env python3
"""HCP-001 Z4 stage 3 — mutual filtering, labelled dedup, D43 canonicalization,
and direct (R,F) evaluation of survivors.

Enumeration strategy and its completeness argument
--------------------------------------------------
Every quadruple T of non-cycle chords contains at least one chord; that chord
lies in some cyclic-distance class d, and some rotation r maps it onto the
class representative t0(d). So enumerating, for each of the 20 representatives
t0, all 3-hitting-sets of C_{t0} and forming T = {t0} u triple, reaches every
rotation class of quadruples that can satisfy the anchor condition at t0.
Sum of the 20 representative hitting counts = 4,576,960 candidates, versus
196,809,280 labelled anchored triples over all 860 anchors — the 43x saving is
exactly the rotation orbit size.

Rotation orbits have size 43 (43 is prime, so a 4-element chord set admits no
nontrivial rotational stabiliser); a reflection can identify two rotation
orbits, giving D43 orbits of size 43 or 86. Both are asserted, not assumed.

Filters are reported separately and never collapsed:
  raw anchored candidates -> mutual survivors -> distinct labelled -> D43
  representatives -> final direct survivors.
"""
from collections import defaultdict
from itertools import combinations
import hashlib
import json
import platform
import resource
import sys
import time

N = 43
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
cdist = lambda u, v: min((v - u) % N, (u - v) % N)
bcol = lambda e: 1 if (e[1] - e[0]) % N in DIFFS else 0

t_start = time.perf_counter()
chords = [e for e in combinations(range(N), 2) if cdist(*e) != 1]
idx = {e: i for i, e in enumerate(chords)}
M = len(chords)
cls = [cdist(*e) for e in chords]


def rot_e(e, r):
    a, b = (e[0] + r) % N, (e[1] + r) % N
    return (a, b) if a < b else (b, a)


def ref_e(e):
    a, b = (-e[0]) % N, (-e[1]) % N
    return (a, b) if a < b else (b, a)


ROT = [[idx[rot_e(chords[c], r)] for c in range(M)] for r in range(N)]
REF = [idx[ref_e(chords[c])] for c in range(M)]

# --- constraint families and the full record index -------------------------
Fam = defaultdict(list)          # anchor -> list of F bitmasks
byR = defaultdict(list)          # frozenset(R indices) -> list of F bitmasks
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
        if len(R) == 1:
            Fam[R[0]].append(Fm)
t_build = time.perf_counter() - t_start
rec_by_size = {k: sum(len(v) for r, v in byR.items() if len(r) == k) for k in (1, 2, 3, 4)}


def hitting_triples(t):
    """Generate every 3-subset of chords\\{t} hitting all of C_t, via the
    j = |X n U| partition (j=1 singleton + 2 outside U; j=2 pair + 1; j=3)."""
    cons = list(dict.fromkeys(Fam[t]))
    full = (1 << len(cons)) - 1
    Ubits = 0
    for F in cons:
        Ubits |= F
    U = [j for j in range(M) if (Ubits >> j) & 1]
    O = [j for j in range(M) if j != t and not ((Ubits >> j) & 1)]
    hit = {j: sum(1 << i for i, F in enumerate(cons) if (F >> j) & 1) for j in U}
    for a in U:
        if hit[a] == full:
            for x, y in combinations(O, 2):
                yield (a, x, y)
    for a, b in combinations(U, 2):
        if hit[a] | hit[b] == full:
            for x in O:
                yield (a, b, x)
    for a, b, c in combinations(U, 3):
        if hit[a] | hit[b] | hit[c] == full:
            yield (a, b, c)


def anchor_ok(t, others_mask):
    for F in Fam[t]:
        if not (F & others_mask):
            return False
    return True


reps = {}
for t in range(M):
    reps.setdefault(cls[t], t)

raw = 0
mutual = set()
for d in sorted(reps):
    t0 = reps[d]
    n_d = 0
    for tri in hitting_triples(t0):
        n_d += 1
        T = (t0,) + tri
        mT = 0
        for c in T:
            mT |= 1 << c
        ok = True
        for c in T:
            if not anchor_ok(c, mT & ~(1 << c)):
                ok = False
                break
        if ok:
            mutual.add(frozenset(T))
    raw += n_d
    print(f"  d={d:2d} anchored_candidates={n_d:>9d} cumulative_mutual={len(mutual):>7d}",
          flush=True)

t_mutual = time.perf_counter() - t_start


def rot_canon(T):
    best = None
    for r in range(N):
        img = tuple(sorted(ROT[r][c] for c in T))
        if best is None or img < best:
            best = img
    return best


def d43_canon(T):
    a = rot_canon(T)
    b = rot_canon([REF[c] for c in T])
    return min(a, b)


# labelled closure: expand each mutual survivor over its full rotation orbit,
# since enumeration only reached one representative per rotation class.
labelled = set()
for T in mutual:
    for r in range(N):
        labelled.add(tuple(sorted(ROT[r][c] for c in T)))

orbits = defaultdict(set)
for T in labelled:
    orbits[d43_canon(T)].add(T)
orbit_sizes = sorted({len(v) for v in orbits.values()})
orbit_sum = sum(len(v) for v in orbits.values())

# --- direct (R,F) evaluation of survivors -----------------------------------
def survives_direct(T):
    Ts = frozenset(T)
    mT = 0
    for c in T:
        mT |= 1 << c
    for k in range(1, 5):
        for sub in combinations(sorted(Ts), k):
            recs = byR.get(frozenset(sub))
            if not recs:
                continue
            for Fm in recs:
                if not (Fm & mT):
                    return False        # a witness stays monochromatic
    return True


direct = [T for T in labelled if survives_direct(T)]
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 3)

print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"records_by_R_size_1to4={[rec_by_size[k] for k in (1,2,3,4)]} sum={sum(rec_by_size.values())}")
print(f"raw_anchored_candidates_over_20_representatives={raw}")
print(f"mutual_survivors_representative_level={len(mutual)}")
print(f"distinct_labelled_after_rotation_closure={len(labelled)}")
print(f"anchored_occurrence_check_4x_distinct={4*len(labelled)}")
print(f"d43_representatives={len(orbits)}")
print(f"d43_orbit_size_sum={orbit_sum} equals_distinct_labelled={orbit_sum==len(labelled)}")
print(f"d43_orbit_sizes_observed={orbit_sizes} all_in_43_86={set(orbit_sizes)<= {43,86}}")
print(f"final_direct_survivors={len(direct)}")
print(f"runtime_seconds_build={t_build:.1f} runtime_seconds_mutual={t_mutual:.1f} "
      f"runtime_seconds_total={time.perf_counter()-t_start:.1f} peak_rss_gb={peak:.2f}")
if direct:
    blob = "\n".join(json.dumps(sorted(T)) for T in sorted(direct)) + "\n"
    open("z4_stage3_survivors.jsonl", "w", newline="").write(blob)
    print("survivors_sha256=" + hashlib.sha256(blob.encode()).hexdigest())
