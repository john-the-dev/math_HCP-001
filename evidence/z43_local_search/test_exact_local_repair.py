#!/usr/bin/env python3
"""Direct checks for the local-repair CNF generator."""

import hashlib
import itertools
import unittest

import exact_local_repair as repair


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


if __name__ == "__main__":
    unittest.main()
