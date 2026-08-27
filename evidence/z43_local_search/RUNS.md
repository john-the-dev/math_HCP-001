# Initial run record

Environment: Apple clang 21.0.0, arm64; Python 3.12.4. The two timed
searches below ran concurrently, so their wall rates include mutual CPU
contention.

Build:

```bash
c++ -O3 -DNDEBUG -std=c++20 -Wall -Wextra -pedantic \
  evidence/z43_local_search/z43_tabu.cpp -o /tmp/z43_tabu
```

Search commands:

```bash
/usr/bin/time -l /tmp/z43_tabu --seed 41 --seconds 60 --noise 8 \
  --tenure 5 --restart-after 15000 --output /tmp/z43-seed41.txt
/usr/bin/time -l /tmp/z43_tabu --seed 43 --seconds 60 --noise 25 \
  --tenure 9 --restart-after 15000 --output /tmp/z43-seed43.txt
```

Seed 41 completed 57,237 moves and three restarts in 60.0012 seconds;
seed 43 completed 54,847 moves and three restarts in 60.0006 seconds. Both
used 124,895,232 bytes peak RSS. Neither improved `F=2`, so both exited 2.

Independent audit command, run once on each output:

```bash
python3 evidence/z43_local_search/verify_solution.py /tmp/z43-seed41.txt
```

Both output files were identical, with SHA-256
`b13c0207149ff618acef13c822a4841ef21d60782dd40b94317887ad2d28beec`.
Direct enumeration reported 454 edges, 962,598 five-sets checked, zero K5s,
two I5s, and `F=2`; the verifier exited 2 as expected for a non-solution.

These are search metrics, not evidence that an `F=0` graph does not exist.
