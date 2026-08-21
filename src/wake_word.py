import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model
from rich.console import Console

console = Console()

class JarvisWakeWord:
    def __init__(self, threshold: float = 0.5):
        """
        Ensures model weights exist and initializes the 'hey_jarvis' ONNX engine.
        """
        console.print("[cyan]Checking and initializing local wake-word engine...[/cyan]")
        
        # Download pre-trained models if they are missing locally
        openwakeword.utils.download_models()

        self.model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        self.threshold = threshold
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms audio frames (16000 * 0.08)
        console.print("[green]✓ Wake-word detector active ('Hey Jarvis')[/green]")

    def wait_for_wake_word(self):
        """
        Continuously listens on low CPU power until 'Hey Jarvis' is detected.
        """
        console.print("\n[bold dim cyan]👂 Standing by... Say 'Hey Jarvis' to activate.[/bold dim cyan]")
        
        self.model.reset()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.chunk_size
        ) as stream:
            while True:
                audio_data, _ = stream.read(self.chunk_size)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Predict on chunk
                prediction = self.model.predict(audio_array)
                
                # Check all output keys for the jarvis model prediction score
                for mdl in prediction:
                    if "jarvis" in mdl.lower() and prediction[mdl] >= self.threshold:
                        console.print("\n[bold green]⚡ Wake-Word Detected: 'Hey Jarvis'[/bold green]")
                        self.model.reset()
                        return

def test_wake():
    detector = JarvisWakeWord()
    detector.wait_for_wake_word()
    console.print("[bold yellow]Assistant Activated Successfully![/bold yellow]")

if __name__ == "__main__":
    test_wake()