"""Text-to-speech helper. Optional; returns False if no provider is configured."""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

log = logging.getLogger("tts")


def synthesize(text: str, out_path: Path) -> bool:
    """Write narration audio to out_path. Returns True on success.

    Uses OpenAI TTS if OPENAI_API_KEY is set. Extend with ElevenLabs as needed.
    """
    if not text.strip():
        return False
    if settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.audio.speech.create(
                model="tts-1", voice="onyx", input=text[:4000]
            )
            resp.stream_to_file(str(out_path))
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("OpenAI TTS failed: %s", exc)
            return False
    return False
