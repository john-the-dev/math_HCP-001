# Exact local repair around the F=2 seed

This experiment exhaustively excludes a **fixed-label Hamming ball** around the
published 43-vertex `F=2` seed. It does not quotient by graph isomorphism, does
not exclude a ball around any relabeling other than the one explicitly encoded,
and says nothing about graphs outside that labeled ball. In particular, this is
not a global `R(5,5)` result.

`exact_local_repair.py` assigns one Boolean variable to each of the 903 labeled
edges. For every one of the 962,598 five-vertex sets it emits one clause
forbidding all ten edges and one forbidding all ten non-edges. A one-way
sequential counter then limits the number of edge values differing from the
seed. The implications in the counter force a prefix count whenever enough
flip literals are true; its last clauses prohibit count `radius + 1`.

The seed is reconstructed independently from the short cyclic/deletion
description in `z43_tabu.cpp`. Its text form has 454 edges and SHA-256
`b13c0207149ff618acef13c822a4841ef21d60782dd40b94317887ad2d28beec`,
matching every recorded tabu-search output.

## Reproduction

CaDiCaL 3.0.1 generated the DRAT proofs. Every proof was checked externally by
`drat-trim` commit `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`:

```sh
python3 "$(git rev-parse --show-toplevel)/evidence/z43_local_search/test_exact_local_repair.py"
for radius in 1 2 3 4; do
  ./run_exact_local_repair.sh "$radius" /tmp/z43-local \
    "$(command -v cadical)" /path/to/drat-trim ascii
done
for radius in 5 6 7 8 9 10; do
  ./run_exact_local_repair.sh "$radius" /tmp/z43-local \
    "$(command -v cadical)" /path/to/drat-trim binary
done
for radius in 11 12; do
  ./run_exact_local_repair.sh "$radius" /tmp/z43-local \
    "$(command -v cadical)" /path/to/drat-trim binary 3600
done
./run_exact_local_repair.sh 13 /tmp/z43-local \
  "$(command -v cadical)" /path/to/drat-trim binary 7200
python3 verify_exact_local_evidence.py
```

The runner treats only CaDiCaL status 20 followed by `drat-trim`'s exact
`s VERIFIED` output as an exclusion. A timeout or any other status is not a
verdict. If a later radius is SAT, decode its model with `exact_local_repair.py
decode` and audit the graph with the pre-existing independent
`verify_solution.py`; this run found no SAT candidate.

## Results

The bounded experiment now reaches radius 13. Radius 13 logically subsumes
radii 1--12: these are one nested exclusion checked at thirteen bounds, not
thirteen independent assurances. The result rests on the radius-13 proof
together with direct audit of the shared encoding; the smaller bounds are
reproducibility and scaling checkpoints only.
All solver times below are real seconds reported by CaDiCaL. Hashes bind both
the generated CNF and the exact proof instance checked in this run; large
transient artifacts were not committed. Radii 1--4 used ASCII DRAT and radii
5--13 used binary DRAT. CaDiCaL proof traces are not canonical: proof format,
solver version/options, and some execution details can change proof bytes while
leaving the deterministic CNF unchanged. Reproduction therefore requires
rechecking the newly generated proof rather than expecting its hash to equal a
previous run. The hashes below identify the proofs that produced the preserved
checker outputs, not every valid reproduction proof.
The runner above independently verifies each newly generated proof. The
optional `--artifact-prefix` mode is instead an authentication check for the
retained original artifacts and is expected to reject non-byte-identical fresh
proofs or checker logs, even when their proof checks succeed.

| radius | format | variables | clauses | solver s | CNF SHA-256 | proof SHA-256 |
|---:|---|---:|---:|---:|---|---|
| 1 | ASCII | 1,806 | 1,927,903 | 1.61 | `df22cc5d6c8bc49554e69cf42fa430a91a56b55881fa9a55bd8ae582f422717a` | `fd51d4d87debef5ce6947910cfbc9285326ff23256bce6e64f94f28e89d1542d` |
| 2 | ASCII | 2,709 | 1,929,705 | 2.49 | `7080b02113c546700ab60caacfa485d1703ad0ea5d7d7fd16cf6d2b044f87104` | `149ff4cbbdf8815b4ba5118559c8fad0511996208fb6ec1f4f7be472c32993a8` |
| 3 | ASCII | 3,612 | 1,931,505 | 6.00 | `203b5ec62f400f4386eacecbfdd9ba36ca32d030ec79124652b9095da0b93390` | `e33ec9fc2c6cc82d8b99b573c0dd706dbdafc08937dceb47cd697ce086422e55` |
| 4 | ASCII | 4,515 | 1,933,303 | 11.98 | `126cac8aadfd5687a731e783e07c017fe278e574a39b39287ba0b45a3305f228` | `3465c7865d4e83b694ce6e1d819a0c3a67e7e432439d88f627b09b0c2ee17413` |
| 5 | binary | 5,418 | 1,935,099 | 22.43 | `d569f0663f0ed3ad4ceb1d38618f0c9546eb86c0bbfaa56fa28ec403ec982d5a` | `045a78405dfbab1a1a21e1ab0b34200a434bd50e043769fdf97a736f77e6244c` |
| 6 | binary | 6,321 | 1,936,893 | 48.53 | `606451f58561c5ae4d55330539e2e6c3cf1eeb7f35a556445d3f754bdbd6a540` | `3d8f975658a82d633ac4c78de714c22ad3e05d9dc91317e53a3022549a11c539` |
| 7 | binary | 7,224 | 1,938,685 | 81.62 | `e9022858ae3b3eeb39eb76888fa5980b845ac284ddd363f20d6744852b62f784` | `b80373400fdd8821be31e9994c914f1ac3752fa162b97d9f8c2db4138e135eaf` |
| 8 | binary | 8,127 | 1,940,475 | 137.16 | `9fac70649980dd0f757a879bfadd6fa5f68dff0e740d3f8d5e0c5cb2083a3c73` | `e43a0282f1d34f74e2486100d41adc9e3e6edce5322de9b6691fdf796552f12d` |
| 9 | binary | 9,030 | 1,942,263 | 258.91 | `ffc36a6a4ddec53a415d38a77a9f7bd4d231d117fe1f6d86994648369f2c6f62` | `ee0202de75e58025f304f52e62e085e9eca2a6713b4ce8bfabdb95931d05a650` |
| 10 | binary | 9,933 | 1,944,049 | 564.31 | `7eac77809d7b935f944fb1b702070cdc7ee6039a5f55674f955f275c2c5c3f12` | `0d49d765d26559f30520e76f8145e1f13413a2a5518ab3ada000152392ad8233` |
| 11 | binary | 10,836 | 1,945,833 | 983.18 | `f09d495e146114216ee8a5c4b8c9c2bdf87aeaeb56c1eefa8a0ba640a96573a0` | `6548f728b94f971768435a4a680af3cda3d79f6e7d4ffaa93f05dad242a3508f` |
| 12 | binary | 11,739 | 1,947,615 | 1,469.90 | `87d6117bf54b2941e394383aab84a2debd62325209f8aab50409acf06ded8a97` | `d499241517602d296b760543477853f1329eb23cd064eff000a0f1beb888a7f9` |
| 13 | binary | 12,642 | 1,949,395 | 1,994.31 | `57d5d8a4d8b6e6e43c7f660a9ad565263565c3bc27f59cc6ed9f03e9c7e315db` | `9b9ca606086d89cc642c4057bfb8fe141e89f2163cc6f950eb501eff71c1ba72` |

The checker exited 0 at every radius. Raw output hashes bind the exact terminal
streams; readable transcripts under `verification_logs/` remove terminal
carriage control, blank lines, trailing progress padding, and the
`/usr/bin/time` resource footer without changing the substantive checker
lines. Each transcript reports `s VERIFIED`.

| radius | checker exit | raw checker-output SHA-256 |
|---:|---:|---|
| 1 | 0 | `f1287919404ea4b941bb9e10ce23f779993f760e2466b38cf9e12a5ba5a25fdb` |
| 2 | 0 | `d179f390107cc3481f171602d3b2d6f0f682efbbe46b402ae3140c48e7575741` |
| 3 | 0 | `2d59985d1661d48037a496fb796d6e81eac8d294659b6ba6c7348249c84b3daa` |
| 4 | 0 | `fd307160fbaf224c46838285658faf5b77534e093486bb40eb012d905abea952` |
| 5 | 0 | `24cf772f523e21959ece1e1639f024aaa18d9654b6ab5d48b9e6db792d7c1c46` |
| 6 | 0 | `b9e3ec2f299ace5a70d4c948a415b7308d66d90b00204304df174010eef97779` |
| 7 | 0 | `7004311fb1a204efda45eeedefbb7b158cea0122b8b30e3049604c72f162069d` |
| 8 | 0 | `a9b933d18485596e0c93fafbe759061c712e2cb71eb048ecacaf5a1783ea7345` |
| 9 | 0 | `861456b7a876d2c436ea14993aa833c65b6d5a97112d44d224f08bacae788bb8` |
| 10 | 0 | `4b25a08a03013fe413e7e977feeca579b2d9e7b2243e85f89bd57d8592f8026d` |
| 11 | 0 | `c8a85e416e1a335dae4a3097a3580c5f84ab1c42fe3cda1b15aaa54685a2a0a9` |
| 12 | 0 | `9f280f44167b99a00d47b946de183ba7f6bd4e78d0bd7788ee0a07e3332898e8` |
| 13 | 0 | `f6f87e3e7da15e8e9d565d1b76d9112a8010d15e296ff7e0c2e2308fc9fac26e` |

The exact conclusion is: no `(5,5)`-avoiding graph on labeled vertices
`0..42` differs in at most thirteen edge positions from this exact seed.

## Radius-11 through radius-13 run history

A first radius-11 attempt generated the deterministic 10,836-variable,
1,945,833-clause CNF recorded in the table above.
CaDiCaL reached its 900-second real-time cap after 2,556,191 conflicts and
returned UNKNOWN with status 0. The original runner did not invoke the checker.
A subsequent audit passed the 849,200,443-byte partial trace to the pinned
`drat-trim`; it exited 1 with `ERROR: no conflict` and `s NOT VERIFIED`. The
partial trace is not evidence of UNSAT.

The runner maps this solver status to a nonzero wrapper exit and never invokes
`drat-trim`, so automation cannot confuse the timeout with the verified path.
A subsequent run on the byte-identical CNF used a 3,600-second cap and returned
UNSAT after 983.18 real seconds. The pinned checker verified that run's
1,011,963,256-byte proof in 466.393 seconds; only this later proof supports the
radius-11 row and conclusion above.

The radius-12 continuation generated the deterministic 11,739-variable,
1,947,615-clause CNF in the table. CaDiCaL returned UNSAT after 1,469.90 real
seconds and wrote a 1,631,318,478-byte binary proof. The pinned checker exited
0 with exact `s VERIFIED` after 525.679 seconds; its backward check used
395,601,802 resolution steps and zero RAT lemmas. This checked radius-12 proof,
rather than either exact-shell timeout attempt, supports the current
fixed-label conclusion.

The direct radius-13 continuation generated a deterministic 12,642-variable,
1,949,395-clause CNF. CaDiCaL returned UNSAT after 1,994.31 real seconds and
wrote a 2,712,997,050-byte binary proof. The pinned checker exited 0 with exact
`s VERIFIED` after 764.368 seconds; its backward check used 671,936,876
resolution steps and zero RAT lemmas. This checked direct proof establishes
the fixed-label radius-13 conclusion without relying on an exact-shell result.

## Exact-shell continuation

The verified radius-12 certificate permits a disjoint decomposition of the
next ball. If the Ramsey clauses are `F` and `D` is Hamming distance from the
fixed seed, then

```text
{D <= 13} = {D <= 12} disjoint-union {D = 13}.
```

Consequently, a separately checked UNSAT proof for `F and D=13`, together
with the existing checked proof for `F and D<=12`, would certify the same
fixed-label radius-13 ball. An exact-shell proof alone would not do so, and
the two DRAT traces must not be concatenated because they have different
initial CNFs and auxiliary meanings.

`exact_local_repair.py build --distance-mode exact` makes the existing
one-way sequential-counter states bidirectional and asserts the terminal
state. Merely asserting that state without the reverse clauses would be
unsound because the original auxiliary variables may otherwise float true.
For distance 12, the exact-shell encoding retains the 11,739 variables of the
at-most formula and adds 20,638 clauses, for 1,968,253 total. The original
at-most clause stream remains the exact prefix, and the default mode remains
byte-compatible with the radius 1--12 generator.

```sh
./run_exact_local_repair.sh 13 /tmp/z43-shell \
  "$(command -v cadical)" /path/to/drat-trim binary 3600 exact
```

Exact-mode artifacts use a distinct `z43-local-rN-exact` stem. A SAT output
must be decoded with the matching `--expected-distance`, then checked with the
independent graph verifier. A 900-second exact-distance-11 attempt and a
separate 900-second exact-distance-12 attempt both returned UNKNOWN with
status 0; neither partial trace was checked or used as evidence. The direct
at-most radius-12 proof above, rather than either shell attempt, establishes
the current fixed-label exclusion.
