import sounddevice as sd
import numpy as np
from config import SAMPLE_RATE, CAPTURE_DURATION, CHANNELS, AUDIO_DEVICE


def capture():
    """
    Record audio from the configured input device (or system default).
    Returns a flat int16 numpy array.
    """
    audio = sd.rec(
        int(CAPTURE_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        device=AUDIO_DEVICE,
    )
    sd.wait()
    return audio.flatten()
