#!/usr/bin/env python3
"""Regression tests for the optional pair-propagation constraints."""
from itertools import product
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


def literal_value(literal, values):
    value = values[abs(literal) - 1]
    return value if literal > 0 else not value


class PairPropagationTests(unittest.TestCase):
    def check_projection(self, conjunctions, guard):
        clauses = []
        pool = IDPool(start_from=5)
        SAT.conditional_conjunction_atmost(
            clauses, pool, conjunctions, 1, guard)
        with Solver(name="cadical195", bootstrap_with=clauses) as solver:
            for values in product((False, True), repeat=4):
                assumptions = [index if value else -index
                               for index, value in enumerate(values, 1)]
                active = all(literal_value(literal, values)
                             for literal in guard)
                count = sum(all(literal_value(literal, values)
                                for literal in conjunction)
                            for conjunction in conjunctions)
                self.assertEqual(
                    solver.solve(assumptions=assumptions),
                    not active or count <= 1)

    def test_guarded_encoding_is_exact_after_projection(self):
        self.check_projection(
            ((1, 2), (1, -3), (-2, 3)), (4,))
        self.check_projection(
            ((-1, -2), (-1, 3), (2, -3)), (-4,))

    def test_pair_layer_is_opt_in_with_block_bounds_default_on(self):
        for j in (2, 13):
            default, default_top = SAT.core_clauses(20, None, j)
            combined, combined_top = SAT.core_clauses(
                20, None, j, enforce_pair_propagation=True)
            self.assertEqual((len(default), default_top),
                             (720934, 355465))
            self.assertEqual((len(combined), combined_top),
                             (2022766, 1028767))

    def test_direct_verifier_rejects_both_dual_violations(self):
        complete = [(1 << SAT.N) - 1 - (1 << u) for u in range(SAT.N)]
        with self.assertRaisesRegex(
                ValueError, "edge common-neighbor bound violated"):
            SAT.verify_pair_propagation(complete)

        empty = [0] * SAT.N
        with self.assertRaisesRegex(
                ValueError, "nonedge common-nonneighbor bound violated"):
            SAT.verify_pair_propagation(empty)


if __name__ == "__main__":
    unittest.main()
