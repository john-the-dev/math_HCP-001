#!/usr/bin/env python3
"""Verify complete agreement between the two recorded K14 implementations."""
from csv import DictReader
from decimal import Decimal
from pathlib import Path

from replay_published import (EMPTY_SHA256, IMPLEMENTATION, MODE, digest,
                              load_completed)

DISTANCES = set(range(2, 22))
INTMASK_IMPLEMENTATION = "independent_intmask_dedupe_maxincidence"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    here = Path(__file__).parent
    repo_root = here.parents[1]
    source = repo_root / "evidence" / "z4_z12" / "z_general_memo.py"
    source_label = str(source.relative_to(repo_root))
    source_sha = digest(source)
    published = load_completed(
        here / "published-checkpoints.jsonl", source_label, source_sha, 14)
    require(set(published) == DISTANCES,
            "published replay must contain every distance 2..21 exactly once")

    table_path = repo_root / "evidence" / "k14_independent" \
        / "anchor-results.tsv"
    with table_path.open(newline="") as handle:
        rows = [row for row in DictReader(handle, delimiter="\t")
                if row["distance"] != "TOTAL"]
    require(len(rows) == 20, "intmask table must contain 20 anchor rows")
    intmask = {int(row["distance"]): row for row in rows}
    require(set(intmask) == DISTANCES,
            "intmask table must contain every distance 2..21 exactly once")

    for distance in sorted(DISTANCES):
        left = published[distance]
        right = intmask[distance]
        require(right["implementation"] == INTMASK_IMPLEMENTATION,
                f"bad intmask identity at distance {distance}")
        require(right["k"] == "14" and right["mode"] == MODE,
                f"bad intmask run mode at distance {distance}")
        require(left["implementation"] == IMPLEMENTATION,
                f"bad published identity at distance {distance}")
        for field in ("under_target_hits", "target_size_hits"):
            require(left[field] == int(right[field]),
                    f"survivor-count disagreement at distance {distance}")
            if left[field] == 0:
                prefix = field.removesuffix("_hits")
                require(left[f"{prefix}_sha256"] == EMPTY_SHA256,
                        f"empty survivor digest mismatch at distance {distance}")

    states = sum(record["states"] for record in published.values())
    runtime = sum(Decimal(str(record["runtime_seconds"]))
                  for record in published.values())
    print(f"published_source_sha256={source_sha}")
    print("implementations=published_tuple_frozenset,"
          "independent_intmask_dedupe_maxincidence")
    print("distances=2..21 anchors=20")
    print("under_target_agreement=20/20 all_zero=True")
    print("target_size_agreement=20/20 all_zero=True")
    print(f"published_total_states={states} runtime_seconds={runtime}")
    print("DUAL_REPLAY=PASS")


if __name__ == "__main__":
    main()
