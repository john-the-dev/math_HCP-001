#!/usr/bin/env bash
# Memo-preservation differential, within ONE program (z_general_memo.py), so
# the only variable is --memo. Bounds held at "on" throughout.
set -euo pipefail
for k in 5 8 9 10; do
  for m in off on; do
    echo "=== k=${k} bounds=on memo=${m}"
    python3 z_general_memo.py --k "${k}" --bounds on --memo "${m}"
  done
done
