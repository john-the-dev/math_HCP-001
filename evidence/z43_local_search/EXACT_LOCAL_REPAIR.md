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
python3 -m unittest -v test_exact_local_repair.py
./run_exact_local_repair.sh 8 /tmp/z43-local \
  "$(command -v cadical)" /path/to/drat-trim
```

The runner treats only CaDiCaL status 20 followed by `drat-trim`'s exact
`s VERIFIED` output as an exclusion. A timeout or any other status is not a
verdict. If a later radius is SAT, decode its model with `exact_local_repair.py
decode` and audit the graph with the pre-existing independent
`verify_solution.py`; this run found no SAT candidate.

## Results

The bounded experiment stopped after radius 8, well inside its 30-minute cap.
All solver times below are real seconds reported by CaDiCaL. Hashes bind both
the generated CNF and its proof; large transient artifacts were not committed.

| radius | variables | clauses | solver s | CNF SHA-256 | proof SHA-256 |
|---:|---:|---:|---:|---|---|
| 1 | 1,806 | 1,927,903 | 1.87 | `df22cc5d6c8bc49554e69cf42fa430a91a56b55881fa9a55bd8ae582f422717a` | `c4baad3d993b3724b302087f4d10ed2845091454417b558dc213bf68a6734134` |
| 2 | 2,709 | 1,929,705 | 2.77 | `7080b02113c546700ab60caacfa485d1703ad0ea5d7d7fd16cf6d2b044f87104` | `a5b4b430cbdef361d93e8da374f86c54700ea82691db223862041135cf76f8d3` |
| 3 | 3,612 | 1,931,505 | 6.55 | `203b5ec62f400f4386eacecbfdd9ba36ca32d030ec79124652b9095da0b93390` | `e15f0a9993fb3868d8fd9863eceb2b049a1b31c9bfb44109bd718a5745632530` |
| 4 | 4,515 | 1,933,303 | 11.14 | `126cac8aadfd5687a731e783e07c017fe278e574a39b39287ba0b45a3305f228` | `be3219f61ec2eb37ad309764cf712fd055d6e3c96a4b03c790f972d9ed699544` |
| 5 | 5,418 | 1,935,099 | 22.43 | `d569f0663f0ed3ad4ceb1d38618f0c9546eb86c0bbfaa56fa28ec403ec982d5a` | `045a78405dfbab1a1a21e1ab0b34200a434bd50e043769fdf97a736f77e6244c` |
| 6 | 6,321 | 1,936,893 | 48.53 | `606451f58561c5ae4d55330539e2e6c3cf1eeb7f35a556445d3f754bdbd6a540` | `3d8f975658a82d633ac4c78de714c22ad3e05d9dc91317e53a3022549a11c539` |
| 7 | 7,224 | 1,938,685 | 81.62 | `e9022858ae3b3eeb39eb76888fa5980b845ac284ddd363f20d6744852b62f784` | `b80373400fdd8821be31e9994c914f1ac3752fa162b97d9f8c2db4138e135eaf` |
| 8 | 8,127 | 1,940,475 | 137.16 | `9fac70649980dd0f757a879bfadd6fa5f68dff0e740d3f8d5e0c5cb2083a3c73` | `e43a0282f1d34f74e2486100d41adc9e3e6edce5322de9b6691fdf796552f12d` |

The exact conclusion is: no `(5,5)`-avoiding graph on labeled vertices
`0..42` differs in at most eight edge positions from this exact seed.
