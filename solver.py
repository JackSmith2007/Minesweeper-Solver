

"returns a list of all of the neighbours of cell (r, c)"
def neighbours(r, c, rows, cols):
    "all cells touching (r, c) staying inside the board"
    result = []
    "dr is the distance from the cell in row space"
    "dc is distance from the cell in column space"
    for dr in (-1, 0 , 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            "nr/c is the number of the row/column of the cell"
            nr, nc = r + dr, c + dc
            "checking to make sure it is actually within the grid"
            if 0 <= nr < rows and 0 <= nc < cols:
                "adding cells to 'results'"
                result.append((nr, nc))
    return result

def build_constraints(grid):
    "Turn the board into a list of constraints."
    "Each constraint is [set_of_cells, mine_count]"

    "grid is really just an array"
    rows, cols = len(grid), len(grid[0])
    constraints = []
    for r in range(rows):
        for c in range(cols):
            "ch is one character/cell of the board"
            ch = grid[r][c]
            if ch.isdigit():
                cells = set() #creates a new empty set
                count = int(ch)
                for nr, nc in neighbours(r, c, rows, cols):
                    if grid[nr][nc] == "?":
                        cells.add((nr, nc)) # unknown: add to the constraint
                    elif grid[nr][nc] == "F":
                        count -=1 # flagged mine: -1 from the mine count
                    if cells: # cells is non empty. ie. the cell has no unknown neighbours.
                        constraints.append([cells, count]) # tells us nothing. Skip it.
    return constraints

def settle(constraints, cell, is_mine):
    "we need to update constraints depending on if 'cell' is a mine or not"

    for con in constraints:
        if cell in con[0]: # does this constraint mention 'cell'
            con[0].remove(cell)
            if is_mine:
                con[1] -= 1 #remove one from the mine count for that constraint

def propagate(constraints):
    #apply the obvious rules until nothing changes
    # RULE A: a constraint needing 0 mines -> all its cells are safe.
    # RULE B: a constraint needing as many mines as it has cells -> all are miens.
    # Settling cells shrinks other constraints, which can make them obvious, so
    #keep  sweeping until nothing changes.

    mines, safes = set(), set() # creating new mines and safes sets
    changed = True 
    while changed: # sweep while constraints have changed
        changed = False
        for cells, count in constraints:
            if not cells: # cells is empty
                continue
            if count == 0: # RULE A
                for cell in list(cells):
                    safes.add(cell)
                    settle(constraints, cell, is_mine=False)
                changed = True
            elif count == len(cells): # RULE B
                for cell in list(cells):
                    mines.add(cell)
                    settle(constraints, cell, is_mine=True)
                changed = True
    return mines, safes

def subtract(constraints):
    '''STEP 2: find one constraint nested inside another and find the difference
    
    If B says "x mines among a big set" and A says "Y mines among a subset", then thecells in B but not A
    must hold exactly x - y mines. The difference is a new constraint. Returns true if anything new was added'''

    added = False
    live = [con for con in constraints if con[0]]
    for a in live:
        for b in live:
            if a is b: # dont compare to itself
                continue
            if a[0] < b[0]: #a is a subset of b
                new_cells = b[0] - a[0] # cells only B covers
                new_count = b[1] - a[1]

                if not any(con[0] == new_cells and con[1] == new_count for con in constraints):
                    constraints.append([new_cells, new_count])
                    added = True
    return added

def solve(grid):
    constraints = build_constraints(grid)
    mines, safes = set(), set()
    while True:
        m, s = propagate(constraints)
        mines |= m # |= merges the new findings into totals
        safes |= s
        if not subtract(constraints):
            break
    return mines, safes
    
                