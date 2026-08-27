# 42-core extension certificates

This packet independently checks all four 42-vertex cores obtained by deleting
vertex 6, 7, 11, or 12 from the verified 43-vertex near-candidate at commit
`5c1b2c2898271cd7fdc882fb6dce0518debdcc40`.

For a new vertex with neighborhood variables `x_i`, every K4 in the core
requires at least one `x_i = 0`, while every independent 4-set requires at
least one `x_i = 1`. These monotone CNFs are necessary and sufficient for an
extension that creates neither a K5 nor an independent 5-set.

The JSON contains complete DPLL proof trees. The self-contained checker
reconstructs the candidate and every K4/I4 clause, then validates that each:

- unit step cites a clause with exactly the asserted literal unassigned;
- branch covers both Boolean values of an unassigned variable;
- leaf cites a clause falsified by the branch assignment.

Run:

```bash
python3 extension_certificate.py check extension-unsat-cert.json
```

Expected summary:

```text
PASS remove=6 clauses=2318 proof_nodes=214
PASS remove=7 clauses=2331 proof_nodes=173
PASS remove=11 clauses=2331 proof_nodes=161
PASS remove=12 clauses=2318 proof_nodes=196
```

Regenerate deterministically with:

```bash
python3 extension_certificate.py emit extension-unsat-cert.json
```

SHA-256:

```text
fc4b89e3d63bd99090666595919c628e8472aa9502b87cac07e528792548f30d  extension_certificate.py
95a4a41738e5d5a54889fcd166277e4335e95da04d0185373c71e8aca2f3a42d  extension-unsat-cert.json
```

Scope: this excludes arbitrary one-vertex extensions of these four cores.
It does not exclude other 42-vertex cores or solve HCP-001.
