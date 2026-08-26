#!/usr/bin/env python3
"""Standalone exact verifier for the HCP-001 Z43 boundary results."""

from itertools import combinations
import platform
import time


N = 43
ALL = (1 << N) - 1
S = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
DIFFS = S | {(-d) % N for d in S}
DELETED_CYCLE_INDICES = {
    3, 4, 5, 6,
    11, 12, 13, 14,
    20, 21, 22, 23,
    29, 30, 31,
    37, 38, 39, 40,
}
EXPECTED_I5 = {
    (3, 6, 7, 11, 12),
    (6, 7, 11, 12, 15),
}


def base_edge(u, v):
    return u != v and (v - u) % N in DIFFS


def cycle_index(u, v):
    if (v - u) % N == 1:
        return u
    if (u - v) % N == 1:
        return v
    return None


def build_candidate():
    adj = [0] * N
    for u, v in combinations(range(N), 2):
        if base_edge(u, v):
            adj[u] |= 1 << v
            adj[v] |= 1 << u
    for i in DELETED_CYCLE_INDICES:
        u, v = i, (i + 1) % N
        assert (adj[u] >> v) & 1
        adj[u] ^= 1 << v
        adj[v] ^= 1 << u
    return adj


def exhaustive_violations(adj):
    k5 = []
    i5 = []
    for q in combinations(range(N), 5):
        edges = sum((adj[u] >> v) & 1 for u, v in combinations(q, 2))
        if edges == 10:
            k5.append(q)
        elif edges == 0:
            i5.append(q)
    return k5, i5


def triangles(mask, adj):
    count = 0
    remaining = mask
    while remaining:
        bit_u = remaining & -remaining
        u = bit_u.bit_length() - 1
        remaining ^= bit_u
        later_neighbors = adj[u] & remaining
        while later_neighbors:
            bit_v = later_neighbors & -later_neighbors
            v = bit_v.bit_length() - 1
            later_neighbors ^= bit_v
            count += (adj[u] & adj[v] & later_neighbors).bit_count()
    return count


def all_flip_deltas(adj):
    comp = [(~adj[u]) & ALL ^ (1 << u) for u in range(N)]
    result = []
    for u, v in combinations(range(N), 2):
        rest = ALL ^ (1 << u) ^ (1 << v)
        common_neighbors = adj[u] & adj[v] & rest
        common_nonneighbors = comp[u] & comp[v] & rest
        clique_created = triangles(common_neighbors, adj)
        independent_created = triangles(common_nonneighbors, comp)
        if (adj[u] >> v) & 1:
            delta = independent_created - clique_created
        else:
            delta = clique_created - independent_created
        result.append((delta, (u, v)))
    return result


def toggle(adj, edge):
    u, v = edge
    changed = adj.copy()
    changed[u] ^= 1 << v
    changed[v] ^= 1 << u
    return changed


def verify_radius_two(candidate, base_f):
    edges = list(combinations(range(N), 2))
    first_deltas = all_flip_deltas(candidate)
    assert [edge for _, edge in first_deltas] == edges

    best = base_f
    best_states = {()}
    neutral_single = []
    for delta, edge in first_deltas:
        value = base_f + delta
        if value < best:
            best, best_states = value, {(edge,)}
        elif value == best:
            best_states.add((edge,))
        if delta == 0:
            neutral_single.append(edge)

    neutral_pairs = []
    for first_index, (delta1, edge1) in enumerate(first_deltas):
        changed = toggle(candidate, edge1)
        second_deltas = all_flip_deltas(changed)
        for second_index in range(first_index + 1, len(edges)):
            delta2, edge2 = second_deltas[second_index]
            value = base_f + delta1 + delta2
            state = (edge1, edge2)
            if value < best:
                best, best_states = value, {state}
            elif value == best:
                best_states.add(state)
                if value == base_f:
                    neutral_pairs.append(state)

    distinct_scope = 1 + len(edges) + len(edges) * (len(edges) - 1) // 2
    assert distinct_scope == 408_157
    assert best == 2
    assert set(neutral_single) == {(6, 7), (11, 12)}
    assert set(neutral_pairs) == {
        ((6, 7), (28, 29)),
        ((11, 12), (32, 33)),
    }
    assert len(best_states) == 5
    return distinct_scope, best, len(best_states), neutral_single, neutral_pairs


def z0_clauses():
    clauses = []
    for i in range(N):
        clauses.append(((i, 1), ((i + 1) % N, 1), ((i + 22) % N, 1)))
        clauses.append(((i, 0), ((i + 4) % N, 0)))
        clauses.append(((i, 0), ((i + 5) % N, 0)))
    return [tuple(sorted(clause)) for clause in clauses]


def dpll(clauses):
    assignment = [-1] * N

    def search(current):
        while True:
            changed = False
            for clause in clauses:
                if any(current[var] == value for var, value in clause):
                    continue
                unset = [(var, value) for var, value in clause if current[var] < 0]
                if not unset:
                    return None
                if len(unset) == 1:
                    var, value = unset[0]
                    current[var] = value
                    changed = True
            if not changed:
                break
        if all(value >= 0 for value in current):
            return current
        scores = [0] * N
        for clause in clauses:
            if any(current[var] == value for var, value in clause):
                continue
            for var, _ in clause:
                if current[var] < 0:
                    scores[var] += 1
        var = max((v for v in range(N) if current[v] < 0), key=scores.__getitem__)
        for value in (1, 0):
            branch = current.copy()
            branch[var] = value
            solved = search(branch)
            if solved is not None:
                return solved
        return None

    return search(assignment)


def verify_z0():
    clauses = z0_clauses()
    assert len(clauses) == 129
    assert len(set(clauses)) == 129
    assert dpll(clauses) is None

    # One raw violation could only be one surviving baseline K5. Removing each
    # positive clause in turn remains UNSAT; a violated negative clause creates
    # two independent 5-sets in this family.
    positive = [i for i, clause in enumerate(clauses) if len(clause) == 3]
    assert len(positive) == 43
    for omitted in positive:
        assert dpll([c for i, c in enumerate(clauses) if i != omitted]) is None
    return len(clauses), len(positive)


def toggled_edge(u, v, k):
    value = base_edge(u, v)
    if (u, v) == (0, k):
        value = not value
    return value


def verify_z1_direct_witnesses():
    witnesses = {}
    no_cycle_fives = [
        q for q in combinations(range(N), 5)
        if all(cycle_index(u, v) is None for u, v in combinations(q, 2))
    ]
    for k in range(2, 22):
        found = None
        for q in no_cycle_fives:
            values = [toggled_edge(u, v, k) for u, v in combinations(q, 2)]
            if all(values) or not any(values):
                found = ("K5" if all(values) else "I5", q)
                break
        assert found is not None
        witnesses[k] = found
    assert len(witnesses) == 20
    return witnesses


def main():
    started = time.perf_counter()
    candidate = build_candidate()
    k5, i5 = exhaustive_violations(candidate)
    degrees = sorted(mask.bit_count() for mask in candidate)
    edges = sum(degrees) // 2
    assert not k5
    assert set(i5) == EXPECTED_I5
    assert edges == 454
    assert degrees == [20] * 14 + [21] * 10 + [22] * 19

    z0_count, z0_positive = verify_z0()
    witnesses = verify_z1_direct_witnesses()
    radius = verify_radius_two(candidate, len(k5) + len(i5))

    print(f"python={platform.python_version()}")
    print(f"candidate_edges={edges}")
    print("degree_counts=20:14,21:10,22:19")
    print(f"candidate_K5={len(k5)} candidate_I5={len(i5)} F={len(k5) + len(i5)}")
    print(f"candidate_I5_sets={i5}")
    print(f"Z0_clauses={z0_count} positive_clauses={z0_positive} SAT=False exact_min_F=2")
    print("Z1_classes=20 direct_unaffected_witnesses=20")
    for k, witness in witnesses.items():
        direction = "delete" if k in S else "add"
        print(f"Z1 k={k:2d} toggle={direction:6s} witness={witness[0]} {witness[1]}")
    scope, best, best_count, singles, pairs = radius
    print(f"radius_le_2_distinct_states={scope} min_F={best} minimizer_count={best_count}")
    print(f"radius1_neutral={singles}")
    print(f"radius2_nontrivial_neutral={pairs}")
    print(f"runtime_seconds={time.perf_counter() - started:.6f}")


if __name__ == "__main__":
    main()
