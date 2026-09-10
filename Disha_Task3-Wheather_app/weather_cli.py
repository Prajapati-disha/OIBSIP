"""
Basic Weather App - Beginner Tier
Command-line tool that fetches real-time weather from OpenWeatherMap.

Setup:
    1. pip install requests
    2. Put your API key in config.py (API_KEY = "...")
    3. Run: python weather_cli.py
"""

import requests
from config import API_KEY

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_city_input():
    """Prompt the user for a city name or ZIP code, rejecting empty input."""
    while True:
        city = input("Enter a city name or ZIP code: ").strip()
        if city:
            return city
        print("City/ZIP cannot be empty. Please try again.")


def fetch_weather(location, api_key):
    """
    Call the OpenWeatherMap API and return the parsed JSON.
    Raises requests exceptions or ValueError on failure; caller handles them.
    """
    # OpenWeatherMap accepts a plain city name via 'q'.
    # A 5-digit input is treated as a US ZIP code via 'zip'.
    params = {"appid": api_key, "units": "metric"}
    if location.isdigit() and len(location) == 5:
        params["zip"] = f"{location},us"
    else:
        params["q"] = location

    response = requests.get(BASE_URL, params=params, timeout=10)

    if response.status_code == 401:
        raise ValueError("Invalid API key. Check config.py and make sure the key is active.")
    if response.status_code == 404:
        raise ValueError(f"Could not find a location matching '{location}'.")
    response.raise_for_status()  # raises for any other HTTP error (e.g. 5xx)

    return response.json()


def display_weather(data):
    """Print formatted weather details from the API response."""
    name = data.get("name", "Unknown location")
    country = data.get("sys", {}).get("country", "")

    temp_c = data["main"]["temp"]
    temp_f = temp_c * 9 / 5 + 32
    feels_like_c = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"].title()
    wind_speed = data["wind"]["speed"]  # meters/sec

    print("\n" + "=" * 40)
    print(f"Weather for {name}, {country}")
    print("=" * 40)
    print(f"Condition:     {description}")
    print(f"Temperature:   {temp_c:.1f}°C  /  {temp_f:.1f}°F")
    print(f"Feels like:    {feels_like_c:.1f}°C")
    print(f"Humidity:      {humidity}%")
    print(f"Wind speed:    {wind_speed} m/s")
    print("=" * 40 + "\n")


def main():
    print("=== Basic Weather App ===\n")

    if API_KEY == "PASTE_YOUR_API_KEY_HERE" or not API_KEY:
        print("ERROR: You need to set your API key in config.py before running this app.")
        return

    city = get_city_input()

    try:
        data = fetch_weather(city, API_KEY)
        display_weather(data)
    except ValueError as e:
        # Known/expected errors: bad city, bad key
        print(f"Error: {e}")
    except requests.exceptions.Timeout:
        print("Error: The request timed out. Check your internet connection and try again.")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the weather service. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        print(f"Error: An unexpected network error occurred: {e}")


if __name__ == "__main__":
    main()
