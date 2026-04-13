import sys
import threading
import time

# Detect Pi by checking for the device tree model file
try:
    with open("/sys/firmware/devicetree/base/model") as f:
        IS_PI = "raspberry pi" in f.read().lower()
except (FileNotFoundError, PermissionError):
    IS_PI = False

if IS_PI:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from luma.core.render import canvas
    from PIL import ImageFont


class Display:
    """
    Abstracts output between OLED (Pi) and terminal (Mac/dev).

    On Pi: 128x64 SSD1306 OLED via I2C.
      - Line 1: artist (static, truncated)
      - Line 2: track title (scrolling marquee)

    On Mac: formatted terminal output with ANSI overwrite.
    """

    SCROLL_SPEED = 2        # pixels per tick
    SCROLL_PAUSE = 40       # ticks to pause before restarting
    TICK_INTERVAL = 0.05    # seconds per display tick (20fps)

    def __init__(self):
        self._artist = ""
        self._title = ""
        self._status = "listening..."
        self._has_track = False
        self._scroll_x = 0
        self._scroll_pause_ticks = 0

        if IS_PI:
            serial = i2c(port=1, address=0x3C)
            self._device = ssd1306(serial)
            try:
                self._font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
                )
            except OSError:
                self._font = ImageFont.load_default()

            # Scroll thread — only needed on Pi for OLED animation
            self._running = True
            t = threading.Thread(target=self._scroll_loop, daemon=True)
            t.start()

    def show_track(self, artist, title):
        self._artist = artist
        self._title = title
        self._has_track = True
        self._scroll_x = 0
        self._scroll_pause_ticks = self.SCROLL_PAUSE

        if not IS_PI:
            self._print_terminal()

    def show_status(self, message):
        self._has_track = False
        self._status = message
        if not IS_PI:
            self._print_terminal()

    def show_qr(self, url):
        """
        During setup: show the auth URL as a QR code.
        On Pi: render QR image onto OLED (small but scannable up close).
        On Mac: handled by setup_device._print_qr_terminal(), nothing extra needed.
        """
        if not IS_PI:
            return

        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="white", back_color="black").convert("1")

        # Scale to fit OLED height, leaving top 12px for label
        available_h = 52
        scale = max(1, available_h // qr_img.size[1])
        qr_img = qr_img.resize(
            (qr_img.size[0] * scale, qr_img.size[1] * scale),
            Image.NEAREST,
        )

        frame = Image.new("1", (128, 64), 0)
        frame.paste(qr_img, (0, 12))

        with canvas(self._device) as draw:
            draw.text((0, 0), "Scan to set up", font=self._font, fill="white")
            self._device.display(frame)

    def clear(self):
        if IS_PI:
            self._running = False
            self._device.clear()
        else:
            sys.stdout.write("\n")
            sys.stdout.flush()

    # --- Pi OLED ---

    def _scroll_loop(self):
        """Continuously redraws the OLED — runs in background thread on Pi."""
        while self._running:
            self._draw_oled()
            time.sleep(self.TICK_INTERVAL)

    def _draw_oled(self):
        with canvas(self._device) as draw:
            if not self._has_track:
                draw.text((0, 26), self._status, font=self._font, fill="white")
                return

            # Artist — static, truncated to fit
            draw.text((0, 2), self._artist[:21], font=self._font, fill="white")

            # Title — scrolling marquee on bottom half
            draw.text((128 - self._scroll_x, 34), self._title, font=self._font, fill="white")

        # Advance scroll
        title_px = len(self._title) * 7  # rough char width
        if title_px <= 128:
            return  # title fits, no scroll needed

        if self._scroll_pause_ticks > 0:
            self._scroll_pause_ticks -= 1
        else:
            self._scroll_x += self.SCROLL_SPEED
            if self._scroll_x > title_px + 128:
                self._scroll_x = 0
                self._scroll_pause_ticks = self.SCROLL_PAUSE

    # --- Mac terminal ---

    def _print_terminal(self):
        if self._has_track:
            line = f"  {self._artist} — {self._title}"
        else:
            line = f"  {self._status}"

        sys.stdout.write(f"\r\033[K{line}")
        sys.stdout.flush()
