import ollama
from rich.console import Console
from rich.panel import Panel

console = Console()

class JarvisBrain:
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.system_prompt = (
            "You are J.A.R.V.I.S., a highly capable, polite, and witty AI assistant. "
            "Keep voice responses concise (1-3 sentences) unless asked for deep technical detail."
        )
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def ask(self, user_input: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_input})
        
        response = ollama.chat(
            model=self.model_name,
            messages=self.conversation_history
        )
        
        reply = response["message"]["content"]
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

def run_diagnostics():
    console.clear()
    console.print(Panel.fit("[bold cyan]J.A.R.V.I.S. CORE BRAIN INITIALIZATION[/bold cyan]\n[dim]Model: qwen2.5:3b | Target: Local GPU/VRAM[/dim]", border_style="cyan"))
    
    brain = JarvisBrain()
    
    console.print("[yellow]Connecting to local model on GPU...[/yellow]\n")
    reply = brain.ask("Jarvis, system diagnostic check. Report your readiness.")
    
    console.print(f"[bold cyan]J.A.R.V.I.S.:[/bold cyan] {reply}\n")
    console.print("[bold green]✓ Phase 1 Complete: Local GPU brain pipeline is fully online and operational![/bold green]")

if __name__ == "__main__":
    run_diagnostics()