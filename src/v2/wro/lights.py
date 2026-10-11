#!/usr/bin/env python3
"""Adeept RGB headlights + 3 status LEDs + buzzer.

Cauta modulul robotLight.py al kitului in cfg.ADEEPT_WEB_DIR (sau in Desktop).
Daca nu il gaseste, farurile RGB sunt pur si simplu dezactivate.
"""
import importlib.util
import os
import pwd
import threading
import time

from . import config as cfg


def _find_web_module(name):
    original_user = os.environ.get("SUDO_USER")
    homes = [os.path.expanduser("~")]
    if original_user:
        try:
            homes.insert(0, pwd.getpwnam(original_user).pw_dir)
        except KeyError:
            pass
    homes.append("/home/robonavodari")
    candidates = [cfg.ADEEPT_WEB_DIR, os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")]
    for home in dict.fromkeys(homes):
        candidates.extend([
            os.path.join(home, "Desktop/ADR012-V5.1_PiCar-B_MarsRover_SmartCarKit_for_RPi-20260407/Code/adeept_picar-b2/web"),
            os.path.join(home, "Desktop/ADR012-V5.1_PiCar-B_MarsRover_SmartCarKit_for_RPi-20260407(1)/Code/adeept_picar-b2/web"),
        ])
    for base in candidates:
        path = os.path.join(base, name + ".py")
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


class AdeeptLights:
    COLORS = {
        "orange": (255, 90, 0),
        "blue": (0, 80, 255),
        "white": (150, 150, 150),
        "green": (0, 180, 0),
        "red": (220, 0, 0),
        "wall": (255, 200, 0),          # galben: camera vede peretele (nicio linie/stalp)
        "off": (0, 0, 0),
    }

    def __init__(self):
        self.last_color = None
        self.shown = None
        self._lock = threading.Lock()
        self._rgb = None
        self._status = None
        self._buzzer = None
        self._switch = None
        try:
            self._rgb = _find_web_module("robotLight")
            self._rgb = self._rgb.RobotLight() if self._rgb else None
        except Exception as exc:
            print("RGB lights unavailable: %s" % exc)
            self._rgb = None
        try:
            from gpiozero import LED
            self._status = [LED(p) for p in cfg.STATUS_LED_PINS]
        except Exception as exc:
            print("Status LEDs unavailable: %s" % exc)
            self._status = []
        try:
            from gpiozero import TonalBuzzer
            self._buzzer = TonalBuzzer(cfg.BUZZER_PIN)
        except Exception as exc:
            print("Buzzer unavailable: %s" % exc)

        self.all_status_off()
        self.set_color("white")

    def set_color(self, color):
        if color not in self.COLORS:
            return
        with self._lock:
            k = cfg.LIGHTS_BRIGHTNESS           # faruri slabe: lumina puternica se reflecta in podea si pare stalp/linie
            r, g, b = (c * k for c in self.COLORS[color])
            self.shown = color
            if self._rgb is not None:
                try:
                    self._rgb.both_on(r, g, b)
                except Exception:
                    pass
            if color in ("orange", "blue", "red", "green"):
                self.last_color = color

    def restore_last_color(self):
        if self.last_color:
            self.set_color(self.last_color)

    def all_status_off(self):
        for led in self._status:
            try:
                led.off()
            except Exception:
                pass

    def status_ready(self):
        self.all_status_off()
        if self._status:
            self._status[0].on()

    def status_running(self):
        self.all_status_off()
        if len(self._status) > 1:
            self._status[1].on()

    def status_finish(self):
        self.all_status_off()
        if len(self._status) > 2:
            self._status[2].on()

    def status_alarm(self):
        for led in self._status:
            try:
                led.on()
            except Exception:
                pass

    def beep(self, note="C5", duration=0.10):
        if self._buzzer is None:
            return
        try:
            self._buzzer.play(note)
            time.sleep(duration)
        finally:
            try:
                self._buzzer.stop()
            except Exception:
                pass

    def start_tone(self):
        self.beep("C5", 0.08)
        self.beep("G5", 0.12)

    def finish_tone(self):
        for note in ("C5", "E5", "G5"):
            self.beep(note, 0.08)

    def shutdown(self):
        self.all_status_off()
        try:
            if self._buzzer:
                self._buzzer.stop()
        except Exception:
            pass
        if self._rgb:
            try:
                self._rgb.both_off()
            except Exception:
                pass

