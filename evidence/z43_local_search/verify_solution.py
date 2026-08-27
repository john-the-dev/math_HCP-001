#!/usr/bin/env python3
"""Directly enumerate all 43-choose-5 sets in a local-search output graph."""

import argparse
import hashlib
import itertools
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph", type=Path)
    args = parser.parse_args()
    raw = args.graph.read_bytes()
    lines = raw.decode().splitlines()
    assert lines[0] == "n 43"
    edges = set()
    for line in lines[1:]:
        tag, left, right = line.split()
        edge = tuple(sorted((int(left), int(right))))
        assert tag == "e" and 0 <= edge[0] < edge[1] < 43 and edge not in edges
        edges.add(edge)
    k5 = []
    i5 = []
    checked = 0
    for vertices in itertools.combinations(range(43), 5):
        count = sum(tuple(sorted(edge)) in edges
                    for edge in itertools.combinations(vertices, 2))
        checked += 1
        if count == 10:
            k5.append(vertices)
        elif count == 0:
            i5.append(vertices)
    print(f"sha256={hashlib.sha256(raw).hexdigest()}")
    print(f"edges={len(edges)} five_sets_checked={checked}")
    print(f"K5={len(k5)} I5={len(i5)} F={len(k5) + len(i5)}")
    if k5 or i5:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
