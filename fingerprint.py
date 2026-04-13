import acoustid
from config import ACOUSTID_API_KEY, SAMPLE_RATE, CHANNELS, MIN_SCORE


def identify(audio_data):
    """
    Fingerprint a raw int16 numpy audio array and look it up on AcoustID.

    Returns a dict with 'artist', 'title', 'duration' on success, or None.
    AcoustID only needs artist + title — album is not requested.
    """
    if not ACOUSTID_API_KEY:
        raise RuntimeError("ACOUSTID_API_KEY is not set in .env")

    try:
        duration = len(audio_data) / SAMPLE_RATE
        fingerprint = acoustid.fingerprint(SAMPLE_RATE, CHANNELS, audio_data.tobytes())
        response = acoustid.lookup(
            ACOUSTID_API_KEY,
            fingerprint,
            duration,
            meta="recordings",
        )

        if response.get("status") != "ok":
            return None

        for result in response.get("results", []):
            if result.get("score", 0) < MIN_SCORE:
                continue

            recordings = result.get("recordings", [])
            if not recordings:
                continue

            rec = recordings[0]
            artists = rec.get("artists", [])
            artist = artists[0]["name"] if artists else ""
            title = rec.get("title", "")

            if artist and title:
                return {
                    "artist": artist,
                    "title": title,
                    "duration": rec.get("duration", 0),
                    "score": result["score"],
                }

    except acoustid.NoBackendError:
        print("  [error] chromaprint not found — run: brew install chromaprint")
    except acoustid.FingerprintGenerationError:
        pass  # silence, low audio or too short
    except Exception as e:
        print(f"  [error] fingerprint: {e}")

    return None
