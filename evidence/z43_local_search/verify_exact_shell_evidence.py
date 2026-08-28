#!/usr/bin/env python3
"""Authenticate checked exact-shell local-repair certificates."""

import argparse
import hashlib
from pathlib import Path


CASES = {
    13: (
        "fa1f2fc2c3bec954a2e1800356819d21347908497b4b0f1cf2688bb270c22a50",
        "8b53cdbdcaabec794494d48447345674f76bc3a60125db1aa8f493856a048dcc",
        "2ad121317b384413483b7d2c85a1bfbc408c82b626e7e1c95ae4f8269a286e38",
    ),
    14: (
        "eaf05a7db3802d79ff1dc7960fddcdb7196555dbd478c7febde63624f9ce5ebc",
        "51bf1e4767d080f6bf2bba261b95e8f3f6765d00c31a42113ef079032a211c3d",
        "c4374092211dd984be514427cda4120619aa7cc583989f28d9c1082e758ac584",
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    require(path.is_file(), f"missing artifact: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def require_transcript_in_raw(raw_path, transcript_path):
    raw_lines = [
        line.rstrip()
        for line in raw_path.read_text().replace("\r", "\n").splitlines()
        if line.strip()
    ]
    transcript_lines = transcript_path.read_text().splitlines()
    matches = sum(
        raw_lines[index:index + len(transcript_lines)] == transcript_lines
        for index in range(len(raw_lines) - len(transcript_lines) + 1)
    )
    require(matches == 1,
            "raw checker output does not uniquely match transcript")


def verify(distance=14, artifact_prefix=None):
    require(distance in CASES, f"unsupported exact distance: {distance}")
    hashes = CASES[distance]
    here = Path(__file__).resolve().parent
    documentation = (here / "EXACT_LOCAL_REPAIR.md").read_text()
    require(all(documentation.count(value) == 1 for value in hashes),
            "exact-shell hash table drift")
    transcript = (here / "exact_verification_logs"
                  / f"r{distance}.drat-trim.log")
    require(transcript.read_text().splitlines().count("s VERIFIED") == 1,
            "exact-shell transcript is not uniquely VERIFIED")
    if artifact_prefix is not None:
        prefix = Path(artifact_prefix)
        actual = (
            digest(Path(f"{prefix}.cnf")),
            digest(Path(f"{prefix}.drat")),
            digest(Path(f"{prefix}.drat-trim.log")),
        )
        require(actual == hashes, "exact-shell artifact hash mismatch")
        require_transcript_in_raw(
            Path(f"{prefix}.drat-trim.log"), transcript)
    print(f"EXACT_SHELL_EVIDENCE=PASS distance={distance} "
          f"artifacts={'checked' if artifact_prefix else 'not-requested'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--distance", type=int, default=14)
    parser.add_argument("--artifact-prefix")
    args = parser.parse_args()
    verify(args.distance, args.artifact_prefix)


if __name__ == "__main__":
    main()
