import os
import sys
import ctypes
import threading
import time
import webbrowser
import psutil
import httpx
import screen_brightness_control as sbc
from PIL import ImageGrab
from datetime import datetime

class JarvisTools:
    def __init__(self, voice_engine=None):
        self.voice = voice_engine
        self.active_timers = []
        self.notes_file = os.path.join("data", "notes.txt")
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, "w", encoding="utf-8") as f:
                f.write("# J.A.R.V.I.S. Quick Notes\n")

        self.app_map = {
            "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "terminal": "wt.exe",
            "cmd": "cmd.exe",
            "taskmanager": "taskmgr.exe",
            "vscode": "code",
            "spotify": "spotify.exe"
        }

    # ---------------- 1. DAILY BRIEFING ---------------- #

    def get_morning_briefing(self) -> str:
        """Assembles a comprehensive morning status briefing."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A, %B %d")
        
        # Weather
        weather_summary = self.get_live_weather()
        
        # Battery / System
        battery = psutil.sensors_battery()
        bat_str = f"Battery is at {battery.percent}%" if battery else "System is on AC power"
        
        # Check notes count
        note_count = 0
        if os.path.exists(self.notes_file):
            with open(self.notes_file, "r", encoding="utf-8") as f:
                note_count = len([line for line in f if line.strip().startswith("-")])
        
        notes_brief = f"You have {note_count} active items on your scratchpad." if note_count > 0 else "Your scratchpad is clear."
        
        return f"Good day, sir. It is {time_str} on {day_str}. {weather_summary} {bat_str}. {notes_brief}"

    # ---------------- 2. VOICE SCRATCHPAD & QUICK NOTES ---------------- #

    def add_note(self, note_text: str) -> str:
        """Appends a timestamped note to data/notes.txt."""
        if not note_text.strip():
            return "What would you like me to note down, sir?"
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        with open(self.notes_file, "a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] {note_text.strip()}\n")
        return f"Recorded to your notes: {note_text.strip()}"

    def read_notes(self) -> str:
        """Reads recent items from the notes scratchpad."""
        if not os.path.exists(self.notes_file):
            return "You have no recorded notes, sir."
        with open(self.notes_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip().startswith("-")]
        if not lines:
            return "Your scratchpad is currently empty, sir."
        recent = lines[-3:]
        cleaned = " ".join([l.lstrip("- ") for l in recent])
        return f"Here are your latest notes: {cleaned}"

    # ---------------- 3. FOCUS / WORKSPACE SESSIONS ---------------- #

    def start_focus_session(self, duration_minutes: str = "25") -> str:
        """Sets display brightness to 60%, mutes alerts, and sets a 25-minute Pomodoro timer."""
        try:
            mins = int("".join(filter(str.isdigit, str(duration_minutes))) or 25)
            self.set_brightness("60")
            self.set_timer(f"{mins} minutes")
            return f"Focus mode engaged for {mins} minutes. Display calibrated and countdown initiated, sir."
        except Exception as e:
            return f"Error initiating focus mode: {str(e)}"

    def launch_workspace(self, mode: str) -> str:
        """One-word preset configurations for coding, media, or night routines."""
        mode_clean = mode.lower().strip()
        if "code" in mode_clean or "dev" in mode_clean:
            self.open_application("vscode")
            os.system("start wt.exe")
            webbrowser.open("https://github.com")
            return "Development environment initialized: VS Code, Terminal, and GitHub are ready."
        elif "night" in mode_clean or "sleep" in mode_clean:
            self.set_brightness("15")
            self.set_volume("20")
            self.lock_workstation()
            return "Goodnight sir. Brightness reduced, volume dimmed, and workstation locked."
        elif "media" in mode_clean or "chill" in mode_clean:
            self.set_volume("40")
            self.open_youtube()
            return "Media mode engaged. Volume set to 40 percent."
        return f"Workspace profile '{mode}' not recognized."

    # ---------------- 4. UNIT / TIMEZONE CONVERTER ---------------- #

    def convert_units(self, query: str) -> str:
        """Fast offline calculation and unit resolver."""
        q = query.lower().strip()
        try:
            # Storage Conversions
            if "gb" in q and "mb" in q:
                val = float("".join(filter(lambda c: c.isdigit() or c == '.', q)))
                if "gb to mb" in q:
                    return f"{val} Gigabytes is equal to {int(val * 1024)} Megabytes."
                return f"{val} Megabytes is equal to {round(val / 1024, 2)} Gigabytes."
            
            # Simple Math Evaluator
            math_expr = re.sub(r'[^0-9\+\-\*\/\.\(\)]', '', query)
            if math_expr and any(op in math_expr for op in ['+', '-', '*', '/']):
                res = eval(math_expr, {"__builtins__": {}}, {})
                return f"The result of {math_expr} is {res}."
        except Exception:
            pass
        return self.get_live_web_facts(query)

    # ---------------- TIME & COUNTDOWN TIMERS ---------------- #

    def get_current_time(self) -> str:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A, %B %d, %Y")
        return f"The current time is {time_str} on {day_str}, sir."

    def _timer_worker(self, seconds: int, label: str):
        time.sleep(seconds)
        if self.voice:
            self.voice.speak(f"Sir, your timer for {label} is up.")
        else:
            ctypes.windll.user32.MessageBeep(0xFFFFFFFF)

    def set_timer(self, duration_str: str) -> str:
        try:
            dur = duration_str.lower().strip()
            digits = "".join(filter(str.isdigit, dur))
            if not digits:
                return "Please specify a valid duration for the timer, sir."
            val = int(digits)
            if "minute" in dur or "min" in dur:
                total_seconds = val * 60
                label = f"{val} minute{'s' if val > 1 else ''}"
            elif "hour" in dur or "hr" in dur:
                total_seconds = val * 3600
                label = f"{val} hour{'s' if val > 1 else ''}"
            else:
                total_seconds = val
                label = f"{val} second{'s' if val > 1 else ''}"

            t = threading.Thread(target=self._timer_worker, args=(total_seconds, label), daemon=True)
            t.start()
            self.active_timers.append(t)
            return f"Timer set for {label}."
        except Exception as e:
            return f"Unable to set timer: {str(e)}"

    # ---------------- NATIVE MEDIA CONTROLS ---------------- #

    def media_play_pause(self) -> str:
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        return "Toggled media playback."

    def media_next(self) -> str:
        ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB0, 0, 2, 0)
        return "Skipped to next track."

    def media_prev(self) -> str:
        ctypes.windll.user32.keybd_event(0xB1, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB1, 0, 2, 0)
        return "Playing previous track."

    # ---------------- LIVE GROUNDING & SYSTEM STATUS ---------------- #

    def get_live_weather(self, location: str = "") -> str:
        try:
            query_loc = location.strip().replace(" ", "+") if location else ""
            url = f"https://wttr.in/{query_loc}?format=j1"
            with httpx.Client(timeout=4.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    current = data["current_condition"][0]
                    temp_c = current["temp_C"]
                    desc = current["weatherDesc"][0]["value"]
                    humidity = current["humidity"]
                    area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", location or "your area")
                    return f"The current weather in {area} is {desc} with a temperature of {temp_c}°C and {humidity}% humidity."
                return "Unable to fetch the weather report at this moment."
        except Exception as e:
            return f"Weather retrieval error: {str(e)}"

    def get_live_web_facts(self, query: str) -> str:
        if not query.strip():
            return ""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            with httpx.Client(timeout=4.0, headers=headers) as client:
                ddg_url = f"https://api.duckduckgo.com/?q={httpx.URL(query)}&format=json&no_html=1&skip_disambig=1"
                resp = client.get(ddg_url)
                if resp.status_code == 200:
                    abstract = resp.json().get("AbstractText", "").strip()
                    if abstract:
                        return abstract

                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{httpx.URL(query)}"
                resp_wiki = client.get(wiki_url)
                if resp_wiki.status_code == 200:
                    extract = resp_wiki.json().get("extract", "").strip()
                    if extract:
                        return extract
            return f"No direct summary found for '{query}'."
        except Exception as e:
            return f"Search error: {str(e)}"

    def get_system_status(self) -> str:
        cpu_usage = psutil.cpu_percent(interval=0.3)
        memory = psutil.virtual_memory()
        status_msg = f"CPU load is currently at {cpu_usage} percent. Memory utilization stands at {memory.percent} percent."
        battery = psutil.sensors_battery()
        if battery:
            plugged = "plugged in" if battery.power_plugged else "discharging on battery"
            status_msg += f" Battery is at {battery.percent} percent and {plugged}."
        return status_msg

    def lock_workstation(self) -> str:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked successfully, sir."

    def take_screenshot(self) -> str:
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join("screenshots", f"screenshot_{timestamp}.png")
        ImageGrab.grab().save(filepath)
        return "Desktop screenshot captured."

    def set_brightness(self, level: str) -> str:
        try:
            val = max(0, min(100, int("".join(filter(str.isdigit, str(level))))))
            sbc.set_brightness(val)
            return f"Display brightness set to {val} percent."
        except Exception as e:
            return f"Unable to adjust brightness: {str(e)}"

    def set_volume(self, level: str) -> str:
        try:
            val = max(0, min(100, int("".join(filter(str.isdigit, str(level))))))
            os.system(f"powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]174 * 50); (New-Object -ComObject WScript.Shell).SendKeys([char]175 * {int(val/2)})\"")
            return f"Master volume set to {val} percent."
        except Exception as e:
            return f"Unable to set volume: {str(e)}"

    def toggle_mute(self) -> str:
        os.system("powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]173)\"")
        return "Audio mute toggled."

    def open_application(self, app_name: str) -> str:
        app_clean = app_name.lower().strip()
        for key, path in self.app_map.items():
            if key in app_clean:
                try:
                    os.startfile(path)
                    return f"Opening {key.capitalize()} now, sir."
                except Exception:
                    os.system(f"start {key}")
                    return f"Launching {key}."
        try:
            os.system(f"start {app_clean}")
            return f"Opening {app_name}."
        except Exception as e:
            return f"Unable to launch {app_name}: {str(e)}"

    def open_github(self) -> str:
        webbrowser.open("https://github.com")
        return "Opening your GitHub dashboard."

    def search_web(self, query: str) -> str:
        if not query.strip():
            return "What would you like to search for?"
        webbrowser.open(f"https://www.google.com/search?q={webbrowser.quote(query)}")
        return f"Searching Google for {query}."

    def open_youtube(self, query: str = "") -> str:
        if query.strip():
            webbrowser.open(f"https://www.youtube.com/results?search_query={webbrowser.quote(query)}")
            return f"Searching YouTube for {query}."
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."