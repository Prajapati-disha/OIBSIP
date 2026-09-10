# Basic Weather App

A weather app with two versions:
- `weather_cli.py` — beginner, command-line
- `weather_gui.py` — advanced, tkinter GUI with icons, forecasts, unit toggle, and IP auto-locate

## 1. Get an API key

1. Sign up free at https://openweathermap.org/api
2. Go to your account → **My API Keys**
3. Copy your key
4. **Note:** a brand-new key can take up to 2 hours to activate. If you get a
   "401 Invalid API key" error right away, just wait and try again later.

## 2. Configure the app

Open `config.py` and paste your key:

```python
API_KEY = "your_actual_key_here"
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `tkinter` is missing (only needed for the GUI version):
- **Windows / Mac:** it's bundled with the standard Python installer — reinstall
  Python from python.org and make sure "tcl/tk" is checked.
- **Linux (Debian/Ubuntu):** `sudo apt-get install python3-tk`
- **Linux (Fedora):** `sudo dnf install python3-tkinter`

## 4. Run it

Beginner CLI:
```bash
python weather_cli.py
```

Advanced GUI:
```bash
python weather_gui.py
```

## What each version does

### CLI (`weather_cli.py`)
- Prompts for a city name or 5-digit US ZIP code
- Rejects empty input and re-prompts
- Fetches current weather (temp in °C and °F, humidity, condition, wind speed)
- Handles: city not found (404), bad API key (401), timeouts, connection errors

### GUI (`weather_gui.py`)
- Window with city input, "Get Weather" button, and results panel
- Weather condition icons pulled from OpenWeatherMap's icon CDN
- "Next 6 Hours" panel (two 3-hour forecast steps from the free 5-day/3-hour API)
- "Next 5 Days" panel (one representative reading per day, closest to midday)
- Celsius/Fahrenheit toggle button (re-renders cached data instantly, no extra API call)
- "Use My Location" button — auto-detects your city via ipinfo.io based on your IP
- All errors shown as a red banner inside the window, never printed to a terminal

## Notes on API limitations (free tier)

OpenWeatherMap's free tier doesn't include true hourly or long-range daily
forecasts — those require a paid "One Call" subscription. This app works
around that using the free **5 day / 3 hour forecast** endpoint:
- "Hourly" = the next two 3-hour data points (~6 hours out)
- "Daily" = one representative reading per calendar day for the next 5 days

This is a reasonable approximation and keeps the whole project on the free tier.
