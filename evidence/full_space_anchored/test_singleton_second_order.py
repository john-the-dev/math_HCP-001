#!/usr/bin/env python3
"""Tests for singleton distinguished-pair second-order bounds."""
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


class SingletonSecondOrderTests(unittest.TestCase):
    def test_generator_exact_scope_polarity_and_self_exclusion(self):
        calls = []
        original = SAT._conditional_conjunction_atmost

        def record(conjunctions, bound, condition, pool):
            calls.append((tuple(conjunctions), bound, condition, pool))
            return []

        SAT._conditional_conjunction_atmost = record
        pool = IDPool()
        try:
            self.assertEqual(SAT.singleton_second_order_clauses(
                20, 2, 8, pool), [])
        finally:
            SAT._conditional_conjunction_atmost = original

        expected = []
        block_b = list(range(20, SAT.N))
        for w, x in SAT.combinations(block_b, 2):
            expected.append((tuple(
                (SAT.edge_var(0, w), SAT.edge_var(1, w),
                 SAT.edge_var(0, x), SAT.edge_var(1, x),
                 SAT.edge_var(0, y), SAT.edge_var(1, y),
                 -SAT.edge_var(w, y), -SAT.edge_var(x, y))
                for y in block_b if y not in (w, x)),
                2, -SAT.edge_var(w, x), pool))
        block_a = list(range(20))
        for w, x in SAT.combinations(block_a, 2):
            expected.append((tuple(
                (-SAT.edge_var(20, w), -SAT.edge_var(29, w),
                 -SAT.edge_var(20, x), -SAT.edge_var(29, x),
                 -SAT.edge_var(20, y), -SAT.edge_var(29, y),
                 SAT.edge_var(w, y), SAT.edge_var(x, y))
                for y in block_a if y not in (w, x)),
                2, SAT.edge_var(w, x), pool))
        self.assertEqual(calls, expected)

    def test_independent_activation_and_exact_deltas(self):
        cases = (
            (20, 2, None, 24948, 12936),
            (20, None, 8, 18240, 9500),
            (20, 2, 8, 43188, 22436),
            (18, 0, 10, 12852, 6732),
        )
        for degree, j, k, clause_delta, variable_delta in cases:
            bounded, bounded_top = SAT.core_clauses(
                degree, a_internal_degree=j, b_internal_degree=k)
            unbounded, unbounded_top = SAT.core_clauses(
                degree, a_internal_degree=j, b_internal_degree=k,
                enforce_singleton_second_order_bounds=False)
            self.assertEqual(len(bounded) - len(unbounded), clause_delta)
            self.assertEqual(bounded_top - unbounded_top, variable_delta)
        self.assertEqual(
            SAT.singleton_second_order_clauses(18, 0, None, IDPool()), [])
        self.assertEqual(
            SAT.singleton_second_order_clauses(20, None, 21, IDPool()), [])

    def test_production_counters_hit_both_signed_boundaries(self):
        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        clauses = SAT.singleton_second_order_clauses(20, 2, None, pool)
        base = [-SAT.edge_var(20, 21)]
        for z in (20, 21):
            base.extend((SAT.edge_var(0, z), SAT.edge_var(1, z)))
        with Solver(name="glucose4", bootstrap_with=clauses) as solver:
            for count, expected in ((2, True), (3, False)):
                assumptions = list(base)
                for y in range(22, 22 + count):
                    assumptions.extend((
                        SAT.edge_var(0, y), SAT.edge_var(1, y),
                        -SAT.edge_var(20, y), -SAT.edge_var(21, y)))
                self.assertEqual(solver.solve(assumptions=assumptions),
                                 expected)
            self.assertTrue(solver.solve(assumptions=[SAT.edge_var(20, 21)]
                + base[1:] + [literal for y in (22, 23, 24)
                              for literal in (SAT.edge_var(0, y),
                                              SAT.edge_var(1, y),
                                              -SAT.edge_var(20, y),
                                              -SAT.edge_var(21, y))]))

        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        clauses = SAT.singleton_second_order_clauses(20, None, 8, pool)
        base = [SAT.edge_var(0, 1)]
        for z in (0, 1):
            base.extend((-SAT.edge_var(20, z), -SAT.edge_var(29, z)))
        with Solver(name="glucose4", bootstrap_with=clauses) as solver:
            for count, expected in ((2, True), (3, False)):
                assumptions = list(base)
                for y in range(2, 2 + count):
                    assumptions.extend((
                        -SAT.edge_var(20, y), -SAT.edge_var(29, y),
                        SAT.edge_var(0, y), SAT.edge_var(1, y)))
                self.assertEqual(solver.solve(assumptions=assumptions),
                                 expected)
            self.assertTrue(solver.solve(assumptions=[-SAT.edge_var(0, 1)]
                + base[1:] + [literal for y in (2, 3, 4)
                              for literal in (-SAT.edge_var(20, y),
                                              -SAT.edge_var(29, y),
                                              SAT.edge_var(0, y),
                                              SAT.edge_var(1, y))]))

    def test_verifier_accepts_boundaries_and_rejects_violations(self):
        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 1)
        for z in range(20, 24):
            set_edge(adjacency, 0, z)
            set_edge(adjacency, 1, z)
        SAT.verify_singleton_second_order_bounds(adjacency, 20, 2, None)
        set_edge(adjacency, 0, 24)
        set_edge(adjacency, 1, 24)
        with self.assertRaisesRegex(ValueError, "singleton A"):
            SAT.verify_singleton_second_order_bounds(
                adjacency, 20, 2, None)

        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 1)
        for z in (2, 3):
            set_edge(adjacency, 0, z)
            set_edge(adjacency, 1, z)
        SAT.verify_singleton_second_order_bounds(adjacency, 20, None, 8)
        set_edge(adjacency, 0, 4)
        set_edge(adjacency, 1, 4)
        with self.assertRaisesRegex(ValueError, "singleton B"):
            SAT.verify_singleton_second_order_bounds(
                adjacency, 20, None, 8)


if __name__ == "__main__":
    unittest.main()
