# Full-space anchored SAT model

This is an exact search over all 43-vertex graphs with neither a K5 nor an
independent 5-set. It does not assume the cyclic template.

Complement a hypothetical graph so it has at most 451 edges and choose a
minimum-degree vertex `v`. `R(4,5)=25` bounds every degree to `18..24`, while
the average degree is below 21, so `d=deg(v)` is one of `18,19,20`. Relabel
`A=N(v)` and set `H=G-v`.

For each `d`, the CNF searches all 861 edges of `H` and enforces:

- no K5 or independent 5-set in `H`;
- no K4 in `A` and no independent 4-set in `B`;
- the exact known edge ranges for the induced `R(4,5,n)` blocks;
- `deg_H(a) in [d-1,23]` and `deg_H(b) in [d,24]`;
- at most `451-d` edges;
- nondecreasing full `H`-degrees independently inside `A` and `B`.

The last constraint is sound under `Sym(A) x Sym(B)`: the shared edge of two
compared vertices cancels, and every orbit has a degree-sorted representative.
The conditions are sufficient because a forbidden 5-set either lies in `H` or
contains `v`, in which case it yields a forbidden K4 in `A` or I4 in `B`.

Appendix Table 1 of Angeltveit and McKay,
[R(5,5) <= 46](https://arxiv.org/abs/2409.15709v2), gives the edge ranges
for `R(4,5,n)` graphs. Thus `G[A]` has respectively `50..85`, `57..92`,
or `68..100` edges for `d=18,19,20`. The complement of `G[B]` is an
`R(4,5,42-d)` graph. Subtracting its table range from `C(42-d,2)` gives the
following default-on bounds for `G[B]`:

| `d` | `|E(G[A])|` | `|E(G[B])|` |
| --- | --- | --- |
| 18 | 50..85 | 144..160 |
| 19 | 57..92 | 131..152 |
| 20 | 68..100 | 117..143 |

`--no-block-edge-bounds` disables only these redundant constraints for
diagnostic comparisons. It must not be used for the production proof ledger.

Python 3.10+ and `python-sat` are required. The development environment used
`python-sat 1.9.dev15`.

List the exact edge-count partitions:

```sh
python3 anchored_sat.py --list-partitions
```

Run a discovery partition:

```sh
python3 anchored_sat.py --degree 20 --edges 410 --solver cadical195 \
  --json d20-e410.json
```

For a proof-producing rerun, preserve the exact DIMACS formula and proof:

```sh
python3 anchored_sat.py --degree 20 --edges 410 --solver glucose4 \
  --cnf d20-e410.cnf --proof d20-e410.drat --json d20-e410.json
drat-trim d20-e410.cnf d20-e410.drat
```

An UNSAT solver verdict is discovery-only until the proof checker accepts the
corresponding formula/proof pair. Exact edge partitions cover `410..431` for
`d=20`, `390..432` for `d=19`, and `369..433` for `d=18`; these lower bounds
follow by summing the per-vertex degree lower bounds.

## Distinguished-A-vertex refinement

Choose a minimum-degree vertex of `A`, relabel it as
vertex 0, and relabel its `j` neighbors in `A` as vertices `1..j`. The formula
fixes those incident edges, requires `deg_H(0) <= deg_H(a)` for every other
`a in A`, and sorts degrees only within the three residual symmetry blocks:
the fixed neighbors, fixed nonneighbors, and `B`. This is sound because every
graph has a minimum-degree vertex in `A`, and the relabeling uses only
`Sym(A) x Sym(B)`.

The exact Ramsey values `R(3,5)=14` and `R(4,4)=18` restrict `j`: the
neighbors of vertex 0 inside `A` avoid K3/I5, while its nonneighbors inside
`A` avoid K4/I4. Thus `max(0,d-18) <= j <= 13`.

The practical proof frontier partitions only by `(d,j)`. Omitting `--edges`
does not omit the edge bounds: the per-vertex degree constraints imply
`|E(H)| >= ceil(41d/2)`, and every formula explicitly enforces
`|E(H)| <= 451-d`. Consequently these 39 formulas cover every admissible edge
count and remain exhaustive:

```sh
python3 anchored_sat.py --write-manifest j_partition_manifest.json \
  --manifest-mode j-only
python3 anchored_sat.py --degree 20 --a-internal-degree 2 \
  --solver cadical195 --json d20-j2.json
python3 verify_manifest.py j_partition_manifest.json
```

On the development host, constructing the d20 j-frontier core before adding
the global 5-set clauses produced these measurements (Python 3.12,
`python-sat 1.9.dev15`):

| case | block bounds | core clauses | encoded variables | build seconds |
| --- | --- | ---: | ---: | ---: |
| d20-j2 | off | 634,614 | 312,247 | 0.149 |
| d20-j2 | on | 720,934 | 355,465 | 0.222 |
| d20-j13 | off | 634,614 | 312,247 | 0.212 |
| d20-j13 | on | 720,934 | 355,465 | 0.276 |

These are formula-construction measurements, not solver benchmarks or UNSAT
claims.

`discovery_runs.jsonl` records bounded discovery attempts that ended without a
solver verdict. `INTERRUPTED_NO_VERDICT` means exactly that: it is throughput
evidence only and is never accepted by the completion-ledger verifier as an
UNSAT claim.

Every j-only manifest row records the recomputed `edge_min` and `edge_max`
even though `edges` is null. The manifest describes work to run; it does not
claim that any partition is UNSAT or that proof artifacts currently exist.

Certified results belong in a separate completion ledger. Each UNSAT claim
must name relative CNF, proof, and checker-output paths and give the SHA-256
of each artifact. The verifier hashes all three files and requires the checker
output to contain an exact `s VERIFIED` line. Use `--require-complete` only
when all 39 cases have independently checked proof artifacts:

```sh
python3 verify_manifest.py j_partition_manifest.json \
  --ledger completion_ledger.json
python3 verify_manifest.py j_partition_manifest.json \
  --ledger completion_ledger.json --require-complete
```

Ledger shape:

```json
{"schema": 1, "claims": [{"id": "d18-j0", "status": "UNSAT",
  "artifacts": {
    "cnf": {"path": "d18-j0.cnf", "sha256": "<64 lowercase hex>"},
    "proof": {"path": "d18-j0.drat", "sha256": "<64 lowercase hex>"},
    "checker": {"path": "d18-j0.check.txt", "sha256": "<64 lowercase hex>"}
  }}]}
```

For smaller proof jobs, `(d,edge_count,j)` further divides the same space into
1,733 formulas. Generate that exhaustive manifest with:

```sh
python3 anchored_sat.py --write-manifest partition_manifest.json
```

Run and independently certify a refined partition:

```sh
python3 anchored_sat.py --degree 20 --edges 410 --a-internal-degree 7 \
  --solver glucose4 --cnf d20-e410-j7.cnf --proof d20-e410-j7.drat \
  --json d20-e410-j7.json
drat-trim d20-e410-j7.cnf d20-e410-j7.drat
```
