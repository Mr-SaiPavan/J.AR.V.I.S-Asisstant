import os
import sys
import ctypes
import webbrowser
import psutil
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
        """Immediately locks the Windows session."""
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked successfully, sir."

    def take_screenshot(self) -> str:
        """Captures the full desktop and saves it with a timestamp."""
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join("screenshots", f"screenshot_{timestamp}.png")
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        return f"Desktop screenshot captured and saved to screenshots folder."

    # ---------------- DISPLAY BRIGHTNESS CONTROL ---------------- #

    def set_brightness(self, level: str) -> str:
        """Sets display brightness from 0 to 100 percent."""
        try:
            # Extract digits from string
            digits = "".join(filter(str.isdigit, str(level)))
            if not digits:
                return "Please specify a brightness percentage between 0 and 100."
            val = max(0, min(100, int(digits)))
            sbc.set_brightness(val)
            return f"Display brightness adjusted to {val} percent."
        except Exception as e:
            return f"Unable to adjust display brightness: {str(e)}"

    # ---------------- AUDIO VOLUME CONTROL ---------------- #

    def set_volume(self, level: str) -> str:
        """Sets Windows master volume using PowerShell core audio automation."""
        try:
            digits = "".join(filter(str.isdigit, str(level)))
            if not digits:
                return "Please specify a volume percentage between 0 and 100."
            val = max(0, min(100, int(digits)))
            
            # Using native Windows NirCmd/PowerShell volume scalar
            scalar = val / 100.0
            ps_script = (
                f"$obj = [Activator]::CreateInstance([Type]::GetTypeFromProgID('WScript.Shell'));"
                f"$wsh = New-Object -ComObject WScript.Shell;"
            )
            # Use PowerShell to run volume adjustment cleanly
            os.system(f"powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]174 * 50); (New-Object -ComObject WScript.Shell).SendKeys([char]175 * {int(val/2)})\"")
            return f"Master audio volume set to approximately {val} percent."
        except Exception as e:
            return f"Unable to set volume: {str(e)}"

    def toggle_mute(self) -> str:
        """Toggles master volume mute."""
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