"tkinter front end for the minesweeper solver in solver.py"
"tkinter ships with Python, so no third-party packages are needed"
import tkinter as tk
"messagebox gives us the small pop-up windows used for error messages"
from tkinter import messagebox
"solve(grid) is the only thing we need from solver.py"
from solver import solve

"the biggest board we allow in either direction, so the window stays usable"
MAX_SIZE = 40
"every character a cell is allowed to hold (lowercase f is normalised to F)"
ALLOWED = set("012345678?F")

"colours used when painting the board after a solve"
COLOR_MINE = "#f28b82"     # red   : the solver proved this cell is a mine
COLOR_SAFE = "#81c995"     # green : the solver proved this cell is safe
COLOR_UNKNOWN = "#c0c0c0"  # gray  : still unknown after solving
COLOR_NEUTRAL = "white"    # white : cells the user typed into / untouched


class SolverApp:
    "the whole application: a size form, then a grid of entry boxes"

    def __init__(self, root):
        "root is the main tkinter window"
        self.root = root
        self.root.title("Minesweeper Solver")
        "the current board size, filled in once the user submits the form"
        self.rows = 0
        self.cols = 0
        "entries[r][c] is the Entry widget for cell (r, c)"
        self.entries = []
        "vars[r][c] is the StringVar holding the text of cell (r, c)"
        self.vars = []
        "the frame currently on screen (size form or board) so we can destroy it"
        self.frame = None
        "start on the size form"
        self.show_size_form()

    # ------------------------------------------------------------------
    # screen 1: the size form
    # ------------------------------------------------------------------

    def clear_frame(self):
        "throw away whatever screen is currently showing"
        if self.frame is not None:
            self.frame.destroy()
        "a fresh frame for the next screen to build into"
        self.frame = tk.Frame(self.root, padx=10, pady=10)
        self.frame.pack()

    def show_size_form(self):
        "ask for rows and columns, then build the grid on 'Create grid'"
        self.clear_frame()
        "label + entry for the number of rows"
        tk.Label(self.frame, text="Rows:").grid(row=0, column=0, sticky="e")
        self.rows_var = tk.StringVar(value="9")
        tk.Entry(self.frame, textvariable=self.rows_var, width=5).grid(row=0, column=1)
        "label + entry for the number of columns"
        tk.Label(self.frame, text="Cols:").grid(row=1, column=0, sticky="e")
        self.cols_var = tk.StringVar(value="9")
        tk.Entry(self.frame, textvariable=self.cols_var, width=5).grid(row=1, column=1)
        "the button that reads both numbers and moves on to the board"
        tk.Button(self.frame, text="Create grid", command=self.create_grid).grid(
            row=2, column=0, columnspan=2, pady=(8, 0)
        )
        "a reminder of the size cap so the user is not surprised by the error"
        tk.Label(self.frame, text=f"(max {MAX_SIZE} each)").grid(row=3, column=0, columnspan=2)

    def create_grid(self):
        "validate the size form, then switch to the board screen"
        try:
            "int() raises ValueError on anything that is not a whole number"
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
        except ValueError:
            messagebox.showerror("Bad size", "Rows and cols must be whole numbers.")
            return
        "both dimensions must be at least 1 and at most MAX_SIZE"
        if not (1 <= rows <= MAX_SIZE and 1 <= cols <= MAX_SIZE):
            messagebox.showerror("Bad size", f"Rows and cols must be between 1 and {MAX_SIZE}.")
            return
        "size is good: remember it and build the board"
        self.rows, self.cols = rows, cols
        self.show_board()

    # ------------------------------------------------------------------
    # screen 2: the board
    # ------------------------------------------------------------------

    def show_board(self):
        "draw a rows x cols grid of one-character entry boxes plus the buttons"
        self.clear_frame()
        self.entries = []
        self.vars = []
        "register the validation function once so tkinter can call it per keystroke"
        "%P is the text the entry WOULD contain if the edit were allowed"
        "%W is the name of the widget being edited, so we know which cell it is"
        vcmd = (self.root.register(self.validate), "%P", "%W")
        "a sub-frame just for the cells so the buttons can sit underneath"
        board = tk.Frame(self.frame)
        board.grid(row=0, column=0, columnspan=3)
        for r in range(self.rows):
            row_entries = []
            row_vars = []
            for c in range(self.cols):
                var = tk.StringVar()
                "width=2 keeps each cell small; justify centres the character"
                entry = tk.Entry(
                    board,
                    textvariable=var,
                    width=2,
                    justify="center",
                    font=("Consolas", 12),
                    validate="key",
                    validatecommand=vcmd,
                    bg=COLOR_NEUTRAL,
                )
                entry.grid(row=r, column=c)
                "remember the coordinates on the widget for the focus-jump logic"
                entry.coords = (r, c)
                "when a cell gains focus, select its text so typing replaces it"
                "(otherwise typing into a cell that already has M/S/a digit would be rejected)"
                entry.bind("<FocusIn>", lambda e: e.widget.selection_range(0, tk.END))
                row_entries.append(entry)
                row_vars.append(var)
            self.entries.append(row_entries)
            self.vars.append(row_vars)
        "the three action buttons under the board"
        tk.Button(self.frame, text="Solve", command=self.solve_board).grid(row=1, column=0, pady=(8, 0))
        tk.Button(self.frame, text="Clear board", command=self.clear_board).grid(row=1, column=1, pady=(8, 0))
        tk.Button(self.frame, text="New size", command=self.show_size_form).grid(row=1, column=2, pady=(8, 0))
        "put the cursor in the top-left cell so the user can start typing at once"
        self.entries[0][0].focus_set()

    def validate(self, proposed, widget_name):
        "called on every keystroke; return True to accept the edit, False to reject"
        "an empty box is always fine: it means unrevealed"
        if proposed == "":
            return True
        "never allow more than one character in a cell"
        if len(proposed) > 1:
            return False
        "lowercase f is fine, we will normalise it to F just below"
        ch = proposed.upper()
        if ch not in ALLOWED:
            return False
        "look up the Entry widget from its tkinter name"
        entry = self.root.nametowidget(widget_name)
        if proposed != ch:
            "typed 'f': replace it with 'F' after this validation finishes"
            "after_idle avoids editing the box while tkinter is still validating it"
            self.root.after_idle(lambda: self.set_cell(entry, ch))
        "jump to the next cell so the user can keep typing without clicking"
        self.root.after_idle(lambda: self.focus_next(entry))
        return True

    def set_cell(self, entry, ch):
        "overwrite the text of a cell (used to turn 'f' into 'F')"
        "validation is temporarily switched off so this edit is not re-checked"
        entry.configure(validate="none")
        entry.delete(0, tk.END)
        entry.insert(0, ch)
        entry.configure(validate="key")

    def focus_next(self, entry):
        "move focus to the cell after 'entry', reading left-to-right, top-to-bottom"
        r, c = entry.coords
        "advance one column, wrapping to the start of the next row"
        c += 1
        if c >= self.cols:
            c = 0
            r += 1
        "stop at the bottom-right corner: there is nowhere further to go"
        if r >= self.rows:
            return
        "focus_set triggers the <FocusIn> binding, which selects the cell's text"
        self.entries[r][c].focus_set()

    # ------------------------------------------------------------------
    # button actions
    # ------------------------------------------------------------------

    def read_grid(self):
        "convert the entry boxes into the list-of-strings format solver.py expects"
        grid = []
        for r in range(self.rows):
            line = ""
            for c in range(self.cols):
                ch = self.vars[r][c].get().strip().upper()
                "empty box or ? -> unrevealed; F and digits pass through untouched"
                if ch == "" or ch == "?":
                    line += "?"
                else:
                    line += ch
            grid.append(line)
        return grid

    def reset_colors(self):
        "put every cell back to the neutral colour and drop any M/S markers"
        for r in range(self.rows):
            for c in range(self.cols):
                entry = self.entries[r][c]
                entry.configure(bg=COLOR_NEUTRAL)
                "M and S are solver output, not user input, so strip them out"
                if self.vars[r][c].get() in ("M", "S"):
                    self.set_cell(entry, "")

    def solve_board(self):
        "run the solver on the current board and paint the results"
        "start from a clean slate so re-solving after edits works properly"
        self.reset_colors()
        grid = self.read_grid()
        try:
            mines, safes = solve(grid)
        except Exception as exc:  # solver hit something it could not handle
            messagebox.showerror("Solver error", str(exc))
            return
        for r in range(self.rows):
            for c in range(self.cols):
                entry = self.entries[r][c]
                "only unknown cells get coloured; typed numbers and F stay as they are"
                if grid[r][c] != "?":
                    continue
                if (r, c) in mines:
                    self.set_cell(entry, "M")
                    entry.configure(bg=COLOR_MINE)
                elif (r, c) in safes:
                    self.set_cell(entry, "S")
                    entry.configure(bg=COLOR_SAFE)
                else:
                    entry.configure(bg=COLOR_UNKNOWN)

    def clear_board(self):
        "wipe every cell back to empty and neutral"
        self.reset_colors()
        for r in range(self.rows):
            for c in range(self.cols):
                self.set_cell(self.entries[r][c], "")
        "back to the top-left corner, ready for a new position"
        self.entries[0][0].focus_set()


def main():
    "build the window and hand control to tkinter's event loop"
    root = tk.Tk()
    SolverApp(root)
    root.mainloop()


"only open a window when run directly; 'import gui' does nothing visible"
if __name__ == "__main__":
    main()
