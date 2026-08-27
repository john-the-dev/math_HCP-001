# Independent K14 exclusion

This directory records a separately written integer-mask implementation of the
generalized mutual-obligation search.  It does not import the published
`z_general_memo.py` implementation.

The 20 cyclic-distance anchors `2..21` cover all non-cycle edge orbits under
the template's dihedral symmetry.  Every anchor returned zero survivors of
size at most 14.  The run explored 18,101,717 memoized states in aggregate.

Reproduce one anchor with:

```sh
python3 z_intmask.py --k 14 --distance 2
```

Reproduce all anchors independently (parallelism is optional):

```sh
seq 2 21 | xargs -P 3 -I{} python3 z_intmask.py --k 14 --distance {}
```

`anchor-results.tsv` is the captured summary from Python 3.12.4. Runtime is
informational; survivor counts are the result invariant.

Scope: this excludes toggle sets of size at most 14 in the cyclic-template
obligation model. It is not a proof that no 43-vertex Ramsey graph exists.
