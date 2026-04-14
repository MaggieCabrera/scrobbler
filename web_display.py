"""
Browser-based OLED simulator for development on Mac.
Serves a page that looks like the 128x64 display on the physical device.
"""

import base64
import io
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

FONTS_DIR = Path(__file__).parent / "fonts"

PORT = 8765

_state = {"mode": "status", "status": "starting..."}
_lock = threading.Lock()

HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Scrobbler</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    @font-face {
      font-family: 'Doto';
      src: url('/fonts/Doto-Regular.ttf') format('truetype');
      font-weight: 400;
    }
    @font-face {
      font-family: 'Doto';
      src: url('/fonts/Doto-Bold.ttf') format('truetype');
      font-weight: 700;
    }

    body {
      background: #111;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: 'Courier New', monospace;
      gap: 16px;
    }

    .device {
      background: #222;
      border-radius: 14px;
      padding: 18px 20px 14px;
      box-shadow: 0 12px 48px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.05);
    }

    /* OLED screen — 3× scale of 128×64 */
    .screen {
      width: 384px;
      height: 192px;
      background: #000;
      border-radius: 4px;
      overflow: hidden;
      position: relative;
    }

    /* Scanline overlay */
    .screen::after {
      content: '';
      position: absolute;
      inset: 0;
      background: repeating-linear-gradient(
        transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
      );
      pointer-events: none;
      z-index: 20;
    }

    /* Plain text for status states */
    #statusOverlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 5;
    }

    .status-text {
      color: #ddd;
      font-family: 'Doto', 'Courier New', monospace;
      font-size: 13px;
      letter-spacing: 2px;
    }

    .status-text.identifying { color: #7cf; }
    .status-text.no-match    { color: #f44; }
    .status-text.paused      { color: #555; }

    .dot {
      display: inline-block;
      animation: blink 1.2s step-start infinite;
    }
    .dot:nth-child(2) { animation-delay: 0.4s; }
    .dot:nth-child(3) { animation-delay: 0.8s; }
    @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }

    /* Track view: album art + text side by side */
    #trackView {
      position: absolute;
      inset: 0;
      display: none;
      z-index: 5;
    }

    #coverArt {
      width: 192px;
      height: 192px;
      object-fit: cover;
      flex-shrink: 0;
      background: #111;
    }

    #trackInfo {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 0 16px;
      overflow: hidden;
    }

    .artist {
      color: #fff;
      font-family: 'Doto', 'Courier New', monospace;
      font-weight: 700;
      font-size: 15px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .title-clip {
      overflow: hidden;
      margin-top: 6px;
    }

    .title {
      color: #888;
      font-family: 'Doto', 'Courier New', monospace;
      font-weight: 400;
      font-size: 12px;
      white-space: nowrap;
      display: inline-block;
    }

    .title.scrolling {
      animation: marquee var(--dur, 10s) linear infinite;
      padding-left: 100%;
    }

    @keyframes marquee {
      from { transform: translateX(0); }
      to   { transform: translateX(-100%); }
    }

    /* Setup / QR */
    #setupOverlay {
      position: absolute;
      inset: 0;
      background: #000;
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      z-index: 10;
    }

    .setup-label {
      color: #fff;
      font-size: 10px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }

    .qr {
      width: 150px;
      height: 150px;
      image-rendering: pixelated;
    }

    .label {
      color: #444;
      font-size: 10px;
      letter-spacing: 3px;
      text-transform: uppercase;
    }
  </style>
</head>
<body>
  <div class="device">
    <div class="screen">
      <div id="statusOverlay"></div>
      <div id="trackView">
        <img id="coverArt" src="" alt="">
        <div id="trackInfo">
          <div class="artist" id="overlayArtist"></div>
          <div class="title-clip">
            <span class="title" id="overlayTitle"></span>
          </div>
        </div>
      </div>
      <div id="setupOverlay"></div>
    </div>
  </div>
  <div class="label">Scrobbler &mdash; Display Preview</div>

  <script>
    const statusOverlay = document.getElementById('statusOverlay');
    const trackView     = document.getElementById('trackView');
    const setupOverlay  = document.getElementById('setupOverlay');

    // ── Render functions ───────────────────────────────────────────────────
    let prev = {};

    function renderStatus(s) {
      if (s.status === prev.status && prev.mode === 'status') return;
      trackView.style.display     = 'none';
      setupOverlay.style.display  = 'none';
      statusOverlay.style.display = 'flex';

      const st      = s.status;
      const hasDots = st.endsWith('...');
      const text    = st.replace('...', '');
      const cls     = st.startsWith('identifying') ? 'identifying'
                    : st === 'no match'            ? 'no-match'
                    : st === 'paused'              ? 'paused' : '';
      const dots    = hasDots
        ? '<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>'
        : '';
      statusOverlay.innerHTML = `<span class="status-text ${cls}">${text}${dots}</span>`;
    }

    function renderTrack(s) {
      if (s.artist === prev.artist && s.title === prev.title && s.cover === prev.cover) return;

      statusOverlay.style.display = 'none';
      setupOverlay.style.display  = 'none';
      trackView.style.display     = 'flex';

      document.getElementById('coverArt').src           = s.cover || '';
      document.getElementById('overlayArtist').textContent = s.artist;

      const chars   = s.title.length;
      const titleEl = document.getElementById('overlayTitle');
      titleEl.textContent = s.title;
      titleEl.className   = 'title' + (chars > 20 ? ' scrolling' : '');
      titleEl.style.setProperty('--dur', Math.max(6, chars * 0.18) + 's');
    }

    function renderSetup(s) {
      if (prev.mode === 'setup' && prev.qr === s.qr) return;
      trackView.style.display     = 'none';
      statusOverlay.style.display = 'none';
      setupOverlay.style.display  = 'flex';
      setupOverlay.innerHTML = `
        <div class="setup-label">Scan to set up Last.fm</div>
        <img class="qr" src="${s.qr}">`;
    }

    async function update() {
      try {
        const s = await fetch('/state').then(r => r.json());
        if      (s.mode === 'setup') renderSetup(s);
        else if (s.mode === 'track') renderTrack(s);
        else                         renderStatus(s);
        prev = {...s};
      } catch (_) {}
    }

    update();
    setInterval(update, 800);
  </script>
</body>
</html>"""


class _Server(HTTPServer):
    allow_reuse_address = True


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/state":
            with _lock:
                body = json.dumps(_state).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/fonts/"):
            filename = self.path[len("/fonts/"):]
            font_path = FONTS_DIR / "Doto" / "static" / filename
            if font_path.exists() and font_path.suffix == ".ttf":
                body = font_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "font/ttf")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress request logs


def start():
    server = _Server(("localhost", PORT), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    webbrowser.open(f"http://localhost:{PORT}")


def set_status(message):
    with _lock:
        _state.update({"mode": "status", "status": message})


def set_track(artist, title, cover=""):
    with _lock:
        _state.update({"mode": "track", "artist": artist, "title": title, "cover": cover})


def set_qr(url):
    import qrcode
    from PIL import Image

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="black")
    img = img.resize((150, 150), Image.NEAREST)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    with _lock:
        _state.update({"mode": "setup", "qr": data_url, "url": url})
