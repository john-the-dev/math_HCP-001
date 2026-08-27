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
