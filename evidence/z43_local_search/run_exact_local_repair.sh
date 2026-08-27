#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 6 ]]; then
  echo "usage: $0 RADIUS OUTPUT_DIR CADICAL DRAT_TRIM [binary|ascii] [timeout-seconds]" >&2
  exit 2
fi

radius="$1"
output_dir="$2"
cadical="$3"
drat_trim="$4"
proof_format="${5:-binary}"
timeout_seconds="${6:-900}"
if [[ "$proof_format" == binary ]]; then
  proof_option="--binary=true"
elif [[ "$proof_format" == ascii ]]; then
  proof_option="--binary=false"
else
  echo "proof format must be binary or ascii" >&2
  exit 2
fi
if [[ ! "$timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then
  echo "timeout must be a positive integer" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$output_dir"
prefix="$output_dir/z43-local-r$radius"

python3 "$script_dir/exact_local_repair.py" build \
  --radius "$radius" --output "$prefix.cnf" --metadata "$prefix.json"

set +e
"$cadical" --seed=0 --checkproof=3 "$proof_option" -t "$timeout_seconds" \
  "$prefix.cnf" "$prefix.drat" \
  > "$prefix.cadical.log" 2>&1
solver_status=$?
set -e
if [[ $solver_status -ne 20 ]]; then
  echo "CaDiCaL did not prove UNSAT (exit $solver_status)" >&2
  if [[ $solver_status -eq 0 ]]; then
    exit 1
  fi
  exit "$solver_status"
fi

"$drat_trim" "$prefix.cnf" "$prefix.drat" > "$prefix.drat-trim.log" 2>&1
tr '\r' '\n' < "$prefix.drat-trim.log" | grep -qx 's VERIFIED'
shasum -a 256 "$prefix.cnf" "$prefix.drat"
