"""
Random Password Generator — Beginner Tier
--------------------------------------------
Command-line tool that builds a password from user-chosen character sets.

Concepts demonstrated:
- The `random` module for generating random values (NOTE: not cryptographically
  secure — see the Advanced tier, which switches to `secrets`)
- The `string` module's pre-built character constants
- Input validation with a retry loop
- List comprehensions / random.choice in a loop to build a string
"""

import random
import string


def get_length():
    """Ask the user for a password length, re-prompting until valid."""
    while True:
        raw = input("Password length (minimum 8): ").strip()
        if not raw.isdigit():
            print("  -> Please enter a whole number.")
            continue
        length = int(raw)
        if length < 8:
            print("  -> Length must be at least 8 characters.")
            continue
        return length


def get_character_types():
    """Ask which character types to include; require at least 2."""
    print("\nWhich character types should the password include?")
    print("(Answer y/n for each)")

    choices = {
        "uppercase": input("  Include UPPERCASE letters? (y/n): ").strip().lower() == "y",
        "lowercase": input("  Include lowercase letters? (y/n): ").strip().lower() == "y",
        "numbers":   input("  Include numbers?           (y/n): ").strip().lower() == "y",
        "symbols":   input("  Include symbols (!@#$...)? (y/n): ").strip().lower() == "y",
    }

    selected_count = sum(choices.values())
    if selected_count < 2:
        print("  -> You must select at least 2 character types. Let's try again.\n")
        return get_character_types()  # simple recursive retry

    return choices


def build_character_pool(choices):
    """Turn the yes/no choices into one big string of allowed characters."""
    pool = ""
    if choices["uppercase"]:
        pool += string.ascii_uppercase       # 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if choices["lowercase"]:
        pool += string.ascii_lowercase       # 'abcdefghijklmnopqrstuvwxyz'
    if choices["numbers"]:
        pool += string.digits                # '0123456789'
    if choices["symbols"]:
        pool += string.punctuation           # '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    return pool


def generate_password(length, pool):
    """Pick `length` random characters from the pool."""
    # random.choice picks ONE random character from the pool each time.
    # We do this `length` times, then join the results into a single string.
    return "".join(random.choice(pool) for _ in range(length))


def main():
    print("=== Random Password Generator (Beginner Tier) ===\n")

    while True:
        length = get_length()
        choices = get_character_types()
        pool = build_character_pool(choices)

        password = generate_password(length, pool)
        print(f"\nYour generated password:\n  {password}\n")

        again = input("Generate another password? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break
        print()  # spacing before next round


if __name__ == "__main__":
    main()
