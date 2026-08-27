#!/usr/bin/env python3
"""Regression tests for whole-H pair common-set propagation cuts."""
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


class GlobalPairCommonBoundsTests(unittest.TestCase):
    def test_production_generator_covers_every_pair_and_both_polarities(self):
        calls = []
        original = SAT._conditional_conjunction_atmost

        def record(conjunctions, bound, condition, pool, encoding):
            calls.append((tuple(conjunctions), bound, condition, encoding))
            return []

        SAT._conditional_conjunction_atmost = record
        try:
            self.assertEqual(SAT.global_pair_common_clauses(IDPool()), [])
        finally:
            SAT._conditional_conjunction_atmost = original

        pairs = list(SAT.combinations(range(SAT.N), 2))
        self.assertEqual(len(calls), 2 * len(pairs))
        for index, (u, v) in enumerate(pairs):
            edge = SAT.edge_var(u, v)
            others = [w for w in range(SAT.N) if w not in (u, v)]
            positive, negative = calls[2 * index:2 * index + 2]
            self.assertEqual(positive, (
                tuple((SAT.edge_var(u, w), SAT.edge_var(v, w))
                      for w in others), 13, edge, SAT.EncType.kmtotalizer))
            self.assertEqual(negative, (
                tuple((-SAT.edge_var(u, w), -SAT.edge_var(v, w))
                      for w in others), 13, -edge, SAT.EncType.kmtotalizer))

    def test_kmtotalizer_projection_is_exact_at_boundary(self):
        for condition in (1, -1):
            pool = IDPool(start_from=100)
            conjunctions = [(2 * index + 2, 2 * index + 3)
                            for index in range(15)]
            clauses = SAT._conditional_conjunction_atmost(
                conjunctions, 13, condition, pool, SAT.EncType.kmtotalizer)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for count, expected in ((13, True), (14, False)):
                    assumptions = [condition]
                    for index, literals in enumerate(conjunctions):
                        assumptions.extend(literals if index < count
                                           else (-literals[0], literals[1]))
                    self.assertEqual(solver.solve(assumptions=assumptions),
                                     expected)
                self.assertTrue(solver.solve(
                    assumptions=[-condition]
                    + [literal for pair in conjunctions for literal in pair]))

    def test_direct_verifier_rejects_both_boundary_violations(self):
        adjacency = [0] * SAT.N
        set_edge(adjacency, 0, 1)
        for w in range(2, 16):
            set_edge(adjacency, 0, w)
            set_edge(adjacency, 1, w)
        with self.assertRaisesRegex(ValueError, "global pair"):
            SAT.verify_global_pair_common_bounds(adjacency)

        adjacency = [(1 << SAT.N) - 1 - (1 << u) for u in range(SAT.N)]
        adjacency[0] &= ~(1 << 1)
        adjacency[1] &= ~(1 << 0)
        for w in range(2, 16):
            adjacency[0] &= ~(1 << w)
            adjacency[w] &= ~(1 << 0)
            adjacency[1] &= ~(1 << w)
            adjacency[w] &= ~(1 << 1)
        with self.assertRaisesRegex(ValueError, "global pair"):
            SAT.verify_global_pair_common_bounds(adjacency)

    def test_constraints_are_default_on_with_diagnostic_opt_out(self):
        bounded, bounded_top = SAT.core_clauses(
            20, None, 2, enforce_cross_block_pair_common_bounds=False,
            enforce_distinguished_cross_pair_degree_bounds=False)
        unbounded, unbounded_top = SAT.core_clauses(
            20, None, 2, enforce_global_pair_common_bounds=False,
            enforce_cross_block_pair_common_bounds=False,
            enforce_distinguished_cross_pair_degree_bounds=False)
        self.assertEqual(len(bounded) - len(unbounded), 723240)
        self.assertEqual(bounded_top - unbounded_top, 311682)
        self.assertEqual((len(unbounded), unbounded_top), (879802, 440369))


if __name__ == "__main__":
    unittest.main()
