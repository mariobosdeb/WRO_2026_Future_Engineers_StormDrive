"""Reluare offline a unei curse Obstacle inregistrate (debug/rec_<ts>/): nu misca motoarele.

    python3 replay.py debug/rec_1791460305
    python3 replay.py debug/rec_1791460305 --seeds 5                 # cat de bine e constransa pozitia (varianta intre seminte)
    python3 replay.py debug/rec_1791460305 --set CAM_PITCH_DEG=14.5  # "ce-ar fi daca": alt parametru, aceleasi date

Fara adevar de teren (pe masina nu stim pozitia reala), localizarea se judeca dupa INOVATII: cat de departe e fiecare
masuratoare de ce prezice pozitia estimata INAINTE de a o folosi. Un filtru sanatos are inovatii mici si fara tendinta:
  - ultrasonic: distanta masurata - raza pana la perete din pozitia estimata (cm)
  - camera: distanta punctelor de perete (proiectate cu pozitia estimata) pana la cel mai apropiat perete al hartii (cm)
Statisticile se fac dupa decizia directiei (inainte, pozitia de start e inca necunoscuta in sectiune).
Inovatii mari si sistematice = calibrare (pitch/inaltime camera, viteza, raza de viraj) sau model gresit, nu ghinion.
"""
import argparse
import math
import os
import sys

import numpy as np

from wro import config as cfg


def apply_cfg(values):
    for k, v in values.items():
        if hasattr(cfg, k) and isinstance(getattr(cfg, k), tuple) and isinstance(v, list):
            v = tuple(v)
        setattr(cfg, k, v)


def parse_set(items):
    out = {}
    for it in items:
        k, v = it.split("=", 1)
        try:
            v = float(v) if "." in v or "e" in v.lower() else int(v)
        except ValueError:
            v = {"True": True, "False": False, "None": None}.get(v, v)
        out[k] = v
    return out


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def run(rec_dir, seed=None, overrides=None, quiet=False):
    from wro.record import ReplayHAL, STATE
    hal = ReplayHAL(rec_dir)
    apply_cfg(hal.meta["cfg"])
    apply_cfg(overrides or {})
    from wro.pathdrive import PathDriver
    from wro.pf import ParticleFilter
    drv = PathDriver(hal, verbose=False)
    drv.seed = hal.meta["seed"] if seed is None else seed
    drv.pf = ParticleFilter(seed=drv.seed)
    b, pf = drv.b, drv.pf
    b._head_step = lambda t: None                  # capul: starea inregistrata, nu logica live
    st = dict(son=[], cam=[], path=[], live=[], hits=[], dir_t=None, dir_p=None, sig=[])

    up_sonar, up_points = pf.update_sonar, pf.update_points

    def prior():
        return pf.estimate(drv.dir or None)[0]

    def sonar_hook(r, pan_deg=0.0, head_fwd=0.15, sigma=0.04):
        if drv.dir and r is not None and 0.05 <= r <= 2.4:     # inainte de decizia directiei pozitia nu e inca fixata
            x, y, th = prior()
            ox, oy, a = x + head_fwd * math.cos(th), y + head_fwd * math.sin(th), th + math.radians(pan_deg)
            e = float(pf.wf.ray(np.array([ox]), np.array([oy]), np.array([a]), rmax=2.5)[0])
            st["son"].append((hal.row["t"], pan_deg, r, e))
            st["hits"].append((ox + r * math.cos(a), oy + r * math.sin(a)))
        up_sonar(r, pan_deg, head_fwd, sigma)

    def points_hook(X, Y, delta=(0.0, 0.0, 0.0), **kw):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        uv = kw.get("uv")
        if drv.dir and len(X) >= 4 and uv is not None and pf.selfcal:     # cu calibrarea camerei estimata de filtru
            from wro.geometry import CameraModel
            dpd, kf = pf.calib(drv.dir)
            cam0 = uv[3]
            cam = CameraModel(hfov_deg=math.degrees(2 * math.atan(cam0.w / 2 / (cam0.f * kf))), pitch_deg=math.degrees(cam0.pitch) + dpd)
            Xh, Yh, _ = cam.pixel_to_ground(uv[0], uv[1])
            X, Y = b.perceiver._to_car(Xh, Yh, uv[2])
        if drv.dir and len(X) >= 4:
            x, y, th = prior()
            dx, dy, dth = delta
            c, s = math.cos(dth), math.sin(dth)
            px = c * (X - dx) + s * (Y - dy)
            py = -s * (X - dx) + c * (Y - dy)
            gx = x + math.cos(th) * px - math.sin(th) * py
            gy = y + math.sin(th) * px + math.cos(th) * py
            st["cam"].append((hal.row["t"], float(np.median(pf.wf.lookup(gx, gy))), len(X)))
        up_points(X, Y, delta, **kw)

    pf.update_sonar, pf.update_points = sonar_hook, points_hook

    rows = hal.rows
    for i, row in enumerate(rows):
        hal.load(row)
        if row.get("dir", 0) != drv.dir:
            drv.dir = row["dir"]
            if drv.dir:
                st["dir_t"], st["dir_p"] = row["t"], pf.dir_prob()
                pf.collapse(drv.dir)
        for k in STATE:
            if k in row:
                setattr(b, k, row[k])
        if row.get("s"):
            pose = drv._sense()
            if drv.dir:                            # inainte de decizie poza e media celor doua ipoteze (fara sens)
                st["path"].append((row["t"],) + tuple(pose))
                st["sig"].append(drv.sig)
            nxt = rows[i + 1].get("lp") if i + 1 < len(rows) else None
            if nxt is not None:
                st["live"].append((row["t"],) + tuple(nxt) + tuple(pose))
        else:
            b.tick()
    st["missing"] = hal.missing
    st["drv"] = drv
    st["rows"] = len(rows)
    st["frames"] = sum(1 for r in rows if r.get("f") is not None)
    return st


def pct(a, q):
    return float(np.percentile(a, q)) if len(a) else float("nan")


def report(st):
    print("pasi %d, cadre %d (lipsa %d), durata %.1f s" % (
        st["rows"], st["frames"], st["missing"], st["path"][-1][0] - st["path"][0][0] if st["path"] else 0.0))
    if st["dir_t"] is not None:
        d = st["drv"].dir
        print("directie: %s la t=%.1f (p_antiorar=%.3f inainte de decizie)" % ("antiorar" if d > 0 else "orar", st["dir_t"], st["dir_p"]))
    for name, sel in (("ultrasonic fata", lambda p: abs(p) < 2.0), ("ultrasonic lateral", lambda p: abs(p) >= 2.0)):
        s = [(r, e) for (_, p, r, e) in st["son"] if sel(p)]
        if not s:
            continue
        inn = np.array([r - e for r, e in s])
        print("%-19s n=%4d  inovatie mediana %+5.1f cm  |inov| med %4.1f  p90 %5.1f cm  >15cm %3.0f%%" % (
            name, len(s), 100 * np.median(inn), 100 * np.median(np.abs(inn)), 100 * pct(np.abs(inn), 90),
            100 * np.mean(np.abs(inn) > 0.15)))
    if st["cam"]:
        c = np.array([d for (_, d, _) in st["cam"]])
        print("camera pereti   n=%4d cadre  dist. mediana la perete %4.1f cm  p90 %5.1f cm  cadre >5cm %3.0f%%" % (
            len(c), 100 * np.median(c), 100 * pct(c, 90), 100 * np.mean(c > 0.05)))
    if st["drv"].pf.selfcal:
        print("calibrare camera estimata: pitch %+.2f grade, focala x%.3f (perechi sonar-camera: %d)" % (
            *st["drv"].pf.calib(st["drv"].dir or None), getattr(st["drv"], "n_camsonar", 0)))
    if st["sig"]:
        s = np.array(st["sig"])
        print("incertitudine PF (dupa directie): sx %.1f cm  sy %.1f cm  sth %.1f grade (mediane)" % (
            100 * np.median(s[:, 0]), 100 * np.median(s[:, 1]), math.degrees(np.median(s[:, 2]))))
    if st["live"]:
        L = np.array(st["live"])
        dp = np.hypot(L[:, 1] - L[:, 4], L[:, 2] - L[:, 5])
        print("fata de cursa reala: |pozitie reluare - pozitie live| mediana %.1f cm, max %.1f cm" % (100 * np.median(dp), 100 * dp.max()))
    pills = st["drv"].map.pillars(st["drv"].dir or 1)
    print("harta stalpi: %s" % (" ".join("%s(%.2f,%.2f)" % ("R" if c == 0 else "V", x, y) for (x, y, c, _, _) in pills) or "-"))


def draw(st, path):
    import cv2
    from wro.pf import WALLS
    k, m = 200, 20
    n = int(3 * k + 2 * m)
    img = np.full((n, n, 3), 255, np.uint8)
    P = lambda x, y: (int(m + x * k), int(n - m - y * k))
    for (x0, y0, x1, y1) in WALLS:
        cv2.line(img, P(x0, y0), P(x1, y1), (0, 0, 0), 2)
    for (hx, hy) in st["hits"]:
        cv2.circle(img, P(hx, hy), 1, (0, 140, 255), -1)          # unde a lovit ultrasonicul (ar trebui sa fie pe pereti)
    for row in st["live"]:
        cv2.circle(img, P(row[1], row[2]), 1, (170, 170, 170), -1)
    pts = [P(r[1], r[2]) for r in st["path"]]
    for a, c in zip(pts, pts[1:]):
        cv2.line(img, a, c, (200, 80, 0), 1)
    for (x, y, col, _, _) in st["drv"].map.pillars(st["drv"].dir or 1):
        cv2.circle(img, P(x, y), 10, (0, 0, 220) if col == 0 else (0, 160, 0), 2)
    cv2.putText(img, "albastru=reluare  gri=live  portocaliu=ecou ultrasonic", (m, m - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.imwrite(path, img)
    print("desen: %s" % path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("--seed", type=int, default=None, help="implicit: samanta din cursa (reluare identica)")
    ap.add_argument("--seeds", type=int, default=1, help="ruleaza cu N seminte diferite si compara")
    ap.add_argument("--set", action="append", default=[], metavar="CHEIE=VAL")
    a = ap.parse_args()
    over = parse_set(a.set)
    if a.seeds <= 1:
        st = run(a.rec, a.seed, over)
        report(st)
        draw(st, os.path.join(a.rec, "replay.png"))
        return
    ends = []
    for s in range(a.seeds):
        st = run(a.rec, s, over)
        print("--- samanta %d" % s)
        report(st)
        ends.append(st["path"][-1][1:])
    E = np.array(ends)
    print("=== pozitia finala intre seminte: sx %.1f cm  sy %.1f cm  sth %.1f grade" % (
        100 * E[:, 0].std(), 100 * E[:, 1].std(), math.degrees(np.std([wrap(t - E[0, 2]) for t in E[:, 2]]))))


if __name__ == "__main__":
    sys.exit(main())

