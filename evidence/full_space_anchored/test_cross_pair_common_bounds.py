#!/usr/bin/env python3
"""Regression tests for global A-B pair common-set propagation cuts."""
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


class CrossPairCommonBoundsTests(unittest.TestCase):
    def test_kmtotalizer_projection_is_exact_at_boundary(self):
        pool = IDPool(start_from=100)
        conjunctions = [(2 * index + 2, 2 * index + 3)
                        for index in range(15)]
        clauses = SAT._conditional_conjunction_atmost(
            conjunctions, 13, 1, pool, SAT.EncType.kmtotalizer)
        with Solver(name="cadical195", bootstrap_with=clauses) as solver:
            for count, expected in ((13, True), (14, False)):
                assumptions = [1]
                for index, literals in enumerate(conjunctions):
                    assumptions.extend(literals if index < count
                                       else (-literals[0], literals[1]))
                self.assertEqual(solver.solve(assumptions=assumptions),
                                 expected)
            self.assertTrue(solver.solve(
                assumptions=[-1] + [literal for pair in conjunctions
                                    for literal in pair]))

    def test_direct_verifier_rejects_both_boundary_violations(self):
        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 20)
        for w in range(1, 15):
            set_edge(adjacency, 0, w)
            set_edge(adjacency, 20, w)
        with self.assertRaisesRegex(ValueError, "cross-block pair"):
            SAT.verify_cross_pair_common_bounds(adjacency, 20)

        adjacency = [(1 << SAT.N) - 1 - (1 << u) for u in range(SAT.N)]
        adjacency[0] &= ~(1 << 20)
        adjacency[20] &= ~(1 << 0)
        for w in range(1, 15):
            adjacency[0] &= ~(1 << w)
            adjacency[w] &= ~(1 << 0)
            adjacency[20] &= ~(1 << w)
            adjacency[w] &= ~(1 << 20)
        with self.assertRaisesRegex(ValueError, "cross-block pair"):
            SAT.verify_cross_pair_common_bounds(adjacency, 20)

    def test_constraints_are_default_on_with_diagnostic_opt_out(self):
        bounded, bounded_top = SAT.core_clauses(20, None, 2)
        unbounded, unbounded_top = SAT.core_clauses(
            20, None, 2, enforce_cross_pair_common_bounds=False)
        self.assertGreater(len(bounded), len(unbounded))
        self.assertGreater(bounded_top, unbounded_top)
        self.assertEqual((len(unbounded), unbounded_top), (879802, 440369))


if __name__ == "__main__":
    unittest.main()
