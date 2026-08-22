import os
import sys
import ctypes
import webbrowser
import psutil
import httpx
from duckduckgo_search import DDGS
import screen_brightness_control as sbc
from PIL import ImageGrab
from datetime import datetime

class JarvisTools:
    def __init__(self):
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
            "vscode": "code"
        }

    # ---------------- REAL-TIME WEB & WEATHER GROUNDING ---------------- #

    def get_live_weather(self, location: str = "") -> str:
        """Fetches real-time weather metrics using the wttr.in endpoint."""
        try:
            query_loc = location.strip().replace(" ", "+") if location else ""
            url = f"https://wttr.in/{query_loc}?format=j1"
            
            with httpx.Client(timeout=6.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    current = data["current_condition"][0]
                    temp_c = current["temp_C"]
                    desc = current["weatherDesc"][0]["value"]
                    humidity = current["humidity"]
                    area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", location or "your area")
                    
                    return f"The current weather in {area} is {desc} with a temperature of {temp_c}°C and {humidity}% humidity."
                return "I was unable to retrieve the weather report at this moment."
        except Exception as e:
            return f"Weather retrieval error: {str(e)}"

    def get_live_web_facts(self, query: str) -> str:
        """Performs a live DuckDuckGo query and extracts high-confidence text snippets."""
        try:
            if not query.strip():
                return ""
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if not results:
                    return "No recent web search results found for that query."
                
                snippets = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    snippets.append(f"Title: {title}\nSnippet: {body}")
                
                return "\n---\n".join(snippets)
        except Exception as e:
            return f"Web search retrieval error: {str(e)}"

    # ---------------- HARDWARE & SYSTEM STATUS ---------------- #

    def get_system_status(self) -> str:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        
        status_msg = f"CPU load is currently at {cpu_usage} percent. Memory utilization stands at {ram_usage} percent."

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
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        return "Desktop screenshot captured and saved to screenshots folder."

    # ---------------- DISPLAY & AUDIO CONTROLS ---------------- #

    def set_brightness(self, level: str) -> str:
        try:
            digits = "".join(filter(str.isdigit, str(level)))
            if not digits:
                return "Please specify a brightness percentage between 0 and 100."
            val = max(0, min(100, int(digits)))
            sbc.set_brightness(val)
            return f"Display brightness adjusted to {val} percent."
        except Exception as e:
            return f"Unable to adjust display brightness: {str(e)}"

    def set_volume(self, level: str) -> str:
        try:
            digits = "".join(filter(str.isdigit, str(level)))
            if not digits:
                return "Please specify a volume percentage between 0 and 100."
            val = max(0, min(100, int(digits)))
            os.system(f"powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]174 * 50); (New-Object -ComObject WScript.Shell).SendKeys([char]175 * {int(val/2)})\"")
            return f"Master audio volume set to approximately {val} percent."
        except Exception as e:
            return f"Unable to set volume: {str(e)}"

    def toggle_mute(self) -> str:
        os.system("powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]173)\"")
        return "Audio mute toggled."

    # ---------------- APPLICATION & BROWSER LAUNCHERS ---------------- #

    def open_application(self, app_name: str) -> str:
        app_clean = app_name.lower().strip()
        for key, path in self.app_map.items():
            if key in app_clean:
                try:
                    os.startfile(path)
                    return f"Opening {key.capitalize()} for you now, sir."
                except Exception:
                    os.system(f"start {key}")
                    return f"Attempting to launch {key}."
        try:
            os.system(f"start {app_clean}")
            return f"Attempting to open {app_name}."
        except Exception as e:
            return f"Unable to launch {app_name}: {str(e)}"

    def open_github(self) -> str:
        webbrowser.open("https://github.com")
        return "Opening your GitHub dashboard."

    def search_web(self, query: str) -> str:
        if not query.strip():
            return "What would you like me to search for, sir?"
        url = f"https://www.google.com/search?q={webbrowser.quote(query)}"
        webbrowser.open(url)
        return f"Searching Google for {query}."

    def open_youtube(self, query: str = "") -> str:
        if query.strip():
            url = f"https://www.youtube.com/results?search_query={webbrowser.quote(query)}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."