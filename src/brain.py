import json
import re
import ollama
from rich.console import Console
from src.tools import JarvisTools
from src.rag_engine import JarvisRAG

console = Console()

SYSTEM_PROMPT = """You are J.A.R.V.I.S., a witty, concise, and sophisticated AI assistant.
Keep spoken conversational responses to 1-2 sharp sentences.

You have access to real-time system and live web tools. When the user asks for actions or live data, reply ONLY with a single JSON object:
{"tool": "<tool_name>", "argument": "<argument>"}

Available Tools:
- "get_live_weather" (argument: "<city name or blank>") -> Current weather and temperature.
- "get_live_web_facts" (argument: "<search keywords>") -> Fetches latest real-time facts/news from the web.
- "get_system_status" (argument: "") -> CPU, RAM, and battery stats.
- "set_brightness" (argument: "<0-100>") -> Sets screen brightness percentage.
- "set_volume" (argument: "<0-100>") -> Sets master volume percentage.
- "toggle_mute" (argument: "") -> Mutes/unmutes audio.
- "lock_workstation" (argument: "") -> Locks PC screen.
- "take_screenshot" (argument: "") -> Captures full screen.
- "open_application" (argument: exact app name e.g. "brave", "chrome", "notepad", "calculator", "vscode", "terminal")
- "open_github" (argument: "")
- "open_youtube" (argument: "<query or blank>")
- "search_web" (argument: "<query>") -> Opens search in default web browser.

Examples:
- "What's the weather in Pitapuram?" -> {"tool": "get_live_weather", "argument": "Pitapuram"}
- "Who won the latest F1 race?" -> {"tool": "get_live_web_facts", "argument": "latest F1 race winner"}
- "Lock my PC" -> {"tool": "lock_workstation", "argument": ""}

If context is provided under [CONTEXT], synthesize a concise answer.
If no tool is required, reply directly with your normal conversational response in plain text.
"""

class JarvisBrain:
    def __init__(self, model: str = "qwen2.5:3b", max_history: int = 8):
        self.model = model
        self.tools = JarvisTools()
        self.rag = JarvisRAG()
        self.max_history = max_history
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def ask(self, prompt: str) -> str:
        try:
            # 1. Semantic Check in Local RAG
            rag_context = self.rag.search(prompt, top_k=2)
            augmented_prompt = prompt
            if rag_context:
                augmented_prompt = f"[LOCAL NOTES CONTEXT]:\n{rag_context}\n\n[USER QUERY]: {prompt}"

            # 2. Append turn to memory
            self.history.append({"role": "user", "content": augmented_prompt})

            if len(self.history) > (self.max_history * 2 + 1):
                self.history = [self.history[0]] + self.history[-(self.max_history * 2):]

            response = ollama.chat(
                model=self.model,
                messages=self.history
            )
            raw_reply = response["message"]["content"].strip()

            # 3. Tool Execution
            json_match = re.search(r"\{.*?\}", raw_reply, re.DOTALL)
            if json_match:
                try:
                    tool_data = json.loads(json_match.group(0))
                    tool_name = tool_data.get("tool") or tool_data.get("tool_name")
                    arg = str(tool_data.get("argument") or tool_data.get("query") or "").strip()

                    tool_output = ""

                    if tool_name == "get_live_weather":
                        console.print(f"[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]get_live_weather({arg})[/cyan]")
                        tool_output = self.tools.get_live_weather(arg)

                    elif tool_name == "get_live_web_facts":
                        console.print(f"[bold magenta]⚡ Executing Tool:[/bold magenta] [cyan]get_live_web_facts({arg})[/cyan]")
                        search_snippets = self.tools.get_live_web_facts(arg)
                        grounded_prompt = f"[LIVE WEB RESULTS]:\n{search_snippets}\n\nAnswer concisely in 1-2 spoken sentences: {prompt}"
                        summary_res = ollama.chat(
                            model=self.model,
                            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": grounded_prompt}]
                        )
                        tool_output = summary_res["message"]["content"].strip()

                    elif tool_name == "get_system_status":
                        tool_output = self.tools.get_system_status()
                    elif tool_name == "set_brightness":
                        tool_output = self.tools.set_brightness(arg)
                    elif tool_name == "set_volume":
                        tool_output = self.tools.set_volume(arg)
                    elif tool_name == "toggle_mute":
                        tool_output = self.tools.toggle_mute()
                    elif tool_name == "lock_workstation":
                        tool_output = self.tools.lock_workstation()
                    elif tool_name == "take_screenshot":
                        tool_output = self.tools.take_screenshot()
                    elif tool_name in ["open_github", "github"]:
                        tool_output = self.tools.open_github()
                    elif tool_name in ["open_application", "open_app"]:
                        target_app = arg if arg else tool_data.get("tool_name", "")
                        tool_output = self.tools.open_application(target_app)
                    elif tool_name in ["search_web", "google_search"]:
                        tool_output = self.tools.search_web(arg)
                    elif tool_name in ["open_youtube", "youtube_search"]:
                        tool_output = self.tools.open_youtube(arg)

                    if tool_output:
                        # Append the response to conversational history to break repetition loops
                        self.history.append({"role": "assistant", "content": tool_output})
                        return tool_output

                except json.JSONDecodeError:
                    pass

            self.history.append({"role": "assistant", "content": raw_reply})
            return raw_reply

        except Exception as e:
            return f"Error communicating with local LLM engine: {str(e)}"