# 🧮 BMI Calculator — Task 2

A two-tier Python project that calculates Body Mass Index (BMI) and classifies it into
standard health categories. The **beginner tier** is a command-line tool; the
**advanced tier** is a full desktop GUI app with multi-user support, persistent
storage, and BMI trend graphing.

---

## 📁 Project Files

| File                      | Tier      | Description                                   |
|----------------------------|-----------|------------------------------------------------|
| `bmi_calculator_cli.py`     | Beginner  | Command-line BMI calculator                   |
| `bmi_calculator_gui.py`     | Advanced  | tkinter GUI with SQLite storage & matplotlib graph |
| `bmi_records.db`            | Advanced  | Auto-created SQLite database (generated on first GUI run) |

---

## 🧠 How BMI Works

```
BMI = weight (kg) / height (m)²
```

| Category      | BMI Range        |
|---------------|-------------------|
| Underweight   | < 18.5            |
| Normal        | 18.5 – 24.9       |
| Overweight    | 25 – 29.9         |
| Obese         | ≥ 30              |

---

## 🟢 Beginner Tier — CLI

### Tech Stack
- Python 3
- `input()`, basic arithmetic (standard library only — no installs needed)

### Features
- ✅ Prompts for weight (kg) via terminal
- ✅ Prompts for height in **meters, feet, or feet+inches** — auto-detected
  (see [Height Formats](#-height-formats-accepted) below)
- ✅ Calculates BMI using the standard formula
- ✅ Classifies into Underweight / Normal / Overweight / Obese
- ✅ Displays BMI rounded to 2 decimal places, plus category
- ✅ Validates input — rejects non-numeric, unparseable, and negative values
  with a clear error message, then re-prompts instead of crashing

### Run it
```bash
python bmi_calculator_cli.py
```

### Example Session
```
Enter your weight in kg: 70
Enter your height (m, ft, or ft+in - e.g. 1.75, 5.5ft, 5'6"): 5'6"

--------------------------------------------------
  Weight       : 70.0 kg
  Height       : 1.6764 m
  Your BMI     : 24.91
  Category     : Normal
--------------------------------------------------

Calculate another BMI? (y/n): n
```

### 📏 Height Formats Accepted
You can type your height in **any** of these formats — the program
auto-detects which one you used:

| Format          | Examples                              |
|------------------|----------------------------------------|
| Meters           | `1.75`, `1.75m`, `1.75 meters`, `1.75 metres` |
| Feet only        | `5.5ft`, `5.5 ft`, `5.5'`, `5.5 feet` |
| Feet + inches    | `5'6"`, `5' 6"`, `5ft 6in`, `5 ft 6 in`, `5'6` |

> A bare number with no unit (e.g. `1.75`) is always treated as **meters**.
> To enter feet, you must include `ft`, `'`, or `feet`.

---

## 🔵 Advanced Tier — GUI

### Tech Stack
- Python 3
- `tkinter` (built into Python — no install needed)
- `matplotlib` (for the trend graph)
- `sqlite3` (built into Python — used for persistent storage)

### Features
- ✅ Full GUI window — no command line involved
- ✅ Labeled input fields for weight and height, plus a **Calculate** button
- ✅ Height field accepts **meters, feet, or feet+inches** — same
  auto-detecting parser as the CLI tier (a hint below the field shows the
  accepted formats)
- ✅ Colour-coded result: 🟢 green = Normal, 🟠 amber = Under/Overweight, 🔴 red = Obese
- ✅ Multi-user support — enter any username to keep separate histories
- ✅ Every calculation is saved to a local SQLite database (`bmi_records.db`)
- ✅ **View BMI Trend Graph** button plots a user's BMI over time with matplotlib,
  including reference lines at the 18.5 / 25 / 30 category boundaries
- ✅ All database reads/writes are wrapped in error handling — a DB failure shows
  a friendly popup instead of crashing the app

### Setup
```bash
# from your activated virtual environment
pip install matplotlib
```
> `tkinter` and `sqlite3` ship with standard Python, so no separate install is
> needed for those.

### Run it
```bash
python bmi_calculator_gui.py
```

### How to Use
1. Enter a **user name** (new or existing).
2. Enter **weight (kg)** and **height** — height accepts meters, feet, or
   feet+inches (see the hint text under the field, or the
   [Height Formats](#-height-formats-accepted) table above).
3. Click **Calculate** — the result box updates with your BMI and a colour-coded category.
4. The record is automatically saved to the database under that username.
5. Select a user from the **History & Trend** dropdown and click
   **View BMI Trend Graph** to see their BMI change over time.

---

## ✅ Feature Checklist Status

**Beginner Tier**
- [x] Prompt for weight/height via CLI
- [x] Calculate BMI
- [x] Classify into 4 categories
- [x] Display BMI (2 dp) + category
- [x] Input validation (non-numeric & negative rejection)

**Advanced Tier**
- [x] GUI built with tkinter
- [x] Labeled input fields + Calculate button
- [x] Colour-coded result feedback
- [x] Multi-user support
- [x] Historical records in SQLite
- [x] matplotlib BMI trend graph
- [x] Error handling for database read/write failures

---

## 🛠 Notes & Learnings

- BMI category boundaries use `<` / strict comparisons so edge values
  (e.g. exactly 18.5, 25, 30) fall into the correct next category.
- The GUI stores dates as text (`YYYY-MM-DD HH:MM:SS`) and plots BMI against
  record order rather than a parsed date axis — this keeps the graph dependency-free
  while still showing a clear chronological trend.
- All SQLite operations are centralized in a single `BMIDatabase` class so error
  handling only needs to be written once.

---

## 📌 Environment

- Python 3.10
- Windows + PowerShell
- Virtual environment: `.venv\Scripts\Activate.ps1`
