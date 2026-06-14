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

# ──────────────────────────────────────────────────────────────────────────────
# 🔑 CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
API_KEY  = "b997917b5cc8ee8caa32d9bad8b0fcb1"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# ──────────────────────────────────────────────────────────────────────────────
# 🎨 THEME COLORS
# ──────────────────────────────────────────────────────────────────────────────
BG_DARK   = "#1a1a2e"
BG_CARD   = "#16213e"
ACCENT    = "#e94560"
TEXT_MAIN = "#e2e2e2"
TEXT_DIM  = "#7a7a9a"

# ──────────────────────────────────────────────────────────────────────────────
# 🌦️ WEATHER ICONS
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
# 🔵 ROUNDED CARD — Canvas with a smooth rounded rectangle background.
# ══════════════════════════════════════════════════════════════════════════════
class RoundedCard(tk.Canvas):

    def __init__(self, parent, fill=BG_CARD, radius=14,
                 inner_padx=16, inner_pady=12, **kwargs):
        try:
            outer_bg = parent.cget("bg")
        except Exception:
            outer_bg = BG_DARK

        super().__init__(parent, bg=outer_bg,
                         highlightthickness=0, **kwargs)
        self.fill       = fill
        self.radius     = radius
        self.inner_padx = inner_padx
        self.inner_pady = inner_pady

        self.inner = tk.Frame(self, bg=fill)
        self._wid  = self.create_window(inner_padx, inner_pady,
                                        window=self.inner, anchor="nw")

        self.bind("<Configure>",       self._on_canvas_resize)
        self.inner.bind("<Configure>", self._on_inner_resize)

    def _on_canvas_resize(self, e):
        self.delete("bg")
        w, h = e.width, e.height
        r    = min(self.radius, max(1, w // 2), max(1, h // 2))
        pts  = [
            r, 0,   w-r, 0,
            w, 0,   w,   r,
            w, h-r, w,   h,
            w-r, h, r,   h,
            0, h,   0,   h-r,
            0, r,   0,   0,
        ]
        self.create_polygon(pts, smooth=True, fill=self.fill,
                            outline="", tags="bg")
        self.tag_lower("bg")
        self.itemconfig(self._wid, width=max(1, w - 2 * self.inner_padx))

    def _on_inner_resize(self, e):
        new_h = e.height + 2 * self.inner_pady
        self.config(height=new_h)


# ══════════════════════════════════════════════════════════════════════════════
# 🔍 SEARCH BAR (Big headache)
# ══════════════════════════════════════════════════════════════════════════════
class SearchBar(tk.Frame):
    def __init__(self, parent, command, font_subtitle, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.command = command
        self.f_subtitle = font_subtitle
        
        # Colors from the UI design spec
        self.NORMAL_BG = "#f8f9fa"
        self.HOVER_BG  = "#f1f5f9"
        self.FOCUS_BG  = "#ffffff"
        
        self.NORMAL_BORDER = "#cbd5e1"
        self.FOCUS_BORDER  = "#3b82f6"
        
        self.TEXT_COLOR = "#1e293b"
        self.PLACEHOLDER_COLOR = "#94a3b8"
        
        self.current_bg = self.NORMAL_BG
        self.current_border = self.NORMAL_BORDER
        self.is_focused = False
        
        # Pill Canvas container
        self.canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0, height=48, width=380)
        self.canvas.pack(pady=4)
        self.canvas.bind("<Configure>", self._draw)
        
        # Icon
        self.icon = tk.Label(self.canvas, text="🔍", bg=self.current_bg, fg="#64748b", font=("Helvetica", 14))
        self.icon_win = self.canvas.create_window(20, 24, window=self.icon, anchor="w")
        
        # Entry
        self.entry = tk.Entry(
            self.canvas, font=self.f_subtitle,
            bg=self.current_bg, fg=self.PLACEHOLDER_COLOR,
            insertbackground="#1e293b",
            relief="flat", bd=0, width=28
        )
        self.entry_win = self.canvas.create_window(52, 24, window=self.entry, anchor="w")
        
        self.entry.insert(0, "Search")
        
        # Bindings for functionality
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", lambda e: self.command())
        self.entry.bind("<KeyPress>", self._on_keypress)
        self.entry.bind("<BackSpace>", self._on_backspace)
        
        # Bindings for hover states
        for w in (self.canvas, self.icon, self.entry):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def get(self):
        val = self.entry.get().strip()
        if val in ("Search", "Type to search"):
            return ""
        return val

    def _draw(self, event=None):
        self.canvas.delete("bg")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        r = 24 # Half of height for perfect circular pill ends
        
        pts = [
            r, 1,   w-r, 1,
            w-1, 1,   w-1,   r,
            w-1, h-r, w-1,   h-1,
            w-r, h-1, r,   h-1,
            1, h-1,   1,   h-r,
            1, r,   1,   1,
        ]
        self.canvas.create_polygon(pts, smooth=True, fill=self.current_bg, 
                                   outline=self.current_border, width=2, tags="bg")
        self.canvas.tag_lower("bg")
        self.canvas.coords(self.icon_win, 24, h//2)
        self.canvas.coords(self.entry_win, 56, h//2)

    def _update_colors(self):
        self.icon.config(bg=self.current_bg)
        self.entry.config(bg=self.current_bg)
        self._draw()

    def _on_enter(self, e):
        if not self.is_focused:
            self.current_bg = self.HOVER_BG
            self._update_colors()

    def _on_leave(self, e):
        if not self.is_focused:
            self.current_bg = self.NORMAL_BG
            self._update_colors()

    def _on_focus_in(self, e):
        self.is_focused = True
        self.current_bg = self.FOCUS_BG
        self.current_border = self.FOCUS_BORDER
        if self.entry.get() == "Search":
            self.entry.delete(0, "end")
            self.entry.insert(0, "Type to search")
            self.entry.icursor(0)
        self._update_colors()

    def _on_focus_out(self, e):
        self.is_focused = False
        self.current_bg = self.NORMAL_BG
        self.current_border = self.NORMAL_BORDER
        if not self.get():
            self.entry.delete(0, "end")
            self.entry.insert(0, "Search")
            self.entry.config(fg=self.PLACEHOLDER_COLOR)
        self._update_colors()

    def _on_keypress(self, e):
        # Clear placeholder immediately on printable keystroke
        if e.char and e.keysym not in ("BackSpace", "Return", "Tab", "Escape"):
            if self.entry.get() == "Type to search" and self.entry.cget("fg") == self.PLACEHOLDER_COLOR:
                self.entry.delete(0, "end")
                self.entry.config(fg=self.TEXT_COLOR)

    def _on_backspace(self, e):
        # Prevent backspace from removing placeholder characters
        if self.entry.get() == "Type to search" and self.entry.cget("fg") == self.PLACEHOLDER_COLOR:
            return "break"


# ══════════════════════════════════════════════════════════════════════════════
# 🌤️ WEATHER APP (Even more bigger headache 🤕)
# ══════════════════════════════════════════════════════════════════════════════
class WeatherApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🌤️ Weather App")
        self.root.geometry("840x710")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.root.minsize(620, 560)

        self.unit         = "metric"
        self.current_city = ""
        self.unit_var     = tk.StringVar(value="°C")

        self._init_fonts()
        self._build_header()
        self._build_search_section()
        self._build_scroll_area()
        self._show_welcome()

        self.root.bind("<Escape>", lambda e: self._show_welcome())

    def _init_fonts(self):
        self.f_title    = font.Font(family="Helvetica", size=26, weight="bold")
        self.f_subtitle = font.Font(family="Helvetica", size=13)
        self.f_big_temp = font.Font(family="Helvetica", size=60, weight="bold")
        self.f_label    = font.Font(family="Helvetica", size=11)
        self.f_small    = font.Font(family="Helvetica", size=9)
        self.f_medium   = font.Font(family="Helvetica", size=12, weight="bold")
        self.f_day      = font.Font(family="Helvetica", size=14, weight="bold")

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_CARD, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌤️  Weather App",
                 font=self.f_title, bg=BG_CARD, fg=TEXT_MAIN).pack()
        tk.Label(hdr, text="Python Mini Project  |  Powered by OpenWeatherMap",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_DIM).pack(pady=(2, 0))

    def _build_search_section(self):
        outer = tk.Frame(self.root, bg=BG_DARK, pady=22)
        outer.pack(fill="x")

        # Custom Search Bar Replacement
        self.search_bar = SearchBar(outer, command=self.fetch_weather, font_subtitle=self.f_subtitle)
        self.search_bar.pack()

        # Unit toggle row ──────────────────────────────────────────────────────
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
        container = tk.Frame(self.root, bg=BG_DARK)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self._cwin = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._cwin, width=e.width))
        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(
                                   scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(
                                 -1 * (e.delta // 120), "units"))

    def _clear_frame(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

    def _show_welcome(self):
        self._clear_frame()
        tk.Label(
            self.scroll_frame,
            text="\n\n🌍\n\nSearch for any city to see live weather!",
            font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM,
            justify="center"
        ).pack(expand=True, pady=80)

    def _show_loading(self):
        self._clear_frame()
        tk.Label(
            self.scroll_frame,
            text="\n\n⏳  Fetching weather data…",
            font=self.f_subtitle, bg=BG_DARK, fg=TEXT_DIM
        ).pack(pady=80)

    def _on_unit_change(self):
        self.unit = "metric" if self.unit_var.get() == "°C" else "imperial"
        if self.current_city:
            self.fetch_weather()

    def fetch_weather(self):
        # We now query our custom SearchBar for the value
        city = self.search_bar.get()
        if not city:
            messagebox.showwarning("Missing Input", "Please enter a city name!")
            return

        self.current_city = city
        self._show_loading()
        threading.Thread(target=self._fetch_data, args=(city,), daemon=True).start()

    def _fetch_data(self, city: str):
        try:
            cur_url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units={self.unit}"
            cr = requests.get(cur_url, timeout=10)

            if cr.status_code == 401:
                self.root.after(0, lambda: messagebox.showerror(
                    "Invalid API Key",
                    "Your key is invalid or not yet activated.\n"
                    "New keys take up to 2 hours to activate."))
                self.root.after(0, self._show_welcome); return

            if cr.status_code == 404:
                self.root.after(0, lambda: messagebox.showerror(
                    "City Not Found", f"'{city}' not found.\nCheck spelling."))
                self.root.after(0, self._show_welcome); return

            if cr.status_code != 200:
                self.root.after(0, lambda: messagebox.showerror(
                    "API Error", f"Error {cr.status_code}. Try again."))
                self.root.after(0, self._show_welcome); return

            current = cr.json()

            fc_url   = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units={self.unit}&cnt=40"
            fr       = requests.get(fc_url, timeout=10)
            forecast = fr.json() if fr.status_code == 200 else None

            self.root.after(0, lambda: self._display_weather(current, forecast))

        except requests.ConnectionError:
            self.root.after(0, lambda: messagebox.showerror(
                "No Internet", "Cannot connect.\nCheck your internet connection."))
            self.root.after(0, self._show_welcome)

        except Exception as err:
            self.root.after(0, lambda: messagebox.showerror("Error", str(err)))
            self.root.after(0, self._show_welcome)

    def _display_weather(self, data: dict, forecast_data: dict):
        self._clear_frame()

        unit_sym = "°C" if self.unit == "metric" else "°F"
        spd_unit = "m/s" if self.unit == "metric" else "mph"
        main     = data["main"]
        weather  = data["weather"][0]
        wind     = data["wind"]
        sys_info = data["sys"]
        icon     = WEATHER_ICONS.get(weather["main"], "🌡️")
        PX       = 32          # page horizontal padding

        tk.Label(
            self.scroll_frame,
            text=f"📍  {data['name']}, {sys_info['country']}",
            font=self.f_day, bg=BG_DARK, fg=TEXT_MAIN
        ).pack(pady=(16, 0), padx=PX, anchor="w")

        tk.Label(
            self.scroll_frame,
            text=datetime.now().strftime("%A, %d %B %Y   •   %I:%M %p"),
            font=self.f_small, bg=BG_DARK, fg=TEXT_DIM
        ).pack(padx=PX, anchor="w", pady=(0, 4))

        main_card = RoundedCard(self.scroll_frame, fill=BG_CARD,
                                radius=18, inner_padx=28, inner_pady=20)
        main_card.pack(fill="x", padx=PX, pady=(6, 10))

        left = tk.Frame(main_card.inner, bg=BG_CARD)
        left.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(left, text=icon,
                 font=font.Font(size=56), bg=BG_CARD).pack(pady=(4, 0))
        tk.Label(left, text=weather["description"].title(),
                 font=self.f_subtitle, bg=BG_CARD, fg=TEXT_DIM).pack()

        right = tk.Frame(main_card.inner, bg=BG_CARD)
        right.pack(side="right", expand=True, fill="both", padx=8)
        tk.Label(right, text=f"{round(main['temp'])}{unit_sym}",
                 font=self.f_big_temp, bg=BG_CARD, fg=ACCENT).pack(pady=(4, 0))
        tk.Label(right, text=f"Feels like  {round(main['feels_like'])}{unit_sym}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_DIM).pack()

        grid_outer = tk.Frame(self.scroll_frame, bg=BG_DARK)
        grid_outer.pack(fill="x", padx=PX, pady=(0, 8))

        for col in range(3):
            grid_outer.columnconfigure(col, weight=1)

        info_items = [
            ("💧 Humidity",   f"{main['humidity']} %"),
            ("🌬️ Wind Speed", f"{wind['speed']} {spd_unit}"),
            ("📊 Pressure",   f"{main['pressure']} hPa"),
            ("👁️ Visibility", f"{data.get('visibility', 'N/A')} m"),
            ("🌡️ Min Temp",   f"{round(main['temp_min'])}{unit_sym}"),
            ("🌡️ Max Temp",   f"{round(main['temp_max'])}{unit_sym}"),
        ]

        for idx, (lbl, val) in enumerate(info_items):
            row, col = divmod(idx, 3)
            cell = RoundedCard(grid_outer, fill=BG_CARD,
                               radius=12, inner_padx=14, inner_pady=10)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

            tk.Label(cell.inner, text=lbl, font=self.f_small,
                     bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w")
            tk.Label(cell.inner, text=val, font=self.f_medium,
                     bg=BG_CARD, fg=TEXT_MAIN).pack(anchor="w")

        sunrise = datetime.fromtimestamp(sys_info["sunrise"]).strftime("%I:%M %p")
        sunset  = datetime.fromtimestamp(sys_info["sunset"]).strftime("%I:%M %p")

        sun_card = RoundedCard(self.scroll_frame, fill=BG_CARD,
                               radius=18, inner_padx=28, inner_pady=14)
        sun_card.pack(fill="x", padx=PX, pady=(0, 10))
        tk.Label(sun_card.inner, text=f"🌅  Sunrise:  {sunrise}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)
        tk.Label(sun_card.inner, text=f"🌇  Sunset:  {sunset}",
                 font=self.f_label, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left", padx=20)

        if forecast_data and "list" in forecast_data:
            tk.Label(
                self.scroll_frame, text="📅  5-Day Forecast",
                font=self.f_medium, bg=BG_DARK, fg=TEXT_MAIN
            ).pack(anchor="w", padx=PX, pady=(4, 6))

            fc_row = tk.Frame(self.scroll_frame, bg=BG_DARK)
            fc_row.pack(fill="x", padx=PX, pady=(0, 18))
            for col in range(5):
                fc_row.columnconfigure(col, weight=1)

            seen, daily = set(), []
            for item in forecast_data["list"]:
                date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                hour = datetime.fromtimestamp(item["dt"]).hour
                if date not in seen and 11 <= hour <= 14:
                    seen.add(date); daily.append(item)
                if len(daily) == 5:
                    break

            for col_i, day_item in enumerate(daily):
                day_name = datetime.fromtimestamp(day_item["dt"]).strftime("%a\n%d %b")
                day_icon = WEATHER_ICONS.get(day_item["weather"][0]["main"], "🌡️")
                day_temp = round(day_item["main"]["temp"])
                day_desc = day_item["weather"][0]["description"].title()

                fc_cell = RoundedCard(fc_row, fill=BG_CARD,
                                      radius=14, inner_padx=8, inner_pady=10)
                fc_cell.grid(row=0, column=col_i, padx=4, sticky="ew")

                tk.Label(fc_cell.inner, text=day_name, font=self.f_small,
                         bg=BG_CARD, fg=TEXT_DIM, justify="center").pack()
                tk.Label(fc_cell.inner, text=day_icon,
                         font=font.Font(size=24), bg=BG_CARD).pack()
                tk.Label(fc_cell.inner, text=f"{day_temp}{unit_sym}",
                         font=self.f_medium, bg=BG_CARD, fg=TEXT_MAIN).pack()
                tk.Label(fc_cell.inner, text=day_desc, font=self.f_small,
                         bg=BG_CARD, fg=TEXT_DIM, wraplength=85,
                         justify="center").pack()

        self.canvas.yview_moveto(0)


# ══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
