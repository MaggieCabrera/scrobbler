"""
First-time Last.fm authentication.

The user never touches an API key. Flow:
  1. Request a Last.fm auth token
  2. Build the auth URL and render it as a QR code + clickable link
  3. User clicks or scans the link and approves the app on Last.fm's site
  4. Poll until approved — if the token expires, generate a new one automatically
  5. Save the session key to .session; never asks again
"""

import json
import time
import sys
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
    Automatically refreshes the token if it expires.
    Returns (session_key, username).
    """
    import pylast

    sg = pylast.SessionKeyGenerator(network)

    while True:
        url = sg.get_web_auth_url()

        print("\n  ── Last.fm Setup ─────────────────────────────")
        print("  Scan the QR code with your phone to log in.\n")
        _print_qr_terminal(url)
        print(f"\n  → {url}\n")

        display.show_qr(url)

        print("  Waiting", end="", flush=True)

        try:
            session_key, username = _poll(sg, network, url)
        except _TokenExpired:
            print("\n  Token expired — generating a new one...\n")
            continue  # loop back and get a fresh token

        save_session(session_key, username)
        print(f"\n\n  ✓ Logged in{f' as {username}' if username else ''}.\n")
        display.show_status(f"Hi, {username or 'User'}!")
        time.sleep(2)
        return session_key, username


class _TokenExpired(Exception):
    pass


def _poll(sg, network, url):
    import pylast
    import urllib.parse

    # Extract the token from the auth URL so we can make one auth.getSession
    # call and get both the session key and username from the same response.
    token = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["token"][0]

    while True:
        try:
            response = network._request("auth.getSession", False, {"token": token})
            session_key = response["session"]["key"]
            username = response["session"]["name"]
            return session_key, username
        except pylast.WSError as e:
            if e.status == 14:
                # Not yet approved — keep waiting
                print(".", end="", flush=True)
                time.sleep(5)
            elif e.status in (4, 15):
                # Token expired or invalid — caller will get a fresh one
                raise _TokenExpired()
            else:
                raise


def _print_qr_terminal(url):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
