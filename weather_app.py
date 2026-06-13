"""
╔══════════════════════════════════════════════════╗
║         🌤️  WEATHER APP — Python Mini Project    ║
║         Built with Tkinter + OpenWeatherMap API  ║
╚══════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import font, messagebox
import requests
import json
from datetime import datetime
import threading
import webbrowser

# ──────────────────────────────────────────────────────────────────────────────
# 🔑 CONFIGURATION — Replace with your free API key from openweathermap.org
# ──────────────────────────────────────────────────────────────────────────────
API_KEY = "b997917b5cc8ee8caa32d9bad8b0fcb1"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# ──────────────────────────────────────────────────────────────────────────────
# 🎨 THEME COLORS
# ──────────────────────────────────────────────────────────────────────────────
BG_DARK    = "#1a1a2e"
BG_CARD    = "#16213e"
BG_INPUT   = "#0f3460"
ACCENT     = "#e94560"
TEXT_MAIN  = "#e2e2e2"
TEXT_DIM   = "#7a7a9a"

# ──────────────────────────────────────────────────────────────────────────────
# 🌦️ WEATHER ICONS (emoji-based — works cross-platform without image files)
# ──────────────────────────────────────────────────────────────────────────────
WEATHER_ICONS = {
    "Clear"        : "☀️",
    "Clouds"       : "☁️",
    "Rain"         : "🌧️",
    "Drizzle"      : "🌦️",
    "Thunderstorm" : "⛈️",
    "Snow"         : "❄️",
    "Mist"         : "🌫️",
    "Fog"          : "🌫️",
    "Haze"         : "🌫️",
    "Smoke"        : "🌫️",
    "Dust"         : "🌪️",
    "Sand"         : "🌪️",
    "Tornado"      : "🌪️",
}


# ══════════════════════════════════════════════════════════════════════════════
class WeatherApp:
    """Main Weather Application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🌤️ Weather App")
        self.root.geometry("820x680")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.root.minsize(600, 550)

        # App state
        self.unit          = "metric"   # "metric" = °C | "imperial" = °F
        self.current_city  = ""
        self.unit_var      = tk.StringVar(value="°C")

        # Build fonts
        self._init_fonts()

        # Build all UI sections
        self._build_header()
        self._build_search_bar()
        self._build_unit_toggle()
        self._build_weather_canvas()

        # Show welcome screen
        self._show_welcome()

        # Bind keyboard shortcuts
        self.root.bind("<Control-g>", self._launch_antigravity)   # 🚀 Easter egg!
        self.root.bind("<Escape>",    lambda e: self._show_welcome())

    # ──────────────────────────────────────────────────────────────────────────
    # FONTS
    # ──────────────────────────────────────────────────────────────────────────
    def _init_fonts(self):
        self.f_title    = font.Font(family="Helvetica", size=26, weight="bold")
        self.f_subtitle = font.Font(family="Helvetica", size=13)
        self.f_big_temp = font.Font(family="Helvetica", size=60, weight="bold")
        self.f_label    = font.Font(family="Helvetica", size=11)
        self.f_small    = font.Font(family="Helvetica", size=9)
        self.f_medium   = font.Font(family="Helvetica", size=12, weight="bold")
        self.f_day      = font.Font(family="Helvetica", size=14, weight="bold")

    # ──────────────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_CARD, pady=14)
        header.pack(fill="x")

        tk.Label(header, text="🌤️  Weather App",
                 font=self.f_title, bg=BG_CARD, fg=TEXT_MAIN).pack()

        tk.Label(header, text="Python Mini Project  |  Powered by OpenWeatherMap",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_DIM).pack(pady=(2, 0))

    # ──────────────────────────────────────────────────────────────────────────
    # SEARCH BAR
    # ──────────────────────────────────────────────────────────────────────────
    def _build_search_bar(self):
        bar = tk.Frame(self.root, bg=BG_DARK, pady=18)
        bar.pack(fill="x", padx=50)

        # Entry field
        self.city_entry = tk.Entry(
            bar, font=self.f_subtitle,
            bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            relief="flat", bd=0, width=28
        )
        self.city_entry.pack(side="left", ipady=10, ipadx=14)
        self.city_entry.insert(0, "Enter city name…")
        self.city_entry.bind("<FocusIn>",  self._clear_hint)
        self.city_entry.bind("<FocusOut>", self._restore_hint)
        self.city_entry.bind("<Return>",   lambda e: self.fetch_weather())

        # Search button
        tk.Button(
            bar, text="🔍  Search",
            font=self.f_label, bg=ACCENT, fg="white",
            relief="flat", bd=0, padx=18, pady=10,
            cursor="hand2", activebackground="#c73652",
            activeforeground="white",
            command=self.fetch_weather
        ).pack(side="left", padx=(10, 0))

    # ──────────────────────────────────────────────────────────────────────────
    # UNIT TOGGLE  (°C / °F)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_unit_toggle(self):
        row = tk.Frame(self.root, bg=BG_DARK)
        row.pack()

        for label, value in [("°C  Celsius", "°C"), ("°F  Fahrenheit", "°F")]:
            tk.Radiobutton(
                row, text=label, variable=self.unit_var, value=value,
                bg=BG_DARK, fg=TEXT_MAIN, selectcolor=BG_DARK,
                activebackground=BG_DARK, activeforeground=TEXT_MAIN,
                font=self.f_label, cursor="hand2",
                command=self._on_unit_change
            ).pack(side="left", padx=12)

    # ──────────────────────────────────────────────────────────────────────────
    # SCROLLABLE CANVAS  (main content area)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_weather_canvas(self):
        container = tk.Frame(self.root, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=0, pady=(8, 0))

        self.canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )

        # Resize scroll_frame width with canvas
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(
                                   scrollregion=self.canvas.bbox("all")
                               ))
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER: CLEAR CONTENT FRAME
    # ──────────────────────────────────────────────────────────────────────────
    def _clear_frame(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    # WELCOME SCREEN
    # ──────────────────────────────────────────────────────────────────────────
    def _show_welcome(self):
        self._clear_frame()
        tk.Label(self.scroll_frame,
                 text="\n\n🌍\n\nSearch for any city to see live weather!\n\n"
                      "💡 Tip: Press  Ctrl + G  for a surprise 🚀",
                 font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM,
                 justify="center").pack(expand=True, pady=60)

    # ──────────────────────────────────────────────────────────────────────────
    # PLACEHOLDER ENTRY HINT
    # ──────────────────────────────────────────────────────────────────────────
    def _clear_hint(self, _event):
        if self.city_entry.get() == "Enter city name…":
            self.city_entry.delete(0, "end")
            self.city_entry.config(fg=TEXT_MAIN)

    def _restore_hint(self, _event):
        if not self.city_entry.get().strip():
            self.city_entry.insert(0, "Enter city name…")
            self.city_entry.config(fg=TEXT_DIM)

    # ──────────────────────────────────────────────────────────────────────────
    # UNIT CHANGE
    # ──────────────────────────────────────────────────────────────────────────
    def _on_unit_change(self):
        self.unit = "metric" if self.unit_var.get() == "°C" else "imperial"
        if self.current_city:
            self.fetch_weather()


    # ──────────────────────────────────────────────────────────────────────────
    # FETCH WEATHER  (public entry point)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_weather(self):
        city = self.city_entry.get().strip()

        if not city or city == "Enter city name…":
            messagebox.showwarning("Missing Input", "Please enter a city name!")
            return

        if API_KEY == "YOUR_API_KEY_HERE":
            messagebox.showerror(
                "API Key Missing",
                "Please add your free API key!\n\n"
                "1. Visit openweathermap.org\n"
                "2. Sign up → API Keys\n"
                "3. Paste it in weather_app.py as API_KEY"
            )
            return

        self.current_city = city
        self._show_loading()
        threading.Thread(target=self._fetch_data, args=(city,), daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # LOADING SCREEN
    # ──────────────────────────────────────────────────────────────────────────
    def _show_loading(self):
        self._clear_frame()
        tk.Label(self.scroll_frame,
                 text="\n\n⏳  Fetching weather data…",
                 font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM).pack(pady=80)

    # ──────────────────────────────────────────────────────────────────────────
    # API CALLS  (runs in background thread)
    # ──────────────────────────────────────────────────────────────────────────
    def _fetch_data(self, city: str):
        try:
            # --- Current weather ---
            current_url = (
                f"{BASE_URL}/weather"
                f"?q={city}&appid={API_KEY}&units={self.unit}"
            )
            cur_resp = requests.get(current_url, timeout=10)

            # Handle error codes
            if cur_resp.status_code == 401:
                self.root.after(0, lambda: messagebox.showerror(
                    "Invalid API Key",
                    "Your API key is invalid or not yet activated.\n"
                    "New keys take up to 2 hours to activate."
                ))
                self.root.after(0, self._show_welcome)
                return
            elif cur_resp.status_code == 404:
                self.root.after(0, lambda: messagebox.showerror(
                    "City Not Found",
                    f"'{city}' was not found.\nCheck spelling or try another city."
                ))
                self.root.after(0, self._show_welcome)
                return
            elif cur_resp.status_code != 200:
                self.root.after(0, lambda: messagebox.showerror(
                    "API Error", f"Error {cur_resp.status_code}. Try again."
                ))
                self.root.after(0, self._show_welcome)
                return

            current_data = cur_resp.json()

            # --- 5-day forecast ---
            forecast_url = (
                f"{BASE_URL}/forecast"
                f"?q={city}&appid={API_KEY}&units={self.unit}&cnt=40"
            )
            fc_resp = requests.get(forecast_url, timeout=10)
            forecast_data = fc_resp.json() if fc_resp.status_code == 200 else None

            self.root.after(0, lambda: self._display_weather(current_data, forecast_data))

        except requests.ConnectionError:
            self.root.after(0, lambda: messagebox.showerror(
                "No Internet", "Cannot connect to the server.\nCheck your internet connection."
            ))
            self.root.after(0, self._show_welcome)

        except Exception as err:
            self.root.after(0, lambda: messagebox.showerror("Unexpected Error", str(err)))
            self.root.after(0, self._show_welcome)



    # ──────────────────────────────────────────────────────────────────────────
    # DISPLAY WEATHER  (called on main thread)
    # ──────────────────────────────────────────────────────────────────────────
    def _display_weather(self, data: dict, forecast_data: dict):
        self._clear_frame()

        unit_sym  = "°C" if self.unit == "metric" else "°F"
        spd_unit  = "m/s" if self.unit == "metric" else "mph"
        main      = data["main"]
        weather   = data["weather"][0]
        wind      = data["wind"]
        sys_info  = data["sys"]
        condition = weather["main"]
        icon      = WEATHER_ICONS.get(condition, "🌡️")

        pad = {"padx": 30}

        # ── City & Date ──────────────────────────────────────────────────────
        tk.Label(self.scroll_frame,
                 text=f"📍  {data['name']}, {sys_info['country']}",
                 font=self.f_day, bg=BG_DARK, fg=TEXT_MAIN
                 ).pack(pady=(12, 0), **pad, anchor="w")

        tk.Label(self.scroll_frame,
                 text=datetime.now().strftime("%A, %d %B %Y   •   %I:%M %p"),
                 font=self.f_small, bg=BG_DARK, fg=TEXT_DIM
                 ).pack(anchor="w", **pad)

        # ── Main Card ────────────────────────────────────────────────────────
        card = tk.Frame(self.scroll_frame, bg=BG_CARD, pady=18, padx=24)
        card.pack(fill="x", padx=30, pady=12)

        # Left side: icon + description
        left = tk.Frame(card, bg=BG_CARD)
        left.pack(side="left", expand=True)
        tk.Label(left, text=icon,
                 font=font.Font(size=54), bg=BG_CARD).pack()
        tk.Label(left, text=weather["description"].title(),
                 font=self.f_subtitle, bg=BG_CARD, fg=TEXT_DIM).pack()

        # Right side: temperature
        right = tk.Frame(card, bg=BG_CARD)
        right.pack(side="right", expand=True)
        tk.Label(right,
                 text=f"{round(main['temp'])}{unit_sym}",
                 font=self.f_big_temp, bg=BG_CARD, fg=ACCENT).pack()
        tk.Label(right,
                 text=f"Feels like  {round(main['feels_like'])}{unit_sym}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_DIM).pack()

        # ── Info Grid ────────────────────────────────────────────────────────
        grid_frame = tk.Frame(self.scroll_frame, bg=BG_DARK)
        grid_frame.pack(fill="x", padx=30, pady=(0, 8))

        info_items = [
            ("💧  Humidity",      f"{main['humidity']} %"),
            ("🌬️  Wind Speed",    f"{wind['speed']} {spd_unit}"),
            ("📊  Pressure",      f"{main['pressure']} hPa"),
            ("👁️  Visibility",    f"{data.get('visibility', 'N/A')} m"),
            ("🌡️  Min Temp",      f"{round(main['temp_min'])}{unit_sym}"),
            ("🌡️  Max Temp",      f"{round(main['temp_max'])}{unit_sym}"),
        ]

        for idx, (label, value) in enumerate(info_items):
            row, col = divmod(idx, 3)
            cell = tk.Frame(grid_frame, bg=BG_CARD, padx=14, pady=10)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            grid_frame.columnconfigure(col, weight=1)

            tk.Label(cell, text=label,
                     font=self.f_small, bg=BG_CARD, fg=TEXT_DIM
                     ).pack(anchor="w")
            tk.Label(cell, text=value,
                     font=self.f_medium, bg=BG_CARD, fg=TEXT_MAIN
                     ).pack(anchor="w")

        # ── Sunrise / Sunset ─────────────────────────────────────────────────
        sunrise = datetime.fromtimestamp(sys_info["sunrise"]).strftime("%I:%M %p")
        sunset  = datetime.fromtimestamp(sys_info["sunset"]).strftime("%I:%M %p")

        sun_frame = tk.Frame(self.scroll_frame, bg=BG_CARD, padx=24, pady=12)
        sun_frame.pack(fill="x", padx=30, pady=(0, 8))
        tk.Label(sun_frame, text=f"🌅  Sunrise:  {sunrise}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)
        tk.Label(sun_frame, text=f"🌇  Sunset:  {sunset}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)



        # ── 5-Day Forecast ────────────────────────────────────────────────────
        if forecast_data and "list" in forecast_data:
            tk.Label(self.scroll_frame, text="📅  5-Day Forecast",
                     font=self.f_medium, bg=BG_DARK, fg=TEXT_MAIN
                     ).pack(anchor="w", padx=30, pady=(8, 4))

            fc_row = tk.Frame(self.scroll_frame, bg=BG_DARK)
            fc_row.pack(fill="x", padx=30, pady=(0, 14))

            # Pick one reading per day (closest to noon)
            seen, daily = set(), []
            for item in forecast_data["list"]:
                date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                hour = datetime.fromtimestamp(item["dt"]).hour
                if date not in seen and 11 <= hour <= 14:
                    seen.add(date)
                    daily.append(item)
                if len(daily) == 5:
                    break

            for col_idx, day_item in enumerate(daily):
                day_name   = datetime.fromtimestamp(day_item["dt"]).strftime("%a\n%d %b")
                day_icon   = WEATHER_ICONS.get(day_item["weather"][0]["main"], "🌡️")
                day_temp   = round(day_item["main"]["temp"])
                day_desc   = day_item["weather"][0]["description"].title()

                fc_cell = tk.Frame(fc_row, bg=BG_CARD, padx=10, pady=10)
                fc_cell.grid(row=0, column=col_idx, padx=4, sticky="ew")
                fc_row.columnconfigure(col_idx, weight=1)

                tk.Label(fc_cell, text=day_name,
                         font=self.f_small, bg=BG_CARD, fg=TEXT_DIM,
                         justify="center").pack()
                tk.Label(fc_cell, text=day_icon,
                         font=font.Font(size=24), bg=BG_CARD).pack()
                tk.Label(fc_cell, text=f"{day_temp}{unit_sym}",
                         font=self.f_medium, bg=BG_CARD, fg=TEXT_MAIN).pack()
                tk.Label(fc_cell, text=day_desc,
                         font=self.f_small, bg=BG_CARD, fg=TEXT_DIM,
                         wraplength=90, justify="center").pack()

        # ── Footer hint ───────────────────────────────────────────────────────
        tk.Label(self.scroll_frame,
                 text="🚀  Psst… try pressing  Ctrl + G  !",
                 font=self.f_small, bg=BG_DARK, fg="#333355"
                 ).pack(pady=(4, 16))

        # Scroll to top after render
        self.canvas.yview_moveto(0)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    app  = WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
