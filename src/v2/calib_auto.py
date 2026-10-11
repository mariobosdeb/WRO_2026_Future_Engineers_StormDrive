#!/usr/bin/env python3
"""Calibrare automata, pas cu pas, fara intrebari (ultrasonicul pe post de ruleta). Nimic nu se salveaza fara --save.

    python3 calib_auto.py sonar                 # capul drept: distanta ultrasonic (compara cu ruleta de la BOT la perete)
    python3 calib_auto.py pan [--save]          # botul perpendicular pe perete la 30-60 cm: centrarea capului (PAN_TRIM_DEG)
    python3 calib_auto.py viteza [--save]       # botul spre un perete la ~2 m, culoar liber: V_PER_PCT (m/s per 1%)
    python3 calib_auto.py drept stanga|dreapta [--save]   # paralel cu un perete (pe partea data) la 20-35 cm, 1.5 m liberi:
                                                          # cat trage mersul drept => STEER_TRIM_DEG
    python3 calib_auto.py camera H_cm [--save]  # botul perpendicular pe perete NEGRU la ~15 cm, 1.3 m liberi in spate:
                                                # da cu spatele in pasi, ultrasonic vs randul pixelului => CAM_PITCH_DEG, CAM_HFOV_DEG
    python3 calib_auto.py ir [secunde]          # senzorul de linie: afiseaza cele 3 canale cand se schimba
    python3 calib_auto.py culori                # poza + pixeli portocaliu/albastru/rosu/verde + HSV-ul petelor gasite
    python3 calib_auto.py verif                 # in culoar, nemiscata: pereti din camera vs ultrasonic stanga/fata/dreapta
"""
import math
import os
import statistics
import sys
import time

import numpy as np

from wro import config as cfg

SONAR_FACE = 0.0          # hw.sonar() da deja distanta de la axa pan (cfg.SONAR_FWD)


def sonar_med(hw, n=9, dt=0.06):
    vals = []
    for _ in range(n):
        r = hw.sonar()
        if r is not None:
            vals.append(r)
        time.sleep(dt)
    return statistics.median(vals) if len(vals) >= max(3, n // 3) else None


def head(hw, pan, wait=0.6):
    hw.set_head(pan)
    time.sleep(wait)


def save(d, ok):
    print("PROPUN:", d)
    if ok:
        cfg.save_calibration(d)
        print("SALVAT in calibration.json")
    else:
        print("(nesalvat; ruleaza din nou cu --save ca sa salvezi)")


# ----------------------------------------------------------------------------------------------------------------
def p_sonar(hw, a):
    head(hw, 0)
    for _ in range(3):
        r = sonar_med(hw, 15)
        if r is None:
            print("ultrasonic: fara ecou")
        else:
            print("ultrasonic %.1f cm de la axa capului => de la BOT la perete %.1f cm" % (
                r * 100, (r - (cfg.REAR_TO_FRONT - cfg.REAR_TO_HEAD)) * 100))
        time.sleep(0.3)


def _wall_angle(hw, per, pan, n=8):
    """Unghiul peretelui din fata vazut de camera (grade; 0 = perpendicular pe directia comandata a capului)."""
    from wro.perception import ST_WALL
    head(hw, pan, 0.7)
    out = []
    t_end = time.time() + 2.0
    while len(out) < n and time.time() < t_end:
        fr = hw.frame()
        if fr and fr[2]:
            p = per.process(fr[0], 0.0, hw.now())
            m = (p.state == ST_WALL) & (np.abs(p.Y) < 0.35)
            if m.sum() >= 12:
                b, a0 = np.polyfit(p.Y[m], p.X[m], 1)
                out.append(math.degrees(math.atan(b)))
        time.sleep(0.03)
    return statistics.median(out) if len(out) >= 3 else None


def p_pan(hw, a):
    from wro.perception import Perceiver
    per = Perceiver()
    pans, angs = [], []
    for p in (-10.0, -5.0, 0.0, 5.0, 10.0):
        al = _wall_angle(hw, per, p)
        print("  pan comandat %+5.1f: peretele apare la %s grade" % (p, "--" if al is None else "%+.1f" % al))
        if al is not None:
            pans.append(p)
            angs.append(al)
    head(hw, 0)
    if len(pans) < 3:
        print("camera nu vede peretele din fata")
        return
    k, c = np.polyfit(pans, angs, 1)
    if abs(k) < 0.5:
        print("unghiul nu urmeaza capul (panta %.2f) - masuratoare nesigura" % k)
        return
    p0 = -c / k                                   # pan comandat la care peretele apare perpendicular
    print("peretele e perpendicular la pan comandat %+.1f grade (panta %.2f); acum PAN_TRIM_DEG=%.1f" % (p0, k, cfg.PAN_TRIM_DEG))
    save({"PAN_TRIM_DEG": round(float(cfg.PAN_TRIM_DEG + p0), 1)}, a.save)


def _drive_log(hw, pct, steer, dur, pan=0.0, stop_r=None):
    head(hw, pan)
    hw.set_steer(steer)
    time.sleep(0.3)
    out = []
    t0 = time.time()
    hw.set_speed(pct)
    try:
        while time.time() - t0 < dur:
            r = hw.sonar()
            out.append((time.time() - t0, r))
            if stop_r is not None and r is not None and r < stop_r:
                break
            time.sleep(0.03)
    finally:
        hw.stop()
        hw.set_steer(0)
    time.sleep(0.5)
    return out


def p_viteza(hw, a):
    res = []
    for pct in (30, 36):
        r0 = sonar_med(hw)
        if r0 is None or r0 < 1.2:
            print("pune masina cu botul spre perete la 1.5-2 m (acum %s)" % (None if r0 is None else "%.0f cm" % (r0 * 100)))
            return
        log = _drive_log(hw, pct, 0.0, 4.0, 0.0, stop_r=0.45)
        pts = [(t, r) for t, r in log if r is not None and t > 0.6 and 0.45 < r < r0 - 0.05]
        if len(pts) < 8:
            print("%d%%: prea putine citiri" % pct)
            continue
        T, R = np.array(pts).T
        k = np.polyfit(T, R, 1)
        v = -k[0]
        resid = float(np.std(R - np.polyval(k, T)))
        print("%d%%: viteza %.3f m/s => V_PER_PCT %.5f (imprastiere %.1f cm, %d citiri)" % (pct, v, v / pct, resid * 100, len(pts)))
        res.append(v / pct)
        if pct == 30:
            print("   intoarce masina la 1.5-2 m de perete pentru 36%... (ai 8 s)")
            time.sleep(8)
    if res:
        save({"V_PER_PCT": round(float(np.mean(res)), 5)}, a.save)


def p_drept(hw, a):
    side = +1 if a.args and a.args[0].startswith("st") else -1
    pan = side * 88.0
    r0 = None
    head(hw, pan, 0.8)
    r0 = sonar_med(hw)
    if r0 is None or r0 > 0.6:
        print("nu vad peretele pe %s (pune masina paralel, la 20-35 cm)" % ("stanga" if side > 0 else "dreapta"))
        head(hw, 0)
        return
    pct = 32
    v = cfg.V_PER_PCT * pct
    log = _drive_log(hw, pct, 0.0, 1.5 / v, pan)
    head(hw, 0)
    pts = [(t, r) for t, r in log if r is not None and t > 0.5 and r < 0.9]
    if len(pts) < 10:
        print("prea putine citiri")
        return
    T, R = np.array(pts).T
    S = (T - 0.25) * v                                   # drum (m), cu demaraj aproximat
    c2, c1, c0 = np.polyfit(S, R, 2)
    # d(s) = d0 + b s + c2 s^2; curbura spre stanga (+) apropie peretele din stanga: c2 = -side * kappa / 2
    kappa = -2.0 * c2 * side
    wheel = math.degrees(math.atan(kappa * cfg.WHEELBASE))
    servo = wheel / max(0.15, cfg.WHEEL_PER_SERVO)
    print("perete %s: %.1f -> %.1f cm pe %.2f m (unghi initial %.1f grade); curbura %.3f 1/m" % (
        "stanga" if side > 0 else "dreapta", R[0] * 100, R[-1] * 100, S[-1], math.degrees(math.atan(c1)), kappa))
    print("masina vireaza singura %s cu ~%.1f grade servo (acum STEER_TRIM_DEG=%.1f)" % (
        "STANGA" if servo > 0 else "DREAPTA", abs(servo), cfg.STEER_TRIM_DEG))
    if abs(servo) < 0.7:
        print("merge drept (sub 0.7 grade): nu e nevoie de corectie")
        return
    save({"STEER_TRIM_DEG": round(cfg.STEER_TRIM_DEG - servo, 1)}, a.save)


def p_camera(hw, a):
    from wro.geometry import CameraModel
    from wro.perception import Perceiver
    if not a.args:
        print("da inaltimea lentilei in cm: python3 calib_auto.py camera 15.5")
        return
    hgt = float(a.args[0].replace(",", ".")) / 100.0
    per = Perceiver()
    head(hw, 0)
    r = sonar_med(hw)
    if r is not None and 0.2 < r < 1.6:            # ne apropiem incet pana la ~17 cm, ca sa avem si puncte apropiate
        _drive_log(hw, cfg.SPEED_MIN + 4, 0.0, 3.0, 0.0, stop_r=0.17)
    from wro.perception import ST_WALL
    pairs = []
    for step in range(16):
        r = sonar_med(hw, 9)
        vs, angs = [], []
        t_end = time.time() + 0.9
        while time.time() < t_end:
            fr = hw.frame()
            if fr and fr[2]:
                p = per.process(fr[0], 0.0, hw.now())
                v, has = per.last_v, per.last_has
                n = len(v)
                sl = slice(n // 2 - 6, n // 2 + 6)
                if has[sl].sum() >= 6:
                    vs.append(float(np.median(v[sl][has[sl]])))
                m = (p.state == ST_WALL) & (np.abs(p.Y) < 0.35)
                if m.sum() >= 12:
                    angs.append(math.degrees(math.atan(np.polyfit(p.Y[m], p.X[m], 1)[0])))
            time.sleep(0.03)
        th = statistics.median(angs) if len(angs) >= 3 else 0.0
        if r is not None and len(vs) >= 4 and float(np.std(vs)) < 2.0:
            # ultrasonicul (fascicul larg) da distanta perpendiculara; camera masoara pe axa capului => /cos(unghi)
            X = cfg.REAR_TO_HEAD + (SONAR_FACE + r) / math.cos(math.radians(th))
            pairs.append((X, float(np.median(vs))))
            print("  ultrasonic %.1f cm  unghi fata de perete %+.1f grade  rand pixel %.1f" % (r * 100, th, pairs[-1][1]))
        else:
            print("  ultrasonic %s, cadre cu perete %d - sar" % (None if r is None else "%.0f cm" % (r * 100), len(vs)))
        if r is not None and r > 1.25:
            break
        _drive_log(hw, -cfg.SPEED_REVERSE, 0.0, 0.35)
    if len(pairs) < 4:
        print("prea putine puncte")
        return

    def fit(hfovs):
        best = None
        for hfov in hfovs:
            for pitch in np.arange(0, 45, 0.1):
                cm = CameraModel(pitch_deg=pitch, height=hgt, hfov_deg=hfov)
                e = []
                for X, v in pairs:
                    Xh, _, ok = cm.pixel_to_ground(cm.cx, v)
                    e.append(9.0 if not bool(ok) else float(Xh) + cfg.REAR_TO_HEAD - X)
                err = float(np.sqrt(np.mean(np.square(e))))
                if best is None or err < best[0]:
                    best = (err, pitch, hfov, e)
        return best

    e1, p1, f1, r1 = fit([cfg.CAM_HFOV_DEG])
    e2, p2, f2, r2 = fit(np.arange(50.0, 90.0, 1.0))
    print("HFOV fix %.0f: pitch %.2f  eroare rms %.1f cm | erori: %s" % (f1, p1, e1 * 100, " ".join("%+.1f" % (x * 100) for x in r1)))
    print("HFOV liber : pitch %.2f HFOV %.0f  eroare rms %.1f cm" % (p2, f2, e2 * 100))
    d = {"CAM_HEIGHT": round(hgt, 3), "CAM_PITCH_DEG": round(float(p1), 2)}
    if e2 < e1 - 0.01:
        d = {"CAM_HEIGHT": round(hgt, 3), "CAM_PITCH_DEG": round(float(p2), 2), "CAM_HFOV_DEG": float(f2)}
    print("acum: H=%.3f pitch=%.2f HFOV=%.0f" % (cfg.CAM_HEIGHT, cfg.CAM_PITCH_DEG, cfg.CAM_HFOV_DEG))
    save(d, a.save)


def p_ir(hw, a):
    dur = float(a.args[0]) if a.args else 30.0
    print("senzor linie (GPIO %s), %.0f s; 1/0 = ce vede fiecare ochi (stanga, mijloc, dreapta)" % (cfg.IR_PINS, dur))
    last = None
    t0 = time.time()
    while time.time() - t0 < dur:
        v = hw.ir()
        if v != last:
            print("  %5.1f s  %s" % (time.time() - t0, v), flush=True)
            last = v
        time.sleep(0.01)


def p_culori(hw, a):
    import cv2
    head(hw, 0)
    time.sleep(0.4)
    img, _, _ = hw.frame()
    os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    ann = (img // 3).copy()
    rng = {"portocaliu": [cfg.ORANGE], "albastru": [cfg.BLUE], "rosu": list(cfg.RED), "verde": [cfg.GREEN]}
    col = {"portocaliu": (0, 140, 255), "albastru": (255, 80, 0), "rosu": (0, 0, 255), "verde": (0, 200, 0)}
    for name, rr in rng.items():
        m = sum(cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8)) for lo, hi in rr)
        ann[m > 0] = col[name]
        n = int((m > 0).sum())
        if n:
            q = lambda i, p: int(np.percentile(hsv[m > 0][:, i], p))
            print("%-10s %6d px  H %d..%d  S %d..%d  V %d..%d (percentile 5..95)" % (
                name, n, q(0, 5), q(0, 95), q(1, 5), q(1, 95), q(2, 5), q(2, 95)))
        else:
            print("%-10s      0 px" % name)
    path = os.path.join(cfg.DEBUG_DIR, "culori.jpg")
    cv2.imwrite(path, np.hstack([img, ann]))
    print("poza: %s (stanga ce vede camera, dreapta ce detecteaza)" % path)


def p_verif(hw, a):
    from wro.robot import Brain
    b = Brain(hw)
    b.peek_ok = False
    rows = []
    t_end = time.time() + 3.0
    while time.time() < t_end:
        w = b.tick()
        if w.lane_age < 0.5 and w.dl is not None:
            rows.append((w.dl, w.dr, w.front, math.degrees(w.psi or 0.0)))
        b.wait_period()
    s = {}
    for name, pan in (("stanga", 88.0), ("dreapta", -88.0), ("fata", 0.0)):
        head(hw, pan, 0.8)
        s[name] = sonar_med(hw)
    head(hw, 0)
    if not rows:
        print("CAMERA NU VEDE PERETII (nici un cadru bun in 3 s)")
    else:
        dl, dr, fr, ps = (statistics.median([r[i] for r in rows if r[i] is not None]) if any(r[i] is not None for r in rows) else None for i in range(4))
        f = lambda v: "--" if v is None else "%.1f" % (v * 100)
        print("camera:     stanga %s cm  dreapta %s cm  fata %s cm (de la axa spate)  unghi %+.1f grade" % (f(dl), f(dr), f(fr), ps or 0.0))
    g = lambda k, off: "--" if s[k] is None else "%.1f" % ((s[k] + off) * 100)
    print("ultrasonic: stanga %s cm  dreapta %s cm  fata %s cm (aceleasi repere; la stanga/dreapta din centru masinii)" % (
        g("stanga", SONAR_FACE), g("dreapta", SONAR_FACE), g("fata", cfg.REAR_TO_HEAD + SONAR_FACE)))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pas")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    cfg.load_calibration()
    from wro.hardware import RealHW
    hw = RealHW(use_camera=a.pas in ("pan", "camera", "culori", "verif"))
    try:
        if a.pas in ("pan", "camera", "culori", "verif"):
            t_end = time.time() + 6.0
            while not hw.camera_ok and time.time() < t_end:
                time.sleep(0.1)
        {"sonar": p_sonar, "pan": p_pan, "viteza": p_viteza, "drept": p_drept, "camera": p_camera,
         "ir": p_ir, "culori": p_culori, "verif": p_verif}[a.pas](hw, a)
    except KeyboardInterrupt:
        print("oprit")
    finally:
        hw.stop()
        hw.shutdown()


if __name__ == "__main__":
    main()

