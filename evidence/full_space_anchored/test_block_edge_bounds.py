#!/usr/bin/env python3
"""Regression tests for the R(4,5,n) block-edge constraints."""
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


def adjacency_with_block_counts(degree, a_count, b_count):
    adjacency = [0] * SAT.N
    for vertices, count in (
            (range(degree), a_count), (range(degree, SAT.N), b_count)):
        for u, v in list(SAT.combinations(vertices, 2))[:count]:
            adjacency[u] |= 1 << v
            adjacency[v] |= 1 << u
    return adjacency


class BlockEdgeBoundsTests(unittest.TestCase):
    def test_exact_derived_ranges(self):
        self.assertEqual(SAT.block_edge_bounds(18), ((50, 85), (144, 160)))
        self.assertEqual(SAT.block_edge_bounds(19), ((57, 92), (131, 152)))
        self.assertEqual(SAT.block_edge_bounds(20), ((68, 100), (117, 143)))

    def test_production_encoding_accepts_only_the_closed_ranges(self):
        for degree in (18, 19, 20):
            pool = IDPool(start_from=len(SAT.PAIRS) + 1)
            clauses = SAT.block_edge_clauses(degree, pool)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for edges, (minimum, maximum) in zip(
                        SAT.block_edges(degree), SAT.block_edge_bounds(degree)):
                    for count, expected in (
                            (minimum - 1, False), (minimum, True),
                            (maximum, True), (maximum + 1, False)):
                        assumptions = [literal if index < count else -literal
                                       for index, literal in enumerate(edges)]
                        self.assertEqual(solver.solve(assumptions=assumptions),
                                         expected)

    def test_exact_a_partition_accepts_only_requested_count(self):
        degree = 20
        a_edges = SAT.block_edges(degree)[0]
        for requested in (68, 100):
            pool = IDPool(start_from=len(SAT.PAIRS) + 1)
            clauses = SAT.block_edge_clauses(degree, pool, requested)
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                for count, expected in (
                        (requested - 1, False), (requested, True),
                        (requested + 1, False)):
                    assumptions = [literal if index < count else -literal
                                   for index, literal in enumerate(a_edges)]
                    self.assertEqual(solver.solve(assumptions=assumptions),
                                     expected)

    def test_exact_a_partition_rejects_out_of_range_values(self):
        for value in (67, 101):
            with self.assertRaisesRegex(ValueError,
                                        "A edge count must be in 68..100"):
                SAT.core_clauses(20, None, 2, a_edge_count=value)

    def test_direct_verifier_checks_both_blocks(self):
        for degree in (18, 19, 20):
            (a_minimum, _), (b_minimum, _) = SAT.block_edge_bounds(degree)
            adjacency = adjacency_with_block_counts(
                degree, a_minimum, b_minimum)
            self.assertEqual(
                SAT.verify_block_edge_bounds(adjacency, degree),
                {"a_edges": a_minimum, "b_edges": b_minimum})
            with self.assertRaisesRegex(ValueError,
                                        "A-block edge bound violated"):
                SAT.verify_block_edge_bounds(
                    adjacency_with_block_counts(
                        degree, a_minimum - 1, b_minimum), degree)
            a_maximum = SAT.block_edge_bounds(degree)[0][1]
            with self.assertRaisesRegex(ValueError,
                                        "B-block edge bound violated"):
                SAT.verify_block_edge_bounds(
                    adjacency_with_block_counts(
                        degree, a_minimum, b_minimum - 1), degree)
            b_maximum = SAT.block_edge_bounds(degree)[1][1]
            with self.assertRaisesRegex(ValueError,
                                        "A-block edge bound violated"):
                SAT.verify_block_edge_bounds(
                    adjacency_with_block_counts(
                        degree, a_maximum + 1, b_minimum), degree)
            with self.assertRaisesRegex(ValueError,
                                        "B-block edge bound violated"):
                SAT.verify_block_edge_bounds(
                    adjacency_with_block_counts(
                        degree, a_minimum, b_maximum + 1), degree)

    def test_direct_verifier_enforces_exact_a_partition(self):
        degree = 20
        adjacency = adjacency_with_block_counts(degree, 68, 117)
        needed = SAT.edge_bounds(degree)[0] - 68 - 117
        cross_edges = ((u, v) for u in range(degree)
                       for v in range(degree, SAT.N))
        for u, v in list(cross_edges)[:needed]:
            adjacency[u] |= 1 << v
            adjacency[v] |= 1 << u
        with self.assertRaisesRegex(ValueError, "A edge partition violated"):
            SAT.verify_model(adjacency, degree, a_edge_count=69)

    def test_constraints_are_default_on_for_d20_frontiers(self):
        for j in (2, 13):
            bounded, bounded_top = SAT.core_clauses(
                20, None, j, enforce_block_degree_bounds=False,
                enforce_block_pair_common_bounds=False,
                enforce_global_pair_common_bounds=False)
            unbounded, unbounded_top = SAT.core_clauses(
                20, None, j, enforce_block_edge_bounds=False,
                enforce_block_degree_bounds=False,
                enforce_block_pair_common_bounds=False,
                enforce_global_pair_common_bounds=False)
            self.assertEqual((len(unbounded), unbounded_top),
                             (634614, 312247))
            self.assertEqual((len(bounded), bounded_top),
                             (720934, 355465))


if __name__ == "__main__":
    unittest.main()
