from rich.console import Console
from rich.panel import Panel
from src.ears import JarvisEars
from src.brain import JarvisBrain
from src.voice import JarvisVoice

console = Console()

def run_jarvis():
    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]J.A.R.V.I.S. VOICE ASSISTANT PIPELINE[/bold cyan]\n"
            "[dim]Ears: Dynamic VAD (small.en) | Brain: Qwen2.5:3b | Voice: Neural TTS[/dim]",
            border_style="cyan"
        )
    )

    ears = JarvisEars()
    brain = JarvisBrain()
    voice = JarvisVoice()

    voice.speak("J.A.R.V.I.S. is online and listening. How may I assist you?")

    while True:
        try:
            # 1. Listen dynamically (auto-detects speech start and stop)
            user_speech = ears.listen_and_transcribe()

            if not user_speech:
                continue

            console.print(f"[bold yellow]You:[/bold yellow] {user_speech}")

            # Exit condition
            if any(term in user_speech.lower() for term in ["goodbye", "exit", "quit", "shutdown"]):
                voice.speak("Powering down. Have a good day, sir.")
                break

            # 2. Think (Brain)
            response = brain.ask(user_speech)

            # 3. Speak (Voice)
            voice.speak(response)

        except KeyboardInterrupt:
            console.print("\n[red]Session terminated by user.[/red]")
            break

if __name__ == "__main__":
    run_jarvis()