"""Video agent: render a ~1-min summary video from the script.

Pipeline:
  script segments -> TTS (audio per segment, optional) -> Pillow-drawn frame
  per segment -> MoviePy ImageClips concatenated + audio -> MP4

Rendering uses Pillow to draw each frame (title + wrapped caption) and feeds
them to MoviePy's ImageClip. This avoids TextClip / ImageMagick entirely, so
no extra system dependency is needed. imageio-ffmpeg bundles the ffmpeg binary.

Degrades gracefully: if moviepy is unavailable it still produces a video row
with the saved script .txt so the rest of the app works.
"""
from __future__ import annotations

import logging
import textwrap
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.synthesis.script import build_script
from app.core.config import settings
from app.core.constants import DOMAIN_LABELS
from app.models.db_models import Video

log = logging.getLogger("video")

W, H = 1280, 720
BG = (12, 18, 32)
ACCENT = (78, 161, 255)
WHITE = (235, 240, 250)
WORDS_PER_SEC = 2.6  # narration pace estimate when no TTS audio
MIN_SEG_SECONDS = 3.0


def _script_to_text(script: dict) -> str:
    return "\n".join(seg.get("text", "") for seg in script.get("segments", []))


def _load_font(size: int):
    from PIL import ImageFont

    # Try common Windows fonts, fall back to PIL default.
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _draw_frame(text: str, label: str, out_path: Path) -> None:
    """Render one segment frame (title chip + centered wrapped caption) via Pillow."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = _load_font(34)
    body_font = _load_font(46)

    # domain label, top-left
    draw.text((80, 56), label.upper(), font=title_font, fill=ACCENT)
    draw.line((80, 104, 80 + 360, 104), fill=ACCENT, width=3)

    # wrapped caption, vertically centered
    lines = textwrap.wrap(text, width=42) or [""]
    line_h = body_font.getbbox("Ay")[3] + 16
    block_h = line_h * len(lines)
    y = (H - block_h) // 2
    for line in lines:
        w = draw.textlength(line, font=body_font)
        draw.text(((W - w) // 2, y), line, font=body_font, fill=WHITE)
        y += line_h

    img.save(out_path)


def _try_render(script: dict, out_dir: Path, video_id: str) -> tuple[str | None, int | None]:
    """Render an MP4 from the script. Returns (path, duration) or (None, None) on skip."""
    try:
        from moviepy import (
            AudioFileClip,
            ImageClip,
            concatenate_videoclips,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("moviepy unavailable, skipping render: %s", exc)
        return None, None

    try:
        from app.services.tts import synthesize  # optional
    except Exception:  # noqa: BLE001
        synthesize = None

    clips = []
    for i, seg in enumerate(script.get("segments", [])):
        text = seg.get("text", "")
        label = DOMAIN_LABELS.get(seg.get("domain", ""), seg.get("domain", "").title())

        # frame image
        frame_path = out_dir / f"{video_id}_{i}.png"
        _draw_frame(text, label, frame_path)

        # optional narration audio; else estimate duration from word count
        audio = None
        duration = max(MIN_SEG_SECONDS, len(text.split()) / WORDS_PER_SEC)
        if synthesize:
            mp3 = out_dir / f"{video_id}_{i}.mp3"
            if synthesize(text, mp3):
                audio = AudioFileClip(str(mp3))
                duration = max(MIN_SEG_SECONDS, audio.duration)

        clip = ImageClip(str(frame_path)).with_duration(duration)
        if audio is not None:
            clip = clip.with_audio(audio)
        clips.append(clip)

    if not clips:
        return None, None

    final = concatenate_videoclips(clips, method="chain")
    out_path = out_dir / f"{video_id}.mp4"
    write_kwargs = dict(fps=24, codec="libx264", logger=None)
    if any(c.audio is not None for c in clips):
        write_kwargs["audio_codec"] = "aac"
    final.write_videofile(str(out_path), **write_kwargs)
    duration = int(final.duration)
    final.close()

    # clean up intermediate frame/audio files
    for tmp in out_dir.glob(f"{video_id}_*"):
        tmp.unlink(missing_ok=True)

    # return filename only; API serves it from the /media mount
    return f"{video_id}.mp4", duration


async def generate_video(session: AsyncSession) -> str:
    out_dir = Path(settings.media_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create the row up front so the request always has a tracked artifact,
    # even if script building or rendering fails afterwards.
    video = Video(script="", status="processing")
    session.add(video)
    await session.commit()

    try:
        script = await build_script(session)  # has its own headline fallback
        script_text = _script_to_text(script)
        video.script = script_text

        # always save the script text so there is a usable artifact
        (out_dir / f"{video.id}.txt").write_text(script_text, encoding="utf-8")

        path, duration = _try_render(script, out_dir, video.id)
        video.file_path = path or f"{video.id}.txt"
        video.duration_s = duration or 60
        video.status = "done"
    except Exception as exc:  # noqa: BLE001
        log.exception("Video generation failed")
        video.status = "failed"
        video.error = str(exc)[:1000]

    await session.commit()
    log.info("Video %s -> %s (%s)", video.id, video.status, video.file_path)
    return video.id
