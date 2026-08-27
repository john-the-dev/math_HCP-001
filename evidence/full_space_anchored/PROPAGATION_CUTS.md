# Propagation-cut encoding audit

The optional `--propagation-cuts` layer adds four consequences of the base
Ramsey constraints without changing the set of projected graph models:

- an edge has at most 13 common neighbors;
- a nonedge has at most 13 common nonneighbors;
- a triangle has at most 4 common neighbors;
- an independent triple has at most 4 common nonneighbors.

For an edge, its common neighborhood has neither a triangle nor an independent
5-set, so `R(3,5)=14` gives the first bound. Complementing gives the nonedge
bound. The common neighborhood of a triangle must be independent, while the
global formula forbids an independent 5-set; complementing gives the final
bound.

Each conjunction gets a one-way indicator. The implication from the
conjunction to the indicator, plus a guarded sequential at-most counter, is
exact after existentially projecting the indicators: false positives are never
required, so every graph satisfying the cut extends to an auxiliary assignment.
The exhaustive small-instance audit checks both guard polarities and a
three-literal guard:

```text
case=1 assignments=16 clauses=8 top=9
case=2 assignments=16 clauses=8 top=9
case=3 assignments=128 clauses=8 top=12
PASS assignments=160
```

Observed construction measurements on an Apple Silicon host with Python 3.12
and python-sat 1.9.dev15 follow. These are `d=20`, no fixed edge count, and the
reported clause count excludes the unchanged 1,701,336 global 5-set clauses.

| j | layer | variables | core clauses | build seconds |
|---:|:---|---:|---:|---:|
| 2 | none | 312,247 | 634,614 | 0.133 |
| 2 | pair | 985,549 | 1,936,446 | 0.816 |
| 2 | triple | 4,422,087 | 8,670,614 | 4.656 |
| 13 | none | 312,247 | 634,614 | 0.125 |
| 13 | pair | 985,549 | 1,936,446 | 0.850 |
| 13 | triple | 4,422,087 | 8,670,614 | 4.601 |

The pair layer adds 673,302 variables and 1,301,832 clauses. The triple layer
adds 4,109,840 variables and 8,036,000 clauses and peaked near 1.46 GB RSS just
to construct the Python clause list. The counts do not depend on `j`.

Use the pair layer first for solver A/B tests. Keep the triple layer off by
default unless conflict/propagation measurements justify its much larger memory
footprint. `all` is available for controlled experiments, but is not proposed
as the proof-production default.

```sh
python3 audit_propagation_encoding.py
python3 anchored_sat.py --degree 20 --a-internal-degree 2 \
  --propagation-cuts pair --solver cadical195 --json d20-j2-pair.json
```
