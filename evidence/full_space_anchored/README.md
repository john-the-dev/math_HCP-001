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
- Ramsey-derived internal-degree bounds for every vertex of each block;
- Ramsey-derived common-set bounds for every pair inside each block;
- Ramsey-derived whole-`H` common-set bounds for every pair;
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

The same induced-subgraph conditions give per-vertex bounds. For `a in A`,
its neighbors in `A` avoid K3/I5 and its nonneighbors in `A` avoid K4/I4.
Using `R(3,5)=14` and `R(4,4)=18` gives
`d-18 <= deg_A(a) <= 13`. For `b in B`, its neighbors in `B` avoid K4/I4
and its nonneighbors in `B` avoid K5/I3, giving
`28-d <= deg_B(b) <= 17`. The exact closed ranges are:

| `d` | every `deg_A(a)` | every `deg_B(b)` |
| --- | --- | --- |
| 18 | 0..13 | 10..17 |
| 19 | 1..13 | 9..17 |
| 20 | 2..13 | 8..17 |

`--no-block-edge-bounds` disables only the redundant block-edge constraints
for diagnostic comparisons. It must not be used for the production proof ledger.
`--no-block-degree-bounds` likewise disables only the per-vertex block-degree
constraints for diagnostics; production formulas keep both families enabled.

Together with the global no-K5/no-I5 clauses, the induced block conditions
sharpen the generic pairwise Ramsey cuts. Three of the four bounds below use
those global clauses, so `core_clauses()` by itself is only a construction
component and cannot support a SAT or UNSAT claim.
For an adjacent pair in `A`, its common neighbors in `A` form an independent
set (otherwise there is a K4 in `A`), so there are at most four. For a
nonadjacent pair in `A`, three independent common nonneighbors would form an
I5 with the pair; the set also contains no K4, so `R(4,3)=9` bounds it by
eight. Dually, an adjacent pair in `B`
has at most eight common neighbors by `R(3,4)=9`, and a nonadjacent pair in
`B` has at most four common nonneighbors. The exact default-on implications
are:

| block | pair | bounded set | maximum |
| --- | --- | --- | ---: |
| `A` | edge | common neighbors in `A` | 4 |
| `A` | nonedge | common nonneighbors in `A` | 8 |
| `B` | edge | common neighbors in `B` | 8 |
| `B` | nonedge | common nonneighbors in `B` | 4 |

Each implication uses projected conjunction indicators and a guarded
sequential counter. `--no-block-pair-common-bounds` disables only these
redundant propagation cuts for diagnostics; it is not a production setting.

Every pair in `H` admits the global Ramsey bound from the task plan. For an
adjacent pair, its common neighbors contain no K3, since such a
triangle would complete a K5 with the pair, and contain no I5 by the global
clauses. Thus `R(3,5)=14` bounds the set by 13. Dually, for a nonadjacent
pair, its common nonneighbors contain no I3, since such a triple would
complete an I5, and contain no K5 by the global clauses; `R(5,3)=14` again
bounds the set by 13. The within-block cuts above remain useful because their
smaller bounds apply to the portions of these common sets inside A or B; they
do not replace the whole-`H` bounds.

The global implications use projected conjunction indicators and a guarded
k-cardinality totalizer. `--no-global-pair-common-bounds` disables
them for diagnostic comparisons. These bounds require the global K5/I5
clauses and cannot support a verdict when `core_clauses()` is used alone.

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

On the same Python 3.12 / `python-sat 1.9.dev15` development environment, the
new per-vertex constraints changed the already block-edge-bounded d20 cores as
follows. Times are medians of five construction runs:

| case | block degree bounds | core clauses | encoded variables | build seconds |
| --- | --- | ---: | ---: | ---: |
| d20-j2 | off | 720,934 | 355,465 | 0.325 |
| d20-j2 | on | 732,146 | 361,489 | 0.314 |
| d20-j13 | off | 720,934 | 355,465 | 0.297 |
| d20-j13 | on | 732,146 | 361,489 | 0.294 |

These measurements exclude global 5-set clauses and solving and make no SAT
or UNSAT claim. Build-time differences at this scale are timing noise.

On the same environment, the within-block pair common-set cuts changed the
already block-edge- and block-degree-bounded d20 cores as follows. Times are
medians of five construction runs:

| case | pair common-set cuts | core clauses | encoded variables | build seconds |
| --- | --- | ---: | ---: | ---: |
| d20-j2 | off | 732,146 | 361,489 | 0.312 |
| d20-j2 | on | 879,802 | 440,369 | 0.417 |
| d20-j13 | off | 732,146 | 361,489 | 0.322 |
| d20-j13 | on | 879,802 | 440,369 | 0.420 |

With the 1,701,336 global 5-set clauses included, each bounded d20 formula has
2,581,138 clauses. These are construction measurements, not solver benchmarks
or SAT/UNSAT claims.

`discovery_runs.jsonl` records bounded discovery attempts that ended without a
solver verdict. `INTERRUPTED_NO_VERDICT` means exactly that: it is throughput
evidence only and is never accepted by the completion-ledger verifier as an
UNSAT claim.

Every j-only manifest row records the recomputed `edge_min` and `edge_max`
even though `edges` is null. The manifest describes work to run; it does not
claim that any partition is UNSAT or that proof artifacts currently exist.

### Distinguished-B-vertex refinement

The separate `j-k` frontier further splits every `(d,j)` case by the minimum
internal degree `k` in `B`. After the distinguished A relabeling, all of `B`
is still a symmetry block. Choose a minimum-internal-degree vertex of `B`,
relabel it as vertex `d`, and relabel its `k` neighbors in `B` as
`d+1..d+k`. The formula fixes that neighborhood and requires
`deg_B(d) <= deg_B(b)` for every other `b in B`.

Only permutations within the distinguished vertex's B-neighbor and
B-nonneighbor blocks remain. The formula therefore removes the old global B
degree ordering and sorts full H-degrees separately inside those two residual
blocks. The existing A residual blocks remain unchanged. This gives every
`Sym(A) x Sym(B)` orbit a representative without imposing an ordering across
blocks that are no longer interchangeable.

The default per-vertex B bound gives `k >= 28-d`. If `m=42-d` and `U_B` is
the default upper bound on `|E(B)|`, minimum degree is at most average degree,
so `k <= floor(2 U_B/m)=13` for all three values of `d`. The exhaustive ranges
are therefore `10..13` for `d=18`, `9..13` for `d=19`, and `8..13` for
`d=20`. Combined with every admissible `j`, this produces 193 cases: 56, 65,
and 72 respectively.

```sh
python3 anchored_sat.py --write-manifest j_k_partition_manifest.json \
  --manifest-mode j-k
python3 verify_b_manifest.py j_k_partition_manifest.json
python3 anchored_sat.py --degree 20 --a-internal-degree 2 \
  --b-internal-degree 8 --solver cadical195 --json d20-j2-k8.json
```

`verify_b_manifest.py` recomputes the exact 193-case cover, bounds, IDs, and
artifact names. Its optional completion-ledger path reuses the same fail-closed
hash and exact `s VERIFIED` checks as the 39-case verifier. No manifest row is
itself an UNSAT claim.

Formula-construction measurements on the integration host (Python 3.12,
`python-sat 1.9.dev15`) were medians of three runs with the block-edge,
per-vertex block-degree, and pair common-set bounds all enabled:

| case | core clauses | total clauses | encoded variables | build seconds |
| --- | ---: | ---: | ---: | ---: |
| d20-j2-k8 | 890,223 | 2,591,559 | 445,569 | 0.513 |
| d20-j2-k13 | 890,223 | 2,591,559 | 445,569 | 0.521 |

These measurements include the global 5-set clauses only in the total-clause
column. They exclude solving and make no SAT or UNSAT claim.

### Distinguished-A total-degree refinement

The `j-t-k` frontier further fixes `t=deg_H(0)`, the full degree of the
already distinguished minimum-degree vertex of `A`. This is an exhaustive
partition, not an added structural assumption: every representative in a
`(d,j,k)` case has exactly one such `t`. The existing degree bounds and the
fixed `j` give

```text
max(d-1,j) <= t <= min(23,j+42-d).
```

For the admissible `j` ranges this simplifies to `17..23`, `18..23`, and
`19..23` for `d=18,19,20`. Splitting every `j-k` case by those values gives
1,142 cases: 392 for `d=18`, 390 for `d=19`, and 360 for `d=20`.

```sh
python3 anchored_sat.py --write-manifest j_t_k_partition_manifest.json \
  --manifest-mode j-t-k
python3 verify_a_total_manifest.py j_t_k_partition_manifest.json
python3 anchored_sat.py --degree 20 --a-internal-degree 2 \
  --a-total-degree 19 --b-internal-degree 8 --solver glucose4 \
  --cnf d20-j2-t19-k8.cnf --proof d20-j2-t19-k8.drat \
  --json d20-j2-t19-k8.json
```

`verify_a_total_manifest.py` independently recomputes the 1,142-case cover,
bounds, identifiers, and artifact names. It reuses the fail-closed completion
ledger verifier for proof claims. The manifest itself makes no SAT or UNSAT
claim.

Adding the whole-`H` pair cuts to `d20-j2-k8` changed the core from 890,223
clauses / 445,569 variables to 1,613,463 clauses / 757,251 variables on the
same integration host. The global 1,701,336 five-set clauses are not included
in those core counts. This is a formula-construction comparison, not a solver
benchmark or a SAT/UNSAT claim.

### Exact A-block edge partitions

`--a-edges` fixes `E(A)` while leaving the total edge count unfixed. It is
validated against the proven A-block ranges: `50..85` for `d=18`, `57..92`
for `d=19`, and `68..100` for `d=20`. The 39-case j-only manifest and the
default formula remain unchanged when this option is omitted.

The `a-edge-j` manifest exhausts `(d,j,E(A))` with unique case and artifact
names. Its 1,368 cases split as 504 for `d=18`, 468 for `d=19`, and 396 for
`d=20`. Every row records its exact `a_edges` value and the applicable
`a_edge_min` and `a_edge_max` bounds:

```sh
python3 anchored_sat.py --write-manifest a_edge_partition_manifest.json \
  --manifest-mode a-edge-j
python3 verify_manifest.py a_edge_partition_manifest.json
python3 anchored_sat.py --degree 20 --a-internal-degree 2 --a-edges 68 \
  --solver cadical195 --json d20-a68-j2.json
```

Formula-construction measurements on the development host (Python 3.12,
`python-sat 1.9.dev15`) were:

| case | core clauses | encoded variables | build seconds |
| --- | ---: | ---: | ---: |
| d20-a68-j2 | 730,802 | 360,785 | 0.309 |
| d20-a100-j2 | 733,618 | 362,193 | 0.336 |

These measurements do not include a solve and make no SAT or UNSAT claim.

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
