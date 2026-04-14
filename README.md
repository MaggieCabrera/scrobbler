# scrobbler

A small standalone device that listens to physical media (vinyl, CDs, tapes) and scrobbles to Last.fm using audio fingerprinting. No barcodes, no manual input — just put it next to your speakers.

## How it works

Records ~20 seconds of audio from the mic → sends it to Shazam for identification → scrobbles artist + track to Last.fm. Runs in a continuous loop, detecting track changes as they happen.

## Setup

### 1. Python environment

```bash
python -m venv venv
source venv/bin/activate

# Mac / dev
pip install -r requirements.txt

# Pi
pip install -r requirements.pi.txt
```

### 2. API keys

```bash
cp .env.example .env
```

Edit `.env` with your **Last.fm app-level keys** — registered once by the developer, not per user:
- `LASTFM_API_KEY` and `LASTFM_API_SECRET`: free at https://www.last.fm/api/account/create

Users never touch `.env`. They authenticate their Last.fm account via a QR code on first run (see Auth below).

### 3. Run

```bash
python main.py
```

On Mac, GPIO and the OLED are disabled automatically — a browser window opens at `http://localhost:8765` simulating the device display.

**Choosing an audio input device (Mac):**
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Set `AUDIO_DEVICE=<index>` in `.env` to override the default.

**Controls (Mac):**
- `Enter` — toggle listening on/off
- `q` + `Enter` — quit

**Controls (Pi):**
- Short press button — toggle listening on/off (LED shows state)
- Hold button 3s — safe shutdown

## Auth

Last.fm uses a web OAuth flow — no username or password is ever stored.

**First run:**
1. A QR code appears on the display (and in the browser on Mac)
2. Scan it and approve the app on Last.fm's site
3. The session key is saved to `.session` (gitignored)
4. Never asked again

**Session model:** One set of app-level API keys (in `.env`) works across all devices. Each device gets its own session key stored locally in `.session`:
```json
{"session_key": "...", "username": "..."}
```

If the auth token expires before approval (~30 minutes), a new QR is generated automatically.

## Testing fingerprinting

To test identification against an audio file without using the mic:

```bash
python test_identify.py path/to/song.flac
```

## Project structure

```
main.py              Entry point, main loop
audio.py             Mic capture (sounddevice)
fingerprint.py       Track identification via Shazam
scrobbler.py         Last.fm state + scrobbling logic
display.py           OLED on Pi / browser simulator on Mac
web_display.py       Browser-based display (Mac only, localhost:8765)
setup_device.py      First-run Last.fm auth via QR code
button.py            GPIO button on Pi, keyboard input on Mac
config.py            Settings, loads .env
test_identify.py     Identify a track from an audio file (dev tool)
```

## License

GPL v3
