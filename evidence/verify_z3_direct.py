#!/usr/bin/env python3
"""Exact direct-witness verifier for three non-cycle toggles (HCP-001 Z3)."""

from collections import Counter
from itertools import combinations
import platform
import time

N = 43
S = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
DIFFS = S | {(-d) % N for d in S}


def base_edge(e):
    return (e[1] - e[0]) % N in DIFFS


def cycle_edge(e):
    return min((e[1] - e[0]) % N, (e[0] - e[1]) % N) == 1


started = time.perf_counter()
chords = [e for e in combinations(range(N), 2) if not cycle_edge(e)]
index = {e: i for i, e in enumerate(chords)}
assert len(chords) == 860

# constraints[t] lists the corrective chord sets for every cycle-free 5-set
# made monochromatic by toggling chord t alone. A set remains monochromatic
# after two further toggles iff neither further toggle is corrective for it.
constraints = [[] for _ in chords]
cycle_free_fives = 0
for q in combinations(range(N), 5):
    pairs = list(combinations(q, 2))
    if any(cycle_edge(e) for e in pairs):
        continue
    cycle_free_fives += 1
    present = [e for e in pairs if base_edge(e)]
    if len(present) == 1:
        t = index[present[0]]
        constraints[t].append(frozenset(index[e] for e in pairs if not base_edge(e)))
    elif len(present) == 9:
        missing = next(e for e in pairs if not base_edge(e))
        t = index[missing]
        constraints[t].append(frozenset(index[e] for e in present))

assert cycle_free_fives == 567_987
assert all(constraints)

# Compute every unordered pair hitting every corrective set for each t.
# Completeness: a hitting pair must meet the first row. Fix that member a;
# either a meets every row, or its partner must meet the first row missed by a.
hitting_pairs = []
for t, rows in enumerate(constraints):
    candidates = set()
    for a in rows[0]:
        first_unmet = next((row for row in rows if a not in row), None)
        if first_unmet is None:
            candidates.update(tuple(sorted((a, b))) for b in range(len(chords))
                              if b != a and b != t and a != t)
        else:
            candidates.update(tuple(sorted((a, b))) for b in first_unmet
                              if b != a and b != t and a != t)
    hitting_pairs.append({p for p in candidates
                          if t not in p and all(p[0] in row or p[1] in row for row in rows)})

# If a triple T had no surviving single-toggle witness, then for every t in T
# the other two members of T would be a hitting pair for constraints[t].
candidate_triples = set()
for t, pairs in enumerate(hitting_pairs):
    for a, b in pairs:
        if t not in (a, b):
            candidate_triples.add(tuple(sorted((t, a, b))))

mutually_corrective = []
for triple in candidate_triples:
    if all(tuple(x for x in triple if x != t) in hitting_pairs[t] for t in triple):
        mutually_corrective.append(triple)

pair_size_histogram = Counter(map(len, hitting_pairs))
assert all(t not in pair for t, pairs in enumerate(hitting_pairs) for pair in pairs)
assert sum(map(len, hitting_pairs)) == 451_027
assert len(candidate_triples) == 450_769
assert not mutually_corrective

print(f"python={platform.python_version()}")
unordered_triples = len(chords) * (len(chords) - 1) * (len(chords) - 2) // 6
assert unordered_triples == 105_639_820
print(f"noncycle_chords={len(chords)} unordered_triples={unordered_triples}")
print(f"cycle_free_5sets={cycle_free_fives}")
print("two_toggle_hitting_pair_count_histogram=" + repr(dict(sorted(pair_size_histogram.items()))))
print(f"total_two_toggle_hitting_pairs_across_first_toggles={sum(map(len, hitting_pairs))}")
print(f"candidate_triples_needing_mutual_check={len(candidate_triples)}")
print("mutually_corrective_triples=0")
print("Z3_direct_result=UNSAT_all_105639820_labeled_triples")
print(f"runtime_seconds={time.perf_counter() - started:.6f}")
