"""
main.py — JARVIS Personal AI Assistant Entry Point

Runs a continuous voice assistant loop:
  1. Wait for wake word ("Hey Nova" or configured word)
  2. Listen and transcribe speech
  3. Send command to the Agent (LLM + tools)
  4. Speak the response
  5. Repeat
"""

import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import config
from assistant.agent import Agent
from voice.wakeword import WakeWordDetector
from voice.listen import Transcriber
from voice.speak import Speaker
from utils.logger import logger

console = Console()


def print_banner() -> None:
    """Display a startup banner in the terminal."""
    banner = Text("J.A.R.V.I.S.", style="bold cyan", justify="center")
    subtitle = Text("Personal AI Assistant — powered by Groq + LLaMA 3", style="dim", justify="center")
    console.print(Panel.fit(f"{banner}\n{subtitle}", border_style="cyan"))


def run_text_mode(agent: Agent, speaker: Speaker) -> None:
    """
    Fallback text-mode loop — useful for testing without a microphone.
    Type commands directly in the terminal.
    """
    console.print("[bold yellow]Running in TEXT MODE (no microphone)[/bold yellow]")
    console.print("Type your command and press Enter. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye"}:
            speaker.speak("Goodbye! Have a great day.")
            break

        console.print("[dim]Thinking...[/dim]")
        response = agent.process_command(user_input)
        console.print(f"[bold cyan]Nova:[/bold cyan] {response}\n")
        speaker.speak(response)


def run_voice_mode(agent: Agent, wakeword_detector: WakeWordDetector,
                   transcriber: Transcriber, speaker: Speaker) -> None:
    """
    Full voice-mode loop with wake word → listen → respond.
    """
    console.print("[bold green]Voice mode active.[/bold green] "
                  f"Say '[italic]{config.WAKE_WORD}[/italic]' to start a command.\n")
    speaker.speak(f"Hello! I am Nova, your personal assistant. Say {config.WAKE_WORD} to give me a command.")

    while True:
        try:
            # ----------------------------------------------------------------
            # Step 1: Block until wake word is detected
            # ----------------------------------------------------------------
            detected = wakeword_detector.wait_for_wakeword()
            if not detected:
                # wait_for_wakeword returned False (error); back-off and retry
                time.sleep(1)
                continue

            speaker.speak("Yes?")
            console.print("[bold green]Wake word detected![/bold green] Listening for command...")

            # ----------------------------------------------------------------
            # Step 2: Listen and transcribe
            # ----------------------------------------------------------------
            user_input = transcriber.listen_and_transcribe(duration=5)

            if not user_input:
                speaker.speak("Sorry, I didn't catch that. Please try again.")
                continue

            console.print(f"[bold green]You:[/bold green] {user_input}")

            # ----------------------------------------------------------------
            # Step 3–6: Agent processes command (tool routing + LLM generation)
            # ----------------------------------------------------------------
            console.print("[dim]Thinking...[/dim]")
            response = agent.process_command(user_input)

            # ----------------------------------------------------------------
            # Step 7: Speak response
            # ----------------------------------------------------------------
            console.print(f"[bold cyan]Nova:[/bold cyan] {response}\n")
            speaker.speak(response)

        except KeyboardInterrupt:
            console.print("\n[bold red]Shutting down...[/bold red]")
            speaker.speak("Goodbye! Shutting down now.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            speaker.speak("I ran into an unexpected error. Please try again.")
            time.sleep(1)


def main() -> None:
    """Initialize all components and start the assistant loop."""
    print_banner()

    # Validate that required environment variables are set
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)

    # Parse CLI flags  --text  forces text mode (no mic/wake-word needed)
    text_mode: bool = "--text" in sys.argv

    # ----------------------------------------------------------------
    # Initialize components
    # ----------------------------------------------------------------
    logger.info("Initializing assistant components...")

    agent = Agent()
    speaker = Speaker()

    if text_mode:
        run_text_mode(agent, speaker)
        return

    # Voice mode — initializing mic-dependent components
    try:
        wakeword_detector = WakeWordDetector()
        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
    except Exception as e:
        console.print(
            f"[bold red]Failed to initialize voice components:[/bold red] {e}\n"
            "[yellow]Tip:[/yellow] Run with --text flag to use text-only mode."
        )
        sys.exit(1)

    run_voice_mode(agent, wakeword_detector, transcriber, speaker)


if __name__ == "__main__":
    main()
