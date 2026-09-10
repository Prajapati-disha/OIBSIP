"""
Basic Weather App - Advanced Tier
Tkinter GUI with current weather, icons, hourly/daily forecasts,
a C/F toggle, and automatic IP-based location detection.

Setup:
    1. pip install requests pillow
    2. Put your API key in config.py (API_KEY = "...")
    3. Run: python weather_gui.py

Notes on data sources (free tier only):
    - Current weather:  /data/2.5/weather
    - Forecast (hourly + daily): /data/2.5/forecast
      This endpoint returns data in 3-hour steps for 5 days.
      "Hourly" panel = next 6 hours -> the next two 3-hour steps.
      "Daily" panel   = next 5 days -> one entry per day (the ~midday reading).
    - IP geolocation: https://ipinfo.io/json (no key needed for light use)
"""

import io
import threading
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from datetime import datetime

import requests
from PIL import Image, ImageTk

from config import API_KEY

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"
IPINFO_URL = "https://ipinfo.io/json"


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Weather App")
        self.root.geometry("640x600")
        self.root.resizable(False, False)

        self.unit = "metric"  # "metric" = Celsius, "imperial" = Fahrenheit
        self.last_current_data = None
        self.last_forecast_data = None
        self.icon_cache = {}  # keep PhotoImage refs alive

        self._build_layout()

    # ---------- UI construction ----------

    def _build_layout(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="City or ZIP:").pack(side="left")
        self.city_entry = ttk.Entry(top, width=25)
        self.city_entry.pack(side="left", padx=5)
        self.city_entry.bind("<Return>", lambda e: self.on_get_weather())

        ttk.Button(top, text="Get Weather", command=self.on_get_weather).pack(side="left", padx=5)
        ttk.Button(top, text="Use My Location", command=self.on_auto_locate).pack(side="left", padx=5)

        self.unit_button = ttk.Button(top, text="Switch to °F", command=self.toggle_unit)
        self.unit_button.pack(side="left", padx=5)

        # Error / status banner (in-GUI, no terminal prints)
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(self.root, textvariable=self.error_var, foreground="red",
                                      padding=(10, 0))
        self.error_label.pack(fill="x")

        # Current conditions panel
        current_frame = ttk.LabelFrame(self.root, text="Current Weather", padding=10)
        current_frame.pack(fill="x", padx=10, pady=5)

        self.icon_label = ttk.Label(current_frame)
        self.icon_label.pack(side="left", padx=(0, 10))

        info_frame = ttk.Frame(current_frame)
        info_frame.pack(side="left", fill="x", expand=True)

        self.location_var = tk.StringVar(value="—")
        self.temp_var = tk.StringVar(value="—")
        self.desc_var = tk.StringVar(value="—")
        self.humidity_var = tk.StringVar(value="—")
        self.wind_var = tk.StringVar(value="—")

        ttk.Label(info_frame, textvariable=self.location_var, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.temp_var, font=("Segoe UI", 20)).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.desc_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.humidity_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.wind_var).pack(anchor="w")

        # Hourly forecast panel
        hourly_frame = ttk.LabelFrame(self.root, text="Next 6 Hours", padding=10)
        hourly_frame.pack(fill="x", padx=10, pady=5)
        self.hourly_container = ttk.Frame(hourly_frame)
        self.hourly_container.pack(fill="x")

        # Daily forecast panel
        daily_frame = ttk.LabelFrame(self.root, text="Next 5 Days", padding=10)
        daily_frame.pack(fill="x", padx=10, pady=5)
        self.daily_container = ttk.Frame(daily_frame)
        self.daily_container.pack(fill="x")

    # ---------- Helpers ----------

    def show_error(self, message):
        self.error_var.set(message)

    def clear_error(self):
        self.error_var.set("")

    def celsius_to_f(self, c):
        return c * 9 / 5 + 32

    def format_temp(self, temp_c):
        if self.unit == "metric":
            return f"{temp_c:.1f}°C"
        return f"{self.celsius_to_f(temp_c):.1f}°F"

    def load_icon(self, icon_code, size=(60, 60)):
        if icon_code in self.icon_cache:
            return self.icon_cache[icon_code]
        try:
            resp = requests.get(ICON_URL.format(icon=icon_code), timeout=10)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).resize(size)
            photo = ImageTk.PhotoImage(img)
            self.icon_cache[icon_code] = photo
            return photo
        except Exception:
            return None

    # ---------- API key check ----------

    def api_key_ok(self):
        if not API_KEY or API_KEY == "PASTE_YOUR_API_KEY_HERE":
            self.show_error("No API key set. Add your OpenWeatherMap key to config.py.")
            return False
        return True

    # ---------- Actions ----------

    def on_get_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            self.show_error("Please enter a city name or ZIP code.")
            return
        if not self.api_key_ok():
            return
        self.clear_error()
        threading.Thread(target=self._fetch_and_render, args=(city,), daemon=True).start()

    def on_auto_locate(self):
        if not self.api_key_ok():
            return
        self.clear_error()
        threading.Thread(target=self._auto_locate_and_render, daemon=True).start()

    def toggle_unit(self):
        self.unit = "imperial" if self.unit == "metric" else "metric"
        self.unit_button.config(text="Switch to °C" if self.unit == "imperial" else "Switch to °F")
        # Re-render with cached data using the new unit, no new API call needed
        if self.last_current_data and self.last_forecast_data:
            self.root.after(0, self._render_current, self.last_current_data)
            self.root.after(0, self._render_hourly, self.last_forecast_data)
            self.root.after(0, self._render_daily, self.last_forecast_data)

    # ---------- Network calls (run on background thread) ----------

    def _auto_locate_and_render(self):
        try:
            resp = requests.get(IPINFO_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            city = data.get("city")
            if not city:
                self.root.after(0, self.show_error, "Could not detect your location automatically.")
                return
            self.root.after(0, lambda: self.city_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.city_entry.insert(0, city))
            self._fetch_and_render(city)
        except requests.exceptions.RequestException:
            self.root.after(0, self.show_error, "Location detection failed. Check your internet connection.")

    def _fetch_and_render(self, city):
        params = {"appid": API_KEY, "units": "metric"}
        if city.isdigit() and len(city) == 5:
            params["zip"] = f"{city},us"
        else:
            params["q"] = city

        try:
            current_resp = requests.get(CURRENT_URL, params=params, timeout=10)
            if current_resp.status_code == 401:
                self.root.after(0, self.show_error, "Invalid API key. Check config.py.")
                return
            if current_resp.status_code == 404:
                self.root.after(0, self.show_error, f"City '{city}' not found.")
                return
            current_resp.raise_for_status()
            current_data = current_resp.json()

            forecast_resp = requests.get(FORECAST_URL, params=params, timeout=10)
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

        except requests.exceptions.Timeout:
            self.root.after(0, self.show_error, "Request timed out. Check your internet connection.")
            return
        except requests.exceptions.ConnectionError:
            self.root.after(0, self.show_error, "Could not connect to the weather service.")
            return
        except requests.exceptions.RequestException as e:
            self.root.after(0, self.show_error, f"Unexpected error: {e}")
            return

        self.last_current_data = current_data
        self.last_forecast_data = forecast_data

        self.root.after(0, self.clear_error)
        self.root.after(0, self._render_current, current_data)
        self.root.after(0, self._render_hourly, forecast_data)
        self.root.after(0, self._render_daily, forecast_data)

    # ---------- Rendering (run on main thread) ----------

    def _render_current(self, data):
        name = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        self.location_var.set(f"{name}, {country}")

        temp_c = data["main"]["temp"]
        self.temp_var.set(self.format_temp(temp_c))

        desc = data["weather"][0]["description"].title()
        self.desc_var.set(desc)

        self.humidity_var.set(f"Humidity: {data['main']['humidity']}%")
        self.wind_var.set(f"Wind: {data['wind']['speed']} m/s")

        icon_code = data["weather"][0]["icon"]
        photo = self.load_icon(icon_code)
        if photo:
            self.icon_label.config(image=photo)
            self.icon_label.image = photo

    def _render_hourly(self, forecast_data):
        for widget in self.hourly_container.winfo_children():
            widget.destroy()

        entries = forecast_data.get("list", [])[:2]  # 2 steps x 3h = next 6 hours
        for entry in entries:
            frame = ttk.Frame(self.hourly_container, padding=8, relief="groove")
            frame.pack(side="left", padx=5)

            dt = datetime.fromtimestamp(entry["dt"])
            ttk.Label(frame, text=dt.strftime("%I:%M %p")).pack()

            icon_code = entry["weather"][0]["icon"]
            photo = self.load_icon(icon_code, size=(40, 40))
            icon_lbl = ttk.Label(frame, image=photo if photo else None)
            icon_lbl.image = photo
            icon_lbl.pack()

            temp_c = entry["main"]["temp"]
            ttk.Label(frame, text=self.format_temp(temp_c)).pack()

    def _render_daily(self, forecast_data):
        for widget in self.daily_container.winfo_children():
            widget.destroy()

        by_day = defaultdict(list)
        for entry in forecast_data.get("list", []):
            dt = datetime.fromtimestamp(entry["dt"])
            by_day[dt.date()].append(entry)

        days = sorted(by_day.keys())[:5]
        for day in days:
            # Prefer the reading closest to midday for a representative icon/temp
            day_entries = by_day[day]
            best = min(day_entries, key=lambda e: abs(datetime.fromtimestamp(e["dt"]).hour - 12))

            frame = ttk.Frame(self.daily_container, padding=8, relief="groove")
            frame.pack(side="left", padx=5)

            ttk.Label(frame, text=day.strftime("%a %m/%d")).pack()

            icon_code = best["weather"][0]["icon"]
            photo = self.load_icon(icon_code, size=(40, 40))
            icon_lbl = ttk.Label(frame, image=photo if photo else None)
            icon_lbl.image = photo
            icon_lbl.pack()

            temp_c = best["main"]["temp"]
            ttk.Label(frame, text=self.format_temp(temp_c)).pack()


def main():
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
