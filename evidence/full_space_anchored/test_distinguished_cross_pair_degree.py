#!/usr/bin/env python3
"""Tests for distinguished cross-pair residual-degree bounds."""
from pathlib import Path
import importlib.util
import unittest

from pysat.formula import IDPool
from pysat.solvers import Solver


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "anchored_sat", HERE / "anchored_sat.py")
SAT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAT)


def set_edge(adjacency, u, v):
    adjacency[u] |= 1 << v
    adjacency[v] |= 1 << u


class DistinguishedCrossPairDegreeTests(unittest.TestCase):
    def test_generator_exact_scope_polarity_and_self_exclusion(self):
        calls = []
        original = SAT._conditional_conjunction_atmost

        def record(conjunctions, bound, condition, pool):
            calls.append((tuple(conjunctions), bound, condition, pool))
            return []

        SAT._conditional_conjunction_atmost = record
        pool = IDPool()
        try:
            self.assertEqual(SAT.distinguished_cross_pair_degree_clauses(
                20, 2, 8, pool), [])
        finally:
            SAT._conditional_conjunction_atmost = original
        expected_calls = 2 * (2 * (SAT.N - 20) + (SAT.N - 20 - 8 - 1) * 20)
        self.assertEqual(len(calls), expected_calls)
        first_neighbors, first_nonneighbors = calls[:2]
        self.assertEqual(first_neighbors[1:], (3, SAT.edge_var(0, 20), pool))
        self.assertEqual(first_nonneighbors[1:], (5, SAT.edge_var(0, 20), pool))
        self.assertEqual(first_neighbors[0][0], (
            SAT.edge_var(1, 20), SAT.edge_var(0, 21),
            SAT.edge_var(1, 21), SAT.edge_var(20, 21)))
        self.assertEqual(first_nonneighbors[0][0][:-1],
                         first_neighbors[0][0][:-1])
        self.assertEqual(first_nonneighbors[0][0][-1],
                         -first_neighbors[0][0][-1])
        b_offset = 2 * 2 * (SAT.N - 20)
        first_b_non, first_b_neighbors = calls[b_offset:b_offset + 2]
        u = 29
        self.assertEqual(first_b_non[1:], (3, -SAT.edge_var(20, 0), pool))
        self.assertEqual(first_b_neighbors[1:], (5, -SAT.edge_var(20, 0), pool))
        self.assertEqual(first_b_non[0][0], (
            -SAT.edge_var(u, 0), -SAT.edge_var(20, 1),
            -SAT.edge_var(u, 1), -SAT.edge_var(0, 1)))
        self.assertEqual(len(first_neighbors[0]), SAT.N - 20 - 1)
        self.assertEqual(len(first_b_non[0]), 20 - 1)

    def test_real_guarded_counters_hit_all_boundaries(self):
        cases = ((3, 4), (5, 6))
        for sign in (1, -1):
            for bound, violation in cases:
                pool = IDPool(start_from=100)
                condition = sign
                conjunctions = [
                    (sign * (4 * i + 2), sign * (4 * i + 3),
                     sign * (4 * i + 4), sign * (4 * i + 5))
                    for i in range(7)]
                clauses = SAT._conditional_conjunction_atmost(
                    conjunctions, bound, condition, pool)
                with Solver(name="glucose4", bootstrap_with=clauses) as solver:
                    for count, expected in ((bound, True),
                                            (violation, False)):
                        assumptions = [condition]
                        for index, term in enumerate(conjunctions):
                            assumptions.extend(term if index < count else
                                               (-term[0], *term[1:]))
                        self.assertEqual(
                            solver.solve(assumptions=assumptions), expected)
                    self.assertTrue(solver.solve(assumptions=[-condition]
                        + [literal for term in conjunctions
                           for literal in term]))

    def test_verifier_accepts_boundaries_and_rejects_violations(self):
        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 1)
        common = list(range(20, 26))
        for x in common:
            set_edge(adjacency, 0, x)
            set_edge(adjacency, 1, x)
        for x in common[1:4]:
            set_edge(adjacency, common[0], x)
        SAT.verify_distinguished_cross_pair_degree_bounds(
            adjacency, 20, 1, None)
        set_edge(adjacency, common[0], common[4])
        with self.assertRaisesRegex(ValueError, "A cross-pair neighbor"):
            SAT.verify_distinguished_cross_pair_degree_bounds(
                adjacency, 20, 1, None)

        adjacency = [0] * SAT.N
        for x in range(6, 20):
            set_edge(adjacency, 20, x)
        for u, v in SAT.combinations(range(6), 2):
            set_edge(adjacency, u, v)
        SAT.verify_distinguished_cross_pair_degree_bounds(
            adjacency, 20, None, 20)
        adjacency[20] &= ~(1 << 6)
        adjacency[6] &= ~(1 << 20)
        for x in range(6):
            set_edge(adjacency, x, 6)
        with self.assertRaisesRegex(ValueError, "B cross-pair neighbor"):
            SAT.verify_distinguished_cross_pair_degree_bounds(
                adjacency, 20, None, 20)

    def test_independent_activation_and_exact_deltas(self):
        cases = (
            (2, None, 14784, 7744),
            (None, 8, 76960, 40560),
            (2, 8, 91744, 48304),
            (13, 13, 143456, 75296),
        )
        for j, k, clause_delta, variable_delta in cases:
            bounded, bounded_top = SAT.core_clauses(
                20, a_internal_degree=j, b_internal_degree=k)
            unbounded, unbounded_top = SAT.core_clauses(
                20, a_internal_degree=j, b_internal_degree=k,
                enforce_distinguished_cross_pair_degree_bounds=False)
            self.assertEqual(len(bounded) - len(unbounded), clause_delta)
            self.assertEqual(bounded_top - unbounded_top, variable_delta)
        self.assertEqual(
            SAT.core_clauses(20),
            SAT.core_clauses(
                20, enforce_distinguished_cross_pair_degree_bounds=False))


if __name__ == "__main__":
    unittest.main()
