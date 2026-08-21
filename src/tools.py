import os
import subprocess
import webbrowser
import psutil
from rich.console import Console

console = Console()

class JarvisTools:
    @staticmethod
    def get_system_status() -> str:
        """Returns CPU load, RAM usage, and available memory."""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        available_gb = round(memory.available / (1024 ** 3), 2)
        
        return (
            f"CPU utilization is at {cpu_percent} percent. "
            f"Memory usage is at {ram_percent} percent with {available_gb} gigabytes remaining."
        )

    @staticmethod
    def open_application(app_name: str) -> str:
        """Launches target desktop applications with robust Windows path resolution."""
        app_name_clean = app_name.lower().strip().replace("app", "").replace("the", "").replace("browser", "").strip()

        # Dedicated browser mappings
        if "brave" in app_name_clean:
            try:
                subprocess.Popen("start brave", shell=True)
                return "Opening Brave browser, sir."
            except Exception:
                pass

        if "chrome" in app_name_clean:
            try:
                subprocess.Popen("start chrome", shell=True)
                return "Opening Google Chrome, sir."
            except Exception:
                pass

        if "edge" in app_name_clean or "msedge" in app_name_clean:
            try:
                subprocess.Popen("start msedge", shell=True)
                return "Opening Microsoft Edge, sir."
            except Exception:
                pass

        app_map = {
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "vscode": "code",
            "code": "code",
            "spotify": "spotify",
            "explorer": "explorer.exe",
            "taskmanager": "taskmgr.exe"
        }

        target = app_map.get(app_name_clean, app_name_clean)
        try:
            subprocess.Popen(f"start {target}", shell=True)
            return f"Opening {app_name_clean}, sir."
        except Exception as e:
            return f"Unable to launch {app_name_clean}. Error: {str(e)}"

    @staticmethod
    def open_github(repo_name: str = "") -> str:
        """Opens your personal GitHub repository."""
        base_url = "https://github.com/Mr-SaiPavan/J.AR.V.I.S-Asisstant"
        webbrowser.open(base_url)
        return "Opening your GitHub repository now, sir."

    @staticmethod
    def search_web(query: str) -> str:
        """Executes a Google search in the default browser."""
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Searching Google for {query}."

    @staticmethod
    def open_youtube(query: str = "") -> str:
        """Opens YouTube or queries a search on YouTube."""
        if query:
            url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube now."