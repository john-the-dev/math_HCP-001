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
- `deg_H(a) in [d-1,23]` and `deg_H(b) in [d,24]`;
- at most `451-d` edges;
- nondecreasing full `H`-degrees independently inside `A` and `B`.

The last constraint is sound under `Sym(A) x Sym(B)`: the shared edge of two
compared vertices cancels, and every orbit has a degree-sorted representative.
The conditions are sufficient because a forbidden 5-set either lies in `H` or
contains `v`, in which case it yields a forbidden K4 in `A` or I4 in `B`.

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

Each edge-count partition can be divided further with
`--a-internal-degree j`. Choose a minimum-degree vertex of `A`, relabel it as
vertex 0, and relabel its `j` neighbors in `A` as vertices `1..j`. The formula
fixes those incident edges, requires `deg_H(0) <= deg_H(a)` for every other
`a in A`, and sorts degrees only within the three residual symmetry blocks:
the fixed neighbors, fixed nonneighbors, and `B`. This is sound because every
graph has a minimum-degree vertex in `A`, and the relabeling uses only
`Sym(A) x Sym(B)`.

The exact Ramsey values `R(3,5)=14` and `R(4,4)=18` restrict `j`: the
neighbors of vertex 0 inside `A` avoid K3/I5, while its nonneighbors inside
`A` avoid K4/I4. Thus `max(0,d-18) <= j <= 13`.

Generate the exhaustive `(d, edge_count, j)` manifest (1,733 partitions):

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
