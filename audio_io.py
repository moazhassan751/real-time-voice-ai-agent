"""
Audio I/O helpers — microphone capture and speaker playback.

Recording uses a push-to-talk model:
  1. The caller invokes ``record_audio()``.
  2. Audio is captured continuously from the default mic.
  3. When the user presses Enter a second time, recording stops and
     the raw PCM frames are returned as a WAV-file byte buffer (in-memory).
"""

import io
import sys
import wave
import threading

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, CHANNELS, DTYPE


def record_audio() -> bytes:
    """Record from the microphone until the user presses Enter.

    Returns:
        Raw WAV bytes (16-bit PCM, mono, 16 kHz) suitable for sending
        directly to the Whisper API.
    """
    frames: list[np.ndarray] = []
    stop_event = threading.Event()

    def _callback(indata: np.ndarray, frame_count, time_info, status):
        if status:
            print(f"  [audio] {status}", file=sys.stderr)
        frames.append(indata.copy())

    # Open the mic stream.
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=_callback,
    )

    def _wait_for_enter():
        """Block on stdin; set the event once Enter is pressed."""
        input()  # blocks until Enter
        stop_event.set()

    listener = threading.Thread(target=_wait_for_enter, daemon=True)

    stream.start()
    listener.start()

    # Wait until the user presses Enter (or the listener thread ends).
    stop_event.wait()
    stream.stop()
    stream.close()

    if not frames:
        return b""

    audio_data = np.concatenate(frames, axis=0)

    # Pack into an in-memory WAV file.
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


def play_audio(audio_data: bytes, sample_rate: int = 44100) -> None:
    """Play raw PCM audio bytes (assumed to be signed 16-bit) through the
    default speaker.

    ``audio_data`` should be the **raw PCM bytes** (no WAV header). The
    caller is responsible for stripping the header if needed.
    """
    if not audio_data:
        return
    samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
    # Normalise to [-1, 1] for sounddevice.
    samples /= 32768.0
    sd.play(samples, samplerate=sample_rate)
    sd.wait()
