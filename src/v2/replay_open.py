#!/usr/bin/env python3
"""Reluare offline a unei curse Open inregistrate (debug/rec_<ts>/): nu misca motoarele.

    python3 replay_open.py debug/rec_1791617443
    python3 replay_open.py debug/rec_1791617443 --set CAM_PITCH_DEG=14.5     # aceleasi cadre, alt parametru

Hraneste Brain-ul (perceptie + estimator) cu exact ce a citit masina in cursa (comenzile sunt cele inregistrate) si arata:
  - cat la suta din cadre au dat o masuratoare de culoar (perete lateral) acceptata
  - pentru perioadele "orb" (>0.5 s fara masuratoare): ce a vazut camera (puncte de perete, linii gasite)
  - poze adnotate ale cadrelor oarbe in <rec>/orb/ (puncte galbene = baza peretelui gasita)
"""
import argparse
import math
import os

import numpy as np

from replay import apply_cfg, parse_set


def run(rec_dir, overrides, save_every=0.5):
    from wro.record import ReplayHAL, STATE
    from wro.drive import Driver
    from wro.perception import annotate
    import cv2
    hal = ReplayHAL(rec_dir)
    apply_cfg(hal.meta["cfg"])
    apply_cfg(overrides)
    drv = Driver(hal, mode="open", verbose=False)
    b, est = drv.b, drv.b.est
    b._head_step = lambda t: None                  # capul: starea inregistrata, nu logica live
    out = os.path.join(rec_dir, "orb")
    os.makedirs(out, exist_ok=True)
    n_fr = n_upd = 0
    blind, last_save = [], -1e9
    t_go = hal.rows[0]["t"] + 0.7                  # Driver.start(): 0.7 s pe loc, apoi cursa
    drv.t0 = hal.rows[0]["t"]
    drv.path_last_turn = -0.2
    for row in hal.rows:
        hal.load(row)
        if row.get("dir") and drv.dir != row["dir"]:
            drv.dir = row["dir"]
            drv._on_dir()
        for k in STATE:
            if k in row:
                setattr(b, k, row[k])
        lt0 = est.lane_t
        w = b.tick()
        if row["t"] >= t_go:                       # starea Driver-ului (viraje => resetarea culoarului); comenzile raman cele inregistrate
            drv.w = w
            drv.step(w)
        if b.frame_event is None:
            continue
        n_fr += 1
        per = b.frame_event[0]
        if est.lane_t != lt0:
            n_upd += 1
            continue
        age = row["t"] - est.lane_t
        d = est.dbg or {}
        info = "t=%6.2f orb %.1fs exterior=%s psi=%+.0f y=%+.2f | puncte perete %d (st %d dr %d) linii %s psi_fata %s" % (
            row["t"], min(age, 99), est.outer_only, math.degrees(est.psi), est.y_off, d.get("nvalid", 0), d.get("nleft", 0),
            d.get("nright", 0), d.get("lines"), None if d.get("psi_f") is None else "%.0f" % math.degrees(d["psi_f"]))
        blind.append(info)
        if age > 0.5 and row["t"] - last_save >= save_every and b.last_img is not None:
            last_save = row["t"]
            img = annotate(b.last_img, per, b.perceiver.cam)
            cv2.putText(img, "%.2f orb %.1fs pan %+.0f" % (row["t"], min(age, 99), per.pan), (4, img.shape[0] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.imwrite(os.path.join(out, "%06.2f.jpg" % row["t"]), img)
    print("cadre procesate %d, cu masuratoare de culoar acceptata %d (%.0f%%), cadre lipsa la inregistrare %d" % (
        n_fr, n_upd, 100.0 * n_upd / max(1, n_fr), hal.missing))
    for s in blind[::max(1, len(blind) // 60)]:
        print(s)
    print("poze cadre oarbe: %s" % out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("--set", action="append", default=[], metavar="CHEIE=VAL")
    a = ap.parse_args()
    run(a.rec, parse_set(a.set))


if __name__ == "__main__":
    main()

