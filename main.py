import time
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
            "[dim]Mode: Continuous Conversation with Inactivity Standby (30s)[/dim]",
            border_style="cyan"
        )
    )

    wake_detector = JarvisWakeWord()
    ears = JarvisEars()
    brain = JarvisBrain()
    voice = JarvisVoice()

    voice.speak("J.A.R.V.I.S. is initialized and standing by.")

    # Timeout in seconds before returning to wake-word standby
    SESSION_TIMEOUT = 25  
    is_awake = False
    last_interaction_time = 0

    while True:
        try:
            # Step 1: If asleep, block and wait for "Hey Jarvis"
            if not is_awake:
                wake_detector.wait_for_wake_word()
                voice.speak("Yes, sir?")
                is_awake = True
                last_interaction_time = time.time()

            # Step 2: Listen dynamically for user input
            user_speech = ears.listen_and_transcribe()

            # Handle silence / no speech detected
            if not user_speech:
                # Check if session has timed out from inactivity
                if time.time() - last_interaction_time > SESSION_TIMEOUT:
                    console.print("\n[dim cyan]💤 Inactivity timeout reached. Entering standby...[/dim cyan]")
                    is_awake = False
                continue

            # Update activity timer upon valid speech
            last_interaction_time = time.time()
            console.print(f"[bold yellow]You:[/bold yellow] {user_speech}")

            # Step 3: Explicit sleep/exit commands
            if any(term in user_speech.lower() for term in ["go to sleep", "standby", "rest"]):
                voice.speak("Entering standby mode, sir.")
                is_awake = False
                continue

            if any(term in user_speech.lower() for term in ["goodbye", "exit", "quit", "shutdown"]):
                voice.speak("Powering down. Have a good day, sir.")
                break

            # Step 4: Brain processing & tools
            response = brain.ask(user_speech)

            # Step 5: Speak response
            voice.speak(response)

            # Reset timer after speaking finishes so you have full timeout window to reply
            last_interaction_time = time.time()

        except KeyboardInterrupt:
            console.print("\n[red]Manual override. Terminating session.[/red]")
            break

if __name__ == "__main__":
    run_jarvis()