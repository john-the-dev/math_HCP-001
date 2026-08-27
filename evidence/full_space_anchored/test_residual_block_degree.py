#!/usr/bin/env python3
"""Tests for residual-block Ramsey degree bounds."""
from pathlib import Path
from types import SimpleNamespace
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


class ResidualBlockDegreeTests(unittest.TestCase):
    def test_production_generator_covers_every_admissible_case(self):
        original = SAT.CardEnc.atmost
        try:
            for degree in (18, 19, 20):
                j_minimum, j_maximum = SAT.a_internal_bounds(degree)
                k_minimum, k_maximum = SAT.b_minimum_internal_bounds(degree)
                for j in range(j_minimum, j_maximum + 1):
                    for k in range(k_minimum, k_maximum + 1):
                        calls = []

                        def record(literals, bound, vpool, encoding):
                            calls.append((tuple(literals), bound, vpool,
                                          encoding))
                            return SimpleNamespace(clauses=[])

                        SAT.CardEnc.atmost = record
                        pool = IDPool()
                        clauses = SAT.residual_block_degree_clauses(
                            degree, j, k, pool)
                        self.assertEqual(clauses, [])
                        blocks = (
                            (range(1, j + 1), False),
                            (range(j + 1, degree), True),
                            (range(degree + 1, degree + k + 1), False),
                            (range(degree + k + 1, SAT.N), True),
                        )
                        expected = []
                        for vertices, neighbors in blocks:
                            vertices = list(vertices)
                            if len(vertices) <= 9:
                                continue
                            for u in vertices:
                                expected.append((tuple(
                                    SAT.edge_var(u, v) if neighbors
                                    else -SAT.edge_var(u, v)
                                    for v in vertices if v != u),
                                    8, pool, SAT.EncType.seqcounter))
                        self.assertEqual(calls, expected, (degree, j, k))
        finally:
            SAT.CardEnc.atmost = original

    def test_direct_verifier_rejects_each_residual_block(self):
        with self.assertRaisesRegex(ValueError, "a_plus"):
            SAT.verify_residual_block_degree_bounds(
                [0] * SAT.N, 20, 13, 8)

        with self.assertRaisesRegex(ValueError, "b_plus"):
            SAT.verify_residual_block_degree_bounds(
                [0] * SAT.N, 20, 2, 13)

        adjacency = [0] * SAT.N
        for v in range(4, 13):
            set_edge(adjacency, 3, v)
        with self.assertRaisesRegex(ValueError, "a_minus"):
            SAT.verify_residual_block_degree_bounds(
                adjacency, 20, 2, 13)

        adjacency = [0] * SAT.N
        for u, v in SAT.combinations(range(1, 14), 2):
            set_edge(adjacency, u, v)
        for v in range(30, 39):
            set_edge(adjacency, 29, v)
        with self.assertRaisesRegex(ValueError, "b_minus"):
            SAT.verify_residual_block_degree_bounds(
                adjacency, 20, 13, 8)

    def test_actual_counter_projection_for_both_signed_polarities(self):
        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        positive_clauses = SAT.residual_block_degree_clauses(
            20, 2, 8, pool)
        positive_edges = [SAT.edge_var(u, v)
                          for block in (range(3, 20), range(29, SAT.N))
                          for u, v in SAT.combinations(block, 2)]
        with Solver(name="glucose4", bootstrap_with=positive_clauses) as solver:
            self.assertTrue(solver.solve(
                assumptions=[-edge for edge in positive_edges]))
            violation = {SAT.edge_var(3, v) for v in range(4, 13)}
            self.assertFalse(solver.solve(assumptions=[
                edge if edge in violation else -edge
                for edge in positive_edges]))

        pool = IDPool(start_from=len(SAT.PAIRS) + 1)
        negative_clauses = SAT.residual_block_degree_clauses(
            20, 13, 13, pool)
        negative_edges = [SAT.edge_var(u, v)
                          for block in (range(1, 14), range(21, 34))
                          for u, v in SAT.combinations(block, 2)]
        with Solver(name="glucose4", bootstrap_with=negative_clauses) as solver:
            self.assertTrue(solver.solve(assumptions=negative_edges))
            violation = {SAT.edge_var(1, v) for v in range(2, 11)}
            self.assertFalse(solver.solve(assumptions=[
                -edge if edge in violation else edge
                for edge in negative_edges]))

    def test_default_activation_and_j_only_noop(self):
        bounded, bounded_top = SAT.core_clauses(
            20, a_internal_degree=2, b_internal_degree=8)
        unbounded, unbounded_top = SAT.core_clauses(
            20, a_internal_degree=2, b_internal_degree=8,
            enforce_residual_block_degree_bounds=False)
        self.assertEqual(len(bounded) - len(unbounded), 2956)
        self.assertEqual(bounded_top - unbounded_top, 1504)

        j_only = SAT.core_clauses(20, a_internal_degree=2)
        j_only_disabled = SAT.core_clauses(
            20, a_internal_degree=2,
            enforce_residual_block_degree_bounds=False)
        self.assertEqual(j_only, j_only_disabled)


if __name__ == "__main__":
    unittest.main()
