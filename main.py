#!/usr/bin/env python3
"""
Physical Media Scrobbler
Listens via microphone, identifies tracks with Shazam, scrobbles to Last.fm.

First run: shows a QR code to authenticate with Last.fm.
After that: runs automatically, no interaction needed.
"""

import signal
import sys
import time
import pylast

import setup_device
from audio import capture
from fingerprint import identify
from scrobbler import Scrobbler
from display import Display
from button import Button
from config import LASTFM_API_KEY, LASTFM_API_SECRET

listening = True


def main():
    global listening

    display = Display()

    # ── Auth ────────────────────────────────────────────────────────────────
    if setup_device.session_exists():
        session = setup_device.load_session()
        session_key = session["session_key"]
        username = session.get("username") or ""
        print(f"\n  Welcome back, {username or 'User'}.\n")
    else:
        network = pylast.LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
        )
        session_key, username = setup_device.run(network, display)

    # ── Ready ────────────────────────────────────────────────────────────────
    scrobbler = Scrobbler(session_key)

    def on_toggle(state):
        global listening
        listening = state
        display.show_status("listening..." if state else "paused")
        print(f"\n\n  {'[on]' if state else '[paused]'}\n")

    def on_shutdown():
        print("\n\n  Shutting down...")
        display.clear()
        button.cleanup()
        sys.exit(0)

    button = Button(on_toggle=on_toggle, on_shutdown=on_shutdown)

    signal.signal(signal.SIGINT, lambda *_: on_shutdown())
    signal.signal(signal.SIGTERM, lambda *_: on_shutdown())

    print("  Physical Media Scrobbler")
    print("  ========================")
    display.show_status("listening...")

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        if not listening:
            time.sleep(0.5)
            continue

        # During capture: keep showing the track if we have one, else "listening..."
        if not scrobbler.current:
            display.show_status("listening...")
        audio = capture()

        if not listening:
            continue

        # Always show "identifying..." during the Shazam API call
        display.show_status("identifying...")
        result = identify(audio)

        if result:
            changed = scrobbler.track_changed(result)
            if changed:
                display.show_track(result["artist"], result["title"], result.get("cover", ""))
                print(
                    f"\n\n  Now playing: {result['artist']} — {result['title']}"
                    f"  (confidence: {result['score']:.0%})\n"
                )
            else:
                # Same track — restore track display (was overwritten by "identifying...")
                cur = scrobbler.current
                display.show_track(cur["artist"], cur["title"], cur.get("cover", ""))
        else:
            # No match — show clearly, then revert to last known track
            print("  [no match]")
            display.show_status("no match")
            time.sleep(3)
            if scrobbler.current:
                cur = scrobbler.current
                display.show_track(cur["artist"], cur["title"], cur.get("cover", ""))


if __name__ == "__main__":
    main()
