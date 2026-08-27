# Checkpointed dual K14 replay

This directory replays the previously published tuple/frozenset search one
cyclic-distance anchor at a time and compares its survivor sets with the
separately written integer-mask implementation in `../k14_independent/`.
State counts and runtimes are recorded but are not expected to agree because
the implementations use different internal state representations.

Python 3.10 or newer is required. Run or resume all 20 anchors with:

```sh
python3 replay_published.py --output published-checkpoints.jsonl \
  --distances 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21
```

Each completed anchor is appended, flushed, and fsynced before the next starts.
On resume, the runner rejects schema or source-identity drift and skips only
validated completed anchors. Survivor hashes are computed from canonical edge
lists, not implementation-specific state numbers.

The final verifier intentionally fails on a partial ledger:

```sh
python3 verify_dual.py
```

`DUAL_REPLAY=PASS` means all distances `2..21` occur exactly once and both
implementations agree on their separate under-target and target-size survivor
counts. This is a cyclic-template result only; it does not exclude arbitrary
43-vertex Ramsey graphs.

The completed replay explored 18,644,084 published-implementation states in
4,926.29 seconds. The independent integer-mask run explored 18,101,717 states
in 4,713.16 seconds. Both found zero under-target and zero target-size
survivors for every anchor; internal state totals are not expected to match.

```text
distances=2..21 anchors=20
under_target_agreement=20/20 all_zero=True
target_size_agreement=20/20 all_zero=True
DUAL_REPLAY=PASS
```
