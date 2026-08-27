#!/usr/bin/env python3
"""Run the published K14 implementation one anchor at a time with checkpoints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import time

FIELDS = {
    "distance", "implementation", "k", "mode", "source", "source_sha256",
    "under_target_hits", "target_size_hits", "under_target_sha256",
    "target_size_sha256", "states", "runtime_seconds",
}
IMPLEMENTATION = "published_tuple_frozenset"
MODE = "up_to_k"
EMPTY_SHA256 = hashlib.sha256(b"[]").hexdigest()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def survivor_digest(survivors, chords):
    canonical = []
    for survivor in sorted(survivors):
        canonical.append([list(chords[index]) for index in survivor])
    payload = json.dumps(canonical, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_completed(path, source_label, source_sha, k):
    completed = {}
    if not path.exists():
        return completed
    for number, line in enumerate(path.read_text().splitlines(), 1):
        record = json.loads(line)
        if set(record) != FIELDS:
            raise ValueError(f"checkpoint schema mismatch on line {number}")
        if (record["source"] != source_label
                or record["source_sha256"] != source_sha
                or record["implementation"] != IMPLEMENTATION
                or record["mode"] != MODE or record["k"] != k):
            raise ValueError(f"checkpoint identity mismatch on line {number}")
        distance = record["distance"]
        if distance not in range(2, 22):
            raise ValueError(f"bad checkpoint distance on line {number}")
        for prefix in ("under_target", "target_size"):
            count = record[f"{prefix}_hits"]
            checksum = record[f"{prefix}_sha256"]
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"bad survivor count on line {number}")
            if not isinstance(checksum, str) or len(checksum) != 64:
                raise ValueError(f"bad survivor hash on line {number}")
            if count == 0 and checksum != EMPTY_SHA256:
                raise ValueError(f"empty survivor hash mismatch on line {number}")
        if not isinstance(record["states"], int) or record["states"] <= 0:
            raise ValueError(f"bad state count on line {number}")
        if not isinstance(record["runtime_seconds"], (int, float)) \
                or record["runtime_seconds"] < 0:
            raise ValueError(f"bad runtime on line {number}")
        if distance in completed:
            raise ValueError(f"duplicate checkpoint distance {distance}")
        completed[distance] = record
    return completed


def append_checkpoint(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).parents[1]
                        / "z4_z12" / "z_general_memo.py")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k", type=int, default=14)
    parser.add_argument("--distances", type=int, nargs="+",
                        default=list(range(2, 22)))
    args = parser.parse_args()
    if args.k != 14:
        raise ValueError("this evidence runner is pinned to k=14")
    if len(set(args.distances)) != len(args.distances):
        raise ValueError("duplicate requested distance")
    if any(distance not in range(2, 22) for distance in args.distances):
        raise ValueError("distances must be in 2..21")

    source = args.source.resolve()
    repo_root = Path(__file__).parents[2].resolve()
    try:
        source_label = str(source.relative_to(repo_root))
    except ValueError:
        source_label = source.name
    source_sha = digest(source)
    namespace = runpy.run_path(str(source), run_name="k14_published_replay")
    reps = namespace["reps"]
    original_reps = dict(reps)
    completed = load_completed(
        args.output, source_label, source_sha, args.k)

    for distance in args.distances:
        if distance in completed:
            print(f"distance={distance} checkpoint=SKIP", flush=True)
            continue
        reps.clear()
        reps[distance] = original_reps[distance]
        started = time.perf_counter()
        under, target, states = namespace["search"](args.k, True, True)
        record = {
            "distance": distance,
            "implementation": IMPLEMENTATION,
            "k": args.k,
            "mode": MODE,
            "source": source_label,
            "source_sha256": source_sha,
            "under_target_hits": len(under),
            "target_size_hits": len(target),
            "under_target_sha256": survivor_digest(under, namespace["chords"]),
            "target_size_sha256": survivor_digest(target, namespace["chords"]),
            "states": states,
            "runtime_seconds": round(time.perf_counter() - started, 2),
        }
        append_checkpoint(args.output, record)
        print(json.dumps(record, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
