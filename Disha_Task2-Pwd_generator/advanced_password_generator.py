"""
Random Password Generator — Advanced Tier
--------------------------------------------
GUI application (tkinter) that generates cryptographically secure passwords.

Concepts demonstrated:
- `secrets` module for cryptographically secure randomness (vs `random`)
- tkinter widgets: Label, Entry, Spinbox, Checkbutton, Button, Listbox
- tkinter variable classes (StringVar, IntVar, BooleanVar) that link widgets
  to Python values automatically
- Event-driven programming (a function runs when a button is clicked)
- Guaranteeing character-type coverage instead of relying on pure chance
- A simple heuristic password-strength scorer
- Clipboard integration via pyperclip
- Keeping an in-memory (non-persisted) history for the session

Run with:  python3 advanced_password_generator.py
Requires:  pip install pyperclip
"""

import string
import secrets
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


# Characters that are easy to visually confuse with each other.
AMBIGUOUS_CHARS = "0O1lI|"


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Password Generator")
        self.root.resizable(False, False)

        # In-memory history: list of strings, most recent first, max 5 kept.
        # Deliberately NOT written to disk (see checklist: security).
        self.history = []

        self._build_widgets()

    # ------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------
    def _build_widgets(self):
        padding = {"padx": 10, "pady": 6}

        # --- Length control -------------------------------------------------
        length_frame = ttk.LabelFrame(self.root, text="Length")
        length_frame.grid(row=0, column=0, sticky="ew", **padding)

        # IntVar keeps a Python int in sync with the Spinbox widget automatically.
        self.length_var = tk.IntVar(value=16)
        ttk.Spinbox(
            length_frame, from_=8, to=64, textvariable=self.length_var, width=5
        ).pack(side="left", padx=8, pady=6)
        ttk.Label(length_frame, text="characters (8–64)").pack(side="left")

        # --- Character type checkboxes --------------------------------------
        types_frame = ttk.LabelFrame(self.root, text="Include character types")
        types_frame.grid(row=1, column=0, sticky="ew", **padding)

        # BooleanVar for each checkbox; default all True so a first-time user
        # gets a strong password with zero clicks.
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.exclude_ambiguous = tk.BooleanVar(value=False)

        ttk.Checkbutton(types_frame, text="Uppercase (A-Z)", variable=self.use_upper).pack(anchor="w")
        ttk.Checkbutton(types_frame, text="Lowercase (a-z)", variable=self.use_lower).pack(anchor="w")
        ttk.Checkbutton(types_frame, text="Numbers (0-9)", variable=self.use_digits).pack(anchor="w")
        ttk.Checkbutton(types_frame, text="Symbols (!@#$...)", variable=self.use_symbols).pack(anchor="w")
        ttk.Checkbutton(
            types_frame,
            text="Exclude ambiguous characters (0, O, 1, l, I, |)",
            variable=self.exclude_ambiguous,
        ).pack(anchor="w")

        # --- Generate button --------------------------------------------------
        ttk.Button(self.root, text="Generate Password", command=self.on_generate).grid(
            row=2, column=0, sticky="ew", **padding
        )

        # --- Result display -----------------------------------------------
        result_frame = ttk.LabelFrame(self.root, text="Result")
        result_frame.grid(row=3, column=0, sticky="ew", **padding)

        self.result_var = tk.StringVar(value="")
        result_entry = ttk.Entry(
            result_frame, textvariable=self.result_var, font=("Consolas", 13), width=32,
            state="readonly", justify="center",
        )
        result_entry.pack(padx=8, pady=(8, 4))

        self.strength_var = tk.StringVar(value="")
        self.strength_label = ttk.Label(result_frame, textvariable=self.strength_var, font=("Segoe UI", 10, "bold"))
        self.strength_label.pack(pady=(0, 8))

        ttk.Button(result_frame, text="Copy to Clipboard", command=self.on_copy).pack(pady=(0, 8))

        # --- History -----------------------------------------------------
        history_frame = ttk.LabelFrame(self.root, text="History (this session only, last 5)")
        history_frame.grid(row=4, column=0, sticky="ew", **padding)

        self.history_listbox = tk.Listbox(history_frame, height=5, font=("Consolas", 10))
        self.history_listbox.pack(fill="x", padx=8, pady=8)

    # ------------------------------------------------------------------
    # CORE LOGIC
    # ------------------------------------------------------------------
    def _build_pools(self):
        """Return (combined_pool, list_of_individual_selected_pools)."""
        pools = []
        if self.use_upper.get():
            pools.append(string.ascii_uppercase)
        if self.use_lower.get():
            pools.append(string.ascii_lowercase)
        if self.use_digits.get():
            pools.append(string.digits)
        if self.use_symbols.get():
            pools.append(string.punctuation)

        if self.exclude_ambiguous.get():
            pools = ["".join(c for c in p if c not in AMBIGUOUS_CHARS) for p in pools]

        combined = "".join(pools)
        return combined, pools

    def _generate_secure_password(self, length, combined_pool, individual_pools):
        """
        Build a password that:
          1. Uses `secrets.choice` (cryptographically secure) for every character.
          2. Is GUARANTEED to contain at least one character from each selected
             type — pure random selection over a combined pool can't promise
             this for short passwords, so we seed one char per type first,
             then fill the rest randomly, then shuffle so the guaranteed
             characters aren't predictably in the first N positions.
        """
        # Step 1: guarantee coverage — one secretly-chosen char per selected type.
        guaranteed = [secrets.choice(pool) for pool in individual_pools]

        # Step 2: fill the remaining length with random picks from the full pool.
        remaining_length = max(length - len(guaranteed), 0)
        filler = [secrets.choice(combined_pool) for _ in range(remaining_length)]

        password_chars = guaranteed + filler

        # Step 3: shuffle securely so guaranteed chars aren't always at the start.
        # secrets doesn't have a shuffle function, so we implement Fisher-Yates
        # using secrets.randbelow for each swap — this keeps every step
        # cryptographically secure end-to-end.
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return "".join(password_chars)

    def _score_strength(self, password, individual_pools):
        """
        Simple heuristic strength score, not a substitute for a real
        entropy calculation, but good enough for user-facing feedback:
          - length contributes points
          - each distinct character type used contributes points
        """
        score = 0
        score += min(len(password) // 4, 5)   # up to 5 points for length
        score += len(individual_pools)          # up to 4 points for variety

        if score <= 3:
            return "Weak", "#c0392b"      # red
        elif score <= 6:
            return "Medium", "#d68910"    # amber
        else:
            return "Strong", "#1e8449"    # green

    # ------------------------------------------------------------------
    # EVENT HANDLERS (called automatically by tkinter when the user interacts)
    # ------------------------------------------------------------------
    def on_generate(self):
        length = self.length_var.get()

        if length < 8:
            messagebox.showerror("Invalid length", "Length must be at least 8 characters.")
            return

        combined_pool, individual_pools = self._build_pools()

        if len(individual_pools) < 2:
            messagebox.showerror(
                "Select more character types",
                "Please select at least 2 character types.",
            )
            return

        if length < len(individual_pools):
            messagebox.showerror(
                "Length too short",
                f"Length must be at least {len(individual_pools)} to include "
                f"one of every selected character type.",
            )
            return

        password = self._generate_secure_password(length, combined_pool, individual_pools)
        self.result_var.set(password)

        label, color = self._score_strength(password, individual_pools)
        self.strength_var.set(f"Strength: {label}")
        self.strength_label.configure(foreground=color)

        # Update history: newest first, capped at 5 entries.
        self.history.insert(0, password)
        self.history = self.history[:5]
        self.history_listbox.delete(0, tk.END)
        for pw in self.history:
            self.history_listbox.insert(tk.END, pw)

        # Auto-copy to clipboard on every generation, per spec.
        # The "Copy to Clipboard" button still exists so the user can
        # re-copy this (or a past) password later without regenerating.
        if CLIPBOARD_AVAILABLE:
            pyperclip.copy(password)
            self.strength_var.set(f"Strength: {label}   |   Copied to clipboard")
        else:
            messagebox.showwarning(
                "pyperclip not installed",
                "Password generated, but couldn't auto-copy — run: pip install pyperclip",
            )

    def on_copy(self):
        password = self.result_var.get()
        if not password:
            messagebox.showwarning("Nothing to copy", "Generate a password first.")
            return

        if not CLIPBOARD_AVAILABLE:
            messagebox.showerror(
                "pyperclip not installed",
                "Run: pip install pyperclip",
            )
            return

        pyperclip.copy(password)
        messagebox.showinfo("Copied", "Password copied to clipboard.")


def main():
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()