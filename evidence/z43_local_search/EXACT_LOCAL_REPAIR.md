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
./run_exact_local_repair.sh 8 /tmp/z43-local \
  "$(command -v cadical)" /path/to/drat-trim binary
python3 verify_exact_local_evidence.py --artifact-prefix /tmp/z43-local
```

The runner treats only CaDiCaL status 20 followed by `drat-trim`'s exact
`s VERIFIED` output as an exclusion. A timeout or any other status is not a
verdict. If a later radius is SAT, decode its model with `exact_local_repair.py
decode` and audit the graph with the pre-existing independent
`verify_solution.py`; this run found no SAT candidate.

## Results

The bounded experiment stopped after radius 8, well inside its 30-minute cap.
All solver times below are real seconds reported by CaDiCaL. Hashes bind both
the generated CNF and the exact proof instance checked in this run; large
transient artifacts were not committed. Radii 1--4 used ASCII DRAT and radii
5--8 used binary DRAT. CaDiCaL proof traces are not canonical: proof format,
solver version/options, and some execution details can change proof bytes while
leaving the deterministic CNF unchanged. Reproduction therefore requires
rechecking the newly generated proof rather than expecting its hash to equal a
previous run. The hashes below identify the proofs that produced the preserved
checker outputs, not every valid reproduction proof.

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

The checker exited 0 at every radius. Raw output hashes bind the exact terminal
streams; readable transcripts under `verification_logs/` remove terminal
carriage control, blank lines, and trailing progress padding without changing
the substantive lines. Each transcript reports `s VERIFIED`.

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

The exact conclusion is: no `(5,5)`-avoiding graph on labeled vertices
`0..42` differs in at most eight edge positions from this exact seed.
