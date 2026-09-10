# Minesweeper Solver

You enter a minesweeper position, and the app reports every cell that the position logically determines to be a mine or safe. Anything it cannot prove either way is left as unknown.

## Why "unknown" exists

Some positions are genuinely undecidable from the visible information. A classic example is two unrevealed cells next to a single "1": one of them is a mine, but nothing on the board says which. In those cases the honest answer is "unknown", and the solver leaves such cells alone rather than guessing.

## How it works

Each revealed number becomes a constraint on its unknown neighbours: "exactly N mines among these cells" (flagged neighbours are subtracted from N first). Two obvious rules then settle the easy constraints. If a constraint needs zero mines, all of its cells are safe. If it needs as many mines as it has cells, all of its cells are mines. Settling a cell removes it from every other constraint, which can make those constraints obvious in turn.

When the obvious rules run dry, the solver looks for nested constraints. If one constraint's cells are a subset of another's, subtracting the smaller from the larger yields a new constraint on the leftover cells with the leftover mine count. New constraints feed back into the obvious rules, and the whole thing loops until nothing changes.

Exhaustive enumeration for the remaining hard cases (trying every consistent mine layout and keeping only what is true in all of them) is planned but not built yet.

## How to run

Python 3 is required. There are no dependencies beyond the standard library.

```
python main.py   # console version
python gui.py    # graphical version (tkinter)
```

## Input legend

| Character | Meaning |
|-----------|---------|
| `?`       | unrevealed cell |
| `0`-`8`   | revealed number |
| `F`       | flagged mine |

In the GUI, an empty box also means unrevealed, and a lowercase `f` is accepted as `F`. After solving, proven mines turn red with an `M`, proven safe cells turn green with an `S`, and undecided cells turn gray.

Console output coordinates are `(row, col)`, counted from zero.

## Worked example

Board of 2 rows and 3 columns:

```
???
121
```

The `2` in the middle needs two mines among its three unknown neighbours. The `1`s at each end each need exactly one mine among their two unknown neighbours. Subtracting a `1` constraint from the `2` constraint proves the far corner is a mine, and once both corners are mines, the middle cell must be safe.

Console session:

```
Rows: 2
Cols: 3
ROW 1: ???
ROW 2: 121
Mines:  [(0, 0), (0, 2)]
Safes:  [(0, 1)]
```
