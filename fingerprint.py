"""
Track identification via audio fingerprinting.

Currently uses Shazam via shazamio (MIT licensed).
Sends a short WAV clip to Shazam's servers; returns artist + title.
Requires an internet connection.

To add a new backend (e.g. ACRCloud), implement a function with the signature:
    _identify_<name>(audio_data: np.ndarray) -> dict | None
and register it in _BACKENDS below.
"""

import io
import wave
import asyncio

from config import FINGERPRINT_BACKENDS, SAMPLE_RATE, CHANNELS

# Reuse one event loop and one Shazam instance across all identify() calls.
_loop = asyncio.new_event_loop()
_shazam = None


def identify(audio_data):
    """
    Identify a track from a raw int16 numpy audio array.
    Tries each backend in FINGERPRINT_BACKENDS order; returns first match.
    Returns {'artist', 'title', 'duration', 'score'} or None.
    """
    for name in FINGERPRINT_BACKENDS:
        fn = _BACKENDS.get(name)
        if fn is None:
            print(f"  [warning] unknown backend '{name}', skipping")
            continue
        result = fn(audio_data)
        if result:
            return result
    return None


# ── Shazam ────────────────────────────────────────────────────────────────────

def _identify_shazam(audio_data):
    global _shazam
    try:
        if _shazam is None:
            from shazamio import Shazam
            _shazam = Shazam()
        wav_bytes = _to_wav_bytes(audio_data)
        return _loop.run_until_complete(_shazam_recognize(wav_bytes))
    except Exception as e:
        print(f"  [error] shazam: {e}")
    return None


async def _shazam_recognize(wav_bytes):
    result = await _shazam.recognize(wav_bytes)

    track = result.get("track")
    if not track:
        print(f"  [shazam] no match (response keys: {list(result.keys())})")
        return None

    artist = track.get("subtitle", "")  # artist name
    title = track.get("title", "")
    if artist and title:
        images = track.get("images", {})
        cover = images.get("coverarthq") or images.get("coverart") or ""
        return {
            "artist": artist,
            "title": title,
            "cover": cover,
            "duration": 0,   # Shazam doesn't return duration
            "score": 1.0,    # Shazam doesn't expose a confidence score
        }
    return None


def _to_wav_bytes(audio_data):
    """Convert a raw int16 numpy array to in-memory WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16 = 2 bytes per sample
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


# Registered after function definitions so names resolve without lambda wrappers.
_BACKENDS = {
    "shazam": _identify_shazam,
}
