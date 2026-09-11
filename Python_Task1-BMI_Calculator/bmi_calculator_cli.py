"""
TASK 2 - BMI CALCULATOR (Beginner / CLI Tier)
================================================
A command-line program that:
  1. Asks the user for weight (kg) and height (m / ft / ft+in - any format!)
  2. Calculates BMI using: BMI = weight / (height in meters ** 2)
  3. Classifies the result into a standard health category
  4. Displays the BMI (2 decimal places) and the category
  5. Validates input -> rejects non-numeric and negative values

Run it with:  python bmi_calculator_cli.py
"""

import re

# ---------------------------------------------------------------------------
# STEP 0: Height unit conversion - accepts meters, feet, or feet + inches
# ---------------------------------------------------------------------------
# Users can type height in ANY of these formats and we'll auto-detect it:
#   Meters          -> "1.75", "1.75m", "1.75 meters", "1.75 metres"
#   Feet only       -> "5.5ft", "5.5 ft", "5.5'", "5.5 feet"
#   Feet + inches   -> "5'6\"", "5' 6\"", "5ft 6in", "5 ft 6 in", "5'6"
# ---------------------------------------------------------------------------
FEET_TO_METERS = 0.3048

# Regex patterns are checked in this order: most specific (feet+inches)
# first, then feet-only, then meters as the fallback/default.
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
    Takes whatever the user typed for height and converts it to meters,
    auto-detecting whether they used meters, feet, or feet+inches.

    Raises ValueError (with a helpful message) if the text can't be
    understood or represents a non-positive value.
    """
    text = raw_text.strip().lower()
    if not text:
        raise ValueError("Height cannot be empty.")

    # --- Try "feet + inches" first (it's the most specific pattern) ---
    match = FEET_INCHES_RE.match(text)
    if match:
        feet, inches = float(match.group(1)), float(match.group(2))
        total_feet = feet + (inches / 12)
        if total_feet <= 0:
            raise ValueError("Height must be a positive value.")
        return round(total_feet * FEET_TO_METERS, 4)

    # --- Try "feet only" next ---
    match = FEET_ONLY_RE.match(text)
    if match:
        feet = float(match.group(1))
        if feet <= 0:
            raise ValueError("Height must be a positive value.")
        return round(feet * FEET_TO_METERS, 4)

    # --- Fall back to "meters" (also the default for a bare number) ---
    match = METERS_RE.match(text)
    if match:
        meters = float(match.group(1))
        if meters <= 0:
            raise ValueError("Height must be a positive value.")
        return round(meters, 4)

    # Nothing matched -> the text wasn't a recognisable height format.
    raise ValueError(
        "Could not understand that height. Try formats like: "
        "1.75, 1.75m, 5.5ft, 5.5', 5'6\", or 5ft 6in."
    )


# ---------------------------------------------------------------------------
# STEP 1: Reusable, validated input helpers
# ---------------------------------------------------------------------------
def get_positive_float(prompt: str) -> float:
    """
    Keeps asking the user for input until they type a valid, positive number.
    Used for WEIGHT, which is always in kg (no multi-format needed).

    Why a loop?  We don't want the program to crash if the user types
    something like "abc" or "-5". Instead, we catch the bad input,
    print a helpful message, and ask again.
    """
    while True:
        raw_value = input(prompt).strip()

        # --- Validation Check 1: Is it a number at all? ---
        try:
            value = float(raw_value)
        except ValueError:
            # float() raises ValueError if the text can't be converted,
            # e.g. "abc", "", "12kg", etc.
            print("  -> Invalid input: please enter a numeric value (e.g. 65.5).\n")
            continue  # go back to the top of the loop and ask again

        # --- Validation Check 2: Is it positive? ---
        if value <= 0:
            print("  -> Invalid input: value must be greater than 0.\n")
            continue

        # If we reach here, the value passed both checks.
        return value


def get_height_in_meters(prompt: str) -> float:
    """
    Keeps asking the user for a height until it can be parsed (in meters,
    feet, or feet+inches) and converted to a positive number of meters.
    """
    while True:
        raw_value = input(prompt)
        try:
            return parse_height_to_meters(raw_value)
        except ValueError as e:
            print(f"  -> Invalid input: {e}\n")
            continue


# ---------------------------------------------------------------------------
# STEP 2: Calculate BMI
# ---------------------------------------------------------------------------
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    Standard BMI formula: weight (kg) / height (m) squared.
    """
    return weight_kg / (height_m ** 2)


# ---------------------------------------------------------------------------
# STEP 3: Classify BMI into a health category
# ---------------------------------------------------------------------------
def classify_bmi(bmi: float) -> str:
    """
    Standard WHO-style BMI categories:
        Underweight : BMI < 18.5
        Normal      : 18.5 <= BMI < 25
        Overweight  : 25   <= BMI < 30
        Obese       : BMI >= 30
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:          # i.e. 18.5 <= bmi < 25 (previous branch handled < 18.5)
        return "Normal"
    elif bmi < 30:           # i.e. 25 <= bmi < 30
        return "Overweight"
    else:                     # bmi >= 30
        return "Obese"


# ---------------------------------------------------------------------------
# STEP 4: Tie it all together
# ---------------------------------------------------------------------------
def main():
    print("=" * 50)
    print("           BMI CALCULATOR (CLI)")
    print("=" * 50)

    while True:
        # 1. Get validated input from the user
        weight = get_positive_float("Enter your weight in kg: ")
        height = get_height_in_meters(
            "Enter your height (m, ft, or ft+in - e.g. 1.75, 5.5ft, 5'6\"): "
        )

        # 2. Calculate BMI
        bmi = calculate_bmi(weight, height)

        # 3. Classify it
        category = classify_bmi(bmi)

        # 4. Display result, rounded to 2 decimal places
        print("\n" + "-" * 50)
        print(f"  Weight       : {weight} kg")
        print(f"  Height       : {height} m")
        print(f"  Your BMI     : {round(bmi, 2)}")
        print(f"  Category     : {category}")
        print("-" * 50 + "\n")

        # Ask if the user wants to run it again
        again = input("Calculate another BMI? (y/n): ").strip().lower()
        if again != "y":
            print("\nThanks for using the BMI Calculator. Goodbye!")
            break


# ---------------------------------------------------------------------------
# Standard Python entry-point guard
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
