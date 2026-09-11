# Random Password Generator

A Python password generator with two tiers:
- `beginner_password_generator.py` — command-line version using `random`
- `advanced_password_generator.py` — GUI version using `tkinter` and the
  cryptographically secure `secrets` module

## Setup

```bash
# Beginner tier — no extra installs needed, uses only the standard library
python3 beginner_password_generator.py

# Advanced tier — needs one extra package for clipboard support
pip install pyperclip
python3 advanced_password_generator.py
```

`tkinter` ships with standard Python installs on Windows and macOS. On Linux,
if it's missing, install it with your package manager, e.g.
`sudo apt install python3-tk` on Debian/Ubuntu.

## Why `secrets` instead of `random`?

`random` is a pseudo-random number generator (PRNG) built for speed and
reproducibility (e.g. simulations, games) — its internal state can, in
principle, be inferred from enough observed outputs, which makes it
unsuitable for anything security-sensitive. `secrets` pulls from the
operating system's cryptographically secure randomness source and is the
standard recommended by the Python docs for passwords, tokens, and similar
secrets.

## How character-type coverage is guaranteed

Randomly sampling from a combined character pool does **not** guarantee that
a short password contains, say, a symbol — it's possible (if unlikely) for
16 random draws to skip symbols entirely. To close that gap, the generator:

1. Picks one guaranteed character from each *selected* type first.
2. Fills the remaining length with random draws from the full combined pool.
3. Shuffles the result with a Fisher–Yates shuffle (implemented using
   `secrets.randbelow` at every swap) so the guaranteed characters aren't
   predictably placed at the start of the string.

This was verified with 1,000 trial passwords at the 8-character minimum —
100% included every selected character type.

## Data handling / privacy note

- Generated passwords are **never written to disk** or logged.
- Session history (last 5 passwords) lives only in memory and disappears
  when the app closes.
- The clipboard copy uses `pyperclip`, which interacts with the OS
  clipboard directly — no network calls are made anywhere in this app.
