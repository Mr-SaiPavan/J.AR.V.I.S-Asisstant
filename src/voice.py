import io
import os
import re
import wave
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from rich.console import Console

console = Console()

class JarvisVoice:
    def __init__(self, model_path: str = "models/jarvis.onnx", config_path: str = "models/jarvis.onnx.json"):
        console.print("[cyan]Loading local Paul Bettany (J.A.R.V.I.S.) voice model...[/cyan]")
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError(f"Model files missing at '{model_path}'. Check your models/ directory.")

        self.voice = PiperVoice.load(model_path, config_path=config_path)
        self.is_playing = False
        self._stop_requested = False
        console.print("[green]✓ J.A.R.V.I.S. replica voice engine initialized![/green]")

    def _sanitize_for_speech(self, text: str) -> str:
        """Sanitizes text and normalizes acronyms for natural speech synthesis."""
        cleaned = re.sub(r'J\.?\s*A\.?\s*R\.?\s*V\.?\s*I\.?\s*S\.?', 'Jarvis', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'[\*\_#`]', '', cleaned)
        return cleaned.strip()

    def stop(self):
        """Immediately cuts off audio playback."""
        self._stop_requested = True
        sd.stop()
        self.is_playing = False

    def speak(self, text: str):
        """Synthesizes audio via Piper and plays back through sounddevice."""
        if not text.strip():
            return

        spoken_text = self._sanitize_for_speech(text)
        console.print(f"[bold cyan]J.A.R.V.I.S.:[/bold cyan] {spoken_text}")

        self.stop()
        self._stop_requested = False

        try:
            # Synthesize directly into in-memory WAV buffer
            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_file:
                self.voice.synthesize_wav(spoken_text, wav_file)

            # Read back PCM frames
            wav_io.seek(0)
            with wave.open(wav_io, "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32767.0

            self.is_playing = True
            sd.play(audio_data, samplerate=sample_rate)

            while sd.get_stream() and sd.get_stream().active and not self._stop_requested:
                sd.sleep(40)

        except Exception as e:
            console.print(f"[red]Piper Playback Error: {e}[/red]")
        finally:
            self.stop()

def test_voice():
    v = JarvisVoice()
    v.speak("Allow me to introduce myself. I am Jarvis, your local AI assistant.")

if __name__ == "__main__":
    test_voice()