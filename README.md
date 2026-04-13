# scrobbler

A small standalone device that listens to physical media (vinyl, CDs, tapes) and scrobbles to Last.fm using audio fingerprinting. No barcodes, no manual input — just put it next to your speakers.

See [PLAN.md](../PLAN.md) for hardware list, wiring, and design notes.

## How it works

Records ~12 seconds of audio from the mic → generates a fingerprint with Chromaprint → looks it up on AcoustID → scrobbles artist + track to Last.fm. Runs in a continuous loop, detecting track changes as they happen.

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

Edit `.env` with your keys:
- **AcoustID:** free key at https://acoustid.org/login
- **Last.fm:** free key at https://www.last.fm/api/account/create

### 4. Run

```bash
python main.py
```

On Mac it uses the built-in microphone. GPIO and OLED are disabled automatically — output goes to the terminal instead.

**Controls (Mac):**
- `Enter` — toggle listening on/off
- `q` + `Enter` — quit

**Controls (Pi):**
- Short press button — toggle listening on/off (LED shows state)
- Hold button 3s — safe shutdown

## Project structure

```
main.py          Entry point, main loop
audio.py         Mic capture (sounddevice)
fingerprint.py   Chromaprint + AcoustID lookup
scrobbler.py     Last.fm state + scrobbling logic
display.py       OLED on Pi, terminal output on Mac
button.py        GPIO button on Pi, keyboard input on Mac
config.py        Settings + loads .env
```

## License

GPL v3
