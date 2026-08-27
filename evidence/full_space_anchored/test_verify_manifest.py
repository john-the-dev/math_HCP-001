#!/usr/bin/env python3
"""Regression tests for fail-closed manifest and completion verification."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "verify_manifest", HERE / "verify_manifest.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = VERIFY.read_json(HERE / "j_partition_manifest.json")

    def assertRejected(self, data, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            VERIFY.verify_manifest(data)

    def test_valid_manifest(self):
        self.assertEqual(len(VERIFY.verify_manifest(self.valid)), 39)

    def test_missing_row_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"].pop()
        data["partition_count"] -= 1
        self.assertRejected(data, "case cover mismatch")

    def test_duplicate_row_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"].append(deepcopy(data["partitions"][0]))
        data["partition_count"] += 1
        self.assertRejected(data, "duplicate id")

    def test_bad_bound_is_rejected(self):
        data = deepcopy(self.valid)
        data["partitions"][0]["edge_min"] -= 1
        self.assertRejected(data, "edge_min must be")

    def test_unsat_claim_without_artifacts_is_rejected(self):
        ids = VERIFY.verify_manifest(self.valid)
        ledger = {"schema": 1, "claims": [
            {"id": "d18-j0", "status": "UNSAT", "artifacts": {}}
        ]}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError, "missing cnf record"):
                VERIFY.verify_ledger(path, ids)

    def make_claim(self, directory, checker_text="s VERIFIED\n"):
        artifacts = {}
        for kind, name, content in (
                ("cnf", "case.cnf", "p cnf 1 2\n1 0\n-1 0\n"),
                ("proof", "case.drat", ""),
                ("checker", "case.check.txt", checker_text)):
            path = directory / name
            path.write_text(content)
            artifacts[kind] = {
                "path": name,
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
        return {"id": "d18-j0", "status": "UNSAT", "artifacts": artifacts}

    def test_checked_unsat_claim_passes(self):
        ids = VERIFY.verify_manifest(self.valid)
        with TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            ledger = {"schema": 1, "claims": [self.make_claim(directory)]}
            path = directory / "ledger.json"
            path.write_text(json.dumps(ledger))
            self.assertEqual(VERIFY.verify_ledger(path, ids), {"d18-j0"})

    def test_bad_hash_is_rejected(self):
        ids = VERIFY.verify_manifest(self.valid)
        with TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            claim = self.make_claim(directory)
            claim["artifacts"]["proof"]["sha256"] = "0" * 64
            path = directory / "ledger.json"
            path.write_text(json.dumps({"schema": 1, "claims": [claim]}))
            with self.assertRaisesRegex(ValueError, "proof sha256 mismatch"):
                VERIFY.verify_ledger(path, ids)

    def test_checker_must_have_verified_status_line(self):
        ids = VERIFY.verify_manifest(self.valid)
        with TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            claim = self.make_claim(directory, "s NOT VERIFIED\n")
            path = directory / "ledger.json"
            path.write_text(json.dumps({"schema": 1, "claims": [claim]}))
            with self.assertRaisesRegex(ValueError, "lacks an exact"):
                VERIFY.verify_ledger(path, ids)


if __name__ == "__main__":
    unittest.main()
