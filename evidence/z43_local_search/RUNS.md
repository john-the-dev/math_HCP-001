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

## Two 30-minute runs

Two longer runs used different tabu/noise/restart settings:

```sh
/usr/bin/time -l /tmp/z43_tabu --seed 101 --seconds 1800 --noise 12 \
  --tenure 7 --restart-after 50000 --output /tmp/z43-seed101-1800.txt
/usr/bin/time -l /tmp/z43_tabu --seed 211 --seconds 1800 --noise 35 \
  --tenure 13 --restart-after 30000 --output /tmp/z43-seed211-1800.txt
```

Seed 101 completed 1,306,665 moves and 26 restarts; seed 211 completed
1,224,936 moves and 40 restarts. Both ran for 1,800 seconds, used about 125 MB
peak RSS, and found no state below `F=2`. The independent verifier checked all
962,598 five-sets in each output and reported `K5=0`, `I5=2`, `F=2`.
Both outputs equal the starting graph and have SHA-256
`b13c0207149ff618acef13c822a4841ef21d60782dd40b94317887ad2d28beec`.

These longer timeouts are still only negative search observations, not an
exclusion theorem.

## Two four-hour large-kick runs

Two runs tested restart perturbations much larger than the default 8--24
edge range. They ran concurrently on the same host:

```sh
/usr/bin/time -l /tmp/z43_tabu_large --seed 503 --seconds 14400 \
  --noise 25 --tenure 9 --restart-after 20000 \
  --kick-min 64 --kick-max 128 --output /tmp/z43-large-seed503-14400.txt
/usr/bin/time -l /tmp/z43_tabu_large --seed 607 --seconds 14400 \
  --noise 40 --tenure 5 --restart-after 15000 \
  --kick-min 128 --kick-max 256 --output /tmp/z43-large-seed607-14400.txt
```

Seed 503 completed 3,305,498 moves and 165 restarts; seed 607 completed
787,879 moves and 52 restarts. Each ran for 14,400 seconds and used at most
124,960,768 bytes RSS. Neither improved `F=2`; both returned exit 2. The
independent verifier checked all 962,598 five-sets in each output and reported
`K5=0`, `I5=2`, `F=2`, also with exit 2. Both output files equal the starting
graph and have SHA-256
`b13c0207149ff618acef13c822a4841ef21d60782dd40b94317887ad2d28beec`.
The final search summaries and `/usr/bin/time -l` resource reports are retained
under `large_kick_logs/`.

These runs test two bounded heuristic trajectories only. They do not exclude
another trajectory or any graph outside the explored states.
