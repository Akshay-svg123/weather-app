"""
╔══════════════════════════════════════════════════╗
║         🌤️  WEATHER APP — Python Mini Project    ║
║         Built with Tkinter + OpenWeatherMap API  ║
╚══════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import font, messagebox
import requests
from datetime import datetime
import threading
import logging
import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import configparser
from pathlib import Path

# ──────────────────────────────────────────────────────────────────[...]
# 🔧 LOGGING SETUP
# ──────────────────────────────────────────────────────────────────[...]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────[...]
# 🔑 CONFIGURATION
# ──────────────────────────────────────────────────────────────────[...]
API_KEY = os.getenv("OPENWEATHER_API_KEY", "b997---b5cc8ee-----------------1")
if not API_KEY or API_KEY == "b997---b5cc8ee-------------------1":
    logger.warning("Using hardcoded API key. Set OPENWEATHER_API_KEY environment variable for production.")

BASE_URL = "https://api.openweathermap.org/data/2.5"

# ──────────────────────────────────────────────────────────────────[...]
# 📐 UI CONSTANTS
# ──────────────────────────────────────────────────────────────────[...]
WINDOW_WIDTH, WINDOW_HEIGHT = 840, 710
MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT = 620, 560
SEARCHBAR_HEIGHT, SEARCHBAR_WIDTH = 48, 380
CARD_RADIUS = 14
CARD_RADIUS_LARGE = 18
CARD_RADIUS_SMALL = 12
ICON_SIZE_LARGE = 56
ICON_SIZE_FORECAST = 24
FORECAST_DAYS = 5
FORECAST_HOUR_RANGE = (11, 14)
PAGE_HORIZONTAL_PADDING = 32
API_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_BACKOFF = 2

# ──────────────────────────────────────────────────────────────────[...]
# 🎨 THEME COLORS
# ──────────────────────────────────────────────────────────────────[...]
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
ACCENT = "#e94560"
TEXT_MAIN = "#e2e2e2"
TEXT_DIM = "#7a7a9a"

SEARCHBAR_NORMAL_BG = "#f8f9fa"
SEARCHBAR_HOVER_BG = "#f1f5f9"
SEARCHBAR_FOCUS_BG = "#ffffff"
SEARCHBAR_NORMAL_BORDER = "#cbd5e1"
SEARCHBAR_FOCUS_BORDER = "#3b82f6"
SEARCHBAR_TEXT_COLOR = "#1e293b"
SEARCHBAR_PLACEHOLDER_COLOR = "#94a3b8"
SEARCHBAR_ICON_COLOR = "#64748b"

# ──────────────────────────────────────────────────────────────────[...]
# 🌦️ WEATHER ICONS
# ──────────────────────────────────────────────────────────────────[...]
WEATHER_ICONS = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
    "Smoke": "🌫️",
    "Dust": "🌪️",
    "Sand": "🌪️",
    "Tornado": "🌪️",
}

# ──────────────────────────────────────────────────────────────────[...]
# 💾 CONFIG FILE FOR PERSISTENCE
# ──────────────────────────────────────────────────────────────────[...]
CONFIG_DIR = Path.home() / ".weather_app"
CONFIG_FILE = CONFIG_DIR / "config.ini"


# ──────────────────────────────────────────────────────────────────[...]
# 📊 DATA CLASSES
# ──────────────────────────────────────────────────────────────────[...]
@dataclass
class WeatherInfo:
    """Structured weather data"""
    city: str
    country: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    pressure: int
    visibility: int
    temp_min: float
    temp_max: float
    sunrise: str
    sunset: str
    icon: str
    timestamp: str

    @classmethod
    def from_api(cls, data: dict, unit: str = "metric") -> "WeatherInfo":
        """Create WeatherInfo from API response"""
        if not data or "main" not in data or "weather" not in data:
            raise ValueError("Invalid API response format")

        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]
        sys_info = data["sys"]

        icon = WEATHER_ICONS.get(weather["main"], "🌡️")

        sunrise = datetime.fromtimestamp(sys_info["sunrise"]).strftime("%I:%M %p")
        sunset = datetime.fromtimestamp(sys_info["sunset"]).strftime("%I:%M %p")
        timestamp = datetime.now().strftime("%A, %d %B %Y   •   %I:%M %p")

        return cls(
            city=data["name"],
            country=sys_info["country"],
            temperature=round(main["temp"]),
            feels_like=round(main["feels_like"]),
            description=weather["description"].title(),
            humidity=main["humidity"],
            wind_speed=wind["speed"],
            pressure=main["pressure"],
            visibility=data.get("visibility", 0),
            temp_min=round(main["temp_min"]),
            temp_max=round(main["temp_max"]),
            sunrise=sunrise,
            sunset=sunset,
            icon=icon,
            timestamp=timestamp,
        )


@dataclass
class ForecastDay:
    """5-day forecast data"""
    date: str
    day_name: str
    icon: str
    temperature: float
    description: str

    @classmethod
    def from_api_item(cls, item: dict) -> "ForecastDay":
        """Create ForecastDay from forecast item"""
        dt = datetime.fromtimestamp(item["dt"])
        date = dt.strftime("%Y-%m-%d")
        day_name = dt.strftime("%a\n%d %b")
        icon = WEATHER_ICONS.get(item["weather"][0]["main"], "🌡️")
        temperature = round(item["main"]["temp"])
        description = item["weather"][0]["description"].title()

        return cls(
            date=date,
            day_name=day_name,
            icon=icon,
            temperature=temperature,
            description=description,
        )


# ──────────────────────────────────────────────────────────────────[...]
# 🌐 WEATHER API CLIENT
# ──────────────────────────────────────────────────────────────────[...]
class WeatherAPIClient:
    """Handles all OpenWeatherMap API calls with retry logic"""

    def __init__(self, api_key: str, timeout: int = API_TIMEOUT, max_retries: int = MAX_RETRIES):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        logger.info("WeatherAPIClient initialized")

    def _retry_request(self, url: str) -> requests.Response:
        """Make HTTP request with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request attempt {attempt + 1}/{self.max_retries}: {url}")
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.ConnectionError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Connection failed after {self.max_retries} retries")
                    raise
                wait_time = RETRY_BACKOFF ** attempt
                logger.warning(f"Connection error, retrying in {wait_time}s: {e}")
                import time
                time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise

    def get_current_weather(self, city: str, unit: str = "metric") -> dict:
        """Fetch current weather for a city"""
        url = f"{BASE_URL}/weather?q={city}&appid={self.api_key}&units={unit}"
        logger.info(f"Fetching current weather for: {city}")
        response = self._retry_request(url)
        return response.json()

    def get_forecast(self, city: str, unit: str = "metric", count: int = 40) -> Optional[dict]:
        """Fetch 5-day forecast for a city"""
        url = f"{BASE_URL}/forecast?q={city}&appid={self.api_key}&units={unit}&cnt={count}"
        logger.info(f"Fetching forecast for: {city}")
        try:
            response = self._retry_request(url)
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch forecast: {e}")
            return None


# ──────────────────────────────────────────────────────────────────[...]
# 💾 SETTINGS MANAGER
# ──────────────────────────────────────────────────────────────────[...]
class SettingsManager:
    """Manages persistent app settings"""

    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        CONFIG_DIR.mkdir(exist_ok=True)

    def _load_config(self):
        """Load settings from file"""
        if self.config_file.exists():
            self.config.read(self.config_file)
            logger.info(f"Settings loaded from {self.config_file}")
        else:
            self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize with default settings"""
        if "app" not in self.config:
            self.config["app"] = {}
        self.config["app"]["last_city"] = "London"
        self.config["app"]["unit"] = "°C"
        self._save_config()

    def _save_config(self):
        """Save settings to file"""
        with open(self.config_file, "w") as f:
            self.config.write(f)
        logger.info(f"Settings saved to {self.config_file}")

    def get(self, section: str, key: str, default: str = "") -> str:
        """Get a setting value"""
        try:
            return self.config.get(section, key, fallback=default)
        except Exception:
            return default

    def set(self, section: str, key: str, value: str):
        """Set a setting value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_config()

    def get_last_city(self) -> str:
        """Get the last searched city"""
        return self.get("app", "last_city", "London")

    def set_last_city(self, city: str):
        """Save the last searched city"""
        self.set("app", "last_city", city)


# ──────────────────────────────────────────────────────────────────[...]
# 🎨 UTILITY FUNCTIONS FOR UI
# ──────────────────────────────────────────────────────────────────[...]
def create_label(parent: tk.Widget, text: str, font_obj: font.Font, 
                 color: str = TEXT_MAIN, **kwargs) -> tk.Label:
    """Helper to create styled labels"""
    bg = parent.cget("bg") if hasattr(parent, "cget") else BG_DARK
    return tk.Label(parent, text=text, font=font_obj, bg=bg, fg=color, **kwargs)


# ══════════════════════════════════════════════════════════════════[...]
# 🔵 ROUNDED CARD — Canvas with smooth rounded rectangle background.
# ══════════════════════════════════════════════════════════════════[...]
class RoundedCard(tk.Canvas):
    """Canvas-based rounded rectangle card"""

    def __init__(self, parent, fill=BG_CARD, radius=14,
                 inner_padx=16, inner_pady=12, **kwargs):
        try:
            outer_bg = parent.cget("bg")
        except Exception:
            outer_bg = BG_DARK

        super().__init__(parent, bg=outer_bg, highlightthickness=0, **kwargs)
        self.fill = fill
        self.radius = radius
        self.inner_padx = inner_padx
        self.inner_pady = inner_pady

        self.inner = tk.Frame(self, bg=fill)
        self._wid = self.create_window(inner_padx, inner_pady,
                                       window=self.inner, anchor="nw")

        self.bind("<Configure>", self._on_canvas_resize)
        self.inner.bind("<Configure>", self._on_inner_resize)

    def _on_canvas_resize(self, e):
        self.delete("bg")
        w, h = e.width, e.height
        r = min(self.radius, max(1, w // 2), max(1, h // 2))
        pts = [
            r, 0, w - r, 0,
            w, 0, w, r,
            w, h - r, w, h,
            w - r, h, r, h,
            0, h, 0, h - r,
            0, r, 0, 0,
        ]
        self.create_polygon(pts, smooth=True, fill=self.fill,
                            outline="", tags="bg")
        self.tag_lower("bg")
        self.itemconfig(self._wid, width=max(1, w - 2 * self.inner_padx))

    def _on_inner_resize(self, e):
        new_h = e.height + 2 * self.inner_pady
        self.config(height=new_h)


# ══════════════════════════════════════════════════════════════════[...]
# 🔍 SEARCH BAR
# ══════════════════════════════════════════════════════════════════[...]
class SearchBar(tk.Frame):
    """Custom search bar with rounded pill design"""

    def __init__(self, parent, command, font_subtitle, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.command = command
        self.f_subtitle = font_subtitle

        self.current_bg = SEARCHBAR_NORMAL_BG
        self.current_border = SEARCHBAR_NORMAL_BORDER
        self.is_focused = False

        # Pill Canvas container
        self.canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0,
                               height=SEARCHBAR_HEIGHT, width=SEARCHBAR_WIDTH)
        self.canvas.pack(pady=4)
        self.canvas.bind("<Configure>", self._draw)

        # Icon
        self.icon = tk.Label(self.canvas, text="🔍", bg=self.current_bg,
                            fg=SEARCHBAR_ICON_COLOR, font=("Helvetica", 14))
        self.icon_win = self.canvas.create_window(20, SEARCHBAR_HEIGHT // 2,
                                                  window=self.icon, anchor="w")

        # Entry
        self.entry = tk.Entry(
            self.canvas, font=self.f_subtitle,
            bg=self.current_bg, fg=SEARCHBAR_PLACEHOLDER_COLOR,
            insertbackground=SEARCHBAR_TEXT_COLOR,
            relief="flat", bd=0, width=28
        )
        self.entry_win = self.canvas.create_window(52, SEARCHBAR_HEIGHT // 2,
                                                   window=self.entry, anchor="w")

        self.entry.insert(0, "Search")

        # Bindings
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", lambda e: self.command())
        self.entry.bind("<KeyPress>", self._on_keypress)
        self.entry.bind("<BackSpace>", self._on_backspace)

        for w in (self.canvas, self.icon, self.entry):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def get(self) -> str:
        """Get search value, filtering out placeholder text"""
        val = self.entry.get().strip()
        if val in ("Search", "Type to search"):
            return ""
        return val

    def clear(self):
        """Clear the search bar and reset to placeholder"""
        self.entry.delete(0, "end")
        self.entry.insert(0, "Search")
        self.entry.config(fg=SEARCHBAR_PLACEHOLDER_COLOR)

    def _draw(self, event=None):
        self.canvas.delete("bg")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        r = h // 2  # Perfect circular pill ends

        pts = [
            r, 1, w - r, 1,
            w - 1, 1, w - 1, r,
            w - 1, h - r, w - 1, h - 1,
            w - r, h - 1, r, h - 1,
            1, h - 1, 1, h - r,
            1, r, 1, 1,
        ]
        self.canvas.create_polygon(pts, smooth=True, fill=self.current_bg,
                                   outline=self.current_border, width=2, tags="bg")
        self.canvas.tag_lower("bg")
        self.canvas.coords(self.icon_win, 24, h // 2)
        self.canvas.coords(self.entry_win, 56, h // 2)

    def _update_colors(self):
        self.icon.config(bg=self.current_bg)
        self.entry.config(bg=self.current_bg)
        self._draw()

    def _on_enter(self, e):
        if not self.is_focused:
            self.current_bg = SEARCHBAR_HOVER_BG
            self._update_colors()

    def _on_leave(self, e):
        if not self.is_focused:
            self.current_bg = SEARCHBAR_NORMAL_BG
            self._update_colors()

    def _on_focus_in(self, e):
        self.is_focused = True
        self.current_bg = SEARCHBAR_FOCUS_BG
        self.current_border = SEARCHBAR_FOCUS_BORDER
        if self.entry.get() == "Search":
            self.entry.delete(0, "end")
            self.entry.insert(0, "Type to search")
            self.entry.icursor(0)
        self.entry.config(fg=SEARCHBAR_TEXT_COLOR)
        self._update_colors()

    def _on_focus_out(self, e):
        self.is_focused = False
        self.current_bg = SEARCHBAR_NORMAL_BG
        self.current_border = SEARCHBAR_NORMAL_BORDER
        if not self.get():
            self.entry.delete(0, "end")
            self.entry.insert(0, "Search")
            self.entry.config(fg=SEARCHBAR_PLACEHOLDER_COLOR)
        self._update_colors()

    def _on_keypress(self, e):
        if e.char and e.keysym not in ("BackSpace", "Return", "Tab", "Escape"):
            if self.entry.get() == "Type to search" and \
               self.entry.cget("fg") == SEARCHBAR_PLACEHOLDER_COLOR:
                self.entry.delete(0, "end")
                self.entry.config(fg=SEARCHBAR_TEXT_COLOR)

    def _on_backspace(self, e):
        if self.entry.get() == "Type to search" and \
           self.entry.cget("fg") == SEARCHBAR_PLACEHOLDER_COLOR:
            return "break"


# ══════════════════════════════════════════════════════════════════[...]
# 🌤️ WEATHER APP
# ══════════════════════════════════════════════════════════════════[...]
class WeatherApp:
    """Main weather application"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🌤️ Weather App")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.unit = "metric"
        self.current_city = ""
        self.unit_var = tk.StringVar(value="°C")

        # Initialize managers
        self.settings = SettingsManager()
        self.api_client = WeatherAPIClient(API_KEY)

        self._init_fonts()
        self._build_header()
        self._build_search_section()
        self._build_scroll_area()
        self._show_welcome()

        self.root.bind("<Escape>", lambda e: self._show_welcome())
        
        logger.info("WeatherApp initialized")

    def _init_fonts(self):
        """Initialize all fonts used in the app"""
        self.f_title = font.Font(family="Helvetica", size=26, weight="bold")
        self.f_subtitle = font.Font(family="Helvetica", size=13)
        self.f_big_temp = font.Font(family="Helvetica", size=60, weight="bold")
        self.f_label = font.Font(family="Helvetica", size=11)
        self.f_small = font.Font(family="Helvetica", size=9)
        self.f_medium = font.Font(family="Helvetica", size=12, weight="bold")
        self.f_day = font.Font(family="Helvetica", size=14, weight="bold")

    def _build_header(self):
        """Build the app header"""
        hdr = tk.Frame(self.root, bg=BG_CARD, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌤️  Weather App",
                 font=self.f_title, bg=BG_CARD, fg=TEXT_MAIN).pack()
        tk.Label(hdr, text="Python Mini Project  |  Powered by OpenWeatherMap",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_DIM).pack(pady=(2, 0))

    def _build_search_section(self):
        """Build the search and unit toggle section"""
        outer = tk.Frame(self.root, bg=BG_DARK, pady=22)
        outer.pack(fill="x")

        self.search_bar = SearchBar(outer, command=self.fetch_weather,
                                    font_subtitle=self.f_subtitle)
        self.search_bar.pack()

        # Unit toggle row
        toggle_row = tk.Frame(outer, bg=BG_DARK)
        toggle_row.pack(pady=(10, 0))

        for label, value in [("°C  Celsius", "°C"), ("°F  Fahrenheit", "°F")]:
            tk.Radiobutton(
                toggle_row, text=label,
                variable=self.unit_var, value=value,
                bg=BG_DARK, fg=TEXT_MAIN, selectcolor=BG_DARK,
                activebackground=BG_DARK, activeforeground=TEXT_MAIN,
                font=self.f_small, cursor="hand2",
                command=self._on_unit_change
            ).pack(side="left", padx=14)

    def _build_scroll_area(self):
        """Build the scrollable content area"""
        container = tk.Frame(self.root, bg=BG_DARK)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self._cwin = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._cwin, width=e.width))
        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def _clear_frame(self):
        """Clear all widgets from the scroll frame"""
        for w in self.scroll_frame.winfo_children():
            w.destroy()

    def _show_welcome(self):
        """Display welcome message"""
        self._clear_frame()
        tk.Label(
            self.scroll_frame,
            text="\n\n🌍\n\nSearch for any city to see live weather!",
            font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM,
            justify="center"
        ).pack(expand=True, pady=80)

    def _show_loading(self):
        """Display loading indicator"""
        self._clear_frame()
        tk.Label(
            self.scroll_frame,
            text="\n\n⏳  Fetching weather data…",
            font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM
        ).pack(pady=80)

    def _on_unit_change(self):
        """Handle unit toggle"""
        self.unit = "metric" if self.unit_var.get() == "°C" else "imperial"
        if self.current_city:
            self.fetch_weather()

    def _show_error(self, title: str, message: str):
        """Show error dialog and reset to welcome screen"""
        messagebox.showerror(title, message)
        self.root.after(0, self._show_welcome)
        logger.error(f"{title}: {message}")

    def fetch_weather(self):
        """Fetch weather for the searched city"""
        city = self.search_bar.get()
        if not city:
            messagebox.showwarning("Missing Input", "Please enter a city name!")
            return

        self.current_city = city
        self.settings.set_last_city(city)
        self._show_loading()
        threading.Thread(target=self._fetch_data, args=(city,), daemon=True).start()

    def _fetch_data(self, city: str):
        """Background thread for API calls"""
        try:
            logger.info(f"Fetching weather data for {city}")
            current = self.api_client.get_current_weather(city, self.unit)
            
            # Validate response
            if not current or "main" not in current:
                raise ValueError("Invalid API response")

            forecast = self.api_client.get_forecast(city, self.unit)
            
            # Parse data
            weather_info = WeatherInfo.from_api(current, self.unit)
            forecast_days = self._parse_forecast(forecast) if forecast else []

            self.root.after(0, lambda: self._display_weather(weather_info, forecast_days))
            logger.info(f"Successfully displayed weather for {city}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.root.after(0, lambda: self._show_error(
                    "Invalid API Key",
                    "Your key is invalid or not yet activated.\nNew keys take up to 2 hours to activate."
                ))
            elif e.response.status_code == 404:
                self.root.after(0, lambda: self._show_error(
                    "City Not Found",
                    f"'{city}' not found.\nCheck spelling and try again."
                ))
            else:
                self.root.after(0, lambda: self._show_error(
                    "API Error",
                    f"Error {e.response.status_code}. Try again later."
                ))

        except requests.ConnectionError:
            self.root.after(0, lambda: self._show_error(
                "No Internet",
                "Cannot connect to the API.\nCheck your internet connection."
            ))

        except ValueError as e:
            self.root.after(0, lambda: self._show_error("Invalid Data", str(e)))

        except Exception as e:
            self.root.after(0, lambda: self._show_error("Unexpected Error", str(e)))
            logger.exception(f"Unexpected error fetching weather: {e}")

    def _parse_forecast(self, forecast_data: dict) -> list:
        """Parse forecast data into ForecastDay objects"""
        if not forecast_data or "list" not in forecast_data:
            return []

        seen, daily = set(), []
        for item in forecast_data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date = dt.strftime("%Y-%m-%d")
            hour = dt.hour

            if date not in seen and FORECAST_HOUR_RANGE[0] <= hour <= FORECAST_HOUR_RANGE[1]:
                seen.add(date)
                daily.append(ForecastDay.from_api_item(item))

            if len(daily) == FORECAST_DAYS:
                break

        return daily

    def _display_weather(self, weather: WeatherInfo, forecast_days: list):
        """Display weather information"""
        self._clear_frame()

        unit_sym = "°C" if self.unit == "metric" else "°F"
        spd_unit = "m/s" if self.unit == "metric" else "mph"
        px = PAGE_HORIZONTAL_PADDING

        # Location and time
        tk.Label(
            self.scroll_frame,
            text=f"📍  {weather.city}, {weather.country}",
            font=self.f_day, bg=BG_DARK, fg=TEXT_MAIN
        ).pack(pady=(16, 0), padx=px, anchor="w")

        tk.Label(
            self.scroll_frame,
            text=weather.timestamp,
            font=self.f_small, bg=BG_DARK, fg=TEXT_DIM
        ).pack(padx=px, anchor="w", pady=(0, 4))

        # Main weather card
        main_card = RoundedCard(self.scroll_frame, fill=BG_CARD,
                                radius=CARD_RADIUS_LARGE, inner_padx=28, inner_pady=20)
        main_card.pack(fill="x", padx=px, pady=(6, 10))

        left = tk.Frame(main_card.inner, bg=BG_CARD)
        left.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(left, text=weather.icon,
                 font=font.Font(size=ICON_SIZE_LARGE), bg=BG_CARD).pack(pady=(4, 0))
        tk.Label(left, text=weather.description,
                 font=self.f_subtitle, bg=BG_CARD, fg=TEXT_DIM).pack()

        right = tk.Frame(main_card.inner, bg=BG_CARD)
        right.pack(side="right", expand=True, fill="both", padx=8)
        tk.Label(right, text=f"{weather.temperature}{unit_sym}",
                 font=self.f_big_temp, bg=BG_CARD, fg=ACCENT).pack(pady=(4, 0))
        tk.Label(right, text=f"Feels like  {weather.feels_like}{unit_sym}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_DIM).pack()

        # Info grid
        grid_outer = tk.Frame(self.scroll_frame, bg=BG_DARK)
        grid_outer.pack(fill="x", padx=px, pady=(0, 8))

        for col in range(3):
            grid_outer.columnconfigure(col, weight=1)

        info_items = [
            ("💧 Humidity", f"{weather.humidity} %"),
            ("🌬️ Wind Speed", f"{weather.wind_speed} {spd_unit}"),
            ("📊 Pressure", f"{weather.pressure} hPa"),
            ("👁️ Visibility", f"{weather.visibility} m" if weather.visibility else "N/A"),
            ("🌡️ Min Temp", f"{weather.temp_min}{unit_sym}"),
            ("🌡️ Max Temp", f"{weather.temp_max}{unit_sym}"),
        ]

        for idx, (lbl, val) in enumerate(info_items):
            row, col = divmod(idx, 3)
            cell = RoundedCard(grid_outer, fill=BG_CARD,
                               radius=CARD_RADIUS_SMALL, inner_padx=14, inner_pady=10)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

            tk.Label(cell.inner, text=lbl, font=self.f_small,
                     bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w")
            tk.Label(cell.inner, text=val, font=self.f_medium,
                     bg=BG_CARD, fg=TEXT_MAIN).pack(anchor="w")

        # Sunrise/Sunset
        sun_card = RoundedCard(self.scroll_frame, fill=BG_CARD,
                               radius=CARD_RADIUS_LARGE, inner_padx=28, inner_pady=14)
        sun_card.pack(fill="x", padx=px, pady=(0, 10))
        tk.Label(sun_card.inner, text=f"🌅  Sunrise:  {weather.sunrise}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)
        tk.Label(sun_card.inner, text=f"🌇  Sunset:  {weather.sunset}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)

        # 5-day forecast
        if forecast_days:
            tk.Label(
                self.scroll_frame, text="📅  5-Day Forecast",
                font=self.f_medium, bg=BG_DARK, fg=TEXT_MAIN
            ).pack(anchor="w", padx=px, pady=(4, 6))

            fc_row = tk.Frame(self.scroll_frame, bg=BG_DARK)
            fc_row.pack(fill="x", padx=px, pady=(0, 18))
            for col in range(FORECAST_DAYS):
                fc_row.columnconfigure(col, weight=1)

            for col_i, day in enumerate(forecast_days):
                fc_cell = RoundedCard(fc_row, fill=BG_CARD,
                                      radius=CARD_RADIUS, inner_padx=8, inner_pady=10)
                fc_cell.grid(row=0, column=col_i, padx=4, sticky="ew")

                tk.Label(fc_cell.inner, text=day.day_name, font=self.f_small,
                         bg=BG_CARD, fg=TEXT_DIM, justify="center").pack()
                tk.Label(fc_cell.inner, text=day.icon,
                         font=font.Font(size=ICON_SIZE_FORECAST), bg=BG_CARD).pack()
                tk.Label(fc_cell.inner, text=f"{day.temperature}{unit_sym}",
                         font=self.f_medium, bg=BG_CARD, fg=TEXT_MAIN).pack()
                tk.Label(fc_cell.inner, text=day.description, font=self.f_small,
                         bg=BG_CARD, fg=TEXT_DIM, wraplength=85,
                         justify="center").pack()

        self.canvas.yview_moveto(0)


# ══════════════════════════════════════════════════════════════════[...]
def main():
    """Application entry point"""
    try:
        root = tk.Tk()
        app = WeatherApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
