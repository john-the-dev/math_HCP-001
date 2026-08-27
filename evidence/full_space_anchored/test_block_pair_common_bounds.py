#!/usr/bin/env python3
"""Regression tests for within-block pair common-set propagation cuts."""
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


def valid_a_block(adjacency):
    for u in range(10):
        for v in range(10, 20):
            set_edge(adjacency, u, v)


class BlockPairCommonBoundsTests(unittest.TestCase):
    def test_conditional_cardinality_projects_exactly(self):
        for bound, condition in ((4, 1), (8, 1), (4, -1), (8, -1)):
            pool = IDPool(start_from=30)
            conjunctions = [(2 * index + 2, 2 * index + 3)
                            for index in range(10)]
            clauses = SAT._conditional_conjunction_atmost(
                conjunctions, bound, condition, pool)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for count, expected in ((bound, True), (bound + 1, False)):
                    assumptions = [condition]
                    for index, literals in enumerate(conjunctions):
                        assumptions.extend(literals if index < count
                                           else (-literals[0], literals[1]))
                    self.assertEqual(solver.solve(assumptions=assumptions),
                                     expected)
                disabled = [-condition]
                for literals in conjunctions:
                    disabled.extend(literals)
                self.assertTrue(solver.solve(assumptions=disabled))

    def test_direct_verifier_rejects_each_boundary_violation(self):
        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 1)
        for w in range(2, 7):
            set_edge(adjacency, 0, w)
            set_edge(adjacency, 1, w)
        with self.assertRaisesRegex(ValueError, "A-block pair"):
            SAT.verify_block_pair_common_bounds(adjacency, 20)

        with self.assertRaisesRegex(ValueError, "A-block pair"):
            SAT.verify_block_pair_common_bounds([0] * SAT.N, 20)

        adjacency = [0] * SAT.N
        valid_a_block(adjacency)
        set_edge(adjacency, 20, 21)
        for w in range(22, 31):
            set_edge(adjacency, 20, w)
            set_edge(adjacency, 21, w)
        with self.assertRaisesRegex(ValueError, "B-block pair"):
            SAT.verify_block_pair_common_bounds(adjacency, 20)

        adjacency = [0] * SAT.N
        valid_a_block(adjacency)
        with self.assertRaisesRegex(ValueError, "B-block pair"):
            SAT.verify_block_pair_common_bounds(adjacency, 20)

    def test_constraints_are_default_on_with_diagnostic_opt_out(self):
        bounded, bounded_top = SAT.core_clauses(
            20, None, 2, enforce_global_pair_common_bounds=False,
            enforce_cross_block_pair_common_bounds=False)
        unbounded, unbounded_top = SAT.core_clauses(
            20, None, 2, enforce_block_pair_common_bounds=False,
            enforce_global_pair_common_bounds=False,
            enforce_cross_block_pair_common_bounds=False)
        self.assertEqual((len(unbounded), unbounded_top), (732146, 361489))
        self.assertEqual((len(bounded), bounded_top), (879802, 440369))

    def test_manifest_is_unchanged_by_formula_cut(self):
        before = (HERE / "j_partition_manifest.json").read_bytes()
        temporary = HERE / ".test-pair-common-manifest.json"
        try:
            SAT.write_manifest(temporary, "j-only")
            self.assertEqual(temporary.read_bytes(), before)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
