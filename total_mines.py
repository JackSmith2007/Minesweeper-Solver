"extends solver.py with one extra piece of information: the total number of mines"
"solver.py is left untouched; this module reuses its functions and adds one constraint"
from solver import build_constraints, propagate, subtract, solve


def count_cells(grid):
    "return (set of unknown cells, number of flagged cells) for the board"
    unknown = set()
    flags = 0
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "?":
                unknown.add((r, c))
            elif ch == "F":
                flags += 1
    return unknown, flags


def solve_with_total(grid, total_mines=None):
    '''Solve the board, optionally using the total mine count.

    If total_mines is None this is exactly solver.solve(grid).
    Otherwise one extra "global" constraint is added before solving:
        the unknown cells together hold (total_mines - flagged) mines.
    That is just another [set_of_cells, mine_count] pair, so the existing
    propagate/subtract rules handle it with no special cases. Because every
    number constraint is a subset of the global one, subtract() turns it into
    "the cells no number touches hold the leftover mines", which is exactly the
    deduction a human makes from the mine counter.

    Raises ValueError if total_mines is impossible for this board.'''

    "no count given: fall back to the plain solver"
    if total_mines is None:
        return solve(grid)

    unknown, flags = count_cells(grid)
    "mines still hidden = mines on the board - mines the user already flagged"
    remaining = total_mines - flags
    "sanity checks: the count must be something the board can actually hold"
    if remaining < 0:
        raise ValueError(f"{flags} cells are flagged but only {total_mines} mines exist.")
    if remaining > len(unknown):
        raise ValueError(
            f"{remaining} mines cannot fit in {len(unknown)} unrevealed cells."
        )

    constraints = build_constraints(grid)
    "the global constraint: all unknown cells, remaining mine count"
    "skipped when there are no unknowns, because an empty constraint says nothing"
    if unknown:
        constraints.append([set(unknown), remaining])

    "from here on this is the same loop as solver.solve()"
    mines, safes = set(), set()
    while True:
        m, s = propagate(constraints)
        mines |= m
        safes |= s
        if not subtract(constraints):
            break
    return mines, safes
