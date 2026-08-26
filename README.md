# HCP-001 exact verification

This repository contains reproducible finite verification for the compact
43-vertex HCP-001 candidate and its cyclic-template search boundary.

## Lean verification

The Lean project pins Lean 4.33.1 and uses only `Std`.

Full verification additionally requires Python 3.10 or newer (for
`int.bit_count`) and Node.js.

```bash
lake build
lake exe hcp001_verify
# Full Lean + Python + Node verification:
bash scripts/verify_all.sh
```

`Hcp001/Basic.lean` reconstructs the graph from its cyclic difference set and
deleted cycle edges. Lean exhaustively checks all 962,598 five-vertex subsets
and records theorem statements for:

- 454 edges;
- degree distribution `20×14, 21×10, 22×19`;
- no K5;
- exactly two independent 5-sets.

These finite theorems currently use `native_decide`; their `#print axioms`
output is intentionally preserved during `lake build` so the trust boundary is
visible.

The full verification script also replays `Hcp001.Basic.olean` through
`leanchecker`.

The exact local build record is captured in `LEAN_VERIFIED_OUTPUT.txt`.

## Search-boundary evidence

The `evidence/` directory contains the independently checked Python and Node
verifiers, captured outputs, exact SHA-256 manifest, and scope notes for Z0
through Z3 and the complete Hamming-radius-at-most-two audit.

No HCP-001 solution is claimed. The strongest result here is a template
boundary: arbitrary cycle-edge deletions plus at most three non-cycle chord
toggles cannot eliminate every monochromatic 5-set.
