"""
Speech-to-Text wrapper using the Groq hosted Whisper API.

Includes Whisper prompt biasing: contact names from contacts.json are
injected into the Whisper prompt so non-English names are recognised
more accurately.
"""

from groq import Groq
import logging

logger = logging.getLogger(__name__)

from config import GROQ_API_KEY, STT_MODEL
from contacts_tool import get_contact_names


_client = Groq(api_key=GROQ_API_KEY)


def _build_whisper_prompt() -> str:
    """Build a prompt that biases Whisper toward known contact names."""
    names = get_contact_names()
    if not names:
        return ""
    return "Names: " + ", ".join(names)


def transcribe(audio_bytes: bytes, ext: str = "wav") -> str:
    """Send audio bytes to Groq Whisper and return the transcribed text.

    Returns an empty string if transcription fails or produces no text.
    """
    if not audio_bytes:
        return ""

    try:
        whisper_prompt = _build_whisper_prompt()
        kwargs = {
            "model": STT_MODEL,
            "file": (f"recording.{ext}", audio_bytes),
            "response_format": "text",
        }
        if whisper_prompt:
            kwargs["prompt"] = whisper_prompt

        transcription = _client.audio.transcriptions.create(**kwargs)
        # The SDK returns the text directly when response_format="text".
        text = transcription.strip() if isinstance(transcription, str) else ""
        return text
    except Exception as e:
        logger.error(f"  [STT error] {e}")
        return ""

