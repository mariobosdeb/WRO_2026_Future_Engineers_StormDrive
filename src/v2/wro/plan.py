"""Planificator local pentru Obstacle: rollout-uri cinematice (model bicicleta) in cadrul culoarului.

Cadrul culoarului: s = de-a lungul axei culoarului (inainte), u = lateral (stanga +), centru = 0.
Masina e la (0, y_off) cu heading psi fata de axa.

Pentru fiecare traiectorie candidata (secvente de directie in 3 faze) se calculeaza:
  * ciocniri cu pereti (inclusiv coltul interior si peretele din fata) si cu stalpi,
  * regula culorii (rosu: stalpul ramane in STANGA masinii; verde: in DREAPTA) cand masina e in dreptul lui,
  * abaterea de la centrul culoarului si de la axa.
Se aplica prima directie a celei mai bune traiectorii (MPC, se replanifica la fiecare ciclu).
Acelasi mecanism (arc la directie maxima) verifica daca un viraj de colt e liber, ca sa-l putem intarzia.
"""
import math

import numpy as np

from . import config as cfg

HALF_W = None


def _footprint():
    hw = cfg.CAR_WIDTH / 2.0
    f, r = cfg.REAR_TO_FRONT, -cfg.REAR_TO_BACK
    xs = np.linspace(r, f, 6)
    pts = [(x, hw) for x in xs] + [(x, -hw) for x in xs] + [(f, 0.0), (r, 0.0)]
    return np.array(pts, dtype=np.float64)


def _pt_seg_dist(P, segs):
    """P: (...,2); segs: (M,4) -> (..., M) distante punct-segment."""
    x0, y0, x1, y1 = segs[:, 0], segs[:, 1], segs[:, 2], segs[:, 3]
    dx, dy = x1 - x0, y1 - y0
    den = dx * dx + dy * dy + 1e-12
    px, py = P[..., 0:1], P[..., 1:2]
    t = np.clip(((px - x0) * dx + (py - y0) * dy) / den, 0.0, 1.0)
    return np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


class Obstacles:
    """Mediul in cadrul culoarului."""

    def __init__(self, segs, pillars):
        self.segs = np.asarray(segs, dtype=np.float64).reshape(-1, 4)
        self.pillars = list(pillars)          # (s, u, 'red'|'green')


class Planner:
    def __init__(self):
        L = cfg.WHEELBASE
        self.L = L
        self.ds = 0.05
        k = cfg.WHEEL_PER_SERVO
        self._k = k
        sm = float(cfg.STEER_MAX_DEG)           # candidatele sunt fractii din cursa servo (nu valori fixe)
        d1 = sm * np.array([-1.0, -0.64, -0.32, -0.11, 0.0, 0.11, 0.32, 0.64, 1.0])
        d2 = sm * np.array([-0.79, 0.0, 0.79])
        d3 = sm * np.array([-0.5, 0.0, 0.5])
        lens = (0.30, 0.35, 0.40)
        n_ph = [int(round(l / self.ds)) for l in lens]
        rows = []
        first = []
        for a in d1:
            for b in d2:
                for c in d3:
                    rows.append([a] * n_ph[0] + [b] * n_ph[1] + [c] * n_ph[2])
                    first.append(a)
        self.servo = np.array(rows)                       # (C, N) grade servo
        self.first = np.array(first)
        self.wheel = np.radians(self.servo * k)
        self.C, self.N = self.servo.shape
        self.fp = _footprint()
        self.prev_first = 0.0
        self.last_info = {}

    # ------------------------------------------------------------------ cinematica
    def rollout(self, y0, th0, wheel=None):
        wheel = self.wheel if wheel is None else wheel
        C, N = wheel.shape
        x = np.zeros(C)
        y = np.full(C, y0)
        th = np.full(C, th0)
        X = np.empty((C, N + 1))
        Y = np.empty((C, N + 1))
        T = np.empty((C, N + 1))
        X[:, 0], Y[:, 0], T[:, 0] = x, y, th
        for i in range(N):
            dth = np.tan(wheel[:, i]) / self.L * self.ds
            tm = th + 0.5 * dth
            x = x + self.ds * np.cos(tm)
            y = y + self.ds * np.sin(tm)
            th = th + dth
            X[:, i + 1], Y[:, i + 1], T[:, i + 1] = x, y, th
        return X, Y, T

    def _footprint_pts(self, X, Y, T):
        c, s = np.cos(T)[..., None], np.sin(T)[..., None]
        fx, fy = self.fp[:, 0], self.fp[:, 1]
        px = X[..., None] + fx * c - fy * s
        py = Y[..., None] + fx * s + fy * c
        return np.stack([px, py], axis=-1)           # (C, N+1, P, 2)

    # ------------------------------------------------------------------ evaluare
    def clearance(self, X, Y, T, obs, margin_wall=None, margin_pil=None):
        margin_wall = cfg.PLAN_MARGIN_WALL if margin_wall is None else margin_wall
        margin_pil = cfg.PLAN_MARGIN_PIL if margin_pil is None else margin_pil
        """Intoarce penalizarea de ciocnire (C,) si clearance minim (C,)."""
        pts = self._footprint_pts(X, Y, T)
        C = X.shape[0]
        pen = np.zeros(C)
        minc = np.full(C, 9.0)
        if len(obs.segs):
            d = _pt_seg_dist(pts, obs.segs).min(axis=-1)           # (C,N+1,P)
            dm = d.min(axis=-1)                                      # (C,N+1)
            v = np.clip(margin_wall - dm, 0.0, None)
            pen += (v * v * 4000.0).sum(axis=1) + (dm < 0.012).sum(axis=1) * 400.0
            minc = np.minimum(minc, dm.min(axis=1))
        for (ps, pu, col) in obs.pillars:
            dd = np.hypot(pts[..., 0] - ps, pts[..., 1] - pu) - 0.0354      # raza cercului circumscris
            dm = dd.min(axis=-1)
            v = np.clip(margin_pil - dm, 0.0, None)
            pen += (v * v * 4000.0).sum(axis=1) + (dm < 0.01).sum(axis=1) * 400.0
            minc = np.minimum(minc, dm.min(axis=1))
            # regula culorii cand pilonul e in dreptul masinii
            dx, dy = ps - X, pu - Y
            c, s = np.cos(T), np.sin(T)
            xp = dx * c + dy * s
            yp = -dx * s + dy * c
            win = (xp > -0.12) & (xp < 0.28)
            need = cfg.CAR_WIDTH / 2.0 + 0.025 + 0.06
            if col == "red":
                viol = np.clip(need - yp, 0.0, None)          # stalpul trebuie sa fie la stanga masinii
            else:
                viol = np.clip(need + yp, 0.0, None)          # stalpul trebuie sa fie la dreapta
            pen += (np.where(win, viol, 0.0) ** 1 * 900.0).sum(axis=1)
        return pen, minc

    def plan(self, y0, th0, obs, u_ref=0.0):
        if cfg.WHEEL_PER_SERVO != self._k:                 # raportul roata/servo a fost reinvatat online
            self._k = cfg.WHEEL_PER_SERVO
            self.wheel = np.radians(self.servo * self._k)
        X, Y, T = self.rollout(y0, th0)
        pen, minc = self.clearance(X, Y, T, obs)
        w = np.linspace(0.6, 1.4, self.N + 1)
        c_u = (w * (Y - u_ref) ** 2).sum(axis=1) * 6.0
        c_h = (w * T ** 2).sum(axis=1) * 0.9
        c_end = 40.0 * (Y[:, -1] - u_ref) ** 2 + 12.0 * T[:, -1] ** 2
        c_s = 0.0004 * (self.servo ** 2).sum(axis=1) / self.N
        c_sm = 0.0006 * (self.first - self.prev_first) ** 2
        cost = pen + c_u + c_h + c_end + c_s + c_sm
        i = int(np.argmin(cost))
        self.prev_first = float(self.first[i])
        self.last_info = {"cost": float(cost[i]), "pen": float(pen[i]), "minc": float(minc[i]), "best": i}
        return float(self.first[i]), self.last_info

    # ------------------------------------------------------------------ viraj
    def turn_check(self, y0, th0, sgn, s_off, obs, post=0.5, steer_deg=None):
        """Simuleaza: s_off drept, apoi directie maxima spre sgn (+1 stanga) ~92 grade, apoi `post` m drept
        (ca sa vedem si stalpii imediat dupa colt).  Intoarce (penalizare, clearance_min)."""
        ds = self.ds
        n_s = max(0, int(round(s_off / ds)))
        st = cfg.TURN_STEER_DEG if steer_deg is None else steer_deg
        R = self.L / max(1e-3, math.tan(math.radians(st * cfg.WHEEL_PER_SERVO)))
        n_arc = int(round(R * math.radians(92.0) / ds)) + 1
        n_post = int(round(post / ds))
        wheel = np.zeros((1, n_s + n_arc + n_post))
        wheel[0, n_s:n_s + n_arc] = sgn * math.radians(st * cfg.WHEEL_PER_SERVO)
        X, Y, T = self.rollout(y0, th0, wheel)
        pen, minc = self.clearance(X, Y, T, obs, margin_wall=cfg.PLAN_TURN_MARGIN_WALL, margin_pil=cfg.PLAN_TURN_MARGIN_PIL)
        return float(pen[0]), float(minc[0])

    def best_turn_offset(self, y0, th0, sgn, obs, o_hi, d_pref=0.0, step=0.05, steers=None):
        """Alege momentul si directia virajului. Cost = penalizare + 8*|o-d_pref| + 0.15*(28-steer).
        Intoarce (offset, steer, pen_nominal_la_0, pen_optim)."""
        if steers is None:
            steers = tuple(cfg.TURN_STEER_DEG * f for f in (1.0, 0.79, 0.61))
        offs = [0.0]
        while offs[-1] + step <= o_hi + 1e-9:
            offs.append(offs[-1] + step)
        res = []
        for st in steers:
            for o in offs:
                pn, _ = self.turn_check(y0, th0, sgn, o, obs, steer_deg=st)
                res.append((pn + 8.0 * abs(o - d_pref) + 0.15 * (steers[0] - st) * (28.0 / max(1.0, steers[0])), o, st, pn))
        nom0 = next(r for r in res if r[1] == 0.0 and r[2] == steers[0])
        cb, ob, sb, pb = min(res, key=lambda r: (r[0], r[1], -r[2]))
        if ob <= 1e-9:
            return 0.0, sb, nom0[3], pb
        return ob, sb, nom0[3], pb


def build_obstacles(w, dir_sgn, W, psi, y_off, corner_xy=None, front_x=None, pillars=()):
    """Construieste peretii si stalpii in cadrul culoarului din starea lumii (cadrul masinii)."""
    c, s = math.cos(psi), math.sin(psi)

    def to_lane(X, Y):
        return X * c - Y * s, y_off + X * s + Y * c

    hw = W / 2.0
    sg = float(dir_sgn) if dir_sgn else 0.0
    segs = []
    far = 6.0
    s_c = None
    s_f = None
    if corner_xy is not None:
        s_c, _ = to_lane(*corner_xy)
    if front_x is not None:
        s_f, _ = to_lane(front_x, 0.0)
    if sg == 0.0:
        segs.append((-0.6, hw, far if s_f is None else s_f, hw))
        segs.append((-0.6, -hw, far if s_f is None else s_f, -hw))
        if s_f is not None:
            segs.append((s_f, -hw, s_f, hw))
    else:
        s_end = far if s_f is None else s_f
        segs.append((-0.6, -sg * hw, s_end, -sg * hw))                     # perete exterior
        if s_c is not None:
            segs.append((-0.6, sg * hw, s_c, sg * hw))                      # perete interior pana la colt
            segs.append((s_c, sg * hw, s_c, sg * (hw + 1.2)))               # peretele interior al culoarului urmator
            if s_f is None:
                s_f = s_c + W
            segs.append((s_f, -sg * hw, s_f, sg * (hw + 1.2)))             # peretele din fata
        else:
            segs.append((-0.6, sg * hw, far, sg * hw))
            if s_f is not None:
                segs.append((s_f, -hw, s_f, hw))
    pil = []
    for p in pillars:
        ps, pu = to_lane(p.X, p.Y)
        pil.append((ps, pu, p.color))
    return Obstacles(segs, pil), s_c, s_f

