# Z4–Z12 cyclic-template exclusion — evidence

Audit-critical interpretation lives here, not in the PR body. A PR body is
editable; this file is versioned and hashed.

## Theorem boundary

The generalized mutual-obligation search finds no survivor using at most 13
non-cycle toggles for the tested cyclic-template instance, under `up_to_k`
semantics. Any survivor in this model therefore requires at least 14 non-cycle
toggles.

This is a template-boundary result. It does **not prove that no valid
43-vertex graph exists**, it claims no improved bound on `R(5,5)`, and it makes
no claim about the model's adequacy to HCP-001 itself.

## Definitions

- Base template: `N = 43`, `S = {1,2,7,10,12,13,14,16,18,20,21}`; an edge is
  present iff its cyclic difference lies in `S ∪ −S (mod 43)`.
- Cycle edge: cyclic distance 1. Non-cycle chords: 860 of the 903 pairs.
- Witness `W`: a 5-subset with no distance-one pair (cycle-free), so arbitrary
  distance-one deletions cannot affect it.
- For colour `c`: `R_c(W) = {e ⊂ W : B(e) ≠ c}` (toggles required),
  `F_c(W) = {e ⊂ W : B(e) = c}` (toggles forbidden).
- A toggle set `T` leaves `W` monochromatic in `c` iff `R_c(W) ⊆ T` and
  `T ∩ F_c(W) = ∅`. Only records with `|R_c(W)| ≤ 4` can certify a Z4 quadruple.
- `up_to_k` semantics: a set satisfying every obligation at size `< k` is
  reported immediately. For a **zero** result this is the stronger statement and
  implies exact-`k` zero. It is the wrong mode for enumerating exact-`k`
  survivors.

## Named lemmas

**Persistent obligation.** If `R ⊆ T` and `F ∩ T = ∅`, every satisfying
extension `T' ⊇ T` contains an element of `F`. Obligations grow as `T` grows —
a witness becomes an obligation only once `R ⊆ T` — so this is what makes the
lower bounds below valid.

**Coverage bound.** `m = max_{x ∈ A(T)} |{F ∈ unmet : x ∈ F}|`.
If `unmet` is nonempty and `m = 0`, the node is infeasible.
For `m > 0`, prune iff `ceil(|unmet| / m) > remaining_budget`.
Computing `m` over a **superset** of `A(T)` is safe (inflates `m`, weakens the
prune); a **subset** is not. The implementation computes over `union(unmet F)`,
which contains every allowable positive-incidence element and no selected
toggle (an unmet `F` is disjoint from `T`). Instance note: `min |F| = 6`, so
`m = 0` is unreachable here; the code's `m_max = 1` fallback is a conservative
under-estimate on that unreachable class and is not part of the proof.

**Disjoint-family bound.** `q` pairwise-disjoint unmet `F` sets require at least
`q` additional toggles, since a chord lies in at most one member of a disjoint
family. Implementation: greedy witness, constraints scanned in ascending `|F|`
order, accept `F` iff disjoint from the accumulated union, prune iff the
constructed family size exceeds the remaining budget. The constructed family is
itself the certificate, so greedy is sound; ascending order is a strength
heuristic affecting how often the bound fires, never whether a firing is
justified.

## Instance invariants

```text
records=423937
records_by_R_size_1to4=[10105, 44419, 129129, 240284]
max_R=4
min_F=6
empty_F_possible=False
non_cycle_chords=860
cycle_free_5sets=567987
```

`cycle_free_5sets` agrees with the closed form `n/(n−k)·C(n−k,k) = 43/38·C(38,5)`.

## Frozen status

```text
K4–K6   zero; independent replay; bounds-off/on preservation
K7      zero; independent UNBOUNDED replay; bounds-off/on preservation
K8–K10  zero; independent bounded replay; memo-off/on preservation;
        relies on proved pruning lemmas
K11     zero; independent bounds+memo replay;
        relies on pruning lemmas and memo argument
K12     zero; independent bounds+memo replay;
        relies on pruning lemmas and memo argument
K13     zero; bounds+memo replay, this implementation only;
        relies on pruning lemmas and memo argument; NOT independently reproduced
```

### K13 (added after the K4–K12 packet merged)

```text
python=3.12.14 bounds=on memo=on
mode=up_to_k
target_k=13
under_target_hits=0
target_size_hits=0
total_survivors=0
unique_states=6311447
runtime_seconds=1058.22

command: python3 z_general_memo.py --k 13 --bounds on --memo on
seed:    none / deterministic
capture: k13_run.out
```

K13 differs from K4–K12 in one way that matters: **no second implementation has
reproduced it.** K4–K12 carry independent survivor-set agreement; K13 is this
implementation alone. It is reported at that lower strength deliberately.

State counts differ between implementations and are **work metrics, not
outcomes**: they depend on branching order and memoization. Canonical survivor
sets are the cross-implementation invariant, and they agree at empty on every
level.

## Split prune audit

```text
trials=4000
coverage_only_fired=50
disjoint_only_fired=312
both_fired=1012
union_firing_rate=0.344
coverage_unsound=0
disjoint_unsound=0
union_unsound=0
SPLIT_AUDIT_PASSED=True
```

Terminology: **trigger count** = predicate exercised and falsifiable by a
feasible completion (coverage 1062, disjoint 1324); **exclusive-decision
count** = that predicate alone justified the rejection (coverage 50, disjoint
312); **union count** = the production policy rejected. Coverage is
well-exercised but rarely load-bearing; disjointness is both. Firing rate is
reported because zero violations from a bound that never fires is vacuous.

## Claim / support / limitation

```text
claim                    support                              limitation
search semantics         five-field output + survivor sets    up_to_k, not exact_k
bound soundness          named proofs + split prune audit     audit sampled; proof universal
bounds preserve results  K4–K7 off/on differentials           empirical through K7 only
memo preserves results   memo argument + K5, K8–K10 diffs     empirical at those levels only
zero through K12         two independent implementations'     K8–K12 share proved bounds;
                         canonical survivor sets              K11–K12 also rely on memo
```

## Mode provenance

```text
K12 runtime capture (verbatim): the final 7 lines of k8_k12_runs.out.
Mode provenance (source, not runtime capture): z_general_memo.py:159
unconditionally emits mode=up_to_k. The capture pipeline was

  python3 z_general_memo.py --k $k --bounds on --memo on 2>&1 \
    | grep -E "target_k|under_target_hits|target_size_hits|total_survivors|unique_states|runtime"

and "mode" matches none of those alternatives. No rerun was performed.
```

## Correction log

```text
Correction 1: output mode relabeled exact_k -> up_to_k; zero conclusion unchanged.
Correction 2: split-audit language changed from "50 coverage tests" to
              1,062 triggers / 50 exclusive decisions; audit results unchanged.
Correction 3: coverage described as superset-safe, not scope-invariant;
              implementation already computes over union(unmet F), runs unchanged.
Correction 4: memo-preservation differential was a two-program comparison
              (z_general.py vs z_general_memo.py) presented as a one-flag
              differential. Rerun within one program with --memo off/on and
              captured. State counts unchanged; the CONTROL was invalid and is
              now valid.
```

Corrections 1–3 are description-only, computations untouched. Correction 4 is a
methodological defect in a control, caught in review rather than by the author.
The distinction is recorded so the log does not read as though only prose ever
went wrong.

## Attribution

Independent reference implementation/results and evidence review: Rui Wang's
Sutando/Codex agent (@ruiwangwarm-sutando-rui-codex.agent:ag2.space), including
the branching-order comparison, prune-audit design and split-predicate
refinement, memoization state argument, and up_to_k versus exact_k semantics
distinction.

Replay implementation, production captures, hashes, and assembled artifact
packet: this side.
