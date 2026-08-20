import io
import wave
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console

console = Console()

class JarvisEars:
    def __init__(self, model_size: str = "base.en"):
        """
        Initializes faster-whisper on CPU with int8 quantization for instant offline STT.
        """
        console.print(f"[cyan]Loading Whisper model ({model_size}) on CPU (int8)...[/cyan]")
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=4
        )
        console.print("[green]✓ Speech recognition engine ready![/green]")
        self.sample_rate = 16000

    def record_and_transcribe(self, duration: int = 4) -> str:
        console.print(f"\n[bold yellow]🎙️  Listening for {duration} seconds... Speak now![/bold yellow]")
        
        # Record mono audio from microphone at 16kHz
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        console.print("[dim]Transcribing audio...[/dim]")

        # Write raw PCM frames to in-memory WAV buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        wav_buffer.seek(0)

        # Transcribe
        segments, _ = self.model.transcribe(wav_buffer, beam_size=5)
        text = " ".join([segment.text.strip() for segment in segments]).strip()

        return text

def test_ears():
    ears = JarvisEars()
    transcription = ears.record_and_transcribe(duration=4)
    
    if transcription:
        console.print(f"\n[bold green]Recognized Speech:[/bold green] [bold white]\"{transcription}\"[/bold white]")
    else:
        console.print("\n[red]No speech detected. Check your microphone input.[/red]")

if __name__ == "__main__":
    test_ears()