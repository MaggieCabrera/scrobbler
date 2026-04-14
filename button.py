import sys
import time
import threading
from display import IS_PI
from config import BUTTON_PIN, LED_PIN

HOLD_SECONDS = 3


class Button:
    """
    Abstracts physical button (Pi) and keyboard input (Mac/dev).

    Pi:  GPIO button — short press toggles, hold 3s shuts down.
         LED reflects listening state.
    Mac: Enter toggles, 'q' + Enter shuts down.
    """

    def __init__(self, on_toggle, on_shutdown):
        self._on_toggle = on_toggle
        self._on_shutdown = on_shutdown
        self._listening = True

        if IS_PI:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(LED_PIN, GPIO.OUT)
            GPIO.add_event_detect(
                BUTTON_PIN, GPIO.FALLING,
                callback=self._handle_press,
                bouncetime=200,
            )
            self.set_led(True)
        else:
            print("\n  Press Enter to toggle on/off. Type 'q' + Enter to quit.\n")
            t = threading.Thread(target=self._keyboard_loop, daemon=True)
            t.start()

    def set_led(self, state):
        if IS_PI:
            self._gpio.output(LED_PIN, self._gpio.HIGH if state else self._gpio.LOW)

    def cleanup(self):
        if IS_PI:
            self._gpio.cleanup()

    def _toggle(self):
        self._listening = not self._listening
        self.set_led(self._listening)
        self._on_toggle(self._listening)

    def _handle_press(self, channel):
        """Pi GPIO callback — distinguishes short press from hold."""
        press_start = time.time()
        while self._gpio.input(BUTTON_PIN) == self._gpio.LOW:
            if time.time() - press_start >= HOLD_SECONDS:
                self._on_shutdown()
                return
            time.sleep(0.05)
        self._toggle()

    def _keyboard_loop(self):
        """Mac dev input — runs in background thread."""
        while True:
            line = sys.stdin.readline()
            if not line:
                break  # EOF — stdin closed (e.g. running non-interactively)
            if line.strip().lower() == "q":
                self._on_shutdown()
            else:
                self._toggle()
