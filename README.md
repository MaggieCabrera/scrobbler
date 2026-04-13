# scrobbler

A small standalone device that listens to physical media (vinyl, CDs, tapes) and scrobbles to Last.fm using audio fingerprinting.

See [PLAN.md](../PLAN.md) for full hardware list, wiring, and design notes.

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

On a Mac (for testing without hardware): uses the built-in mic. GPIO and display features are disabled automatically when not running on a Pi.
