"""Ruleaza scenarii in simulator:  python3 simulate.py open --n 6 --seed 1"""
import argparse, math, random, sys, time
from wro import config as cfg
from wro import sim
from wro.drive import Driver


def choose_start(tr, rng, mode):
    """Pozitie de start in sectiunea de start (echipa isi alege locul): cea mai libera. Cu parcare (regulament 2026): zona din
    mijloc (pe latime), in jumatatea sectiunii in care e parcarea. Un stalp prea aproape in fata / alaturi face startul invalid."""
    if mode != "obstacle":
        return sim.start_pose_for(tr, rng)
    x0, y0, x1, y1 = tr.sections()[tr.start_side]
    length = (x1 - x0) if tr.start_side in "BT" else (y1 - y0)
    if tr.markers:
        lo, hi = cfg.REAR_TO_BACK + 0.02, 0.5 * length - cfg.REAR_TO_FRONT - 0.02
        if tr.direction > 0:                           # antiorar: parcarea e la capatul de iesire al sectiunii
            lo, hi = lo + 0.5 * length, hi + 0.5 * length
        fracs = [(lo + (hi - lo) * k / 6) / length for k in range(7)]
    else:
        fracs = (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7)
    best, best_clear = None, -1.0
    for frac in fracs:
        for off in (0.0, -0.06, 0.06, -0.12, 0.12):
            px, py, th = sim.start_pose_for(tr, rng, frac=frac)
            if tr.start_side in "BT":
                py = (y0 + y1) / 2 + off
            else:
                px = (x0 + x1) / 2 + off
            clear = 9.0
            for (qx, qy, c) in tr.pillars:
                dx, dy = qx - px, qy - py
                X = dx * math.cos(th) + dy * math.sin(th)
                Y = -dx * math.sin(th) + dy * math.cos(th)
                if abs(Y) < 0.35 and -0.35 < X < 0.30:
                    clear = -1.0                    # stalp langa masina: start invalid
                    break
                if abs(Y) < 0.35 and X >= 0.30:
                    clear = min(clear, X)
            if clear > best_clear:
                best, best_clear = (px, py, th), clear
    return best if best_clear >= 0.60 else None


def perturbed(seed, level=1.0):
    """Realitate diferita de ce crede codul: toleranta la calibrare imperfecta."""
    r = random.Random(1000 + seed)
    u = lambda a: r.uniform(-a, a) * level
    return sim.SimParams(
        steer_gain=1.0 + u(0.18),             # unghiul real al rotilor +-18% fata de calibrare
        steer_trim_deg=u(4.0),                 # centru gresit (grade servo)
        v_per_pct=cfg.V_PER_PCT * (1.0 + u(0.15)),
        cam_pitch_deg=cfg.CAM_PITCH_DEG + u(3.0),
        cam_height=cfg.CAM_HEIGHT + u(0.02),
        cam_hfov_deg=cfg.CAM_HFOV_DEG + u(3.0),
        light=1.0 + u(0.35),
        slip=1.0 + u(0.12),
        cam_latency=0.07 + abs(u(0.05)),
    )


_WPS0 = cfg.WHEEL_PER_SERVO          # valoarea initiala: drive.learn_gain o modifica in timpul unei curse


def run_one(mode, seed, direction=None, widths=None, params=None, verbose=False, parking=False, max_time=None, park=False):
    cfg.WHEEL_PER_SERVO = _WPS0         # fiecare cursa porneste de la calibrarea initiala
    rng = random.Random(seed)
    tr = sim.random_track(rng, mode=mode, direction=direction, widths=widths, parking=parking)
    if park:
        tr.pillars = []                  # proba de parcare: fara stalpi
    pose = choose_start(tr, rng, mode)
    if pose is None:
        return None
    hw = sim.SimHW(tr, params=params, seed=seed, start_pose=pose)
    if mode == "obstacle":
        from wro.pathdrive import PathDriver
        from wro.parking import ParkDriver
        drv = (ParkDriver if park else PathDriver)(hw, mode=mode, verbose=verbose)
        t = time.time()
        reason = drv.run(max_time=max_time or 180)
        return tr, hw, drv, reason, time.time() - t
    drv = Driver(hw, mode=mode, verbose=verbose)
    try:
        from wro.parking import Parking
        drv.park = Parking() if parking else None
    except ImportError:
        drv.park = None
    t = time.time()
    reason = drv.run(max_time=max_time or 120)
    return tr, hw, drv, reason, time.time() - t


def park_state(tr, hw):
    """'full' (complet in loc si paralel: rotile de pe o parte la max 2 cm diferenta fata de perete), 'part' sau 'no'."""
    r = sim.lot_free(tr)
    if r is None:
        return "no"
    poly = hw.footprint()
    inside = [r[0] - 1e-3 <= px <= r[2] + 1e-3 and r[1] - 1e-3 <= py <= r[3] + 1e-3 for px, py in poly]
    ax = 0.0 if tr.start_side in "BT" else math.pi / 2
    if all(inside) and abs(math.sin(hw.th - ax)) * cfg.WHEELBASE <= 0.02:
        return "full"
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    if min(xs) < r[2] and max(xs) > r[0] and min(ys) < r[3] and max(ys) > r[1]:
        return "part"
    return "no"


def summary(tr, hw, drv, reason, wall):
    ok_stop = hw.in_section(tr.start_side, 0.0)
    return dict(reason=reason, corners=drv.corners, laps=round(hw.laps(), 2), coll=hw.collisions, mk=hw.marker_hits,
                park=park_state(tr, hw),
                pill=hw.pillar_hits, t=round(hw.now(), 1), in_start=ok_stop, dir=tr.direction,
                widths=''.join(str(int(tr.widths[k] * 10)) for k in 'LRBT'), wall=round(wall, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["open", "obstacle", "parcare"])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--list", default="")
    ap.add_argument("--perturb", type=float, default=0.0, help="nivel perturbari fizice (1.0 = tipic)")
    ap.add_argument("--params", default="", help="parametri fizici explicit, ex: steer_gain=1.18,steer_trim_deg=3")
    ap.add_argument("--no-lot", action="store_true", help="fara parcare in teren (implicit: parcarea exista in Obstacle)")
    ap.add_argument("--cal", action="store_true", help="incarca calibration.json (geometria masinii reale) in loc de valorile din config.py")
    a = ap.parse_args()
    park = a.mode == "parcare"
    if park:
        a.mode = "obstacle"
    if a.cal:
        cfg.load_calibration()
        _WPS0 = cfg.WHEEL_PER_SERVO
    good = 0
    seeds = [int(x) for x in a.list.split(',')] if a.list else [a.seed + i for i in range(a.n)]
    for sd in seeds:
        i = sd - a.seed
        r = run_one(a.mode, a.seed + i, verbose=a.verbose, params=(sim.SimParams(**{k: float(v) for k, v in (kv.split('=') for kv in a.params.split(','))}) if a.params else (perturbed(a.seed + i, a.perturb) if a.perturb else None)), parking=(a.mode == 'obstacle' and not a.no_lot), park=park)
        if r is None:
            print('seed %d: sarit (start imposibil)' % (a.seed + i)); continue
        s = summary(*r)
        ok = s["coll"] == 0 and s["pill"] == 0 and s["mk"] == 0 and (s["park"] != "no" if park else s["corners"] >= 12 and s["in_start"])
        good += ok
        print("seed %d: %s %s" % (a.seed + i, "OK " if ok else "FAIL", s), flush=True)
    print("reusit %d/%d" % (good, len(seeds)))

