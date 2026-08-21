import json
import re
import ollama
from rich.console import Console
from src.tools import JarvisTools

console = Console()

SYSTEM_PROMPT = """You are J.A.R.V.I.S., a witty, concise, and sophisticated AI assistant.
Keep spoken conversational responses to 1-2 sharp sentences.

You have access to real-time tools. When the user asks you to check system status, open/launch an application or browser, open their GitHub repository, or search Google/YouTube, reply ONLY with a single JSON object:
{"tool": "<tool_name>", "argument": "<argument>"}

Tool names and arguments:
- "get_system_status" (argument: "")
- "open_application" (argument: exact app name e.g. "brave", "chrome", "edge", "paint", "notepad", "calculator", "vscode", "spotify", "terminal")
- "open_github" (argument: "")
- "search_web" (argument: "<search keywords>")
- "open_youtube" (argument: "<search keywords or blank>")

Examples:
- "Open Brave browser" -> {"tool": "open_application", "argument": "brave"}
- "Open Chrome" -> {"tool": "open_application", "argument": "chrome"}
- "Open my GitHub repository" -> {"tool": "open_github", "argument": ""}

If no tool is required, reply directly with your normal conversational answer in plain text.
"""

class JarvisBrain:
    def __init__(self, model: str = "qwen2.5:3b"):
        self.model = model
        self.tools = JarvisTools()

    def ask(self, prompt: str) -> str:
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            raw_reply = response["message"]["content"].strip()

            # Detect and extract JSON
            json_match = re.search(r"\{.*?\}", raw_reply, re.DOTALL)
            if json_match:
                try:
                    tool_data = json.loads(json_match.group(0))
                    tool_name = tool_data.get("tool") or tool_data.get("tool_name") or tool_data.get("action")
                    arg = tool_data.get("argument") or tool_data.get("query") or ""

                    if tool_name == "get_system_status":
                        console.print("[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]get_system_status()[/cyan]")
                        return self.tools.get_system_status()

                    elif tool_name in ["open_github", "github"]:
                        console.print("[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]open_github()[/cyan]")
                        return self.tools.open_github()

                    elif tool_name in ["open_application", "open_app"]:
                        target_app = arg if arg else tool_data.get("tool_name", "")
                        console.print(f"[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]open_application({target_app})[/cyan]")
                        return self.tools.open_application(target_app)

                    elif tool_name in ["search_web", "google_search"]:
                        console.print(f"[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]search_web({arg})[/cyan]")
                        return self.tools.search_web(arg)

                    elif tool_name in ["open_youtube", "youtube_search"]:
                        console.print(f"[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]open_youtube({arg})[/cyan]")
                        return self.tools.open_youtube(arg)

                except json.JSONDecodeError:
                    pass

            return raw_reply

        except Exception as e:
            return f"Error communicating with local LLM engine: {str(e)}"