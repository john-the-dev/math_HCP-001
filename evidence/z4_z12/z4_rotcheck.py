#!/usr/bin/env python3
"""HCP-001 Z4 — rotation-bijection wiring assertion.

For each cyclic-distance representative t0 (d = 2..21) and every rotation
r = 0..42, assert that rotating t0's complete F-constraint family yields
EXACTLY the independently enumerated family of the translated toggle rot_r(t0).

This touches all 20*43 = 860 anchors and establishes the bijection under which
the per-toggle hitting counts are constant, without recomputing any count.
"""
from collections import defaultdict, Counter
from itertools import combinations
import hashlib
import json
import platform
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
cls = [cdist(*e) for e in chords]


def rot_edge(e, r):
    a, b = (e[0] + r) % N, (e[1] + r) % N
    return (a, b) if a < b else (b, a)


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

reps = {}
for t in range(M):
    reps.setdefault(cls[t], t)

anchors_checked = 0
failures = []
for d, t0i in sorted(reps.items()):
    base = Counter(Fam[t0i])
    e0 = chords[t0i]
    for r in range(N):
        tgt = idx[rot_edge(e0, r)]
        rotated = Counter(
            frozenset(idx[rot_edge(chords[c], r)] for c in F) for F in Fam[t0i]
        )
        if rotated != Counter(Fam[tgt]):
            failures.append((d, r))
        anchors_checked += 1

distinct_anchors = len({idx[rot_edge(chords[reps[d]], r)]
                        for d in reps for r in range(N)})

# --- restate the vector fingerprint under an explicit byte contract --------
wvec = [26, 8, 15, 10, 12, 8, 12, 18, 6, 18, 7, 18, 12, 11, 3, 2, 7, 3, 30, 9]
hvec = [20, 734449, 734449, 6936, 3424, 6984, 3460, 20, 17189, 20,
        3654, 8, 3460, 86, 762530, 68769, 734503, 762530, 20, 734449]
payload = json.dumps({"w": wvec, "h": hvec}, sort_keys=True)
sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()

print(f"python={platform.python_version()} platform={platform.platform()}")
print(f"rotation_anchor_checks={anchors_checked} distinct_anchors_touched={distinct_anchors} of {M}")
print(f"rotation_bijection_failures={len(failures)}")
print(f"rotation_bijection_holds={not failures}")
print(f"vectors_sha256_recomputed={sha}")
print(f"payload_len_bytes={len(payload.encode('utf-8'))}")
print(f"payload_repr={payload!r}")
print(f"runtime_seconds={time.perf_counter()-t0:.2f}")
