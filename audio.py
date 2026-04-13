import sounddevice as sd
import numpy as np
from config import SAMPLE_RATE, CAPTURE_DURATION, CHANNELS


def capture():
    """
    Record audio from the default microphone.
    Returns a flat int16 numpy array.
    """
    audio = sd.rec(
        int(CAPTURE_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()
    return audio.flatten()
