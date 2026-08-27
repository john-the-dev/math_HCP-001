#!/usr/bin/env python3
"""Tests for residual-block Ramsey degree bounds."""
from pathlib import Path
from types import SimpleNamespace
from contextlib import redirect_stdout
import importlib.util
import io
import json
import tempfile
import unittest
from unittest.mock import patch

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

    def test_solve_provenance_matrix_matches_forwarded_flags(self):
        class FakeSolver:
            def __init__(self, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def add_clause(self, _clause):
                pass

            def solve(self):
                return True

            def accum_stats(self):
                return {}

            def get_model(self):
                return []

        cases = (
            (None, None, False, False, "not-applicable", False, False),
            (2, None, False, False, "not-applicable", False, False),
            (None, 8, False, False, "not-applicable", False, False),
            (2, 8, False, False, "enabled", True, True),
            (2, 8, True, False, "disabled", False, True),
            (2, 8, False, True, "disabled", True, False),
        )
        for j, k, cross_off, residual_off, state, cross_active, residual_active in cases:
            for cross_pair_off in (False, True):
                for cross_pair_degree_off in (False, True):
                    with self.subTest(
                            j=j, k=k, cross_off=cross_off,
                            residual_off=residual_off,
                            cross_pair_off=cross_pair_off,
                            cross_pair_degree_off=cross_pair_degree_off):
                        self._check_solve_provenance_case(
                            j, k, cross_off, residual_off, state,
                            cross_active, residual_active, cross_pair_off,
                            cross_pair_degree_off, FakeSolver)

    def _check_solve_provenance_case(
            self, j, k, cross_off, residual_off, state, cross_active,
            residual_active, cross_pair_off, cross_pair_degree_off,
            fake_solver_class):
        core_calls = []
        verify_calls = []

        def fake_core(**kwargs):
            core_calls.append(kwargs)
            return [], len(SAT.PAIRS)

        def fake_verify(*_args, **kwargs):
            verify_calls.append(kwargs)
            return {}

        with tempfile.TemporaryDirectory() as raw_temp:
            result_path = Path(raw_temp) / "result.json"
            args = SimpleNamespace(
                degree=20, edges=None, a_internal_degree=j,
                a_total_degree=None, b_internal_degree=k,
                a_edges=None, no_block_edge_bounds=False,
                no_block_degree_bounds=False,
                no_block_pair_common_bounds=False,
                no_global_pair_common_bounds=False,
                no_cross_block_pair_common_bounds=cross_pair_off,
                no_distinguished_cross_pair_degree_bounds=(
                    cross_pair_degree_off),
                no_distinguished_cross_triple_bounds=cross_off,
                no_residual_block_degree_bounds=residual_off,
                solver="glucose4", cnf=None, proof=None,
                json=str(result_path))
            output = io.StringIO()
            with (patch.object(SAT, "core_clauses", fake_core),
                  patch.object(SAT, "verify_model", fake_verify),
                  patch.object(SAT, "model_adjacency",
                               return_value=[0] * SAT.N),
                  patch.object(SAT, "five_set_clauses",
                               return_value=iter(([], []))),
                  patch.object(SAT, "comb", return_value=1),
                  patch.object(SAT, "Solver", fake_solver_class),
                  redirect_stdout(output)):
                SAT.solve(args)
            record = json.loads(result_path.read_text())
        self.assertIn(
            f"distinguished_cross_triple_bounds={state if cross_off == residual_off else 'disabled' if cross_off else 'enabled'}",
            output.getvalue())
        residual_state = ("disabled" if residual_off else
                          "enabled" if j is not None and k is not None
                          else "not-applicable")
        self.assertIn(f"residual_block_degree_bounds={residual_state}",
                      output.getvalue())
        cross_pair_state = "disabled" if cross_pair_off else "enabled"
        self.assertIn(f"cross_block_pair_common_bounds={cross_pair_state}",
                      output.getvalue())
        a_pair_active = not cross_pair_degree_off and j is not None
        b_pair_active = not cross_pair_degree_off and k is not None
        pair_state = SAT.configured_side_bound_state(
            cross_pair_degree_off, j is not None, k is not None)
        self.assertIn(
            f"distinguished_cross_pair_degree_bounds={pair_state}",
            output.getvalue())
        for call in core_calls + verify_calls:
            self.assertEqual(
                call["enforce_cross_block_pair_common_bounds"],
                not cross_pair_off)
            self.assertEqual(
                call["enforce_distinguished_cross_triple_bounds"],
                cross_active)
            self.assertEqual(
                call["enforce_residual_block_degree_bounds"],
                residual_active)
            self.assertEqual(
                call["enforce_distinguished_cross_pair_degree_bounds"],
                a_pair_active or b_pair_active)
        self.assertEqual(record["distinguished_cross_triple_bounds"],
                         cross_active)
        self.assertEqual(record["residual_block_degree_bounds"],
                         residual_active)
        self.assertEqual(record["cross_block_pair_common_bounds"],
                         not cross_pair_off)
        self.assertEqual(record["distinguished_cross_pair_degree_bounds"],
                         a_pair_active or b_pair_active)
        self.assertEqual(record["distinguished_cross_pair_degree_a"],
                         a_pair_active)
        self.assertEqual(record["distinguished_cross_pair_degree_b"],
                         b_pair_active)


if __name__ == "__main__":
    unittest.main()
