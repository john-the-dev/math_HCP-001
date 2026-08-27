#!/usr/bin/env python3
"""Authenticate the checked exact-distance-13 local-repair certificate."""

import argparse
import hashlib
from pathlib import Path


HASHES = (
    "fa1f2fc2c3bec954a2e1800356819d21347908497b4b0f1cf2688bb270c22a50",
    "8b53cdbdcaabec794494d48447345674f76bc3a60125db1aa8f493856a048dcc",
    "2ad121317b384413483b7d2c85a1bfbc408c82b626e7e1c95ae4f8269a286e38",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    require(path.is_file(), f"missing artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(artifact_prefix=None):
    here = Path(__file__).resolve().parent
    documentation = (here / "EXACT_LOCAL_REPAIR.md").read_text()
    require(all(documentation.count(value) == 1 for value in HASHES),
            "exact-shell hash table drift")
    transcript = here / "exact_verification_logs" / "r13.drat-trim.log"
    require(transcript.read_text().splitlines().count("s VERIFIED") == 1,
            "exact-shell transcript is not uniquely VERIFIED")
    if artifact_prefix is not None:
        prefix = Path(artifact_prefix)
        actual = (
            digest(Path(f"{prefix}.cnf")),
            digest(Path(f"{prefix}.drat")),
            digest(Path(f"{prefix}.drat-trim.log")),
        )
        require(actual == HASHES, "exact-shell artifact hash mismatch")
    print("EXACT_SHELL_EVIDENCE=PASS distance=13 "
          f"artifacts={'checked' if artifact_prefix else 'not-requested'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-prefix")
    args = parser.parse_args()
    verify(args.artifact_prefix)


if __name__ == "__main__":
    main()
