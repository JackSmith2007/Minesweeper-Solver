from solver import solve

def read_board():
    '''Ask for board size, then the board itself, one row at a time.'''

    rows = int(input("Rows: "))
    cols = int(input("Cols: "))
    print(f"Enter the board, one row per line, {cols}, characters each.")
    print("? = unrevealed, 0-8 = revealed number, F = flagged mine")
    grid = []
    for i in range(rows):
        line = ""
        while len(line) != cols:
            line = input(f"ROW {i + 1}: ").strip() # strip() drops stray spaces
        grid.append(line)
    return grid

def main():
    grid = read_board()
    mines, safes = solve(grid)
    print("Mines: ", sorted(mines))
    print("Safes: ", sorted(safes))

if __name__ == "__main__":
    main()