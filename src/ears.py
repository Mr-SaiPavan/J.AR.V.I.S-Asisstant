import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console

console = Console()

class JarvisEars:
    def __init__(self, model_size: str = "small.en", device: str = "cpu", compute_type: str = "int8"):
        console.print(f"[cyan]Initializing High-Precision Ears ({model_size} int8)...[/cyan]")
        
        # small.en with multi-threaded CTranslate2 backend
        self.whisper = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type,
            cpu_threads=4
        )

        self.sample_rate = 16000
        self.block_size = 1024
        self.energy_threshold = 0.025
        self.initial_prompt = "Jarvis, AI, RAG, ChromaDB, CUDA, LLM, Python, C++, terminal, Kakinada, Pithapuram, Rajahmundry, volume, brightness."
        console.print("[green]✓ High-precision ears (small.en) ready.[/green]")

    def listen_and_transcribe(self, max_duration: int = 15, silence_limit: float = 0.7) -> str:
        audio_buffer = []
        is_recording = False
        silence_start_time = None
        start_time = time.time()

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=self.block_size) as stream:
            while True:
                data, _ = stream.read(self.block_size)
                chunk = data.flatten()
                energy = float(np.sqrt(np.mean(chunk ** 2)))

                if energy > self.energy_threshold:
                    if not is_recording:
                        console.print("[bold green]● Listening...[/bold green]", end="\r")
                        is_recording = True
                    audio_buffer.append(chunk)
                    silence_start_time = None
                elif is_recording:
                    audio_buffer.append(chunk)
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time > silence_limit:
                        break

                if is_recording and (time.time() - start_time > max_duration):
                    break
                
                if not is_recording and (time.time() - start_time > 4.0):
                    return ""

        if not audio_buffer or not is_recording:
            return ""

        audio_data = np.concatenate(audio_buffer, axis=0)

        # Discard sub-0.35s taps or clicks
        if len(audio_data) < self.sample_rate * 0.35:
            return ""

        console.print("[dim cyan]Transcribing...[/dim cyan]", end="\r")
        
        # High-precision transcription with native C++ VAD segmenter
        segments, _ = self.whisper.transcribe(
            audio_data,
            beam_size=3,
            initial_prompt=self.initial_prompt,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
            temperature=0.0
        )
        
        return " ".join([seg.text for seg in segments]).strip()