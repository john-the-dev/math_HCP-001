#!/usr/bin/env python3
"""Tests for the exhaustive distinguished-B symmetry partition."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import random
import unittest

from pysat.formula import IDPool
from pysat.solvers import Solver


HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SAT = load("anchored_sat")
VERIFY = load("verify_b_manifest")


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


def canonicalize_b(adjacency, degree):
    block_b = list(range(degree, SAT.N))
    internal = {
        u: sum((adjacency[u] >> v) & 1 for v in block_b if v != u)
        for u in block_b
    }
    chosen = min(block_b, key=lambda u: internal[u])
    full_degrees = [row.bit_count() for row in adjacency]
    neighbors = sorted(
        (u for u in block_b if u != chosen and (adjacency[chosen] >> u) & 1),
        key=lambda u: full_degrees[u])
    nonneighbors = sorted(
        (u for u in block_b if u != chosen and not (adjacency[chosen] >> u) & 1),
        key=lambda u: full_degrees[u])
    order = list(range(degree)) + [chosen] + neighbors + nonneighbors
    return relabel(adjacency, order), internal[chosen]


class DistinguishedBTests(unittest.TestCase):
    def test_exact_k_ranges(self):
        self.assertEqual(SAT.b_minimum_internal_bounds(18), (10, 13))
        self.assertEqual(SAT.b_minimum_internal_bounds(19), (9, 13))
        self.assertEqual(SAT.b_minimum_internal_bounds(20), (8, 13))

    def test_every_b_orbit_has_the_required_representative(self):
        for degree in (18, 19, 20):
            for seed in range(8):
                adjacency, k = canonicalize_b(
                    random_adjacency(100 * degree + seed), degree)
                SAT.verify_distinguished_b(adjacency, degree, k)

    def test_model_verifier_rejects_wrong_fixed_neighborhood(self):
        degree = 20
        adjacency, k = canonicalize_b(random_adjacency(2001), degree)
        neighbor = degree + 1
        nonneighbor = degree + k + 1
        adjacency[degree] ^= (1 << neighbor) | (1 << nonneighbor)
        adjacency[neighbor] ^= 1 << degree
        adjacency[nonneighbor] ^= 1 << degree
        with self.assertRaisesRegex(ValueError, "fixed distinguished B"):
            SAT.verify_distinguished_b(adjacency, degree, k)

    def test_model_verifier_rejects_nonminimum_vertex(self):
        degree = 20
        adjacency, k = canonicalize_b(random_adjacency(2002), degree)
        target = degree + k + 1
        for vertex in range(degree + 1, SAT.N):
            if vertex != target and (adjacency[target] >> vertex) & 1:
                adjacency[target] &= ~(1 << vertex)
                adjacency[vertex] &= ~(1 << target)
        with self.assertRaisesRegex(ValueError, "not minimum-internal-degree"):
            SAT.verify_distinguished_b(adjacency, degree, k)

    def test_fixed_neighborhood_is_encoded(self):
        degree, j, k = 20, 2, 8
        clauses, _ = SAT.core_clauses(
            degree, a_internal_degree=j, b_internal_degree=k)
        units = {clause[0] for clause in clauses if len(clause) == 1}
        for vertex in range(degree + 1, SAT.N):
            literal = SAT.edge_var(degree, vertex)
            self.assertIn(literal if vertex <= degree + k else -literal, units)

    def test_internal_degree_comparator_semantics(self):
        degree = 20
        vertices = range(degree, SAT.N)
        u, w = degree, degree + 1
        rng = random.Random(7)
        for _ in range(20):
            pool = IDPool(start_from=len(SAT.PAIRS) + 1)
            clauses = SAT.internal_degree_leq_clauses(u, w, vertices, pool)
            assignment = {}
            for x in vertices:
                if x not in (u, w):
                    assignment[SAT.edge_var(u, x)] = bool(rng.randrange(2))
                    assignment[SAT.edge_var(w, x)] = bool(rng.randrange(2))
            assumptions = [var if value else -var
                           for var, value in assignment.items()]
            expected = (sum(assignment[SAT.edge_var(u, x)]
                            for x in vertices if x not in (u, w))
                        <= sum(assignment[SAT.edge_var(w, x)]
                               for x in vertices if x not in (u, w)))
            with Solver(name="cadical195", bootstrap_with=clauses) as solver:
                self.assertEqual(solver.solve(assumptions=assumptions), expected)

    def test_bad_k_is_rejected_before_formula_construction(self):
        for degree, k in ((18, 9), (20, 14)):
            with self.assertRaisesRegex(ValueError, "minimum B-internal degree"):
                SAT.core_clauses(degree, a_internal_degree=2,
                                 b_internal_degree=k)

    def test_existing_manifests_are_byte_stable(self):
        modes = (("j-only", "j_partition_manifest.json"),
                 ("edge-j", "partition_manifest.json"),
                 ("a-edge-j", "a_edge_partition_manifest.json"))
        with TemporaryDirectory() as directory:
            for mode, filename in modes:
                path = Path(directory) / filename
                SAT.write_manifest(path, mode)
                self.assertEqual(path.read_bytes(), (HERE / filename).read_bytes())


class DistinguishedBManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = VERIFY.read_json(HERE / "j_k_partition_manifest.json")

    def assertRejected(self, data, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            VERIFY.verify_manifest(data)

    def test_valid_manifest(self):
        self.assertEqual(len(VERIFY.verify_manifest(self.valid)), 193)

    def test_missing_case_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"].pop()
        data["partition_count"] -= 1
        self.assertRejected(data, "case cover mismatch")

    def test_duplicate_case_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"].append(deepcopy(data["partitions"][0]))
        data["partition_count"] += 1
        self.assertRejected(data, "duplicate id")

    def test_bad_k_bound_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"][0]["b_internal_degree_max"] = 14
        self.assertRejected(data, "b_internal_degree_max must be 13")

    def test_bad_artifact_name_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"][0]["proof"] = "wrong.drat"
        self.assertRejected(data, "invalid proof filename")

    def test_unchecked_unsat_claim_is_rejected(self):
        ids = VERIFY.verify_manifest(self.valid)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps({"schema": 1, "claims": [{
                "id": "d18-j0-k10", "status": "UNSAT", "artifacts": {}
            }]}))
            with self.assertRaisesRegex(ValueError, "missing cnf record"):
                VERIFY.BASE.verify_ledger(path, ids)


if __name__ == "__main__":
    unittest.main()
