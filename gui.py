"tkinter front end for the minesweeper solver in solver.py"
"tkinter ships with Python, so no third-party packages are needed"
import tkinter as tk
"messagebox gives us the small pop-up windows used for error messages"
from tkinter import messagebox
"solve_with_total wraps solver.solve and optionally uses the total mine count"
from total_mines import solve_with_total

"the biggest board we allow in either direction, so the window stays usable"
MAX_SIZE = 40
"every character a cell is allowed to hold (lowercase f is normalised to F)"
ALLOWED = set("012345678?F")

"colours used when painting the result grid after a solve"
COLOR_MINE = "#f28b82"     # red   : the solver proved this cell is a mine
COLOR_SAFE = "#81c995"     # green : the solver proved this cell is safe
COLOR_UNKNOWN = "#c0c0c0"  # gray  : still unknown after solving
COLOR_NEUTRAL = "white"    # white : cells the user typed into / untouched
COLOR_SELECTED = "#cfe2ff" # blue  : the input cell chosen in one-cell mode

"the two solve modes offered by the radio buttons"
MODE_BOARD = "board"  # solve and show every cell
MODE_CELL = "cell"    # solve, but only reveal the one cell the user clicked

"font shared by the input cells and the result cells so they line up"
CELL_FONT = ("Consolas", 12)


class SolverApp:
    "the whole application: a size form, then an input grid beside a result grid"

    def __init__(self, root):
        "root is the main tkinter window"
        self.root = root
        self.root.title("Minesweeper Solver")
        "the current board size, filled in once the user submits the form"
        self.rows = 0
        self.cols = 0
        "entries[r][c] is the Entry widget for input cell (r, c)"
        self.entries = []
        "vars[r][c] is the StringVar holding the text of input cell (r, c)"
        self.vars = []
        "results[r][c] is the Label widget for result cell (r, c)"
        self.results = []
        "the (r, c) of the input cell the user last clicked or typed into"
        self.selected = None
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
    # screen 2: the board (input grid on the left, result grid on the right)
    # ------------------------------------------------------------------

    def show_board(self):
        "draw the input grid, the (initially hidden) result grid, and the controls"
        self.clear_frame()
        self.entries = []
        self.vars = []
        self.results = []
        self.selected = None

        "--- left half: the editable input grid ---"
        "a heading so the two grids are easy to tell apart"
        tk.Label(self.frame, text="Input", font=("Segoe UI", 10, "bold")).grid(row=0, column=0)
        "register the validation function once so tkinter can call it per keystroke"
        "%P is the text the entry WOULD contain if the edit were allowed"
        "%W is the name of the widget being edited, so we know which cell it is"
        vcmd = (self.root.register(self.validate), "%P", "%W")
        "a sub-frame just for the input cells"
        board = tk.Frame(self.frame)
        board.grid(row=1, column=0, padx=(0, 10))
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
                    font=CELL_FONT,
                    validate="key",
                    validatecommand=vcmd,
                    bg=COLOR_NEUTRAL,
                )
                entry.grid(row=r, column=c)
                "remember the coordinates on the widget for the focus-jump logic"
                entry.coords = (r, c)
                "when a cell gains focus (click or focus jump) remember it as the"
                "selected cell and select its text so typing replaces it"
                entry.bind("<FocusIn>", lambda e: self.on_focus(e.widget))
                row_entries.append(entry)
                row_vars.append(var)
            self.entries.append(row_entries)
            self.vars.append(row_vars)

        "--- right half: the read-only result grid ---"
        "heading and frame are built now but hidden until the first solve"
        self.result_heading = tk.Label(self.frame, text="Solved", font=("Segoe UI", 10, "bold"))
        self.result_heading.grid(row=0, column=1)
        self.result_frame = tk.Frame(self.frame)
        self.result_frame.grid(row=1, column=1, padx=(10, 0))
        for r in range(self.rows):
            row_labels = []
            for c in range(self.cols):
                "a Label styled like an Entry: same font, same width, sunken border"
                label = tk.Label(
                    self.result_frame,
                    text="",
                    width=2,
                    font=CELL_FONT,
                    bg=COLOR_NEUTRAL,
                    relief="sunken",
                    bd=1,
                )
                label.grid(row=r, column=c)
                row_labels.append(label)
            self.results.append(row_labels)
        "grid_remove hides the widgets but remembers their layout for later"
        self.result_heading.grid_remove()
        self.result_frame.grid_remove()

        "--- bottom: mode switch, mine count field, summary line, and buttons ---"
        controls = tk.Frame(self.frame)
        controls.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        "radio buttons choosing between solving everything and solving one cell"
        self.mode_var = tk.StringVar(value=MODE_BOARD)
        modes = tk.Frame(controls)
        modes.grid(row=0, column=0, columnspan=2)
        tk.Radiobutton(
            modes, text="Whole board", variable=self.mode_var, value=MODE_BOARD,
            command=self.refresh_highlight,
        ).grid(row=0, column=0)
        tk.Radiobutton(
            modes, text="One cell (click it, then Solve)", variable=self.mode_var, value=MODE_CELL,
            command=self.refresh_highlight,
        ).grid(row=0, column=1)
        "total mines on the board; leaving it blank means 'not known'"
        tk.Label(controls, text="Total mines (optional):").grid(row=1, column=0, sticky="e")
        self.mines_var = tk.StringVar()
        tk.Entry(controls, textvariable=self.mines_var, width=5).grid(row=1, column=1, sticky="w")
        "one line of text summarising the last solve, e.g. '2 mines, 1 safe, 3 unknown'"
        self.summary_var = tk.StringVar()
        tk.Label(controls, textvariable=self.summary_var).grid(row=2, column=0, columnspan=2)
        "the three action buttons"
        buttons = tk.Frame(controls)
        buttons.grid(row=3, column=0, columnspan=2, pady=(6, 0))
        tk.Button(buttons, text="Solve", command=self.solve_board).grid(row=0, column=0, padx=3)
        tk.Button(buttons, text="Clear board", command=self.clear_board).grid(row=0, column=1, padx=3)
        tk.Button(buttons, text="New size", command=self.show_size_form).grid(row=0, column=2, padx=3)
        "put the cursor in the top-left cell so the user can start typing at once"
        self.entries[0][0].focus_set()

    def on_focus(self, entry):
        "an input cell was clicked or tabbed into: it becomes the selected cell"
        self.selected = entry.coords
        "select its text so typing replaces it (otherwise a second char is rejected)"
        entry.selection_range(0, tk.END)
        self.refresh_highlight()

    def refresh_highlight(self):
        "tint the selected input cell blue, but only in one-cell mode"
        for r in range(self.rows):
            for c in range(self.cols):
                "everything back to neutral first"
                self.entries[r][c].configure(bg=COLOR_NEUTRAL)
        if self.mode_var.get() == MODE_CELL and self.selected is not None:
            r, c = self.selected
            self.entries[r][c].configure(bg=COLOR_SELECTED)

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
        "overwrite the text of an input cell (used to turn 'f' into 'F' and to clear)"
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
        "convert the input cells into the list-of-strings format solver.py expects"
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

    def read_total_mines(self):
        "return the mine count as an int, None if blank, or raise ValueError if bad"
        text = self.mines_var.get().strip()
        if text == "":
            return None
        "int() raises ValueError on anything that is not a whole number"
        total = int(text)
        if total < 0:
            raise ValueError("negative")
        return total

    def hide_results(self):
        "take the result grid off screen and blank its cells"
        self.result_heading.grid_remove()
        self.result_frame.grid_remove()
        for row in self.results:
            for label in row:
                label.configure(text="", bg=COLOR_NEUTRAL)
        self.summary_var.set("")

    def solve_board(self):
        "run the solver on the current board and paint the result grid beside it"
        "start from a clean slate so re-solving after edits works properly"
        self.hide_results()
        grid = self.read_grid()
        try:
            total = self.read_total_mines()
        except ValueError:
            messagebox.showerror("Bad mine count", "Total mines must be a whole number of 0 or more, or blank.")
            return
        try:
            mines, safes = solve_with_total(grid, total)
        except ValueError as exc:  # impossible mine count for this board
            messagebox.showerror("Bad mine count", str(exc))
            return
        except Exception as exc:  # solver hit something it could not handle
            messagebox.showerror("Solver error", str(exc))
            return
        "the back end is identical for both modes; only the painting differs"
        if self.mode_var.get() == MODE_BOARD:
            self.paint_board(grid, mines, safes)
        else:
            if not self.paint_cell(grid, mines, safes):
                return
        "now that the result grid is filled in, show it next to the input grid"
        self.result_heading.grid()
        self.result_frame.grid()

    def verdict(self, cell, mines, safes):
        "return ('M', red) / ('S', green) / ('?', gray) for one unknown cell"
        if cell in mines:
            return "M", COLOR_MINE
        if cell in safes:
            return "S", COLOR_SAFE
        return "?", COLOR_UNKNOWN

    def paint_board(self, grid, mines, safes):
        "whole-board mode: colour every unknown cell with its verdict"
        "how many cells are still undecided, for the summary line"
        unknown = 0
        for r in range(self.rows):
            for c in range(self.cols):
                label = self.results[r][c]
                ch = grid[r][c]
                "typed numbers and F are copied across on a neutral background"
                if ch != "?":
                    label.configure(text=ch, bg=COLOR_NEUTRAL)
                    continue
                text, color = self.verdict((r, c), mines, safes)
                label.configure(text=text, bg=color)
                if text == "?":
                    unknown += 1
        self.summary_var.set(f"{len(mines)} mines, {len(safes)} safe, {unknown} unknown")

    def paint_cell(self, grid, mines, safes):
        "one-cell mode: copy the input across and reveal only the selected cell"
        "returns False (after an error dialog) if there is no usable selection"
        if self.selected is None:
            messagebox.showerror("No cell selected", "Click a cell in the input grid first.")
            return False
        sr, sc = self.selected
        if grid[sr][sc] != "?":
            messagebox.showerror(
                "Cell already known",
                f"Cell ({sr}, {sc}) is a '{grid[sr][sc]}' you typed in; pick an unrevealed cell.",
            )
            return False
        for r in range(self.rows):
            for c in range(self.cols):
                "every cell mirrors the input exactly, unknowns shown as '?' on white"
                self.results[r][c].configure(text=grid[r][c], bg=COLOR_NEUTRAL)
        "only the selected cell gets its verdict and colour"
        text, color = self.verdict((sr, sc), mines, safes)
        self.results[sr][sc].configure(text=text, bg=color)
        meaning = {"M": "a mine", "S": "safe", "?": "unknown"}[text]
        self.summary_var.set(f"Cell ({sr}, {sc}) is {meaning}")
        return True

    def clear_board(self):
        "wipe every input cell back to empty and hide the result grid"
        self.hide_results()
        for r in range(self.rows):
            for c in range(self.cols):
                self.set_cell(self.entries[r][c], "")
        self.mines_var.set("")
        "back to the top-left corner, ready for a new position"
        "(focus_set fires on_focus, which also resets the selection highlight)"
        self.entries[0][0].focus_set()


def main():
    "build the window and hand control to tkinter's event loop"
    root = tk.Tk()
    SolverApp(root)
    root.mainloop()


"only open a window when run directly; 'import gui' does nothing visible"
if __name__ == "__main__":
    main()
