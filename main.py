"""
Real-Time Voice AI Agent — main orchestration loop.

Pipeline per turn:
    Mic recording → STT (Groq Whisper) → LLM (Groq Llama + tool calling)
    → TTS (ElevenLabs) → Speaker playback → repeat
"""

import sys

from config import validate_config
from audio_io import record_audio
from stt import transcribe
from llm import chat
from tts import speak


def main() -> None:
    # ------------------------------------------------------------------
    # Startup checks
    # ------------------------------------------------------------------
    print("=" * 50)
    print("  Real-Time Voice AI Agent")
    print("=" * 50)

    try:
        validate_config()
    except RuntimeError as e:
        print(f"\n[Config error] {e}")
        print("Please create a .env file with your API keys (see .env.example).")
        sys.exit(1)

    print("\nReady! Press Enter to start talking, then Enter again to stop.")
    print('Type "quit" or "exit" to end the session.\n')

    # ------------------------------------------------------------------
    # Conversation loop
    # ------------------------------------------------------------------
    while True:
        # Wait for the user to press Enter (or type quit/exit).
        prompt = input(">> Press Enter to speak (or type quit/exit): ").strip().lower()
        if prompt in ("quit", "exit"):
            print("\nGoodbye!")
            break

        # ---- 1. Record audio ------------------------------------------
        print("🎙  Recording… press Enter to stop.")
        audio_bytes = record_audio()

        if not audio_bytes:
            print("  (no audio captured — skipping turn)\n")
            continue

        # ---- 2. Speech-to-Text ----------------------------------------
        print("📝  Transcribing…")
        user_text = transcribe(audio_bytes)

        if not user_text:
            print("  (empty transcription — skipping turn)\n")
            continue

        print(f"\n  You: {user_text}")

        # ---- 3. LLM chat (with tool calling) --------------------------
        print("🤖  Thinking…")
        reply = chat(user_text)
        print(f"  Agent: {reply}\n")

        # ---- 4. Text-to-Speech + playback ----------------------------
        print("🔊  Speaking…")
        speak(reply)
        print()  # blank line before next turn


if __name__ == "__main__":
    main()
