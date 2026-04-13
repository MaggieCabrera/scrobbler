#!/usr/bin/env python3
"""
Physical Media Scrobbler
Listens via microphone, identifies tracks with AcoustID, scrobbles to Last.fm.
"""

import signal
import sys
import time

from audio import capture
from fingerprint import identify
from scrobbler import Scrobbler
from display import Display
from button import Button

listening = True
running = True


def main():
    global listening, running

    display = Display()
    scrobbler = Scrobbler()

    def on_toggle(state):
        global listening
        listening = state
        display.show_status("listening..." if state else "paused")
        print(f"\n\n  {'[on]' if state else '[paused]'}\n")

    def on_shutdown():
        global running
        print("\n\n  Shutting down...")
        display.clear()
        button.cleanup()
        sys.exit(0)

    button = Button(on_toggle=on_toggle, on_shutdown=on_shutdown)

    signal.signal(signal.SIGINT, lambda *_: on_shutdown())
    signal.signal(signal.SIGTERM, lambda *_: on_shutdown())

    print("\n  Physical Media Scrobbler")
    print("  ========================")
    display.show_status("listening...")

    while running:
        if not listening:
            time.sleep(0.5)
            continue

        # Capture audio — this blocks for CAPTURE_DURATION seconds
        display.show_status("listening...")
        audio = capture()

        if not listening:
            continue

        # Identify
        display.show_status("identifying...")
        result = identify(audio)

        if result:
            changed = scrobbler.track_changed(result)
            if changed:
                display.show_track(result["artist"], result["title"])
                print(
                    f"\n\n  Now playing: {result['artist']} — {result['title']}"
                    f"  (confidence: {result['score']:.0%})\n"
                )
        else:
            # Keep previous track on display, go back to listening
            if scrobbler.current:
                display.show_track(
                    scrobbler.current["artist"],
                    scrobbler.current["title"],
                )


if __name__ == "__main__":
    main()
