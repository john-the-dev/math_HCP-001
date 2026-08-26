# HCP-001 Z43 boundary evidence

`verify_z43_boundary.py` is a standalone exact verifier using only the Python
standard library. It checks:

- the compact 43-vertex candidate, all 962,598 five-vertex subsets, its degree
  multiset, and its exact two violations;
- the 129-clause Z0 CNF, including exclusion of a one-violation Z0 state;
- one direct cycle-deletion-invariant witness for each of the 20 dihedral Z1
  classes;
- every graph in the full 903-coordinate Hamming ball of radius at most two
  around the candidate: `1 + 903 + C(903,2) = 408,157` distinct graphs.

The radius-two verifier uses the exact flip delta. For an absent pair `uv`,
adding it changes `F=#K5+#I5` by

`triangles(N(u) intersection N(v)) - independent_triples(nonN(u) intersection nonN(v))`.

Deleting a present edge has the opposite delta. The script recomputes all 903
deltas after every possible first flip, then retains only the canonical
second-flip order, so every distinct radius-two state is covered once.

No HCP-001 solution is claimed. The verified candidate has `F=2`; the verified
radius-two minimum is also two.

## Independent radius-two and directed three-flip verifier

`verify_radius2_and_directed3.js` independently reconstructs the candidate and
checks all `1 + 903 + C(903,2) = 408,157` distinct graphs in its full Hamming
ball of radius at most two. This means arbitrary toggles among all 903 graph
edges, not only cycle-edge deletions or repair-directed flips. It finds minimum
`F=2`: two neutral radius-one additions and two nontrivial neutral radius-two
states.

The same script also makes the earlier "three-flip neighborhood" precise. It
is a directed repair neighborhood, **not the full radius-three sphere**:

1. add a missing edge from either of the candidate's two independent 5-sets;
2. delete a present edge from a K5 created by step 1;
3. toggle an edge belonging to a monochromatic 5-set remaining after step 2.

There are 14 first choices, 53,169 directed trajectories, and 42,535 distinct
terminal graphs in that neighborhood. Its exact minimum is also `F=2`.

Interpreter: Node.js v22.22.0
Command: `node verify_radius2_and_directed3.js`
Wall time (`/usr/bin/time -p`): 11.56 seconds
Verifier SHA-256: `468a7e4cf81603b29e5b62c9f30946ee58b618dde8aa5a0a23b1130fd0aa7ca5`
Captured output: `RADIUS2_DIRECTED3_OUTPUT.txt`

## Z2: any two non-cycle toggles plus arbitrary cycle deletions

`verify_z2_direct.py` checks the full Z2 family. Starting from the cyclic base
`B`, choose any two distinct non-cycle chords, toggle both relative to `B`, and
then delete an arbitrary subset of the 43 distance-one cycle edges. There are
860 non-cycle chords and `C(860,2) = 369,370` unordered toggle pairs.

For every one of the 369,370 pairs, the verifier finds a monochromatic 5-set
containing no distance-one pair. Such a witness is unaffected by every allowed
cycle-edge deletion, so all Z2 cases are excluded directly and no SAT solving
is needed. The enumeration uses all 567,987 five-sets containing no cycle pair.
Together with Z0 and Z1, this proves that a successful perturbation in this
template requires at least three non-cycle chord toggles, regardless of how
the 43 cycle edges are deleted. This is a template-boundary theorem, not an
`R(5,5)` lower-bound improvement.

Interpreter: Python 3.12.4
Command: `python3 verify_z2_direct.py`
Wall time (`/usr/bin/time -p`): 3.57 seconds
Verifier SHA-256: `bda5d392bed9eeabf1f7de4176a636accc65ebe7a5bba9ac59e0d742e8d0178d`
Captured output: `Z2_VERIFIED_OUTPUT.txt`

## Z3: any three non-cycle toggles plus arbitrary cycle deletions

`verify_z3_direct.py` extends the direct-witness argument to all
`C(860,3) = 105,639,820` unordered triples of distinct non-cycle chord
toggles. For each first toggle `t`, it enumerates every cycle-free 5-set made
monochromatic by `t` alone and computes all unordered pairs of further toggles
that jointly hit every such witness. Enforcing that both further toggles are
distinct from `t`, there are 451,027 such hitting pairs
across the 860 choices of `t`, producing 450,769 candidate triples requiring a
mutual check.

A triple could evade this direct argument only if, for each of its three
members, the other two form a hitting pair for all witnesses created by that
member. The exact mutual check finds zero such triples. Hence every one of the
105,639,820 Z3 toggle sets leaves a monochromatic 5-set containing no
distance-one cycle edge, and arbitrary deletion of cycle edges cannot repair
it. Together with Z0 through Z2, a successful perturbation in this template
requires at least **four** non-cycle chord toggles. This remains a theorem about
the cyclic-template search boundary, not a solution of HCP-001.

Interpreter: Python 3.12.4
Command: `python3 verify_z3_direct.py`
Wall time (`/usr/bin/time -p`): 3.35 seconds
Verifier SHA-256: `0d2b43ec9a53ec0583d064dbc191131c64022ab8f1d2ef3008c4cbf2a0775456`
Captured output: `Z3_VERIFIED_OUTPUT.txt`

An independent implementation, `verify_z3_direct_independent.py`, explicitly
excludes the fixed first toggle from both partner positions and agrees on all
key counts: 451,027 valid partner-pair incidences, 450,769 distinct candidate
triples, and zero mutually corrective triples. Python 3.12.4, wall 2.59
seconds, SHA-256
`612f3d4e73ef423a9e40294a9535128b6fbeac288666f32d753cd711b10a015f`;
captured output: `Z3_INDEPENDENT_OUTPUT.txt`.
