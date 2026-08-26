#!/usr/bin/env bash
# Exact commands for every run in the manifest. No brace expansion in argument
# position; each invocation takes a single --k. Deterministic: no RNG in any
# production search. The only seeded component is z_prune_audit2.py.
set -euo pipefail

# K4-K7: bounds-preservation differential, no memo (z_general.py has none)
for k in 4 5 6 7; do
  for b in off on; do
    echo "=== k=${k} bounds=${b}"
    python3 z_general.py --k "${k}" --bounds "${b}"
  done
done

# K8-K12: bounds on, memo on
for k in 8 9 10 11 12; do
  echo "=== k=${k} bounds=on memo=on"
  python3 z_general_memo.py --k "${k}" --bounds on --memo on
done

# Memo-preservation differential, within one program
for k in 5 8 9 10; do
  for m in off on; do
    echo "=== k=${k} bounds=on memo=${m}"
    python3 z_general_memo.py --k "${k}" --bounds on --memo "${m}"
  done
done

# Controls
python3 z_prune_audit2.py                              # seeded 20260826
python3 z4_control_replay.py z4_control_instances.jsonl
