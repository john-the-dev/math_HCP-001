#!/usr/bin/env python3
"""Direct checks for the local-repair CNF generator."""

import hashlib
import itertools
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import exact_local_repair as repair
import verify_exact_local_evidence as evidence


def satisfies(clause, assignment):
    return any(assignment[abs(literal)] == (literal > 0) for literal in clause)


class ExactLocalRepairTest(unittest.TestCase):
    def test_seed_is_bound_to_published_search_output(self):
        raw = repair.seed_graph_text().encode()
        self.assertEqual(len(raw.splitlines()) - 1, 454)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "b13c0207149ff618acef13c822a4841ef21d60782dd40b94317887ad2d28beec",
        )

    def test_sequential_counter_truth_table(self):
        for size in range(1, 5):
            for bound in range(size + 1):
                inputs = list(range(1, size + 1))
                first_aux = size + 1
                clauses = list(repair.at_most_clauses(inputs, bound, first_aux))
                aux_count = size * bound if 0 < bound < size else 0
                for bits in itertools.product((False, True), repeat=size):
                    extendable = False
                    for aux in itertools.product((False, True), repeat=aux_count):
                        assignment = {i + 1: value for i, value in enumerate(bits + aux)}
                        if all(satisfies(clause, assignment) for clause in clauses):
                            extendable = True
                            break
                    self.assertEqual(extendable, sum(bits) <= bound, (size, bound, bits))

    def test_base_model_has_two_clauses_per_five_set(self):
        model = repair.local_model(903)
        first = next(model)
        second = next(model)
        self.assertEqual(len(first), 10)
        self.assertEqual(len(second), 10)
        self.assertTrue(all(literal < 0 for literal in first))
        self.assertTrue(all(literal > 0 for literal in second))

    def test_all_preserved_checker_transcripts_are_verified(self):
        logs = Path(__file__).with_name("verification_logs")
        self.assertEqual(
            [path.name for path in sorted(
                logs.glob("*.log"),
                key=lambda path: int(path.name[1:].split(".", 1)[0]))],
            [f"r{radius}.drat-trim.log" for radius in range(1, 14)],
        )
        for path in logs.glob("*.log"):
            self.assertIn("\ns VERIFIED\n", path.read_text())

    def test_documented_hash_table_matches_verifier(self):
        evidence.verify()

    def test_runner_fails_closed_when_solver_times_out(self):
        runner = HERE / "run_exact_local_repair.sh"
        with tempfile.TemporaryDirectory() as raw_temp:
            temp = Path(raw_temp)
            fake_python = temp / "python3"
            fake_solver = temp / "cadical"
            checker_marker = temp / "checker-ran"
            fake_checker = temp / "drat-trim"
            fake_python.write_text("#!/bin/sh\nexit 0\n")
            fake_solver.write_text("#!/bin/sh\nexit 0\n")
            fake_checker.write_text(
                f"#!/bin/sh\ntouch '{checker_marker}'\nexit 0\n")
            for executable in (fake_python, fake_solver, fake_checker):
                executable.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{temp}:{environment['PATH']}"
            completed = subprocess.run(
                [runner, "11", temp / "output", fake_solver, fake_checker,
                 "binary"],
                text=True, capture_output=True, env=environment)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("did not prove UNSAT (exit 0)", completed.stderr)
            self.assertFalse(checker_marker.exists())

    def test_runner_forwards_valid_timeout_and_rejects_bad_value(self):
        runner = HERE / "run_exact_local_repair.sh"
        with tempfile.TemporaryDirectory() as raw_temp:
            temp = Path(raw_temp)
            solver_arguments = temp / "solver-args"
            fake_python = temp / "python3"
            fake_solver = temp / "cadical"
            fake_checker = temp / "drat-trim"
            fake_python.write_text("#!/bin/sh\nexit 0\n")
            fake_solver.write_text(
                f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{solver_arguments}'\n"
                "exit 0\n")
            fake_checker.write_text("#!/bin/sh\nexit 99\n")
            for executable in (fake_python, fake_solver, fake_checker):
                executable.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{temp}:{environment['PATH']}"
            completed = subprocess.run(
                [runner, "11", temp / "output", fake_solver, fake_checker,
                 "binary", "3600"],
                text=True, capture_output=True, env=environment)
            self.assertEqual(completed.returncode, 1)
            arguments = solver_arguments.read_text().splitlines()
            self.assertIn("-t", arguments)
            self.assertEqual(arguments[arguments.index("-t") + 1], "3600")

            completed = subprocess.run(
                [runner, "11", temp / "bad", fake_solver, fake_checker,
                 "binary", "0"],
                text=True, capture_output=True, env=environment)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("timeout must be a positive integer",
                          completed.stderr)


if __name__ == "__main__":
    unittest.main()
