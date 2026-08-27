#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RADIUS OUTPUT_DIR CADICAL DRAT_TRIM" >&2
  exit 2
fi

radius="$1"
output_dir="$2"
cadical="$3"
drat_trim="$4"
script_dir="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$output_dir"
prefix="$output_dir/z43-local-r$radius"

python3 "$script_dir/exact_local_repair.py" build \
  --radius "$radius" --output "$prefix.cnf" --metadata "$prefix.json"

set +e
"$cadical" --seed=0 --checkproof=3 -t 900 "$prefix.cnf" "$prefix.drat" \
  > "$prefix.cadical.log" 2>&1
solver_status=$?
set -e
if [[ $solver_status -ne 20 ]]; then
  echo "CaDiCaL did not prove UNSAT (exit $solver_status)" >&2
  exit "$solver_status"
fi

"$drat_trim" "$prefix.cnf" "$prefix.drat" > "$prefix.drat-trim.log" 2>&1
tr '\r' '\n' < "$prefix.drat-trim.log" | grep -qx 's VERIFIED'
shasum -a 256 "$prefix.cnf" "$prefix.drat"
