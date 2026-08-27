#!/usr/bin/env python3
"""Tests for the distinguished-A total-degree refinement."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import random
from types import SimpleNamespace
import unittest


HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SAT = load("anchored_sat")
VERIFY = load("verify_a_total_manifest")


def random_adjacency(seed):
    rng = random.Random(seed)
    adjacency = [0] * SAT.N
    for u in range(SAT.N):
        for v in range(u + 1, SAT.N):
            if rng.randrange(2):
                adjacency[u] |= 1 << v
                adjacency[v] |= 1 << u
    return adjacency


def relabel(adjacency, old_for_new):
    new_for_old = {old: new for new, old in enumerate(old_for_new)}
    result = [0] * len(adjacency)
    for new_u, old_u in enumerate(old_for_new):
        for old_v in range(len(adjacency)):
            if (adjacency[old_u] >> old_v) & 1:
                result[new_u] |= 1 << new_for_old[old_v]
    return result


def canonicalize_a(adjacency, degree):
    degrees = [row.bit_count() for row in adjacency]
    chosen = min(range(degree), key=lambda u: degrees[u])
    neighbors = sorted(
        (u for u in range(degree)
         if u != chosen and (adjacency[chosen] >> u) & 1),
        key=lambda u: degrees[u])
    nonneighbors = sorted(
        (u for u in range(degree)
         if u != chosen and not (adjacency[chosen] >> u) & 1),
        key=lambda u: degrees[u])
    order = [chosen] + neighbors + nonneighbors + list(range(degree, SAT.N))
    result = relabel(adjacency, order)
    return result, len(neighbors), degrees[chosen]


class ATotalDegreeTests(unittest.TestCase):
    def test_exact_ranges(self):
        for degree, lower in ((18, 17), (19, 18), (20, 19)):
            for j in range(SAT.a_internal_bounds(degree)[0], 14):
                self.assertEqual(SAT.a_total_degree_bounds(degree, j),
                                 (lower, 23))

    def test_every_a_orbit_has_a_representative_with_recorded_t(self):
        for degree in (18, 19, 20):
            for seed in range(8):
                adjacency, j, t = canonicalize_a(
                    random_adjacency(100 * degree + seed), degree)
                self.assertEqual(
                    SAT.verify_distinguished_a(adjacency, degree, j, t), t)

    def test_verifier_rejects_wrong_total_degree(self):
        adjacency, j, t = canonicalize_a(random_adjacency(2001), 20)
        with self.assertRaisesRegex(ValueError, "A-total degree"):
            SAT.verify_distinguished_a(adjacency, 20, j, t + 1)

    def test_formula_validation_and_exact_degree_encoding(self):
        with self.assertRaisesRegex(ValueError, "requires A-internal"):
            SAT.core_clauses(20, a_total_degree=19)
        with self.assertRaisesRegex(ValueError, "must be in 19..23"):
            SAT.core_clauses(20, a_internal_degree=2, a_total_degree=18)
        base, base_top = SAT.core_clauses(20, a_internal_degree=2)
        exact, exact_top = SAT.core_clauses(
            20, a_internal_degree=2, a_total_degree=19)
        self.assertGreater(len(exact), len(base))
        self.assertGreater(exact_top, base_top)

    def test_production_equality_targets_exact_distinguished_incidence(self):
        calls = []
        original = SAT.CardEnc.equals

        def record(literals, bound, vpool, encoding):
            calls.append((tuple(literals), bound, vpool, encoding))
            return SimpleNamespace(clauses=[])

        SAT.CardEnc.equals = record
        try:
            SAT.core_clauses(
                20, a_internal_degree=2, b_internal_degree=8,
                a_total_degree=19)
        finally:
            SAT.CardEnc.equals = original
        self.assertEqual(len(calls), 1)
        literals, bound, _, encoding = calls[0]
        self.assertEqual(literals,
                         tuple(SAT.edge_var(0, vertex)
                               for vertex in range(1, SAT.N)))
        self.assertEqual(bound, 19)
        self.assertEqual(encoding, SAT.EncType.seqcounter)

    def test_model_verifier_rejects_invalid_total_degree_contract_first(self):
        with self.assertRaisesRegex(ValueError, "requires A-internal"):
            SAT.verify_model([0] * SAT.N, 20, a_total_degree=19)
        with self.assertRaisesRegex(ValueError, "must be in 19..23"):
            SAT.verify_model(
                [0] * SAT.N, 20, a_internal_degree=2, a_total_degree=18)


class ATotalDegreeManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = json.loads(
            (HERE / "j_t_k_partition_manifest.json").read_text())

    def assertRejected(self, data, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            VERIFY.verify_manifest(data)

    def test_exact_complete_cover(self):
        self.assertEqual(len(VERIFY.verify_manifest(self.valid)), 1142)

    def test_missing_case_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"].pop()
        data["partition_count"] -= 1
        self.assertRejected(data, "case cover mismatch")

    def test_bad_total_degree_bound_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"][0]["a_total_degree_max"] = 24
        self.assertRejected(data, "a_total_degree_max must be 23")

    def test_bad_artifact_name_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"][0]["proof"] = "wrong.drat"
        self.assertRejected(data, "invalid proof filename")


if __name__ == "__main__":
    unittest.main()
