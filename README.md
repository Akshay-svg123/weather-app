# weather-app
I created a Easy yet complex weather app using Python and GUI(Tkinter) and also with the help of openweathermap.org for it API key.

# 🌤️ Weather App
### Python Mini Project — I Year

> A beautiful real-time weather application built with **Python**, **Tkinter**, and the **OpenWeatherMap API**.  

---

## 📸 Features

| Feature | Details |
|---|---|
| 🔍 City Search | Search weather for any city in the world |
| 🌡️ Current Weather | Temperature, feels-like, description & icon |
| 💧 Detailed Stats | Humidity, Wind Speed, Pressure, Visibility |
| 🌅 Sun Times | Sunrise and sunset for the searched city |
| 📅 5-Day Forecast | Daily weather predictions for the next 5 days |
| 🔄 Unit Toggle | Switch between °Celsius and °Fahrenheit |
| 🌐 Live Data | Real-time data via OpenWeatherMap API |
| 🎨 Dark Theme UI | Clean, modern dark-themed interface |

---

## 🛠️ Technologies Used

```
Language   : Python 3.x
GUI        : Tkinter (built-in)
API        : OpenWeatherMap (free tier)
Libraries  : requests, threading, json, datetime, webbrowser
```

---

## 📁 Project Structure

```
weather-app/
│
├── weather_app.py     ← Main application (run this!)
├── requirements.txt   ← Python dependencies
└── README.md          ← Project documentation (this file)
```

---

## ⚙️ Setup & Installation

### Step 1 — Clone this Repository
```bash
git clone https://github.com/YOUR_USERNAME/weather-app.git
cd weather-app
```

### Step 2 — Install the Required Library
```bash
pip install requests
```

### Step 3 — Get a Free API Key
1. Go to [openweathermap.org](https://openweathermap.org)
2. Click **Sign Up** and create a free account
3. Go to your account → **API Keys**
4. Copy your API key *(new keys activate within 2 hours)*

### Step 4 — Add Your API Key
Open `weather_app.py` and find this line near the top:
```python
API_KEY = "YOUR_API_KEY_HERE"
```
Replace it with your actual key:
```python
API_KEY = "b997917b5cc8ee8caa32d9bad8b0fcb1"
```

### Step 5 — Run the App:
```bash
python weather_app.py
```

---

## 🚀 How to Use

1. **Launch** the app by running `weather_app.py`
2. **Type** any city name in the search box (e.g., `Mumbai`, `New York`, `London`)
3. **Press Enter** or click **🔍 Search**
4. View the current weather + 5-day forecast
5. Toggle **°C / °F** to switch temperature units

---

## 🐍 Python Concepts Used

This project covers the following programming concepts:

- **APIs** — Calling the OpenWeatherMap REST API with `requests`
- **JSON Parsing** — Extracting weather data from JSON responses
- **OOP** — App is structured as a Python class (`WeatherApp`)
- **Tkinter GUI** — Widgets: Label, Entry, Button, Frame, Canvas, Scrollbar, Radiobutton
- **Threading** — Background API calls so the UI never freezes
- **Error Handling** — `try/except` for network and API errors
- **Event Binding** — Keyboard shortcuts (`Enter`, `Escape`)
- **datetime** — Formatting timestamps for sunrise/sunset & date display

---

## 📦 Dependencies

```
requests==2.31.0
```
All other libraries (`tkinter`, `threading`, `json`, `datetime`, `webbrowser`, `antigravity`) are part of Python's standard library — no extra installation needed!

---

## 👨‍💻 Developer

| Field | Details |
|---|---|
| **Name** | [Your Name] |
| **Roll No** | [Your Roll Number] |
| **Course** | Python Programming — I Year |
| **Project Type** | Mini Project (Summer Break Assignment) |

---

## 📄 License

This project is built for educational purposes as part of a Python programming course mini project.

---

*Made with ❤️ and Python*
                        - P Akshay Teja
