#!/usr/bin/env python3
"""Regression tests for opt-in within-block triple common-set cuts."""
from pathlib import Path
import importlib.util
from itertools import combinations
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


class BlockTripleCommonBoundsTests(unittest.TestCase):
    def test_multiliteral_guard_projects_exactly_for_both_polarities(self):
        for conditions, conjunctions in (
                ((1, 2, 3), [(4 + 2 * i, 5 + 2 * i)
                              for i in range(5)]),
                ((-1, -2, -3), [(-4 - 2 * i, -5 - 2 * i)
                                 for i in range(5)])):
            pool = IDPool(start_from=30)
            clauses = SAT._conditional_conjunctions_atmost(
                conjunctions, 3, conditions, pool)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for count, expected in ((3, True), (4, False)):
                    assumptions = list(conditions)
                    for index, literals in enumerate(conjunctions):
                        assumptions.extend(literals if index < count
                                           else (-literals[0], literals[1]))
                    self.assertEqual(solver.solve(assumptions=assumptions),
                                     expected)
                disabled = [-conditions[0], *conditions[1:]]
                disabled.extend(literal for pair in conjunctions
                                for literal in pair)
                self.assertTrue(solver.solve(assumptions=disabled))

    def test_a_independent_triple_boundary_and_guard(self):
        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        clauses = SAT.block_triple_common_clauses(18, pool)
        triple = (0, 1, 2)
        condition = [-SAT.edge_var(u, v)
                     for u, v in combinations(triple, 2)]
        common = [[-SAT.edge_var(u, x) for u in triple] for x in range(3, 7)]
        with Solver(name="cadical195", bootstrap_with=clauses) as solver:
            self.assertTrue(solver.solve(
                assumptions=condition + sum(common[:3], [])
                + [-common[3][0], *common[3][1:]]))
            self.assertFalse(solver.solve(
                assumptions=condition + sum(common, [])))
            self.assertTrue(solver.solve(
                assumptions=[-condition[0], *condition[1:]] + sum(common, [])))

    def test_b_triangle_boundary_and_guard(self):
        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        clauses = SAT.block_triple_common_clauses(20, pool)
        triple = (20, 21, 22)
        condition = [SAT.edge_var(u, v)
                     for u, v in combinations(triple, 2)]
        common = [[SAT.edge_var(u, x) for u in triple] for x in range(23, 27)]
        with Solver(name="cadical195", bootstrap_with=clauses) as solver:
            self.assertTrue(solver.solve(
                assumptions=condition + sum(common[:3], [])
                + [-common[3][0], *common[3][1:]]))
            self.assertFalse(solver.solve(
                assumptions=condition + sum(common, [])))
            self.assertTrue(solver.solve(
                assumptions=[-condition[0], *condition[1:]] + sum(common, [])))

    def test_direct_verifier_rejects_both_violations(self):
        adjacency = [0] * SAT.N
        with self.assertRaisesRegex(ValueError, "A-block triple"):
            SAT.verify_block_triple_common_bounds(adjacency, 18)

        adjacency = [0] * SAT.N
        for u, v in combinations(range(20), 2):
            set_edge(adjacency, u, v)
        for u, v in ((20, 21), (20, 22), (21, 22)):
            set_edge(adjacency, u, v)
        for x in range(23, 27):
            for u in (20, 21, 22):
                set_edge(adjacency, u, x)
        with self.assertRaisesRegex(ValueError, "B-block triple"):
            SAT.verify_block_triple_common_bounds(adjacency, 20)

    def test_opt_in_preserves_default_formula_and_manifest(self):
        default, default_top = SAT.core_clauses(20, None, 2)
        explicit_off, explicit_off_top = SAT.core_clauses(
            20, None, 2, enforce_block_triple_common_bounds=False)
        bounded, bounded_top = SAT.core_clauses(
            20, None, 2, enforce_block_triple_common_bounds=True)
        self.assertEqual((len(default), default_top),
                         (len(explicit_off), explicit_off_top))
        self.assertEqual((len(default), default_top), (879802, 440369))
        self.assertEqual((len(bounded), bounded_top), (1204602, 610809))

        before = (HERE / "j_partition_manifest.json").read_bytes()
        temporary = HERE / ".test-triple-common-manifest.json"
        try:
            SAT.write_manifest(temporary, "j-only")
            self.assertEqual(temporary.read_bytes(), before)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
