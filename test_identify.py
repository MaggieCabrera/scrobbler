#!/usr/bin/env python3
"""
Test track identification from an audio file instead of the mic.
Useful for verifying a backend works before testing with live audio.

Usage:
    python test_identify.py path/to/song.wav [--backend acoustid|shazam]

The file is read, converted to mono int16, and passed through the same
identify() function the main loop uses — so this tests the real pipeline.
"""

import sys
import os
import argparse
import numpy as np

# Allow running from the scrobbler/ directory
sys.path.insert(0, os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="Identify a track from an audio file")
    parser.add_argument("file", help="Path to audio file (WAV, MP3, FLAC, etc.)")
    parser.add_argument(
        "--backends",
        help="Comma-separated backends to try in order, e.g. 'shazam,acoustid' (overrides .env)",
    )
    args = parser.parse_args()

    if args.backends:
        os.environ["FINGERPRINT_BACKENDS"] = args.backends

    # Import after setting env so config picks up the override
    from config import FINGERPRINT_BACKENDS, SAMPLE_RATE
    from fingerprint import identify

    print(f"Backends: {' → '.join(FINGERPRINT_BACKENDS)}")
    print(f"File:    {args.file}")
    print()

    audio = _load_audio(args.file, SAMPLE_RATE)
    if audio is None:
        sys.exit(1)

    print(f"Loaded {len(audio) / SAMPLE_RATE:.1f}s of audio — identifying...")
    result = identify(audio)

    if result:
        print(f"\n  Artist:   {result['artist']}")
        print(f"  Title:    {result['title']}")
        if result.get("duration"):
            print(f"  Duration: {result['duration']}s")
        if result.get("score") < 1.0:
            print(f"  Score:    {result['score']:.0%}")
    else:
        print("\n  No match found.")


def _load_audio(path, target_rate):
    """Load any audio file to a mono int16 numpy array at target_rate Hz."""
    try:
        import soundfile as sf
        data, sr = sf.read(path, dtype="int16", always_2d=True)
        ch = data.shape[1]
        mono = data[:, 0]
        if sr != target_rate:
            print(f"  Note: resampling from {sr}Hz to {target_rate}Hz")
            mono = _resample(mono, sr, target_rate)
        print(f"  {sr}Hz, {ch}ch → mono int16, {len(mono)/target_rate:.1f}s")
        return mono
    except ImportError:
        pass

    # Fallback: use pydub (installed with shazamio)
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(path)
        audio = audio.set_frame_rate(target_rate).set_channels(1).set_sample_width(2)
        return np.frombuffer(audio.raw_data, dtype=np.int16)
    except Exception as e:
        print(f"  [error] could not load file: {e}")
        print("  Try: pip install soundfile")
        return None


def _resample(mono, from_rate, to_rate):
    """Simple linear resample for a mono int16 array."""
    new_len = int(len(mono) * to_rate / from_rate)
    indices = np.linspace(0, len(mono) - 1, new_len)
    return np.interp(indices, np.arange(len(mono)), mono).astype(np.int16)


if __name__ == "__main__":
    main()
