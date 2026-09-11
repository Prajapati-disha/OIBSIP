"""
TASK 2 - BMI CALCULATOR (Advanced / GUI Tier)
================================================
A full tkinter desktop app that:
  1. Provides input fields + a "Calculate" button (no command line)
  2. Shows the BMI result with colour-coded feedback
     (green = normal, orange = under/overweight, red = obese)
  3. Supports MULTIPLE named users
  4. Stores every calculation permanently in an SQLite database
  5. Can plot a user's BMI-over-time trend with matplotlib
  6. Handles database errors gracefully (no crashes on DB failure)

Requirements (all standard library except matplotlib):
    pip install matplotlib

Run it with:  python bmi_calculator_gui.py
"""

import re
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# matplotlib is only needed for the trend graph; imported here and embedded
# directly into the tkinter window using its Tk-specific backend.
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = "bmi_records.db"


# ---------------------------------------------------------------------------
# DATABASE LAYER
# ---------------------------------------------------------------------------
# Keeping all SQLite code in its own class means the GUI code never has to
# know *how* data is stored - it just calls db.save_record(), db.get_users(),
# etc. This also makes it easy to wrap every database call in error handling
# in ONE place instead of repeating try/except everywhere.
# ---------------------------------------------------------------------------
class BMIDatabase:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the records table if it doesn't already exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except sqlite3.Error as e:
            # If we can't even create the table, the app can't function -
            # tell the user clearly instead of crashing with a traceback.
            messagebox.showerror(
                "Database Error",
                f"Could not initialise the database.\n\nDetails: {e}"
            )
            raise

    def save_record(self, username, weight, height, bmi, category):
        """Insert one BMI record. Returns True on success, False on failure."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO bmi_records
                        (username, weight, height, bmi, category, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (username, weight, height, bmi, category,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save record.\n\nDetails: {e}")
            return False

    def get_users(self):
        """Return a sorted list of distinct usernames that have records."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT DISTINCT username FROM bmi_records ORDER BY username COLLATE NOCASE"
                ).fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load users.\n\nDetails: {e}")
            return []

    def get_history(self, username):
        """Return (recorded_at, bmi) tuples for one user, oldest first."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT recorded_at, bmi FROM bmi_records
                    WHERE username = ?
                    ORDER BY recorded_at ASC
                    """,
                    (username,),
                ).fetchall()
            return rows
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load history.\n\nDetails: {e}")
            return []


# ---------------------------------------------------------------------------
# HEIGHT UNIT CONVERSION (same auto-detecting parser as the CLI tier)
# ---------------------------------------------------------------------------
# Accepts height typed as meters, feet, or feet+inches, e.g.:
#   Meters          -> "1.75", "1.75m", "1.75 meters", "1.75 metres"
#   Feet only       -> "5.5ft", "5.5 ft", "5.5'", "5.5 feet"
#   Feet + inches   -> "5'6\"", "5' 6\"", "5ft 6in", "5 ft 6 in", "5'6"
# ---------------------------------------------------------------------------
FEET_TO_METERS = 0.3048

FEET_INCHES_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(?:'|ft\.?|feet)\s*(\d+(?:\.\d+)?)\s*(?:\"|in\.?|inch(?:es)?)?$",
    re.IGNORECASE,
)
FEET_ONLY_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(?:'|ft\.?|feet)$",
    re.IGNORECASE,
)
METERS_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)?$",
    re.IGNORECASE,
)


def parse_height_to_meters(raw_text: str) -> float:
    """
    Auto-detects whether the user typed height in meters, feet, or
    feet+inches, and returns the equivalent in meters.
    Raises ValueError (with a user-friendly message) on bad input.
    """
    text = raw_text.strip().lower()
    if not text:
        raise ValueError("Height cannot be empty.")

    match = FEET_INCHES_RE.match(text)
    if match:
        feet, inches = float(match.group(1)), float(match.group(2))
        total_feet = feet + (inches / 12)
        if total_feet <= 0:
            raise ValueError("Height must be a positive value.")
        return round(total_feet * FEET_TO_METERS, 4)

    match = FEET_ONLY_RE.match(text)
    if match:
        feet = float(match.group(1))
        if feet <= 0:
            raise ValueError("Height must be a positive value.")
        return round(feet * FEET_TO_METERS, 4)

    match = METERS_RE.match(text)
    if match:
        meters = float(match.group(1))
        if meters <= 0:
            raise ValueError("Height must be a positive value.")
        return round(meters, 4)

    raise ValueError(
        "Could not understand that height. Try formats like: "
        "1.75, 1.75m, 5.5ft, 5.5', 5'6\", or 5ft 6in."
    )


# ---------------------------------------------------------------------------
# BMI CALCULATION HELPERS (same logic as the CLI tier)
# ---------------------------------------------------------------------------
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# Colour used for each category's feedback label.
# Green = healthy, amber = caution, red = high risk - a common traffic-light
# convention that makes the result readable at a glance.
CATEGORY_COLORS = {
    "Underweight": "#E67E22",  # amber/orange
    "Normal":      "#27AE60",  # green
    "Overweight":  "#E67E22",  # amber/orange
    "Obese":       "#C0392B",  # red
}


# ---------------------------------------------------------------------------
# MAIN APPLICATION WINDOW
# ---------------------------------------------------------------------------
class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("BMI Calculator")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg="#F4F6F7")

        # The database connection lives for the whole life of the app.
        self.db = BMIDatabase()

        self._build_widgets()
        self._refresh_user_dropdown()

    # -----------------------------------------------------------------
    # UI CONSTRUCTION
    # -----------------------------------------------------------------
    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}

        title_label = tk.Label(
            self, text="BMI Calculator", font=("Segoe UI", 18, "bold"), bg="#F4F6F7"
        )
        title_label.pack(pady=(15, 5))

        form_frame = tk.Frame(self, bg="#F4F6F7")
        form_frame.pack(pady=5)

        # --- Username (supports multiple users) ---
        tk.Label(form_frame, text="User name:", bg="#F4F6F7", anchor="w").grid(
            row=0, column=0, sticky="w", **pad
        )
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(form_frame, textvariable=self.username_var, width=22)
        self.username_entry.grid(row=0, column=1, **pad)

        # --- Weight ---
        tk.Label(form_frame, text="Weight (kg):", bg="#F4F6F7", anchor="w").grid(
            row=1, column=0, sticky="w", **pad
        )
        self.weight_var = tk.StringVar()
        self.weight_entry = tk.Entry(form_frame, textvariable=self.weight_var, width=22)
        self.weight_entry.grid(row=1, column=1, **pad)

        # --- Height (accepts meters, feet, or feet+inches - auto-detected) ---
        tk.Label(form_frame, text="Height:", bg="#F4F6F7", anchor="w").grid(
            row=2, column=0, sticky="w", **pad
        )
        self.height_var = tk.StringVar()
        self.height_entry = tk.Entry(form_frame, textvariable=self.height_var, width=22)
        self.height_entry.grid(row=2, column=1, **pad)

        # Small hint under the height field so users know all 3 formats work.
        height_hint = tk.Label(
            form_frame,
            text="e.g. 1.75  |  1.75m  |  5.5ft  |  5'6\"",
            font=("Segoe UI", 8), fg="#7F8C8D", bg="#F4F6F7", anchor="w"
        )
        height_hint.grid(row=3, column=1, sticky="w", padx=10)

        # --- Calculate button ---
        calc_button = tk.Button(
            self, text="Calculate", font=("Segoe UI", 11, "bold"),
            bg="#2E86C1", fg="white", activebackground="#21618C",
            command=self.on_calculate, width=18
        )
        calc_button.pack(pady=15)

        # --- Result display (colour-coded) ---
        self.result_frame = tk.Frame(self, bg="white", relief="groove", bd=2)
        self.result_frame.pack(padx=20, pady=5, fill="x")

        self.bmi_value_label = tk.Label(
            self.result_frame, text="--", font=("Segoe UI", 26, "bold"), bg="white"
        )
        self.bmi_value_label.pack(pady=(10, 0))

        self.category_label = tk.Label(
            self.result_frame, text="Enter details and press Calculate",
            font=("Segoe UI", 12), bg="white"
        )
        self.category_label.pack(pady=(0, 10))

        # --- Multi-user history / trend section ---
        history_frame = tk.LabelFrame(self, text="History & Trend", bg="#F4F6F7", padx=10, pady=10)
        history_frame.pack(padx=20, pady=15, fill="x")

        tk.Label(history_frame, text="Select user:", bg="#F4F6F7").grid(row=0, column=0, sticky="w")
        self.user_select_var = tk.StringVar()
        self.user_dropdown = ttk.Combobox(
            history_frame, textvariable=self.user_select_var, state="readonly", width=20
        )
        self.user_dropdown.grid(row=0, column=1, padx=8)

        graph_button = tk.Button(
            history_frame, text="View BMI Trend Graph", command=self.on_view_graph
        )
        graph_button.grid(row=1, column=0, columnspan=2, pady=(10, 0))

    # -----------------------------------------------------------------
    # VALIDATION (mirrors the beginner CLI validation rules)
    # -----------------------------------------------------------------
    @staticmethod
    def _parse_positive_float(text: str, field_name: str) -> float:
        """
        Convert text to a positive float, or raise ValueError with a
        message suitable for showing directly to the user.
        """
        try:
            value = float(text)
        except ValueError:
            raise ValueError(f"{field_name} must be a number (e.g. 65.5).")
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than 0.")
        return value

    # -----------------------------------------------------------------
    # EVENT HANDLERS
    # -----------------------------------------------------------------
    def on_calculate(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Missing Info", "Please enter a user name.")
            return

        # Validate weight (kg only) & height (m / ft / ft+in, auto-detected)
        # with helpful, specific error messages.
        try:
            weight = self._parse_positive_float(self.weight_var.get().strip(), "Weight")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        try:
            height = parse_height_to_meters(self.height_var.get())
        except ValueError as e:
            messagebox.showerror("Invalid Height", str(e))
            return

        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)

        # --- Update the colour-coded result display ---
        self.bmi_value_label.config(text=f"{round(bmi, 2)}")
        self.category_label.config(
            text=category, fg=CATEGORY_COLORS[category]
        )
        self.bmi_value_label.config(fg=CATEGORY_COLORS[category])

        # --- Persist to the database ---
        saved = self.db.save_record(username, weight, height, bmi, category)
        if saved:
            self._refresh_user_dropdown(select=username)

    def on_view_graph(self):
        username = self.user_select_var.get()
        if not username:
            messagebox.showinfo("No User Selected", "Please select a user first.")
            return

        history = self.db.get_history(username)
        if len(history) < 1:
            messagebox.showinfo("No Data", f"No BMI records found for '{username}' yet.")
            return

        dates = [row[0] for row in history]
        bmis = [row[1] for row in history]

        self._show_trend_window(username, dates, bmis)

    # -----------------------------------------------------------------
    # GRAPH WINDOW (matplotlib embedded in a new tkinter Toplevel)
    # -----------------------------------------------------------------
    def _show_trend_window(self, username, dates, bmis):
        graph_win = tk.Toplevel(self)
        graph_win.title(f"BMI Trend - {username}")
        graph_win.geometry("600x450")

        fig = Figure(figsize=(5.5, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Use simple integer x-positions with date strings as tick labels,
        # since dates are stored as text - this avoids extra date-parsing
        # dependencies while still showing a clear time-ordered trend.
        x_positions = list(range(len(dates)))
        ax.plot(x_positions, bmis, marker="o", color="#2E86C1", linewidth=2)

        ax.set_title(f"BMI Trend for {username}")
        ax.set_xlabel("Record #")
        ax.set_ylabel("BMI")
        ax.set_xticks(x_positions)
        ax.set_xticklabels([d.split(" ")[0] for d in dates], rotation=45, ha="right", fontsize=7)

        # Reference lines for the category boundaries help the user see
        # at a glance where their trend sits relative to "Normal" range.
        ax.axhline(18.5, color="gray", linestyle="--", linewidth=0.7)
        ax.axhline(25, color="gray", linestyle="--", linewidth=0.7)
        ax.axhline(30, color="gray", linestyle="--", linewidth=0.7)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # -----------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------
    def _refresh_user_dropdown(self, select: str = None):
        users = self.db.get_users()
        self.user_dropdown["values"] = users
        if select and select in users:
            self.user_select_var.set(select)
        elif users:
            self.user_select_var.set(users[0])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = BMIApp()
    app.mainloop()
