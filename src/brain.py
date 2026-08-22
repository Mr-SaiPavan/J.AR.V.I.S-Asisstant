import json
import re
import ollama
from rich.console import Console
from src.tools import JarvisTools
from src.rag_engine import JarvisRAG

console = Console()

SYSTEM_PROMPT = """You are J.A.R.V.I.S., a witty, concise, and sophisticated AI assistant.
Keep spoken conversational responses to 1-2 sharp sentences.

You have access to real-time system and live web tools. When the user asks for actions, routines, or live data, reply ONLY with a single JSON object:
{"tool": "<tool_name>", "argument": "<argument>"}

Available Tools:
- "get_morning_briefing" (argument: "") -> Gives daily briefing (time, weather, battery, notes).
- "add_note" (argument: "<note content>") -> Appends note to scratchpad.
- "read_notes" (argument: "") -> Reads recent notes.
- "start_focus_session" (argument: "<minutes or 25>") -> Enters focus mode (Pomodoro timer + display dimming).
- "launch_workspace" (argument: "<code | night | media>") -> Triggers workspace presets.
- "convert_units" (argument: "<math or conversion query>") -> Evaluates math and storage/timezone conversions.
- "get_current_time" (argument: "") -> Returns current time and date.
- "set_timer" (argument: "<duration e.g. '5 minutes'>") -> Starts countdown timer.
- "media_play_pause" (argument: "") -> Plays/pauses media playback.
- "media_next" (argument: "") -> Next song.
- "media_prev" (argument: "") -> Previous song.
- "get_live_weather" (argument: "<city or blank>") -> Current weather.
- "get_live_web_facts" (argument: "<query>") -> Live web search.
- "get_system_status" (argument: "") -> CPU, RAM, battery.
- "set_brightness" (argument: "<0-100>")
- "set_volume" (argument: "<0-100>")
- "toggle_mute" (argument: "")
- "lock_workstation" (argument: "")
- "take_screenshot" (argument: "")
- "open_application" (argument: "<app name>")
- "open_github" (argument: "")
- "open_youtube" (argument: "<query or blank>")
- "search_web" (argument: "<query>")

Examples:
- "Jarvis, morning briefing" -> {"tool": "get_morning_briefing", "argument": ""}
- "Note down: study segment trees tonight" -> {"tool": "add_note", "argument": "study segment trees tonight"}
- "Read my notes" -> {"tool": "read_notes", "argument": ""}
- "Start a 25 minute focus session" -> {"tool": "start_focus_session", "argument": "25"}
- "Code mode" -> {"tool": "launch_workspace", "argument": "code"}
- "Night mode" -> {"tool": "launch_workspace", "argument": "night"}
- "Convert 32 GB to MB" -> {"tool": "convert_units", "argument": "32 gb to mb"}

If context is provided under [CONTEXT], synthesize a concise answer.
If no tool is required, reply directly with your normal conversational response in plain text.
"""

class JarvisBrain:
    def __init__(self, model: str = "qwen2.5:3b", max_history: int = 8, voice_engine=None):
        self.model = model
        self.tools = JarvisTools(voice_engine=voice_engine)
        self.rag = JarvisRAG()
        self.max_history = max_history
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def set_voice_engine(self, voice_engine):
        self.tools.voice = voice_engine

    def ask(self, prompt: str) -> str:
        try:
            rag_context = self.rag.search(prompt, top_k=2)
            augmented_prompt = prompt
            if rag_context:
                augmented_prompt = f"[LOCAL NOTES CONTEXT]:\n{rag_context}\n\n[USER QUERY]: {prompt}"

            self.history.append({"role": "user", "content": augmented_prompt})

            if len(self.history) > (self.max_history * 2 + 1):
                self.history = [self.history[0]] + self.history[-(self.max_history * 2):]

            response = ollama.chat(
                model=self.model,
                messages=self.history
            )
            raw_reply = response["message"]["content"].strip()

            json_match = re.search(r"\{.*?\}", raw_reply, re.DOTALL)
            if json_match:
                try:
                    tool_data = json.loads(json_match.group(0))
                    tool_name = tool_data.get("tool") or tool_data.get("tool_name")
                    arg = str(tool_data.get("argument") or tool_data.get("query") or "").strip()

                    tool_output = ""

                    # Daily Life Tools
                    if tool_name == "get_morning_briefing":
                        tool_output = self.tools.get_morning_briefing()
                    elif tool_name == "add_note":
                        tool_output = self.tools.add_note(arg)
                    elif tool_name == "read_notes":
                        tool_output = self.tools.read_notes()
                    elif tool_name == "start_focus_session":
                        tool_output = self.tools.start_focus_session(arg)
                    elif tool_name == "launch_workspace":
                        tool_output = self.tools.launch_workspace(arg)
                    elif tool_name == "convert_units":
                        tool_output = self.tools.convert_units(arg)
                    elif tool_name == "get_current_time":
                        tool_output = self.tools.get_current_time()
                    elif tool_name == "set_timer":
                        tool_output = self.tools.set_timer(arg)
                    elif tool_name in ["media_play_pause", "play_pause"]:
                        tool_output = self.tools.media_play_pause()
                    elif tool_name in ["media_next", "next_track"]:
                        tool_output = self.tools.media_next()
                    elif tool_name in ["media_prev", "prev_track"]:
                        tool_output = self.tools.media_prev()
                    elif tool_name == "get_live_weather":
                        tool_output = self.tools.get_live_weather(arg)
                    elif tool_name == "get_live_web_facts":
                        search_snippets = self.tools.get_live_web_facts(arg)
                        grounded_prompt = f"[LIVE WEB RESULTS]:\n{search_snippets}\n\nAnswer in 1-2 spoken sentences: {prompt}"
                        res = ollama.chat(
                            model=self.model,
                            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": grounded_prompt}]
                        )
                        tool_output = res["message"]["content"].strip()
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
                        console.print(f"[bold magenta]⚡ Executed Routine:[/bold magenta] [cyan]{tool_name}({arg})[/cyan]")
                        self.history.append({"role": "assistant", "content": tool_output})
                        return tool_output

                except json.JSONDecodeError:
                    pass

            self.history.append({"role": "assistant", "content": raw_reply})
            return raw_reply

        except Exception as e:
            return f"Error communicating with local LLM engine: {str(e)}"