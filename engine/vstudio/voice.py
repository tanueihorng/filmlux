"""Natural neural voiceover (Microsoft neural voices via edge-tts), cached per line, trimmed and levelled.

The narration TEXT is sent to Microsoft's online speech service: never put personal data in narration.
Behind a corporate HTTPS proxy, `truststore` makes Python use the Windows certificate store (checks stay on).
"""
from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

import av
import numpy as np

from .config import SR

VOICES = {
    "en-US-AvaNeural":      "US female, warm and natural. Default; the team's favourite.",
    "en-US-AndrewNeural":   "US male, calm and trustworthy. Leadership, serious topics.",
    "en-US-EmmaNeural":     "US female, bright and friendly. Onboarding, upbeat explainers.",
    "en-US-BrianNeural":    "US male, relaxed and conversational. Casual walkthroughs.",
    "en-GB-SoniaNeural":    "UK female, crisp. Formal or international audiences.",
    "en-GB-RyanNeural":     "UK male, steady. Formal narration.",
    "en-SG-LunaNeural":     "Singapore English female. Local audiences.",
    "en-SG-WayneNeural":    "Singapore English male. Local audiences.",
    "en-AU-NatashaNeural":  "Australian female, warm.",
    "en-IN-NeerjaNeural":   "Indian English female, clear.",
    "zh-CN-XiaoxiaoNeural": "Mandarin female (for translated narration).",
    "ms-MY-YasminNeural":   "Malay female (for translated narration).",
    "ta-IN-PallaviNeural":  "Tamil female (for translated narration).",
}
DEFAULT_VOICE, DEFAULT_RATE = "en-US-AvaNeural", "-4%"
VO_DB = -17.0          # target RMS of speech (dBFS)


def clip_path(cache: Path, text: str, voice: str, rate: str) -> Path:
    return cache / (hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16] + ".mp3")


def synth(lines, cache: Path, voice=DEFAULT_VOICE, rate=DEFAULT_RATE, force=False):
    """Fetch every missing clip. Returns how many were synthesised."""
    cache.mkdir(parents=True, exist_ok=True)
    todo = [t for t in dict.fromkeys(lines) if t and (force or not clip_path(cache, t, voice, rate).exists()
                                                      or clip_path(cache, t, voice, rate).stat().st_size == 0)]
    if not todo:
        return 0
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("edge-tts is not installed: pip install -r requirements.txt") from e

    async def go():
        for t in todo:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(t, voice, rate=rate).save(str(clip_path(cache, t, voice, rate)))
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1.5)
    try:
        asyncio.run(go())
    except Exception as e:
        raise RuntimeError(f"Voice synthesis failed ({e}). It needs internet access to Microsoft's speech service; "
                           "in a sandbox, enable network for this step.") from e
    return len(todo)


_cache = {}


def load(cache: Path, text: str, voice=DEFAULT_VOICE, rate=DEFAULT_RATE) -> np.ndarray:
    """Mono float32 at SR, silence trimmed, levelled to VO_DB, with tiny fades."""
    p = clip_path(cache, text, voice, rate)
    if p in _cache:
        return _cache[p]
    c = av.open(str(p)); rs = av.AudioResampler(format="fltp", layout="mono", rate=SR); parts = []
    for f in c.decode(audio=0):
        parts += [g.to_ndarray()[0] for g in rs.resample(f)]
    parts += [g.to_ndarray()[0] for g in rs.resample(None)]
    c.close()
    x = np.concatenate(parts).astype(np.float32) if parts else np.zeros(SR // 10, np.float32)
    a = np.abs(x); k = 480; env = np.convolve(a, np.ones(k) / k, "same"); on = np.where(env > .01)[0]
    if len(on):
        x = x[max(0, on[0] - 1200): on[-1] + 2400]
    loud = x[np.abs(x) > .02]
    rms = np.sqrt(np.mean(loud ** 2)) if loud.size else 1
    x = x * (10 ** (VO_DB / 20) / max(rms, 1e-4))
    f = np.linspace(0, 1, 240, dtype=np.float32); x[:240] *= f; x[-240:] *= f[::-1]
    _cache[p] = x.astype(np.float32)
    return _cache[p]


def duration(cache: Path, text: str, voice=DEFAULT_VOICE, rate=DEFAULT_RATE) -> float:
    return len(load(cache, text, voice, rate)) / SR
