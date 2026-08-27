#!/usr/bin/env python3
"""Regression tests for the per-vertex internal block-degree constraints."""
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


def circulant_block(adjacency, vertices, degree):
    vertices = list(vertices)
    size = len(vertices)
    assert degree % 2 == 0
    for index, u in enumerate(vertices):
        for offset in range(1, degree // 2 + 1):
            v = vertices[(index + offset) % size]
            adjacency[u] |= 1 << v
            adjacency[v] |= 1 << u


class BlockDegreeBoundsTests(unittest.TestCase):
    def test_exact_derived_ranges(self):
        self.assertEqual(SAT.block_internal_degree_bounds(18),
                         ((0, 13), (10, 17)))
        self.assertEqual(SAT.block_internal_degree_bounds(19),
                         ((1, 13), (9, 17)))
        self.assertEqual(SAT.block_internal_degree_bounds(20),
                         ((2, 13), (8, 17)))

    def test_production_encoding_projects_to_each_closed_range(self):
        for degree in (18, 19, 20):
            pool = IDPool(start_from=len(SAT.PAIRS) + 1)
            clauses = SAT.block_internal_degree_clauses(degree, pool)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for vertex_edges, (minimum, maximum) in zip(
                        SAT.block_internal_degrees(degree),
                        SAT.block_internal_degree_bounds(degree)):
                    edges = vertex_edges[0]
                    for count, expected in (
                            (minimum - 1, False), (minimum, True),
                            (maximum, True), (maximum + 1, False)):
                        if count < 0:
                            continue
                        assumptions = [literal if index < count else -literal
                                       for index, literal in enumerate(edges)]
                        self.assertEqual(
                            solver.solve(assumptions=assumptions), expected,
                            (degree, minimum, maximum, count))

    def test_direct_verifier_checks_each_block(self):
        for degree in (18, 19, 20):
            adjacency = [0] * SAT.N
            circulant_block(adjacency, range(degree), 12)
            circulant_block(adjacency, range(degree, SAT.N), 10)
            result = SAT.verify_block_internal_degree_bounds(
                adjacency, degree)
            self.assertEqual(result["a_internal_degrees"], [12] * degree)
            self.assertEqual(result["b_internal_degrees"],
                             [10] * (SAT.N - degree))

            bad_a = adjacency.copy()
            for vertex in range(1, 15):
                bad_a[0] |= 1 << vertex
                bad_a[vertex] |= 1
            with self.assertRaisesRegex(
                    ValueError, "A-block internal degree bound violated"):
                SAT.verify_block_internal_degree_bounds(bad_a, degree)

            empty_b = adjacency.copy()
            for u in range(degree, SAT.N):
                for v in range(degree, SAT.N):
                    empty_b[u] &= ~(1 << v)
            with self.assertRaisesRegex(
                    ValueError, "B-block internal degree bound violated"):
                SAT.verify_block_internal_degree_bounds(empty_b, degree)

    def test_constraints_are_default_on_with_diagnostic_opt_out(self):
        for j in (2, 13):
            bounded, bounded_top = SAT.core_clauses(20, None, j)
            unbounded, unbounded_top = SAT.core_clauses(
                20, None, j, enforce_block_degree_bounds=False)
            self.assertGreater(len(bounded), len(unbounded))
            self.assertGreater(bounded_top, unbounded_top)

    def test_exact_a_option_remains_compatible(self):
        clauses, top = SAT.core_clauses(
            20, None, 2, a_edge_count=68,
            enforce_block_pair_common_bounds=False,
            enforce_global_pair_common_bounds=False,
            enforce_cross_block_pair_common_bounds=False,
            enforce_distinguished_cross_pair_degree_bounds=False,
            enforce_singleton_second_order_bounds=False)
        self.assertEqual((len(clauses), top), (730802, 360785))


if __name__ == "__main__":
    unittest.main()
