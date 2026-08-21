import threading
import time
import sounddevice as sd
import numpy as np
from rich.console import Console
from rich.panel import Panel
from src.wake_word import JarvisWakeWord
from src.ears import JarvisEars
from src.brain import JarvisBrain
from src.voice import JarvisVoice

console = Console()

def run_jarvis():
    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]J.A.R.V.I.S. AUTONOMOUS VOICE SYSTEM[/bold cyan]\n"
            "[dim]Barge-In Active | Local RAG | Multi-Turn Memory | Piper Paul Bettany TTS[/dim]",
            border_style="cyan"
        )
    )

    wake_detector = JarvisWakeWord()
    ears = JarvisEars()
    brain = JarvisBrain()
    voice = JarvisVoice()

    voice.speak("J.A.R.V.I.S. is initialized and standing by.")

    SESSION_TIMEOUT = 25  # Inactivity threshold before returning to wake-word standby
    is_awake = False
    last_interaction_time = 0

    def speak_with_interrupt(text: str):
        """Plays TTS in a background thread while monitoring mic for interruption."""
        speech_thread = threading.Thread(target=voice.speak, args=(text,), daemon=True)
        speech_thread.start()

        # Listen for user interruption while the assistant speaks
        with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=1024) as stream:
            while speech_thread.is_alive() and voice.is_playing:
                data, _ = stream.read(1024)
                energy = float(np.sqrt(np.mean(data ** 2)))

                # Voice energy threshold that triggers instant barge-in cut
                if energy > 0.08:
                    voice.stop()
                    console.print("\n[bold red]⚡ Speech interrupted by user.[/bold red]")
                    break
                time.sleep(0.02)
        speech_thread.join(timeout=0.2)

    while True:
        try:
            # 1. Low-power standby loop: blocks until "Hey Jarvis" is spoken
            if not is_awake:
                wake_detector.wait_for_wake_word()
                voice.speak("Yes, sir?")
                is_awake = True
                last_interaction_time = time.time()

            # 2. Dynamic recording with noise gating and silence cutoff
            user_speech = ears.listen_and_transcribe()

            if not user_speech:
                if time.time() - last_interaction_time > SESSION_TIMEOUT:
                    console.print("\n[dim cyan]💤 Inactivity timeout reached. Entering standby...[/dim cyan]")
                    is_awake = False
                continue

            last_interaction_time = time.time()
            console.print(f"[bold yellow]You:[/bold yellow] {user_speech}")

            # 3. Direct quick command handling
            cleaned_speech = user_speech.lower().strip().rstrip(".!?,")

            if cleaned_speech in ["stop", "jarvis stop", "stop talking", "shut up", "be quiet", "pause"]:
                voice.stop()
                voice.speak("Standing by, sir.")
                is_awake = False
                continue

            if any(term in cleaned_speech for term in ["go to sleep", "standby", "rest"]):
                voice.speak("Entering standby mode, sir.")
                is_awake = False
                continue

            if any(term in cleaned_speech for term in ["goodbye", "exit", "quit", "shutdown"]):
                voice.speak("Powering down. Have a good day, sir.")
                break

            # 4. Contextual processing (RAG + Tools + LLM)
            response = brain.ask(user_speech)

            # 5. Spoken neural response with barge-in support
            speak_with_interrupt(response)
            last_interaction_time = time.time()

        except KeyboardInterrupt:
            console.print("\n[red]Manual override. Terminating session.[/red]")
            break

if __name__ == "__main__":
    run_jarvis()