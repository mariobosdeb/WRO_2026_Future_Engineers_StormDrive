#!/usr/bin/env python3
"""WRO 2026 Future Engineers - punct de intrare.

    sudo python3 main.py open                 # Open Challenge
    sudo python3 main.py obstacle             # Obstacle Challenge
    sudo python3 main.py open --competition   # opreste Wi-Fi/Bluetooth (regula 11.10), fara tastatura
    sudo python3 main.py open --autostart     # fara buton: porneste dupa 5 s numaratoare

Pasii: initializare senzori (motorul NU se misca) -> asteptam UN singur buton de start (GPIO26)
-> runda -> oprire. La final salvam debug/trace_<mod>.csv (stare, y_off, psi, directie) pentru analiza.
"""
import os
import subprocess
import sys
import time

from wro import config as cfg


def radios_off():
    for target in ("wifi", "bluetooth"):
        try:
            subprocess.run(["rfkill", "block", target], check=False, timeout=5)
        except Exception as exc:
            print("rfkill %s: %s" % (target, exc))
    print("Wi-Fi / Bluetooth oprite")


class _Tee:
    """Scrie tot ce apare pe ecran si intr-un fisier (debug/run_<mod>_<timp>.log) - pentru analiza dupa o proba."""

    def __init__(self, path):
        self.fh = open(path, "a", buffering=1)
        self.out = sys.__stdout__

    def write(self, s):
        self.out.write(s)
        try:
            self.fh.write(s)
        except Exception:
            pass

    def flush(self):
        self.out.flush()
        try:
            self.fh.flush()
        except Exception:
            pass

    def isatty(self):
        return self.out.isatty()


def _learned(drv, mode):
    """Ce a invatat masina in timpul cursei (valori de pus in calibration.json daca arata rezonabil)."""
    try:
        b = drv.b
        info = {
            "WHEEL_PER_SERVO": round(cfg.WHEEL_PER_SERVO, 3),
            "v_scale (viteza reala / V_PER_PCT)": round(b.v_scale, 3),
            "V_PER_PCT_sugerat": round(cfg.V_PER_PCT * b.v_scale, 5),
            "corectie_pitch_camera_grade": round(b.sonarcal.applied, 2) if getattr(b, "sonarcal", None) else None,
            "CAM_PITCH_DEG_sugerat": round(cfg.CAM_PITCH_DEG + (b.sonarcal.applied if getattr(b, "sonarcal", None) else 0.0), 1),
            "trim_directie_invatat_grade_servo": round(drv.T, 2),
            "corners": drv.corners,
        }
        print("=== Invatat in cursa ===")
        for k, v in info.items():
            print("  %s: %s" % (k, v))
        import json
        os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
        path = os.path.join(cfg.DEBUG_DIR, "learned_%s_%d.json" % (mode, int(time.time())))
        with open(path, "w") as fh:
            json.dump(info, fh, indent=1)
        print("salvat:", path)
    except Exception as exc:
        print("learned nesalvat: %s" % exc)


def main():
    try:
        os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
        _a = [a for a in sys.argv[1:] if not a.startswith("--")]
        sys.stdout = _Tee(os.path.join(cfg.DEBUG_DIR, "run_%s_%d.log" % (_a[0] if _a else cfg.MODE, int(time.time()))))
    except Exception as exc:
        print("log in fisier indisponibil: %s" % exc)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    competition = "--competition" in sys.argv
    mode = args[0] if args else cfg.MODE
    if mode not in ("open", "obstacle", "parcare"):
        raise SystemExit("Mod invalid: %s (open | obstacle | parcare)" % mode)
    if cfg.load_calibration():
        print("calibration.json incarcat")
    else:
        print("ATENTIE: nu exista calibration.json - ruleaza intai: sudo python3 calibrate.py")
    if "--cw" in sys.argv or "--ccw" in sys.argv:          # sensul dat manual; altfel detectat automat
        cfg.FORCE_DIRECTION = -1 if "--cw" in sys.argv else +1
    if competition:
        cfg.ALLOW_KEYBOARD_START = False
        radios_off()
    print("=== WRO FE 2026 | mod=%s | sens=%s | competitie=%s ===" % (
        mode, {None: "automat", 1: "antiorar (CCW)", -1: "orar (CW)"}[cfg.FORCE_DIRECTION], competition))

    from wro.hardware import RealHW
    from wro.drive import Driver
    hw = RealHW()
    drv = rec = None
    try:
        t_end = time.time() + 6.0
        while not hw.camera_ok and time.time() < t_end:
            time.sleep(0.1)
        if not hw.camera_ok:
            raise SystemExit("Camera nu porneste - nu pornesc (eroare: %s)" % getattr(hw, "_cam_error", None))
        hw.lights.status_ready()
        drv = None
        if mode == "parcare":
            from wro.parking import ParkDriver
            drv = ParkDriver(hw, mode=mode, verbose=True)
            print("Parcare: localizare (filtru de particule) + manevra S inapoi")
        elif mode == "obstacle":
            try:
                from wro.pathdrive import PathDriver
                drv = PathDriver(hw, mode=mode, verbose=True)
                print("Obstacle: planificator lattice + filtru de particule (C++)")
            except Exception as exc:
                print("ATENTIE: planificatorul nu porneste (%s) -> folosesc soferul vechi. "
                      "Instaleaza g++:  sudo apt install -y g++" % exc)
                drv = None
        if drv is None:
            if mode == "open" and "--rec" in sys.argv:     # inregistrare cadre+senzori (replay_open.py)
                from wro.record import RecHAL
                rec = RecHAL(hw, os.path.join(cfg.DEBUG_DIR, "rec_%d" % int(time.time())))
            drv = Driver(rec or hw, mode=mode, verbose=True)
        _wait_start(hw, competition)
        hw.lights.start_tone()
        print("GO")
        reason = drv.run()
        print("Terminat: %s | colturi=%d" % (reason, drv.corners))
        hw.lights.finish_tone()
    except KeyboardInterrupt:
        print("\nOprit de operator")
    finally:
        try:
            hw.stop()
        finally:
            if drv is not None:
                _learned(drv, mode)
                _dump_trace(drv, mode)
            if rec is not None:
                n, nf = rec.close()
                print("senzori inregistrati: %s (%d pasi, %d cadre)" % (rec.dir, n, nf))
            hw.shutdown()


def _wait_start(hw, competition):
    import threading
    if "--go" in sys.argv:                                   # pornit din panou.py: butonul a fost deja apasat
        return
    if "--autostart" in sys.argv:
        for k in range(5, 0, -1):
            print("pornesc in %d s..." % k)
            hw.lights.beep("C5", 0.05)
            time.sleep(0.95)
        return
    from gpiozero import Button
    try:
        button = Button(cfg.START_BUTTON_PIN, pull_up=cfg.START_BUTTON_PULL_UP, bounce_time=0.05)
    except Exception as exc:
        button = None
        print("Buton start indisponibil: %s" % exc)
    kb = (not competition) and sys.stdin.isatty()
    if button is None and not kb:
        raise SystemExit("Nu exista nicio sursa de start")
    ev = threading.Event()
    if button is not None:
        button.when_pressed = ev.set
    if kb:
        def key():
            try:
                input()
            except (EOFError, OSError):
                return
            ev.set()
        threading.Thread(target=key, daemon=True).start()
    print("Apasa butonul de start%s..." % (" (sau Enter)" if kb else ""))
    ev.wait()
    if button is not None:
        button.when_pressed = None


def _dump_trace(drv, mode):
    try:
        os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
        path = os.path.join(cfg.DEBUG_DIR, "trace_%s_%d.csv" % (mode, int(time.time())))
        with open(path, "w") as fh:
            fh.write("t,state,y_off_m,psi_deg,steer_deg\n")
            for r in drv.trace:
                fh.write(",".join(str(x) for x in r) + "\n")
        print("trace salvat: %s" % path)
    except Exception as exc:
        print("trace nesalvat: %s" % exc)


if __name__ == "__main__":
    main()

