#!/usr/bin/env python3
"""Exhaustively audit the guarded conjunction-cardinality encoding."""
from itertools import product

from pysat.formula import IDPool
from pysat.solvers import Solver

from anchored_sat import conditional_conjunction_atmost


def literal_value(literal, values):
    value = values[abs(literal) - 1]
    return value if literal > 0 else not value


def audit(conjunctions, bound, guard, source_variables):
    clauses = []
    pool = IDPool(start_from=source_variables + 1)
    conditional_conjunction_atmost(
        clauses, pool, conjunctions, bound, guard)
    checked = 0
    with Solver(name="cadical195", bootstrap_with=clauses) as solver:
        for values in product((False, True), repeat=source_variables):
            assumptions = [index if value else -index
                           for index, value in enumerate(values, 1)]
            active = all(literal_value(literal, values) for literal in guard)
            count = sum(all(literal_value(literal, values)
                            for literal in conjunction)
                        for conjunction in conjunctions)
            expected = not active or count <= bound
            actual = solver.solve(assumptions=assumptions)
            if actual != expected:
                raise AssertionError((values, expected, actual))
            checked += 1
    return checked, len(clauses), pool.top


def main():
    cases = (
        (((1, 2), (1, -3), (-2, 3)), 1, (4,), 4),
        (((-1, -2), (-1, 3), (2, -3)), 1, (-4,), 4),
        (((1, 2, 3), (1, -2, 4), (-1, 3, 4)), 1, (5, 6, -7), 7),
    )
    total = 0
    for index, case in enumerate(cases, 1):
        checked, clauses, top = audit(*case)
        total += checked
        print(f"case={index} assignments={checked} clauses={clauses} top={top}")
    print(f"PASS assignments={total}")


if __name__ == "__main__":
    main()
