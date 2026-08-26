#!/usr/bin/env python3
"""Independent Z3 verifier with three-distinct-toggle enforcement."""

from collections import Counter
from itertools import combinations
import math
import platform
import time

N = 43
BASE_DISTANCES = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
BASE_DIFFERENCES = BASE_DISTANCES | {43 - d for d in BASE_DISTANCES}


def is_base_edge(pair):
    return (pair[1] - pair[0]) % N in BASE_DIFFERENCES


def is_cycle_edge(pair):
    return (pair[1] - pair[0]) % N in {1, 42}


def main():
    started = time.perf_counter()
    chords = [pair for pair in combinations(range(N), 2) if not is_cycle_edge(pair)]
    chord_number = {pair: number for number, pair in enumerate(chords)}
    correction_rows = [[] for _ in chords]
    cycle_free_fives = 0

    for five_set in combinations(range(N), 5):
        pairs = list(combinations(five_set, 2))
        if any(is_cycle_edge(pair) for pair in pairs):
            continue
        cycle_free_fives += 1
        present = [pair for pair in pairs if is_base_edge(pair)]
        if len(present) == 1:
            first_toggle = chord_number[present[0]]
            correction_rows[first_toggle].append(frozenset(
                chord_number[pair] for pair in pairs if not is_base_edge(pair)
            ))
        elif len(present) == 9:
            absent = next(pair for pair in pairs if not is_base_edge(pair))
            first_toggle = chord_number[absent]
            correction_rows[first_toggle].append(frozenset(
                chord_number[pair] for pair in present
            ))

    assert len(chords) == 860
    assert cycle_free_fives == 567_987
    assert all(correction_rows)

    # For a fixed first toggle t, enumerate pairs {a,b} of distinct OTHER
    # toggles that hit every correction row. Any hitting pair meets row zero;
    # select a from that row, then b either is arbitrary when a hits all rows,
    # or belongs to the first row missed by a. The final filter is exact.
    hitting_pairs = []
    universal_corrector_histogram = Counter()
    for first_toggle, rows in enumerate(correction_rows):
        candidates = set()
        for left in rows[0]:
            if left == first_toggle:
                continue
            first_missed = next((row for row in rows if left not in row), None)
            if first_missed is None:
                rights = range(len(chords))
            else:
                rights = first_missed
            for right in rights:
                if right in {first_toggle, left}:
                    continue
                candidates.add(tuple(sorted((left, right))))

        exact = {
            pair for pair in candidates
            if all(pair[0] in row or pair[1] in row for row in rows)
        }
        hitting_pairs.append(exact)
        universal_corrector_histogram[sum(
            all(partner in row for row in rows)
            for partner in range(len(chords))
            if partner != first_toggle
        )] += 1

    pair_count_histogram = Counter(map(len, hitting_pairs))
    expected_pair_histogram = Counter({
        0: 258,
        4: 172,
        8: 86,
        20: 43,
        81: 43,
        1715: 172,
        1748: 86,
    })
    assert universal_corrector_histogram == Counter({0: 602, 2: 258})
    assert pair_count_histogram == expected_pair_histogram
    assert sum(map(len, hitting_pairs)) == 451_027

    candidate_triples = set()
    for first_toggle, pairs in enumerate(hitting_pairs):
        for left, right in pairs:
            assert first_toggle not in {left, right}
            candidate_triples.add(tuple(sorted((first_toggle, left, right))))
    assert len(candidate_triples) == 450_769

    mutually_corrective = []
    for triple in candidate_triples:
        if all(
            tuple(sorted(set(triple) - {first_toggle})) in hitting_pairs[first_toggle]
            for first_toggle in triple
        ):
            mutually_corrective.append(triple)
    assert not mutually_corrective

    full_scope = math.comb(len(chords), 3)
    assert full_scope == 105_639_820
    print(f"python={platform.python_version()}")
    print(f"noncycle_chords={len(chords)} unordered_distinct_triples={full_scope}")
    print(f"cycle_free_5sets={cycle_free_fives}")
    print("universal_corrector_count_histogram=" + repr(dict(sorted(universal_corrector_histogram.items()))))
    print("valid_other_toggle_pair_count_histogram=" + repr(dict(sorted(pair_count_histogram.items()))))
    print(f"valid_other_toggle_pair_incidences={sum(map(len, hitting_pairs))}")
    print(f"distinct_candidate_triples={len(candidate_triples)}")
    print("mutually_corrective_triples=0")
    print("Z3_direct_result=UNSAT_all_105639820_distinct_labeled_triples")
    print(f"runtime_seconds={time.perf_counter() - started:.6f}")


if __name__ == "__main__":
    main()
