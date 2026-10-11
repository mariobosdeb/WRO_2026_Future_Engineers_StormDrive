"""Butonul de start: mouse-ul din portul NEGRU (confiscat cu grab: nu misca cursorul).

  orice click -> START (main.py <mod> --go; sensul CW/CCW e detectat automat)

Click-urile din timpul cursei sunt ignorate. Proba ruleaza ca proces separat, deci mouse-ul nu blocheaza robotul.
Rulare:  python3 -m wro.panou [open|obstacle|parcare]   (implicit open; pornit automat la boot de wro.service)
"""
import glob
import os
import queue
import signal
import subprocess
import sys
import threading
import time

from evdev import InputDevice, ecodes

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # folderul proiectului (unde e main.py)
BUTTON_PORT = "xhci-hcd.1-usb-0:2:1.0"   # portul negru
BUTTONS = (ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE)


def log(msg):
    print("[start %s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


class Mouse(threading.Thread):
    """Fir separat: gaseste mouse-ul dupa port, il confisca, pune fiecare click in coada; la deconectare il cauta din nou."""

    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q
        self.dev = None
        self.running = True

    def _find(self):
        return next((p for p in glob.glob("/dev/input/by-path/*event-mouse") if BUTTON_PORT in p), None)

    def run(self):
        waiting_msg = False
        while self.running:
            path = self._find()
            if path is None:
                if not waiting_msg:
                    log("nu gasesc mouse-ul in portul negru (%s) - astept sa fie conectat" % BUTTON_PORT)
                    waiting_msg = True
                time.sleep(1.0)
                continue
            try:
                self.dev = InputDevice(path)
                self.dev.grab()               # confiscat: nu mai misca cursorul
            except OSError as exc:
                log("mouse-ul nu poate fi deschis (%s) - reincerc" % exc)
                self.dev = None
                time.sleep(1.0)
                continue
            waiting_msg = False
            log("mouse conectat: %s" % self.dev.name)
            try:
                for ev in self.dev.read_loop():
                    if ev.type == ecodes.EV_KEY and ev.code in BUTTONS and ev.value == 0:   # la ridicarea butonului
                        self.q.put(True)
            except OSError:                   # mouse scos
                log("mouse deconectat - astept sa fie conectat din nou")
            finally:
                self.release()
                time.sleep(0.5)

    def release(self):
        dev, self.dev = self.dev, None
        if dev is not None:
            try:
                dev.ungrab()
            except OSError:
                pass
            try:
                dev.close()
            except OSError:
                pass


def safe_stop():
    """Motor oprit, directie pe centru, direct pe PCA9685 (dupa ce proba s-a terminat sau a fost oprita fortat)."""
    try:
        from . import config as cfg
        cfg.load_calibration()
        import busio
        from board import SCL, SDA
        from adafruit_pca9685 import PCA9685
        from adafruit_motor import motor as am, servo as asv
        pca = PCA9685(busio.I2C(SCL, SDA), address=cfg.PCA_ADDRESS)
        pca.frequency = cfg.PCA_FREQUENCY
        mot = am.DCMotor(pca.channels[cfg.MOTOR_IN1], pca.channels[cfg.MOTOR_IN2])
        mot.throttle = 0.0
        st = asv.Servo(pca.channels[cfg.STEER_CH], min_pulse=cfg.SERVO_MIN_PULSE, max_pulse=cfg.SERVO_MAX_PULSE, actuation_range=180)
        st.angle = max(0.0, min(180.0, cfg.SERVO_CENTRE + cfg.STEER_SIGN * cfg.STEER_TRIM_DEG))
    except Exception as exc:
        log("ATENTIE: oprirea motoarelor a esuat: %s" % exc)


class Panou:
    def __init__(self, mode):
        self.mode = mode
        self.q = queue.Queue()
        self.mouse = Mouse(self.q)
        self.proc = None

    def start(self):
        log("START %s" % self.mode)
        self.proc = subprocess.Popen([sys.executable, "-u", os.path.join(HERE, "main.py"), self.mode, "--go"],
                                     cwd=HERE, stdin=subprocess.DEVNULL)

    def stop(self):
        """Opreste proba: SIGINT (main.py opreste motorul si salveaza logurile), dupa 1 s SIGKILL; apoi motor oprit + directie centru."""
        p = self.proc
        if p is not None and p.poll() is None:
            p.send_signal(signal.SIGINT)
            try:
                p.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        safe_stop()
        self.proc = None

    def loop(self):
        self.mouse.start()
        log("astept START (click) - %s" % self.mode)
        while True:
            if self.proc is not None and self.proc.poll() is not None:
                log("cursa terminata (cod %s) - astept START" % self.proc.returncode)
                safe_stop()
                self.proc = None
            try:
                self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            if self.proc is None:
                self.start()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "open"
    if mode not in ("open", "obstacle", "parcare"):
        raise SystemExit("Mod invalid: %s (open | obstacle | parcare)" % mode)
    panou = Panou(mode)

    def term(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, term)          # systemctl stop: aceeasi iesire sigura ca la Ctrl+C
    try:
        panou.loop()
    except KeyboardInterrupt:
        log("iesire")
    finally:
        panou.mouse.running = False
        panou.stop()
        panou.mouse.release()


if __name__ == "__main__":
    main()

