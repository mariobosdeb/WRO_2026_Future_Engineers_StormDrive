#!/usr/bin/env python3
"""Calibrare pe masina reala:  sudo python3 calibrate.py   (rezultatele merg in calibration.json)"""
import math
import os
import time

import numpy as np

from wro import config as cfg
from wro.geometry import CameraModel
from wro.hardware import RealHW
from wro.perception import Perceiver

MENU = """
WRO FE 2026 - calibrare (ordinea recomandata: 1,2,3,4,5,6)
  1  directie: verifica sensul (STEER_SIGN) si centrul (STEER_TRIM_DEG)
  2  motor: sensul (MOTOR_DIRECTION) si V_PER_PCT (m/s per 1% putere)
  3  (NU MAI E NECESAR - unghiul rotii se invata singur in cursa; testul de timp era nesigur)
  4  cap pan + ultrasonic (PAN_SIGN, citiri stanga/fata/dreapta)
  5  camera: foto + culori (HSV) + calibrare inaltime/inclinare
  6  cat de bine vede peretii: distante estimate (pune masina in culoar)
  7  baterie / IR / faruri
  q  iesire
"""


def ask_float(msg, default=None):
    s = input(msg).strip()
    if not s and default is not None:
        return default
    return float(s.replace(",", "."))


def steer_test(hw):
    for a in (0, 20, 0, -20, 0):
        print("steer %+d  (pozitiv TREBUIE sa fie STANGA)" % a)
        hw.set_steer(a)
        time.sleep(1.0)
    if input("Rotile au virat invers? (d/n): ").lower().startswith("d"):
        cfg.save_calibration({"STEER_SIGN": -cfg.STEER_SIGN})
        print("STEER_SIGN =", cfg.STEER_SIGN)
    hw.set_steer(0)
    trim = ask_float("Cu directia pe 0, rotile merg drept? Corectie in grade (+ stanga), Enter=0: ", 0.0)
    if trim:
        cfg.save_calibration({"STEER_TRIM_DEG": cfg.STEER_TRIM_DEG + trim})
        hw.set_steer(0)
        print("STEER_TRIM_DEG =", cfg.STEER_TRIM_DEG)


def motor_test(hw):
    print("MASINA PE SOL, cu spatiu 2 m in fata. Apasa Ctrl+C ca sa opresti.")
    input("Enter ca sa pornesc 1.5 s la 35%... ")
    hw.set_steer(0)
    hw.set_speed(35)
    t0 = time.time()
    time.sleep(1.5)
    hw.stop()
    dt = time.time() - t0
    d = ask_float("A mers INAINTE? (d/n) -> 1/0: ", 1.0)
    if d < 0.5:
        cfg.save_calibration({"MOTOR_DIRECTION": -cfg.MOTOR_DIRECTION})
        print("MOTOR_DIRECTION =", cfg.MOTOR_DIRECTION, "(repeta testul)")
        return
    dist = ask_float("Cati cm a parcurs (include demarajul)? ") / 100.0
    v = dist / dt / 35.0
    print("V_PER_PCT = %.4f m/s per %%  (acum %.4f)" % (v, cfg.V_PER_PCT))
    if input("Salvez? (d/n): ").lower().startswith("d"):
        cfg.save_calibration({"V_PER_PCT": round(v, 5)})


def radius_test(hw):
    """Masoara cat de tare viraza masina la mai multe unghiuri de servo.
    Pentru fiecare unghi: masina merge in cerc, tu apesi Enter cand a facut o JUMATATE de cerc
    (cand priveste exact invers fata de start). Din timp si viteza (V_PER_PCT) rezulta raza."""
    import math
    pw = 35
    v = cfg.V_PER_PCT * pw
    L = cfg.WHEELBASE
    print("MASINA PE SOL, spatiu liber 2.5 m in jur, langa o linie/margine de referinta.")
    print("Pentru fiecare unghi: pune masina cu botul pe o linie. Ea porneste in cerc (stanga).")
    print("Apasa ENTER cand priveste exact INVERS (jumatate de cerc). Daca bazaie servo-ul")
    print("sau roata se opreste in limitator, apasa Ctrl+C si ia unghiul anterior.")
    old_max = cfg.STEER_MAX_DEG
    cfg.STEER_MAX_DEG = 60.0
    res = []
    try:
        for ang in (28, 36, 44, 52):
            input("\nUnghi servo %d: pune masina la start, Enter ca sa porneasca... " % ang)
            hw.set_steer(ang)
            time.sleep(0.5)
            hw.set_speed(pw)
            t0 = time.time()
            input("   Enter cand a facut jumatate de cerc... ")
            t = time.time() - t0
            hw.stop()
            hw.set_steer(0)
            r = v * t / math.pi
            wheel = math.degrees(math.atan(L / r))
            print("   timp %.1f s -> raza ~ %.2f m, roata ~ %.1f grade (servo/roata = %.2f)" %
                  (t, r, wheel, wheel / ang))
            res.append((ang, r, wheel))
    except KeyboardInterrupt:
        print("\nOprit.")
    finally:
        hw.stop()
        hw.set_steer(0)
        cfg.STEER_MAX_DEG = old_max
    if not res:
        return
    ang, r, wheel = min(res, key=lambda x: x[1])
    print("\nCea mai stransa raza: %.2f m la servo %d" % (r, ang))
    if r > 0.5:
        print("ATENTIE: raza > 0.5 m - culoarul de 1 m nu permite colt dintr-o miscare. Verifica directia (pasul 1).")
    if input("Salvez (STEER_MAX_DEG/TURN_STEER_DEG=%d, WHEEL_PER_SERVO=%.3f)? (d/n): " % (ang, wheel / ang)).lower().startswith("d"):
        cfg.save_calibration({"STEER_MAX_DEG": float(ang), "TURN_STEER_DEG": float(ang),
                              "WHEEL_PER_SERVO": round(wheel / ang, 3), "TURN_RADIUS": None})


def auto_pan_trim(hw):
    """Matura capul si cauta unghiul cu distanta minima pana la perete = directia perpendiculara pe perete. Daca masina e
    perpendiculara pe perete, acel unghi (in cadrul masinii) e eroarea de centrare a capului."""
    import statistics
    old = cfg.PAN_TRIM_DEG
    cfg.PAN_TRIM_DEG = 0.0
    angs, ds = [], []
    for a in range(-30, 31, 3):
        hw.set_head(a)
        time.sleep(0.5)
        vals = []
        for _ in range(5):
            s_ = hw.sonar()
            if s_ is not None:
                vals.append(s_)
            time.sleep(0.07)
        if vals:
            angs.append(float(a)); ds.append(statistics.median(vals))
    hw.set_head(0)
    cfg.PAN_TRIM_DEG = old
    if len(angs) < 8:
        print("prea putine citiri ultrasonice")
        return None
    k = min(range(len(ds)), key=lambda i: ds[i])
    lo, hi = max(0, k - 3), min(len(ds), k + 4)
    import numpy as np
    c = np.polyfit(angs[lo:hi], ds[lo:hi], 2)
    if c[0] <= 0:
        print("minim neclar (perete neperpendicular sau prea departe); citiri: %s" % ["%d:%.0f" % (a, d * 100) for a, d in zip(angs, ds)])
        return None
    best = -c[1] / (2 * c[0])
    print("distanta minima la unghiul pan %.1f grade (%.0f cm)" % (best, ds[k] * 100))
    return round(best, 1)


def pan_test(hw):
    print("Capul trebuie sa mearga STANGA la pan pozitiv.")
    for a in (0, 45, 0, -45, 0):
        print("pan %+d" % a)
        hw.set_head(a)
        time.sleep(1.0)
    if input("A mers invers? (d/n): ").lower().startswith("d"):
        cfg.save_calibration({"PAN_SIGN": -cfg.PAN_SIGN})
    print("Centrarea capului: acum e comandat DREPT (pan 0). Daca nu priveste exact inainte, corecteaza.")
    hw.set_head(0)
    trim = cfg.PAN_TRIM_DEG
    if input("Centrare AUTOMATA cu ultrasonicul? Pune masina cu botul perpendicular pe un perete drept, la 30-60 cm (d/n): ").lower().startswith("d"):
        t = auto_pan_trim(hw)
        if t is not None:
            trim = t
            cfg.PAN_TRIM_DEG = trim
            hw.set_head(0)
            time.sleep(0.6)
            print("trim automat: %.1f grade (verifica cu ochiul; poti corecta mai jos)" % trim)
    while True:
        ans = input("corectie in grade (+ = mai spre stanga, - = mai spre dreapta; ex. -5 sau 3), Enter = gata [acum %.1f]: " % trim).strip()
        if not ans:
            break
        try:
            trim += float(ans)
        except ValueError:
            print("numar invalid")
            continue
        cfg.PAN_TRIM_DEG = trim
        hw.set_head(0)
        hw._write_pan(0.0)
        time.sleep(0.6)
    cfg.save_calibration({"PAN_TRIM_DEG": round(trim, 2)})
    print("PAN_TRIM_DEG=%.1f salvat" % trim)
    print("Ultrasonic (de la axa capului; de la BOT = %.1f cm mai putin): Ctrl+C ca sa opresti" % ((cfg.SONAR_FWD + 0.002) * 100))
    try:
        while True:
            row = []
            for a in (70, 0, -70):
                hw.set_head(a)
                time.sleep(0.45)
                s = hw.sonar()
                row.append("%+d: %s" % (a, "--" if s is None else "%.0f cm" % (s * 100)))
            print("   ".join(row))
    except KeyboardInterrupt:
        hw.set_head(0)


def camera_test(hw):
    import cv2
    if not hw.camera_ok:
        print("camera indisponibila")
        return
    os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
    hw.set_head(0)
    time.sleep(0.6)
    if hasattr(hw, "set_tilt"):
        print("Inclinarea capului (tilt) acum: %.1f. Camera trebuie sa vada baza peretilor aproape (liniile de pe jos) dar si peretele din fata." % cfg.TILT_SERVO_DEG)
        while True:
            ans = input("schimba tilt cu X grade (ex. 5 sau -5; nu stiu sensul: incearca si uita-te in poza), Enter = ramane: ").strip()
            if not ans:
                break
            try:
                hw.set_tilt(cfg.TILT_SERVO_DEG + float(ans))
            except ValueError:
                print("numar invalid")
                continue
            time.sleep(0.8)
            im, _, _ = hw.frame()
            cv2.imwrite(os.path.join(cfg.DEBUG_DIR, "cam.jpg"), im)
            print("tilt=%.1f ; poza noua in debug/cam.jpg" % cfg.TILT_SERVO_DEG)
        cfg.save_calibration({"TILT_SERVO_DEG": round(cfg.TILT_SERVO_DEG, 1)})
        print("TILT_SERVO_DEG=%.1f salvat. IMPORTANT: dupa orice schimbare de tilt refa inaltimea/inclinarea (urmeaza)." % cfg.TILT_SERVO_DEG)
    img, _, _ = hw.frame()
    path = os.path.join(cfg.DEBUG_DIR, "cam.jpg")
    cv2.imwrite(path, img)
    print("Salvat", path, "- verifica: imaginea e dreapta (nu rasturnata)? Peretii negri apar intunecati?")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    print("Pixeli pe culoare (pune stalp rosu/verde, linie portocalie/albastra in cadru):")
    for name, rng in (("portocaliu", cfg.ORANGE), ("albastru", cfg.BLUE), ("verde", cfg.GREEN), ("magenta", cfg.MAGENTA)):
        m = cv2.inRange(hsv, np.array(rng[0], np.uint8), np.array(rng[1], np.uint8))
        print("  %-10s %6d" % (name, int((m > 0).sum())))
    m = sum(cv2.inRange(hsv, np.array(a, np.uint8), np.array(b, np.uint8)) for a, b in cfg.RED)
    print("  %-10s %6d" % ("rosu", int((m > 0).sum())))
    print("Daca o culoare nu se detecteaza, ajusteaza intervalul HSV in wro/config.py.")
    if input("Calibrezi inaltimea/inclinarea camerei acum? (d/n): ").lower().startswith("d"):
        camera_geometry(hw)


def _center_v(hw, per):
    v, has = per.last_v, per.last_has
    n = len(v)
    sl = slice(n // 2 - 6, n // 2 + 6)
    ok = has[sl]
    return float(np.median(v[sl][ok])) if ok.sum() >= 6 else None


def camera_geometry(hw):
    """Inaltimea se MASOARA cu ruleta (2 necunoscute din 2 distante dadeau inaltimi absurde, ex. 7.5 cm in loc de 18.5).
    Din 3 distante se potrivesc inclinarea si unghiul de vedere; eroarea reziduala arata daca masuratorile sunt consistente."""
    print("Pune masina cu botul spre un perete NEGRU, perpendicular, capul drept.")
    hgt = ask_float("Inaltimea LENTILEI camerei de la podea, in cm (ruleta): ") / 100.0
    pairs = []
    per = Perceiver()
    for k, ex in enumerate((25, 50, 80), 1):
        s = input("Distanta %d: de la BOTUL masinii la perete, in cm (ex. %d; Enter = gata): " % (k, ex)).strip()
        if not s:
            break
        d = float(s.replace(",", ".")) / 100.0
        time.sleep(0.5)
        vs = []
        for _ in range(12):
            fr = hw.frame()
            if fr and fr[2]:
                per.process(fr[0], 0.0, hw.now())
                v = _center_v(hw, per)
                if v is not None:
                    vs.append(v)
            time.sleep(0.08)
        if len(vs) < 4:
            print("  Nu vad baza peretelui la distanta asta (prea departe/aproape sau lumina) - o sar.")
            continue
        v = float(np.median(vs))
        pairs.append((d + cfg.REAR_TO_FRONT, v))
        print("  rand pixel perete: %.1f (imprastiere %.1f px)" % (v, float(np.std(vs))))
    if len(pairs) < 2:
        print("Prea putine distante valide.")
        return

    def fit(hfovs):
        best = None
        for hfov in hfovs:
            for pitch in np.arange(0, 50, 0.25):
                cm = CameraModel(pitch_deg=pitch, height=hgt, hfov_deg=hfov)
                err = 0.0
                for X_true, v in pairs:
                    Xh, _, valid = cm.pixel_to_ground(cm.cx, v)
                    if not bool(valid):
                        err = 9e9
                        break
                    err += ((float(Xh) + cfg.REAR_TO_HEAD) - X_true) ** 2
                if best is None or err < best[0]:
                    best = (err, pitch, hfov)
        return best[1], best[2], 100 * math.sqrt(best[0] / len(pairs))

    p1, f1, e1 = fit([cfg.CAM_HFOV_DEG])
    print("Cu unghi de vedere fix %.1f: CAM_PITCH_DEG=%.2f  eroare %.1f cm" % (f1, p1, e1))
    save = {"CAM_PITCH_DEG": float(p1), "CAM_HEIGHT": round(hgt, 3)}
    if len(pairs) >= 3:
        p2, f2, e2 = fit(np.arange(40.0, 80.0, 0.5))
        print("Cu unghi de vedere potrivit:  CAM_PITCH_DEG=%.2f  CAM_HFOV_DEG=%.1f  eroare %.1f cm" % (p2, f2, e2))
        if e2 < e1 - 1.0:
            save = {"CAM_PITCH_DEG": float(p2), "CAM_HEIGHT": round(hgt, 3), "CAM_HFOV_DEG": float(f2)}
    else:
        print("(cu doar 2 distante eroarea nu spune nimic; ideal 3)")
    if min(e1, 99) > 3.0 and "CAM_HFOV_DEG" not in save:
        print("ATENTIE: eroare > 3 cm - verifica inaltimea masurata si distantele (de la BOT la baza peretelui).")
    print("Propun:", save)
    if input("Salvez? (d/n): ").lower().startswith("d"):
        cfg.save_calibration(save)
    print("Nota: in timpul cursei masina isi corecteaza singura inclinarea camerei (cu ultrasonicul), deci o eroare de 2-3 grade nu mai e fatala.")


def walls_test(hw):
    from wro.robot import Brain
    b = Brain(hw)
    print("Masina in culoar, NEMISCATA. Ctrl+C ca sa opresti. Compara cu ruleta.")
    t_end = time.time() + 600
    try:
        while time.time() < t_end:
            w = b.tick()
            if w.lane_age < 1.0:
                print("y_off=%+.2f m  psi=%+.1f deg  W=%s  dl=%s dr=%s  front=%s  colt=%s" % (
                    w.y_off, math.degrees(w.psi), None if not w.W else round(w.W, 2),
                    None if w.dl is None else round(w.dl, 2), None if w.dr is None else round(w.dr, 2),
                    None if w.front is None else round(w.front, 2),
                    {k: (round(v.X, 2) if v is not None else None) for k, v in w.corner.items()}))
            else:
                print("nu vad peretii")
            b.wait_period()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass


def misc_test(hw):
    print("baterie (V, %, critic, deconectat):", hw.battery())
    print("IR:", hw.ir())
    hw.lights.status_ready()
    hw.lights.beep()
    time.sleep(0.5)


def main():
    cfg.load_calibration()
    hw = RealHW()
    try:
        while True:
            print(MENU)
            c = input("alege: ").strip().lower()
            try:
                if c == "1":
                    steer_test(hw)
                elif c == "2":
                    motor_test(hw)
                elif c == "3":
                    radius_test(hw)
                elif c == "4":
                    pan_test(hw)
                elif c == "5":
                    camera_test(hw)
                elif c == "6":
                    walls_test(hw)
                elif c == "7":
                    misc_test(hw)
                elif c == "q":
                    break
            except KeyboardInterrupt:
                hw.stop()
                print()
    finally:
        hw.shutdown()


if __name__ == "__main__":
    main()

