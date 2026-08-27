# Independent K14 exclusion

This directory records a separately written integer-mask implementation of the
generalized mutual-obligation search.  It does not import the published
`z_general_memo.py` implementation.

Python 3.10 or newer is required (`int.bit_count`). The recorded run used
Python 3.12.4.

The 20 cyclic-distance anchors `2..21` cover all non-cycle edge orbits under
rotation. `verify_evidence.py` proves the coverage bijectively: the 20 anchor
representatives under all 43 rotations produce 860 pairwise-distinct images,
exactly the complete 860-chord universe. It also checks baseline-color
equivariance for all 860 chords under all 43 rotations. Every anchor returned
zero survivors of size at most 14. The run explored 18,101,717 memoized states
in aggregate.

Reproduce one anchor with:

```sh
python3 z_intmask.py --k 14 --distance 2
```

Reproduce all anchors independently (parallelism is optional):

```sh
seq 2 21 | xargs -P 3 -I{} python3 z_intmask.py --k 14 --distance {}
```

`anchor-results.tsv` is the captured summary from Python 3.12.4. Runtime is
informational; survivor counts and state counts are the result invariants. The
table records the implementation, `k`, and mode on every row. It preserves
`under_target_hits` and `target_size_hits` separately because a nonzero
under-target count witnesses a smaller solution and is not comparable to an
exact-`k` result.

Verify the table metadata, aggregate, and complete anchor bijection with:

```sh
python3 verify_evidence.py
```

Expected terminal lines:

```text
rotation_anchor_checks=860
distinct_anchors_touched=860 of 860
rotation_color_checks=36980 failures=0
rotation_bijection=PASS
PASS
```

Scope: this excludes toggle sets of size at most 14 in the cyclic-template
obligation model. It is not a proof that no 43-vertex Ramsey graph exists.
