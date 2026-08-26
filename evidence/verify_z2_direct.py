#!/usr/bin/env python3
"""Exhaustively certify the HCP-001 two-chord boundary by direct witnesses."""

from itertools import combinations
from collections import Counter
import platform
import time


N = 43
S = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
DIFFS = S | {(-d) % N for d in S}


def edge(u, v):
    return (u, v) if u < v else (v, u)


def base_edge(e):
    u, v = e
    return (v - u) % N in DIFFS


def cycle_edge(e):
    u, v = e
    return min((v - u) % N, (u - v) % N) == 1


def main():
    started = time.perf_counter()
    chords = [e for e in combinations(range(N), 2) if not cycle_edge(e)]
    chord_index = {e: i for i, e in enumerate(chords)}
    assert len(chords) == 860

    # For toggle t, every entry (Q,C) says toggling t alone makes the
    # cycle-edge-free 5-set Q monochromatic; a second toggle can repair Q only
    # if its chord index lies in C.
    constraints = [[] for _ in chords]
    induced_edge_histogram = Counter()
    cycle_free_fives = 0

    for q in combinations(range(N), 5):
        pairs = [edge(u, v) for u, v in combinations(q, 2)]
        if any(cycle_edge(e) for e in pairs):
            continue
        cycle_free_fives += 1
        present = [e for e in pairs if base_edge(e)]
        induced_edge_histogram[len(present)] += 1

        if len(present) == 1:
            toggle = chord_index[present[0]]
            corrective = frozenset(chord_index[e] for e in pairs if not base_edge(e))
            constraints[toggle].append((q, corrective, "I5"))
        elif len(present) == 9:
            missing = next(e for e in pairs if not base_edge(e))
            toggle = chord_index[missing]
            corrective = frozenset(chord_index[e] for e in present)
            constraints[toggle].append((q, corrective, "K5"))

    assert cycle_free_fives == 567_987
    assert induced_edge_histogram[1] == 5_418
    assert induced_edge_histogram[9] == 4_687
    assert all(constraints)

    common_corrective = []
    for rows in constraints:
        allowed = set(rows[0][1])
        for _, corrective, _ in rows[1:]:
            allowed.intersection_update(corrective)
        common_corrective.append(frozenset(allowed))

    allowed_size_histogram = Counter(map(len, common_corrective))
    assert allowed_size_histogram == Counter({0: 602, 2: 258})

    pair_count = 0
    witnesses_from_first = 0
    witnesses_from_second = 0
    examples = []
    mutual_corrective_pairs = []

    for first, second in combinations(range(len(chords)), 2):
        pair_count += 1
        witness = next(
            (row for row in constraints[first] if second not in row[1]),
            None,
        )
        source = first
        if witness is None:
            witness = next(
                (row for row in constraints[second] if first not in row[1]),
                None,
            )
            source = second

        if witness is None:
            mutual_corrective_pairs.append((chords[first], chords[second]))
            continue

        q, _, kind = witness
        if source == first:
            witnesses_from_first += 1
        else:
            witnesses_from_second += 1

        # Directly re-evaluate the ten non-cycle pairs after both toggles.
        toggled = {chords[first], chords[second]}
        values = [base_edge(e) ^ (e in toggled) for e in combinations(q, 2)]
        assert (kind == "K5" and all(values)) or (kind == "I5" and not any(values))
        assert all(not cycle_edge(e) for e in combinations(q, 2))
        if len(examples) < 10:
            examples.append((chords[first], chords[second], kind, q))

    assert pair_count == 369_370
    assert not mutual_corrective_pairs
    assert witnesses_from_first + witnesses_from_second == pair_count

    print(f"python={platform.python_version()}")
    print(f"noncycle_chords={len(chords)} unordered_pairs={pair_count}")
    print(f"cycle_free_5sets={cycle_free_fives}")
    print("base_induced_edge_histogram=" + repr(dict(sorted(induced_edge_histogram.items()))))
    print("single_toggle_direct_witness_counts=" + repr(dict(sorted(Counter(map(len, constraints)).items()))))
    print("common_corrective_partner_count_histogram=" + repr(dict(sorted(allowed_size_histogram.items()))))
    print(f"pair_witnesses_from_first={witnesses_from_first} from_second={witnesses_from_second}")
    print("mutual_corrective_pairs=0")
    print("Z2_direct_result=UNSAT_all_369370_labeled_pairs")
    for first, second, kind, q in examples:
        print(f"example toggles={first},{second} witness={kind} {q}")
    print(f"runtime_seconds={time.perf_counter() - started:.6f}")


if __name__ == "__main__":
    main()
