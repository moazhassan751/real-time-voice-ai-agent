"""
Interactive text-based test harness for the Real-Time Voice AI Agent.

Allows testing the LLM's conversation and tool-calling logic directly via text
keyboard input — without using mic, STT, or TTS audio modules.

=============================================================================
EXAMPLE PHRASES TO TRY:
=============================================================================
1. Single-tool direct phrasing:
   - "What time is it right now?"
   - "What's the weather in Islamabad?"
   - "Remind me to buy coffee tomorrow"
   - "Show my reminders"

2. Ambiguous / indirect phrasing:
   - "Is it going to rain in London today?"
   - "I need to talk to Ahmed sometime tomorrow afternoon"
   - "Do I have anything planned for tomorrow?"

3. Multi-turn context testing:
   - Turn 1: "I spent $10 on lunch today"
   - Turn 2: "Log that in my expenses spreadsheet"

4. Edge cases & conversational fallback:
   - "Schedule a meeting"  (missing time/title)
   - "Tell me a short joke"  (no tool needed)
   - "What's the speed of light?"  (no tool needed)
=============================================================================
"""

import sys

from google_auth import get_google_credentials
from llm import chat, reset_history


def main() -> None:
    print("==================================================")
    print("  Real-Time Voice AI Agent — Text Test Harness")
    print("==================================================")
    print("Initializing Google OAuth credentials...")

    try:
        get_google_credentials()
        print("[OK] Google OAuth credentials validated.\n")
    except Exception as e:
        print(f"[WARNING] Google OAuth validation error: {e}\n")

    print("Type your message and press Enter.")
    print('Type "quit" or "exit" to end the session.\n')
    print("-" * 50)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nGoodbye!")
            break

        # Process message via LLM + tool-calling engine in llm.py
        try:
            print("Thinking...")
            reply = chat(user_input)
            print(f"Agent: {reply}\n")
        except Exception as e:
            print(f"[ERROR] Turn error: {e}\n")


if __name__ == "__main__":
    main()
