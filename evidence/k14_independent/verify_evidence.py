#!/usr/bin/env python3
"""Verify K14 aggregate metadata and cyclic-anchor coverage."""
from csv import DictReader
from decimal import Decimal
from itertools import combinations
from pathlib import Path

N = 43
DISTANCES = set(range(2, 22))
S = frozenset({1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21})
DIFFS = S | frozenset((-d) % N for d in S)
IMPLEMENTATION = "independent_intmask_dedupe_maxincidence"
FIELDS = [
    "distance", "implementation", "k", "mode", "under_target_hits",
    "target_size_hits", "states", "runtime_seconds",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def edge(u, v):
    return (u, v) if u < v else (v, u)


def distance(e):
    u, v = e
    return min((v - u) % N, (u - v) % N)


def baseline_color(e):
    u, v = e
    return int((v - u) % N in DIFFS)


def verify_table(path):
    with path.open(newline="") as handle:
        reader = DictReader(handle, delimiter="\t")
        require(reader.fieldnames == FIELDS, "unexpected TSV schema")
        rows = list(reader)

    totals = [row for row in rows if row["distance"] == "TOTAL"]
    anchors = [row for row in rows if row["distance"] != "TOTAL"]
    require(len(totals) == 1, "expected exactly one TOTAL row")
    require(len(anchors) == 20, "expected exactly 20 anchor rows")
    require({int(row["distance"]) for row in anchors} == DISTANCES,
            "anchor distances must be exactly 2..21")

    for row in rows:
        require(row["implementation"] == IMPLEMENTATION,
                "unexpected implementation")
        require(row["k"] == "14", "unexpected k")
        require(row["mode"] == "up_to_k", "unexpected mode")
        require(row["under_target_hits"] == "0", "under-target survivor")
        require(row["target_size_hits"] == "0", "target-size survivor")

    total = totals[0]
    require(sum(int(row["states"]) for row in anchors) == int(total["states"]),
            "state total mismatch")
    require(sum(Decimal(row["runtime_seconds"]) for row in anchors)
            == Decimal(total["runtime_seconds"]), "runtime total mismatch")
    print("table_rows=20 distances=2..21")
    print(f"implementation={IMPLEMENTATION}")
    print("k=14 mode=up_to_k under_target_hits=0 target_size_hits=0")
    print(f"total_states={total['states']} runtime_seconds={total['runtime_seconds']}")


def verify_rotation_bijection():
    chords = {
        (u, v) for u, v in combinations(range(N), 2)
        if distance((u, v)) != 1
    }
    images = []
    for d in sorted(DISTANCES):
        representative = (0, d)
        require(distance(representative) == d, f"bad representative for {d}")
        for rotation in range(N):
            rotated = edge(rotation, (d + rotation) % N)
            require(distance(rotated) == d, f"rotation left distance class {d}")
            images.append(rotated)

    require(len(images) == 860, "expected 860 rotation images")
    require(len(set(images)) == 860, "rotation images are not pairwise distinct")
    require(set(images) == chords, "rotation images do not cover chord universe")
    color_checks = 0
    for original in chords:
        for rotation in range(N):
            rotated = edge((original[0] + rotation) % N,
                           (original[1] + rotation) % N)
            require(baseline_color(rotated) == baseline_color(original),
                    "baseline color is not rotation-equivariant")
            color_checks += 1
    print("rotation_anchor_checks=860")
    print("distinct_anchors_touched=860 of 860")
    print(f"rotation_color_checks={color_checks} failures=0")
    print("rotation_bijection=PASS")


def main():
    verify_table(Path(__file__).with_name("anchor-results.tsv"))
    verify_rotation_bijection()
    print("PASS")


if __name__ == "__main__":
    main()
