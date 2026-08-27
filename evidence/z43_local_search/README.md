# Z43 low-memory tabu search

This experimental search starts at the repository's exact `F=2` graph, where
`F` is the number of monochromatic five-vertex sets. Each move toggles an edge
of a current violation. It combines tabu tenure, weighted breakout when no
weighted-improving move exists, randomized WalkSAT moves, and kicked restarts
from the best graph seen.

The search stores all `C(43,5)=962,598` five-sets and their 9,625,980 edge-set
incidences. A move updates only the `C(41,3)=10,660` five-sets containing the
toggled edge. The expected working set is under 100 MiB.

Build and run:

```bash
c++ -O3 -DNDEBUG -std=c++20 z43_tabu.cpp -o z43_tabu
./z43_tabu --seed 1 --seconds 60 --output z43_solution.txt
```

Restart kicks default to a uniformly selected 8--24 edge flips. Use
`--kick-min` and `--kick-max` to explore a wider range, or set them equal for
a fixed, reproducible kick size. For example:

```bash
./z43_tabu --seed 1 --seconds 60 --kick-min 64 --kick-max 128 \
  --output z43_solution.txt
```

The accepted range is `0 <= kick-min <= kick-max <= 903`, the number of edges
of a 43-vertex graph. Omitting both options preserves the original 8--24
selection and random-number consumption.

The CLI regression test compiles with `-Wall -Wextra -Wpedantic`, compares
omitted defaults with explicit `--kick-min 8 --kick-max 24`, exercises a fixed
kick, and rejects invalid ranges:

```bash
python3 test_cli.py
```

The best graph is written at exit. Status 0 means it has zero conflicts; status
2 means the time limit expired without improving the published `F=2` boundary.
Any output can be audited by the independent direct enumerator:

```bash
python3 verify_solution.py z43_solution.txt
```

No mathematical conclusion follows from a search that times out, regardless
of the kick range used.
