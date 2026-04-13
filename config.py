import os
from dotenv import load_dotenv

load_dotenv()

# --- AcoustID (app-level key, registered once by the developer) ---
ACOUSTID_API_KEY = os.environ.get("ACOUSTID_API_KEY", "")

# --- Last.fm (app-level keys — users authenticate via QR flow, not here) ---
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_API_SECRET = os.environ.get("LASTFM_API_SECRET", "")

# --- Audio ---
SAMPLE_RATE = 44100
CAPTURE_DURATION = 12   # seconds per fingerprint attempt
CHANNELS = 1

# --- Fingerprinting ---
MIN_SCORE = 0.5         # minimum AcoustID confidence to accept a result

# --- Scrobbling ---
MIN_PLAY_SECONDS = 30
MIN_PLAY_RATIO = 0.5

# --- GPIO pins (Pi only) ---
BUTTON_PIN = 17
LED_PIN = 27
