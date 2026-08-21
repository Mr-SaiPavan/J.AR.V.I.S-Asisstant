import asyncio
import os
import re
import edge_tts
import pygame
from rich.console import Console

console = Console()

class JarvisVoice:
    def __init__(self, voice: str = "en-GB-RyanNeural"):
        """
        Uses Microsoft's neural British voice to match the MCU Jarvis tone.
        Voice options:
          - 'en-GB-RyanNeural' (Refined, crisp British male - MCU style)
          - 'en-GB-ThomasNeural' (Deeper British tone)
        """
        self.voice = voice
        self.temp_audio = "temp_voice.mp3"
        pygame.mixer.init()

    async def _synthesize(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice, rate="+0%", pitch="-2Hz")
        await communicate.save(self.temp_audio)

    def speak(self, text: str):
        if not text:
            return

        console.print(f"[bold cyan]J.A.R.V.I.S.:[/bold cyan] [white]{text}[/white]")
        
        spoken_text = re.sub(r'J\.?\s*A\.?\s*R\.?\s*V\.?\s*I\.?\s*S\.?', 'Jarvis', text, flags=re.IGNORECASE)

        try:
            asyncio.run(self._synthesize(spoken_text))

            pygame.mixer.music.load(self.temp_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            if os.path.exists(self.temp_audio):
                os.remove(self.temp_audio)
        except Exception as e:
            console.print(f"[red]TTS Error: {e}[/red]")

def test_voice():
    voice = JarvisVoice()
    voice.speak("Allow me to introduce myself. I am Jarvis, your personal artificial intelligence assistant.")

if __name__ == "__main__":
    test_voice()