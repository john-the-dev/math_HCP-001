# 42-core extension certificates

This packet independently checks the two 42-vertex cores obtained by deleting
vertex 6 or 7 from the verified 43-vertex near-candidate at commit
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
```

Regenerate deterministically with:

```bash
python3 extension_certificate.py emit extension-unsat-cert.json
```

SHA-256:

```text
c40e53b84943c9b2c174bc8acdecf5c2678fc3f23d2cff114ac8f940e7a8d17e  extension_certificate.py
217d3283981b87a151384da69b840334476946229dbdb502691f287b38eef911  extension-unsat-cert.json
```

Scope: this excludes arbitrary one-vertex extensions of these two core types.
It does not exclude other 42-vertex cores or solve HCP-001.
