import asyncio
import io
import re
import sounddevice as sd
import soundfile as sf
import edge_tts
from rich.console import Console

console = Console()

class JarvisVoice:
    def __init__(self, voice_name: str = "en-GB-RyanNeural"):
        self.voice_name = voice_name
        self.is_playing = False
        self._stop_requested = False
        console.print(f"[green]✓ J.A.R.V.I.S. Neural Voice ({self.voice_name}) initialized.[/green]")

    def _phonetic_normalizer(self, text: str) -> str:
        """Cleans Markdown and expands technical terms for smooth British articulation."""
        cleaned = re.sub(r'[\*\_#`]', '', text)
        
        acronym_map = {
            r'\bJ\.?\s*A\.?\s*R\.?\s*V\.?\s*I\.?\s*S\.?\b': 'Jarvis',
            r'\bAPI\b': 'A P I',
            r'\bLLM\b': 'L L M',
            r'\bRAG\b': 'Rag',
            r'\bVRAM\b': 'V Ram',
            r'\bCUDA\b': 'Cooda',
            r'\bOS\b': 'O S',
            r'\bVS Code\b': 'V S Code',
            r'°C': ' degrees Celsius',
            r'%': ' percent'
        }
        for pattern, replacement in acronym_map.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
        return cleaned.strip()

    def stop(self):
        """Halts playback immediately for instant barge-in support."""
        self._stop_requested = True
        sd.stop()
        self.is_playing = False

    async def _generate_audio_bytes(self, text: str) -> bytes:
        # rate="-3%" and pitch="-1Hz" produces Bettany's deliberate, calm pacing
        communicate = edge_tts.Communicate(text, self.voice_name, rate="-3%", pitch="-1Hz")
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()

    def speak(self, text: str):
        if not text.strip():
            return

        spoken_text = self._phonetic_normalizer(text)
        console.print(f"[bold cyan]J.A.R.V.I.S.:[/bold cyan] {text.strip()}")

        self.stop()
        self._stop_requested = False

        try:
            raw_audio = asyncio.run(self._generate_audio_bytes(spoken_text))
            audio_io = io.BytesIO(raw_audio)
            data, samplerate = sf.read(audio_io, dtype='float32')

            self.is_playing = True
            sd.play(data, samplerate=samplerate)

            while sd.get_stream() and sd.get_stream().active and not self._stop_requested:
                sd.sleep(25)

        except Exception as e:
            console.print(f"[red]Voice Playback Error: {e}[/red]")
        finally:
            self.stop()

if __name__ == "__main__":
    v = JarvisVoice()
    v.speak("All core systems operational. I am online and standing by, sir.")