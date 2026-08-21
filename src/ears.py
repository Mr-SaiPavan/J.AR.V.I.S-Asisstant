import io
import time
import wave
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console

console = Console()

class JarvisEars:
    def __init__(self, model_size: str = "small.en"):
        console.print(f"[cyan]Loading Whisper model ({model_size}) on CPU (int8)...[/cyan]")
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=4
        )
        console.print("[green]✓ Speech recognition engine ready with dynamic VAD![/green]")

        self.sample_rate = 16000
        self.block_size = 1024  # ~64ms chunks for low-latency processing
        self.prompt_context = "Jarvis, J.A.R.V.I.S., computer, artificial intelligence, assistant."

    def listen_and_transcribe(
        self,
        silence_limit: float = 1.0,
        energy_threshold: float = 0.015,
        max_duration: float = 15.0
    ) -> str:
        """
        Dynamically captures audio. Starts capturing when sound volume exceeds
        energy_threshold, and stops automatically after silence_limit seconds of quiet.
        """
        console.print("\n[bold yellow]🎙️  Listening dynamically... (Speak anytime)[/bold yellow]")
        
        audio_buffer = []
        is_speaking = False
        silence_start = None
        start_time = time.time()

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=self.block_size) as stream:
            while True:
                # Read audio block
                data, _ = stream.read(self.block_size)
                energy = float(np.sqrt(np.mean(data ** 2)))
                elapsed_total = time.time() - start_time

                if not is_speaking:
                    # Speech onset detection
                    if energy > energy_threshold:
                        is_speaking = True
                        silence_start = None
                        console.print("[bold green]● Speech detected... recording[/bold green]")
                        audio_buffer.append(data)
                else:
                    audio_buffer.append(data)

                    # Track pauses and silence
                    if energy < energy_threshold:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= silence_limit:
                            console.print("[dim]Pause detected. Transcribing...[/dim]")
                            break
                    else:
                        silence_start = None

                # Safety max recording timeout
                if elapsed_total >= max_duration:
                    break

        if not audio_buffer:
            return ""

        # Concatenate audio blocks and normalize volume
        raw_audio = np.concatenate(audio_buffer, axis=0).flatten()
        max_val = np.max(np.abs(raw_audio))
        if max_val > 0:
            raw_audio = (raw_audio / max_val) * 0.95

        pcm_data = (raw_audio * 32767).astype(np.int16)

        # Pack into WAV buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_data.tobytes())
        wav_buffer.seek(0)

        # Transcribe with Whisper (using internal VAD filters)
        segments, _ = self.model.transcribe(
            wav_buffer,
            beam_size=5,
            initial_prompt=self.prompt_context,
            vad_filter=True
        )
        text = " ".join([segment.text.strip() for segment in segments]).strip()
        return text

def test_ears():
    ears = JarvisEars(model_size="small.en")
    result = ears.listen_and_transcribe()
    
    if result:
        console.print(f"\n[bold green]Recognized Speech:[/bold green] [bold white]\"{result}\"[/bold white]")
    else:
        console.print("\n[red]No speech detected.[/red]")

if __name__ == "__main__":
    test_ears()