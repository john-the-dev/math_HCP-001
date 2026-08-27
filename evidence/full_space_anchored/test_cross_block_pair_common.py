#!/usr/bin/env python3
"""Tests for opposite-block portions of within-block pair bounds."""
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


class CrossBlockPairCommonTests(unittest.TestCase):
    def test_production_generator_has_exact_scope_and_polarity(self):
        for degree in (18, 19, 20):
            calls = []
            original = SAT._conditional_conjunction_atmost

            def record(conjunctions, bound, condition, pool):
                calls.append((tuple(conjunctions), bound, condition, pool))
                return []

            SAT._conditional_conjunction_atmost = record
            pool = IDPool()
            try:
                self.assertEqual(
                    SAT.cross_block_pair_common_clauses(degree, pool), [])
            finally:
                SAT._conditional_conjunction_atmost = original

            expected = []
            block_a = list(range(degree))
            block_b = list(range(degree, SAT.N))
            for u, v in SAT.combinations(block_a, 2):
                expected.append((tuple(
                    (SAT.edge_var(u, w), SAT.edge_var(v, w))
                    for w in block_b), 8, SAT.edge_var(u, v), pool))
            for u, v in SAT.combinations(block_b, 2):
                expected.append((tuple(
                    (-SAT.edge_var(u, w), -SAT.edge_var(v, w))
                    for w in block_a), 8, -SAT.edge_var(u, v), pool))
            self.assertEqual(calls, expected)

    def test_signed_conditional_counter_boundary(self):
        for condition in (1, -1):
            pool = IDPool(start_from=100)
            conjunctions = [(2 * index + 2, 2 * index + 3)
                            for index in range(10)]
            clauses = SAT._conditional_conjunction_atmost(
                conjunctions, 8, condition, pool)
            with Solver(name="glucose4", bootstrap_with=clauses) as solver:
                for count, expected in ((8, True), (9, False)):
                    assumptions = [condition]
                    for index, pair in enumerate(conjunctions):
                        assumptions.extend(pair if index < count
                                           else (-pair[0], pair[1]))
                    self.assertEqual(solver.solve(assumptions=assumptions),
                                     expected)
                self.assertTrue(solver.solve(assumptions=[-condition]
                    + [literal for pair in conjunctions for literal in pair]))

    def test_direct_verifier_rejects_both_boundary_violations(self):
        adjacency = [0] * SAT.N
        for u, v in SAT.combinations(range(20, SAT.N), 2):
            set_edge(adjacency, u, v)
        set_edge(adjacency, 0, 1)
        for w in range(20, 28):
            set_edge(adjacency, 0, w)
            set_edge(adjacency, 1, w)
        self.assertEqual(
            SAT.verify_cross_block_pair_common_bounds(adjacency, 20)[
                "a_edge_common_neighbors_in_b"], 8)
        set_edge(adjacency, 0, 28)
        set_edge(adjacency, 1, 28)
        with self.assertRaisesRegex(ValueError, "A-edge cross-block"):
            SAT.verify_cross_block_pair_common_bounds(adjacency, 20)

        adjacency = [0] * SAT.N
        for u, v in SAT.combinations(range(20, SAT.N), 2):
            set_edge(adjacency, u, v)
        adjacency[20] &= ~(1 << 21)
        adjacency[21] &= ~(1 << 20)
        for w in range(8, 20):
            set_edge(adjacency, 20, w)
        self.assertEqual(
            SAT.verify_cross_block_pair_common_bounds(adjacency, 20)[
                "b_nonedge_common_nonneighbors_in_a"], 8)
        adjacency[20] &= ~(1 << 8)
        adjacency[8] &= ~(1 << 20)
        with self.assertRaisesRegex(ValueError, "B-nonedge cross-block"):
            SAT.verify_cross_block_pair_common_bounds(adjacency, 20)

    def test_default_on_deltas_are_exact(self):
        expected = {18: (93744, 50304), 19: (96264, 51524),
                    20: (97776, 52256)}
        for degree, delta in expected.items():
            bounded, bounded_top = SAT.core_clauses(degree)
            unbounded, unbounded_top = SAT.core_clauses(
                degree, enforce_cross_block_pair_common_bounds=False)
            self.assertEqual((len(bounded) - len(unbounded),
                              bounded_top - unbounded_top), delta)


if __name__ == "__main__":
    unittest.main()
