"""
Text-to-Speech wrapper using edge-tts.

Streams audio chunks from edge-tts and can play them back through the
default speaker using sounddevice.
"""

import numpy as np
import logging
import asyncio
import edge_tts
import re

logger = logging.getLogger(__name__)


async def _synthesize_async(text: str) -> bytes:
    """Async helper to generate audio using edge-tts."""
    if not text:
        return b""
    
    # You can list available voices with: edge-tts --list-voices
    voice = "en-US-AriaNeural"
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)
    except Exception as e:
        logger.error(f"  [TTS error] Failed to synthesize audio: {e}")
        return b""

def synthesize(text: str) -> bytes:
    """Convert *text* to speech and return the raw MP3 bytes."""
    return asyncio.run(_synthesize_async(text))

def stream_synthesize_sentences(text_iterator):
    """Consumes a text iterator, buffers it into sentences, and yields audio chunks.
    
    This provides near real-time audio playback without requiring the full
    LLM response to finish first.
    """
    buffer = ""
    # Simple regex to split on sentence boundaries
    sentence_end_re = re.compile(r'([.?!])\s')

    for chunk in text_iterator:
        buffer += chunk
        # Check if we have a complete sentence
        match = sentence_end_re.search(buffer)
        if match:
            # Extract the sentence
            end_pos = match.end()
            sentence = buffer[:end_pos].strip()
            buffer = buffer[end_pos:]

            if sentence:
                audio_bytes = synthesize(sentence)
                if audio_bytes:
                    yield audio_bytes

    # Flush the remaining buffer
    final_sentence = buffer.strip()
    if final_sentence:
        audio_bytes = synthesize(final_sentence)
        if audio_bytes:
            yield audio_bytes


def play_audio(audio_bytes: bytes) -> None:
    logger.info("  [Audio] Playback is handled by the frontend. play_audio called natively.")


def speak(text: str) -> None:
    """Convert *text* to speech via edge-tts and play it through speakers.

    Decodes MP3 using miniaudio and plays via sounddevice.
    """
    import miniaudio
    import sounddevice as sd

    mp3_bytes = synthesize(text)
    if not mp3_bytes:
        return

    try:
        decoded = miniaudio.decode(mp3_bytes)
        samples = np.frombuffer(decoded.samples, dtype=np.int16).astype(np.float32)
        samples /= 32768.0

        if decoded.nchannels > 1:
            samples = samples.reshape(-1, decoded.nchannels)

        sd.play(samples, samplerate=decoded.sample_rate)
        sd.wait()
    except Exception as e:
        logger.error(f"  [TTS playback error] {e}")
