# scrobbler

A small standalone device that listens to physical media (vinyl, CDs, tapes) and scrobbles to Last.fm using audio fingerprinting. No barcodes, no manual input — just put it next to your speakers.

See [PLAN.md](../PLAN.md) for hardware list, wiring, and design notes.

## How it works

Records ~20 seconds of audio from the mic → generates a Chromaprint fingerprint locally → looks it up on AcoustID → scrobbles artist + track to Last.fm. Runs in a continuous loop, detecting track changes as they happen. No audio ever leaves the device — only the fingerprint (a short string) is sent to AcoustID.

## Setup

### 1. Install system dependency

AcoustID fingerprinting requires the native `libchromaprint` library.

**Mac:**
```bash
brew install chromaprint
```

**Pi:**
```bash
sudo apt install libchromaprint1 libchromaprint-dev
```

### 2. Python environment

```bash
python -m venv venv
source venv/bin/activate

# Mac / dev
pip install -r requirements.txt

# Pi
pip install -r requirements.pi.txt
```

### 3. API keys

```bash
cp .env.example .env
```

Edit `.env` with **app-level** keys only — these are registered once by the developer, not per user:
- **AcoustID:** free key at https://acoustid.org/login
- **Last.fm API key + secret:** free at https://www.last.fm/api/account/create

Users never touch `.env`. They authenticate their Last.fm account via a QR code on first run (see Auth below).

### 4. Run

```bash
python main.py
```

On Mac it uses the system default audio input. GPIO and OLED are disabled automatically — a browser window opens at `http://localhost:8765` simulating the device display.

**Choosing an audio input device (Mac):**
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Set `AUDIO_DEVICE=<index>` in `.env` to override the default. Leave unset to use the system default.

**Mac testing caveat:** Chromaprint needs a clean, close-mic signal to generate a reliable fingerprint. Recording from a mic in a room picks up reverb and echo that can prevent matching. The best Mac test setup is a direct line-in connection (e.g. phone headphone out → audio interface line input). On the actual Pi device, the INMP441 mic sits centimetres from the speaker, giving a clean signal.

**Controls (Mac):**
- `Enter` — toggle listening on/off
- `q` + `Enter` — quit

**Controls (Pi):**
- Short press button — toggle listening on/off (LED shows state)
- Hold button 3s — safe shutdown

## Auth

Last.fm uses a web OAuth flow — no username or password is ever stored in config.

**First run:**
1. A QR code appears on the display (and in the browser on Mac)
2. User scans it and approves the app on Last.fm's site
3. The session key is saved to `.session` (gitignored)
4. Never asked again

**Session model:** One set of app-level API keys (in `.env`) for all devices. Each device/user gets their own session key stored locally. This is standard OAuth — the app key isn't secret from users, it just identifies the app to Last.fm.

`.session` format:
```json
{"session_key": "...", "username": "..."}
```

**Token refresh:** If the auth token expires before the user approves (Last.fm tokens expire in ~30 minutes of inactivity), a new QR is generated automatically.

**Known gotcha:** pylast's `SessionKeyGenerator` internally calls `auth.getSession` when you call `get_web_auth_session_key(url)`. Once the token is exchanged for a session key, it's consumed — calling any method that hits `auth.getSession` a second time returns status 4 ("token not issued") and breaks the flow. After getting the session key, fetch the username via `network.get_authenticated_user().get_name()` instead.

## Project structure

```
main.py              Entry point, main loop
audio.py             Mic capture (sounddevice)
fingerprint.py       Chromaprint + AcoustID lookup
scrobbler.py         Last.fm state + scrobbling logic
display.py           OLED on Pi / browser simulator on Mac
web_display.py       Browser-based display (Mac only, localhost:8765)
setup_device.py      First-run Last.fm auth via QR code
button.py            GPIO button on Pi, keyboard input on Mac
config.py            Settings + loads .env
```

## License

GPL v3
