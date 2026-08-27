#!/usr/bin/env python3
"""Tests for distinguished cross-block triple common-set bounds."""
from pathlib import Path
import importlib.util
import unittest

from pysat.formula import IDPool


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "anchored_sat", HERE / "anchored_sat.py")
SAT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAT)


def set_edge(adjacency, u, v):
    adjacency[u] |= 1 << v
    adjacency[v] |= 1 << u


class DistinguishedCrossTripleTests(unittest.TestCase):
    def test_production_generator_covers_exact_fixed_triples(self):
        calls = []
        original = SAT._conditional_conjunction_atmost

        def record(conjunctions, bound, condition, pool,
                   encoding=SAT.EncType.seqcounter):
            calls.append((tuple(conjunctions), bound, condition, encoding))
            return []

        SAT._conditional_conjunction_atmost = record
        try:
            clauses = SAT.distinguished_cross_triple_clauses(
                20, 2, 8, IDPool())
        finally:
            SAT._conditional_conjunction_atmost = original
        self.assertEqual(clauses, [])
        self.assertEqual(len(calls), 1 + 78)

        a_call = calls[0]
        self.assertEqual(a_call, (
            tuple((SAT.edge_var(0, w), SAT.edge_var(1, w),
                   SAT.edge_var(2, w)) for w in range(20, SAT.N)),
            3, SAT.edge_var(1, 2), SAT.EncType.seqcounter))

        expected_pairs = list(SAT.combinations(range(29, SAT.N), 2))
        for call, (u, v) in zip(calls[1:], expected_pairs):
            self.assertEqual(call, (
                tuple((-SAT.edge_var(20, w), -SAT.edge_var(u, w),
                       -SAT.edge_var(v, w)) for w in range(20)),
                3, -SAT.edge_var(u, v), SAT.EncType.seqcounter))

    def test_direct_verifier_rejects_both_sides(self):
        adjacency = [0] * SAT.N
        for edge in ((0, 1), (0, 2), (1, 2)):
            set_edge(adjacency, *edge)
        for w in range(20, 24):
            for u in (0, 1, 2):
                set_edge(adjacency, u, w)
        with self.assertRaisesRegex(ValueError, "distinguished A triple"):
            SAT.verify_distinguished_cross_triple_bounds(
                adjacency, 20, 2, 8)

        with self.assertRaisesRegex(ValueError, "distinguished B triple"):
            SAT.verify_distinguished_cross_triple_bounds(
                [0] * SAT.N, 20, 2, 8)

    def test_default_activation_and_exact_structural_delta(self):
        bounded, bounded_top = SAT.core_clauses(
            20, a_internal_degree=2, b_internal_degree=8)
        unbounded, unbounded_top = SAT.core_clauses(
            20, a_internal_degree=2, b_internal_degree=8,
            enforce_distinguished_cross_triple_bounds=False)
        self.assertEqual(len(bounded) - len(unbounded), 10760)
        self.assertEqual(bounded_top - unbounded_top, 5617)

        j_only, j_only_top = SAT.core_clauses(20, a_internal_degree=2)
        j_only_disabled, j_only_disabled_top = SAT.core_clauses(
            20, a_internal_degree=2,
            enforce_distinguished_cross_triple_bounds=False)
        self.assertEqual((len(j_only), j_only_top),
                         (len(j_only_disabled), j_only_disabled_top))


if __name__ == "__main__":
    unittest.main()
