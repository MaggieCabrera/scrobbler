"""
First-time Last.fm authentication.

The user never touches an API key. Flow:
  1. Request a Last.fm auth token
  2. Build the auth URL and render it as a QR code
  3. User scans QR with their phone and approves the app on Last.fm's site
  4. Poll until approved, then save the session key to .session
"""

import json
import time
import sys
import os
import qrcode
from pathlib import Path

SESSION_FILE = Path(__file__).parent / ".session"


def session_exists():
    return SESSION_FILE.exists()


def load_session():
    with open(SESSION_FILE) as f:
        return json.load(f)


def save_session(session_key, username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"session_key": session_key, "username": username}, f)


def run(network, display):
    """
    Full auth flow. Blocks until the user approves or Ctrl-C.
    Returns (session_key, username).
    """
    import pylast

    sg = pylast.SessionKeyGenerator(network)
    url = sg.get_web_auth_url()

    print("\n  ── Last.fm Setup ─────────────────────────────")
    print("  Scan the QR code with your phone to log in.")
    print("  The device will continue automatically once approved.\n")

    _print_qr_terminal(url)

    print(f"\n  Or visit:\n  {url}\n")
    display.show_qr(url)

    print("  Waiting for approval", end="", flush=True)
    session_key, username = _poll(sg, url)

    save_session(session_key, username)
    print(f"\n\n  ✓ Logged in as {username}\n")
    display.show_status(f"Hi, {username}!")
    time.sleep(2)
    return session_key, username


def _poll(sg, url):
    import pylast

    while True:
        try:
            session_key, username = sg.get_web_auth_session_key_bundle(url)
            return session_key, username
        except pylast.WSError as e:
            if "Unauthorized" in str(e) or e.status == "14":
                print(".", end="", flush=True)
                time.sleep(5)
            else:
                raise


def _print_qr_terminal(url):
    """Render a scannable QR code in the terminal."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
