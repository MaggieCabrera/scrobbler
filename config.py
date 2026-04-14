import os
from dotenv import load_dotenv

load_dotenv()

# --- Last.fm (app-level keys — users authenticate via QR flow, not here) ---
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_API_SECRET = os.environ.get("LASTFM_API_SECRET", "")

# --- Audio ---
CAPTURE_DURATION = 20   # seconds per fingerprint attempt
CHANNELS = 1
# Device index for audio input. None = system default.
# Run: python -c "import sounddevice as sd; print(sd.query_devices())" to list options.
_device_env = os.environ.get("AUDIO_DEVICE", "")
AUDIO_DEVICE = int(_device_env) if _device_env.strip() else None

# Use the device's native sample rate to avoid PortAudio resampling,
# which can degrade audio quality enough to hurt Shazam identification.
def _native_sample_rate(device=AUDIO_DEVICE):
    try:
        import sounddevice as sd
        idx = device if device is not None else sd.default.device[0]
        return int(sd.query_devices(idx)["default_samplerate"])
    except Exception:
        return 44100

SAMPLE_RATE = _native_sample_rate()

# --- Fingerprinting ---
# Comma-separated list of backends to try in order — first match wins.
# Currently only 'shazam' is supported. Add new backends in fingerprint.py.
FINGERPRINT_BACKENDS = [
    b.strip()
    for b in os.environ.get("FINGERPRINT_BACKENDS", "shazam").split(",")
    if b.strip()
]

# --- Scrobbling ---
MIN_PLAY_SECONDS = 30
MIN_PLAY_RATIO = 0.5

# --- GPIO pins (Pi only) ---
BUTTON_PIN = 17
LED_PIN = 27
