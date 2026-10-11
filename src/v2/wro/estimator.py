"""Estimator: fuzioneaza camera + ultrasonic + odometrie intr-o stare coerenta a lumii.

Stare estimata (cadrul masinii: origine = axa spate, X inainte, Y stanga):
  * pozitia laterala fata de centrul culoarului  y_off  (+ = masina e la stanga de centru)
  * heading fata de axa culoarului               psi    (+ = masina priveste spre stanga)
  * latimea culoarului W si distantele dl, dr la pereti
  * distanta la peretele din fata (camera + ultrasonic), obstacol in fata
  * colturile interioare ("deschiderea" peretelui interior), urmarite cu odometrie
  * stalpi (rosu/verde) si markere de parcare (magenta), urmariti cu odometrie
  * factorul de scara al camerei, invatat online din ultrasonic
"""
import math
from dataclasses import dataclass, field

import numpy as np

from . import config as cfg
from .geometry import ransac_line, line_distance
from .perception import ST_WALL, ST_NONE, ST_OCCLUDED, ST_TOUCH


class Track:
    __slots__ = ("X", "Y", "color", "t_seen", "n", "area", "src")

    def __init__(self, X, Y, color, t, area=0.0):
        self.X, self.Y, self.color, self.t_seen, self.n, self.area = X, Y, color, t, 1, area
        self.src = "wall"

    def __repr__(self):
        return "Track(%s %.2f,%.2f n=%d)" % (self.color, self.X, self.Y, self.n)


@dataclass
class World:
    t: float
    y_off: float = None
    psi: float = None
    W: float = None
    dl: float = None
    dr: float = None
    lane_age: float = 99.0
    lane_sides: int = 0                       # cati pereti au fost vazuti in ultimul cadru
    front: float = None                       # perete in fata (cadrul masinii)
    front_obs: float = None                   # orice obstacol in fata (ultrasonic)
    front_age: float = 99.0
    corner: dict = field(default_factory=lambda: {"left": None, "right": None})
    open_vis: dict = field(default_factory=lambda: {"left": False, "right": False})
    near: dict = field(default_factory=lambda: {"left": False, "right": False, "front": False})
    pillars: list = field(default_factory=list)
    markers: list = field(default_factory=list)
    line_events: list = field(default_factory=list)
    last_line: dict = field(default_factory=dict)
    scale: float = 1.0
    cam_ok: bool = True
    wall_pts: np.ndarray = None
    sonar_side: dict = field(default_factory=dict)
    head_free: bool = True                    # capul e drept si camera valida


class Estimator:
    def __init__(self):
        self.scale = 1.0
        self.y_off = 0.0
        self.psi = 0.0
        self.W = None
        self.auto_width = False     # Open: latimea (0.6 / 1.0) se clasifica singura per sectiune, apoi filtrul Kalman
        self._w_votes = []
        self.kf_incons = 0
        self.outer_pref = None
        self.outer_only = None      # Open: urmareste doar peretele exterior ('left'/'right'), latime virtuala OUTER_W
        self.W_fixed = None         # latimea cunoscuta (Obstacle: 1.0 m) => foloseste filtrul Kalman (y, psi)
        self.P = np.diag([0.25 ** 2, 0.5 ** 2])
        self._kf_fresh = True       # prima masuratoare seteaza starea direct
        self._kf_rej = 0
        self.lane_t = -1e9          # ultima actualizare din camera
        self.lane_sides = 0
        self.dl = self.dr = None
        self.front_cam = None       # (X, t)
        self.front_sonar = None     # (X, t)
        self.obs_sonar = None
        self.side_sonar = {"left": None, "right": None}   # (d_origin, t)
        self._path = 0.0
        self.front_veto = -1e9
        self._sd_hist = {"left": None, "right": None}     # (d_origin, drum) pentru unghiul din ultrasonic
        self.corner = {"left": None, "right": None}
        self.open_vis = {"left": False, "right": False}
        self.open_t = {"left": -1e9, "right": -1e9}
        self.pillars = []
        self.use_pillars = True          # Open: nu exista stalpi -> detectiile rosii/verzi sunt false si se ignora
        self.markers = []
        self.last_line = {}
        self._line_events = []
        self.wall_pts = None
        self.near = {"left": False, "right": False, "front": False}
        self._last_cam_side = {"left": -1e9, "right": -1e9}
        self._cam_side_d = {"left": None, "right": None}
        self._cam_bad = {"left": -1e9, "right": -1e9}      # ultrasonicul a contrazis camera pe partea asta (timp)
        self._nofit = {"left": 0, "right": 0}
        self.cam_ok = True

    # ------------------------------------------------------------------ odometrie
    @staticmethod
    def _xform(X, Y, dx, dy, dth):
        """Punct masurat in cadrul de la t_cap -> cadrul curent (masina s-a miscat cu dx,dy,dth)."""
        px, py = X - dx, Y - dy
        c, s = math.cos(dth), math.sin(dth)
        return px * c + py * s, -px * s + py * c

    def propagate(self, ds, dth):
        """Actualizeaza starea cu miscarea masinii intr-un pas (ds metri inainte, dth rad)."""
        mid = 0.5 * dth
        self._path += abs(ds)
        dx, dy = ds * math.cos(mid), ds * math.sin(mid)
        for side in ("left", "right"):
            c = self.corner[side]
            if c is not None:
                c.X, c.Y = self._xform(c.X, c.Y, dx, dy, dth)
        for lst in (self.pillars, self.markers):
            for p in lst:
                p.X, p.Y = self._xform(p.X, p.Y, dx, dy, dth)
        for key in ("front_cam", "front_sonar"):
            v = getattr(self, key)
            if v is not None and abs(dth) < 0.5:
                setattr(self, key, (v[0] - ds * math.cos(self.psi), v[1]))
        if self.W_fixed:
            c = math.cos(self.psi)
            F = np.array([[1.0, ds * c], [0.0, 1.0]])
            a = abs(ds)
            Q = np.diag([1.5e-4 * a + 1e-6, 1.2e-3 * a + 0.04 * abs(dth) ** 2 + 1e-6])
            self.P = F @ self.P @ F.T + Q
        self.psi += dth
        self.y_off += ds * math.sin(self.psi - 0.5 * dth)

    # ------------------------------------------------------------------ intrare camera
    def ingest_camera(self, per, t_now, delta, turning=False):
        """per: Perception (la momentul t_cap), delta=(dx,dy,dth) miscare de la t_cap pana acum."""
        dx, dy, dth = delta
        self.cam_ok = per.ok
        H = cfg.REAR_TO_HEAD
        sc = self.scale
        Xs = H + (per.X - H) * sc
        Ys = per.Y * sc
        valid = per.state == ST_WALL
        valid &= (Xs > 0.05) & (Xs < cfg.CAM_MAX_X)
        self.near = {"left": False, "right": False, "front": False}
        touch = per.state == ST_TOUCH
        if touch.any():
            self.near["left"] = bool((touch & (per.az > 12)).any())
            self.near["right"] = bool((touch & (per.az < -12)).any())
            self.near["front"] = bool((touch & (np.abs(per.az) <= 12)).any())

        pts_all = np.column_stack([Xs, Ys])
        # ---- orientatia peretelui din fata (perpendicular pe axa culoarului) => psi
        psi_f, nf, front_c, front_line, span_f, xbar_f = None, 0, None, None, 0.0, 1.0
        cen_f = valid & (np.abs(per.az) <= 26.0) & (Xs < cfg.FRONT_FIT_X_MAX)
        pf = pts_all[cen_f]
        if len(pf) >= 8:
            res = ransac_line(np.column_stack([pf[:, 1], pf[:, 0]]), inlier=0.03, min_points=8)
            if res is not None:
                af, bf, mf = res
                inl = pf[mf]
                gap = float(np.diff(np.sort(inl[:, 1])).max())     # inliere din doi pereti diferiti (fata + lateral) => linie falsa
                if np.ptp(inl[:, 1]) > 0.18 and 0.2 < af < 3.0 and gap < cfg.FRONT_FIT_MAX_GAP:
                    psi_f, nf, front_c, front_line = math.atan(bf), int(mf.sum()), af, (af, bf)
                    span_f, xbar_f = float(np.ptp(inl[:, 1])), float(inl[:, 0].mean())
        fit_ok = valid & (Xs < cfg.FIT_X_MAX)
        if front_line is not None:       # punctele peretelui din fata nu sunt perete lateral
            fit_ok &= np.abs(Xs - (front_line[0] + front_line[1] * Ys)) > 0.05
        left_idx = np.where(fit_ok & (Ys > cfg.SIDE_MIN_Y))[0]
        right_idx = np.where(fit_ok & (Ys < -cfg.SIDE_MIN_Y))[0]
        lines = {}
        for side, idx in (("left", left_idx), ("right", right_idx)):
            res = ransac_line(pts_all[idx]) if len(idx) >= cfg.FIT_MIN_POINTS else None
            if res is not None:
                a, b, mask = res
                lines[side] = (a, b, idx, mask)
                self._nofit[side] = 0
            else:
                self._nofit[side] += 1
        self.wall_pts = pts_all[valid]
        for side in list(lines.keys()):
            if t_now - self._cam_bad[side] < cfg.CAM_BAD_HOLD:
                del lines[side]                 # camera masoara gresit peretele asta (departe): conteaza ultrasonicul

        # linii laterale incompatibile cu orientarea cunoscuta (perete din fata / estimarea anterioara) => respinse
        ref0 = psi_f if psi_f is not None else (self.psi if t_now - self.lane_t < 1.0 else None)
        if ref0 is not None:
            tol = math.radians(10.0 if psi_f is not None else 20.0)
            if self.W_fixed and psi_f is None and not self._kf_fresh:
                tol = math.radians(min(20.0, max(6.0, 3.0 * math.degrees(math.sqrt(max(self.P[1, 1], 1e-6))))))
            for side in list(lines.keys()):
                a, b, idx, mask = lines[side]
                inl = idx[mask]
                span = float(np.ptp(pts_all[inl, 0])) if len(inl) else 0.0
                if span < 0.40 and psi_f is None and self.W_fixed:
                    if len(inl) < 8 or span < 0.15:
                        del lines[side]
                        self._nofit[side] += 1
                    continue
                if span < 0.40:
                    # segment scurt: panta nesigura => o fixam la orientarea cunoscuta
                    b2 = -math.tan(ref0)
                    a2 = float(np.median(pts_all[inl, 1] - b2 * pts_all[inl, 0]))
                    res = np.abs(pts_all[inl, 1] - (a2 + b2 * pts_all[inl, 0]))
                    if res.max() < 0.05:
                        lines[side] = (a2, b2, idx, mask)
                        continue
                    del lines[side]
                    self._nofit[side] += 1
                elif abs(-math.atan(b) - ref0) > tol:
                    del lines[side]
                    self._nofit[side] += 1
        psi_ref = psi_f
        if psi_ref is None and len(lines) == 2:
            psi_ref = -math.atan(0.5 * (lines["left"][1] + lines["right"][1]))
        elif psi_ref is None and len(lines) == 1:
            psi_ref = -math.atan(next(iter(lines.values()))[1])
        elif psi_ref is None and t_now - self.lane_t < 1.0:
            psi_ref = self.psi
        for side, idx in (("left", left_idx), ("right", right_idx)):
            if side in lines or psi_ref is None or len(idx) < 2:
                continue
            b = -math.tan(psi_ref)
            ac = pts_all[idx, 1] - b * pts_all[idx, 0]
            dc = np.abs(ac) / math.sqrt(1 + b * b)
            okc = (dc > 0.15) & (dc < 0.9) & (pts_all[idx, 0] > 0.25)
            best, bn = None, 1
            for k in np.where(okc)[0]:
                n_in = int((okc & (np.abs(ac - ac[k]) < 0.03)).sum())
                if n_in > bn:
                    best, bn = k, n_in
            if best is not None:
                sel = okc & (np.abs(ac - ac[best]) < 0.03)
                if np.ptp(pts_all[idx][sel, 0]) < 0.05:        # puncte pe peretele din fata, nu pe cel lateral
                    continue
                a_ = float(np.median(ac[sel]))
                lines[side] = (a_, b, idx[sel], np.ones(int(sel.sum()), bool))
                self._nofit[side] = 0

        # ---- lateral / heading
        meas = {}
        for side, (a, b, idx, mask) in lines.items():
            d = line_distance(a, b)
            nin = int(mask.sum())
            meas[side] = (d, -math.atan(b), nin)
            self._cam_side_d[side] = d
            self._last_cam_side[side] = per.t
        # pereti paraleli? daca pantele difera mult, pastram doar linia mai buna
        if len(meas) == 2:
            if abs(meas["left"][1] - meas["right"][1]) > math.radians(12):
                better = max(meas, key=lambda k: meas[k][2])
                meas = {better: meas[better]}
        self.lane_sides = len(meas)
        self.dbg = dict(psi_f=psi_f, nf=nf, lines={k: (round(v[0], 2), round(math.degrees(-math.atan(v[1])), 1), int(v[3].sum())) for k, v in lines.items()}, nleft=len(left_idx), nright=len(right_idx), nvalid=int(valid.sum()))
        if self.W_fixed:
            self.W = self.W_fixed
            self._kf_camera(per, t_now, (dx, dy, dth), lines, pts_all, psi_f, nf, span_f, xbar_f)
            meas = {}
        elif not meas and psi_f is not None and (t_now - self.lane_t < 1.5 or abs(psi_f + dth - self.psi) < math.radians(25.0)):
            psi_n = psi_f + dth                 # doar peretele din fata (orb lateral, ex. in colt): ramane sursa de unghi
            self.psi = cfg.SMOOTH * psi_n + (1 - cfg.SMOOTH) * self.psi
        if meas and not self.W_fixed:
            tot = sum(m[2] for m in meas.values())
            psi_m = sum(m[1] * m[2] for m in meas.values()) / tot
            if psi_f is not None and abs(psi_f - psi_m) < math.radians(10):
                psi_m = (psi_m * tot + psi_f * 1.5 * nf) / (tot + 1.5 * nf)
            if len(meas) == 2 and self.W_fixed and abs(meas["left"][0] + meas["right"][0] - self.W_fixed) > 0.12:
                better = max(meas, key=lambda k: meas[k][2])      # incoerent => o singura parte
                meas = {better: meas[better]}
                tot = meas[better][2]
                psi_m = meas[better][1]
            if self.W_fixed:
                self.W = self.W_fixed
            if len(meas) == 2:
                dl, dr = meas["left"][0], meas["right"][0]
                W_m = dl + dr
                y_m = (dr - dl) / 2.0
                if not self.W_fixed and cfg.CORRIDOR_W_RANGE[0] <= W_m <= cfg.CORRIDOR_W_RANGE[1] + 0.2:
                    self.W = W_m if self.W is None else 0.7 * self.W + 0.3 * W_m
                if self.auto_width and not self.W_fixed and abs(psi_m) < math.radians(15) and min(meas["left"][2], meas["right"][2]) >= 8:
                    self._w_votes.append(W_m)
                    self._w_votes = self._w_votes[-8:]
                    if len(self._w_votes) >= 6 and max(self._w_votes) - min(self._w_votes) < cfg.W_VOTE_SPREAD:
                        med = float(np.median(self._w_votes))
                        cls = min(cfg.OPEN_WIDTHS, key=lambda c: abs(c - med))
                        if abs(med - cls) <= cfg.W_VOTE_TOL:
                            self.engage_width(cls)
                self.dl, self.dr = dl, dr
            else:
                side = next(iter(meas))
                W0 = self.W if self.W else cfg.CORRIDOR_W_NOMINAL
                d = meas[side][0]
                y_m = (W0 / 2.0 - d) if side == "left" else (d - W0 / 2.0)
                self.dl = d if side == "left" else W0 - d
                self.dr = d if side == "right" else W0 - d
            # propagam masuratoarea de la t_cap pana acum
            ds = math.copysign(math.hypot(dx, dy), dx if abs(dx) > 1e-9 else 1.0)
            psi_n = psi_m + dth
            y_n = y_m + ds * math.sin(psi_m + 0.5 * dth)
            if self.lane_t < -1e8:
                self.y_off, self.psi = y_n, psi_n
            else:
                a_ = cfg.SMOOTH
                # limitam saltul pe cadru (masuratori izolate gresite nu mai rastoarna estimarea)
                gate_y = cfg.GATE_Y + 0.5 * max(0.0, t_now - self.lane_t)
                y_n = self.y_off + max(-gate_y, min(gate_y, y_n - self.y_off))
                psi_n = self.psi + max(-cfg.GATE_PSI, min(cfg.GATE_PSI, psi_n - self.psi))
                self.y_off = a_ * y_n + (1 - a_) * self.y_off
                self.psi = a_ * psi_n + (1 - a_) * self.psi
            self.lane_t = per.t

        # ---- perete in fata (doar din fit-ul peretelui perpendicular pe axa: stalpii si peretii laterali nu conteaza)
        if front_c is not None:
            fx, _ = self._xform(front_c * math.cos(psi_f or 0.0), 0.0, dx, dy, dth)
            self.front_cam = (fx, per.t)

        # ---- deschideri (colturi interioare)
        for side in ("left", "right"):
            self._opening(side, per, Xs, Ys, valid, lines.get(side), t_now, (dx, dy, dth))

        # ---- coltul din intersectia liniilor colorate
        self._line_corner(per, t_now, (dx, dy, dth), sc)

        # ---- stalpi / markere
        if self.use_pillars:
            self._update_tracks(self.pillars, per.pillars, per, t_now, (dx, dy, dth), sc)
        self._update_tracks(self.markers, per.markers, per, t_now, (dx, dy, dth), sc)
        for c in per.line_events:
            self.last_line[c] = t_now
            self._line_events.append(c)


    # ------------------------------------------------------------------ filtru Kalman (Obstacle, W cunoscut)
    def _kf_scalar(self, i, z, R, gate=3.0):
        """Actualizare scalara a starii i (0=y, 1=psi). Intoarce True daca masuratoarea a fost acceptata."""
        x = self.y_off if i == 0 else self.psi
        S = self.P[i, i] + R
        innov = z - x
        if innov * innov > gate * gate * S:
            return False
        K = self.P[:, i] / S
        if i == 0:
            self.y_off += K[0] * innov
            self.psi += K[1] * innov
        else:
            self.y_off += K[0] * innov
            self.psi += K[1] * innov
        H = np.zeros((1, 2))
        H[0, i] = 1.0
        self.P = (np.eye(2) - np.outer(K, H[0])) @ self.P
        self.P = 0.5 * (self.P + self.P.T)
        return True

    def _kf_camera(self, per, t_now, delta, lines, pts_all, psi_f, nf, span_f, xbar_f):
        dx, dy, dth = delta
        ds = math.copysign(math.hypot(dx, dy), dx if abs(dx) > 1e-9 else 1.0)
        W = self.W_fixed
        items = []                 # (tip, valoare_la_t_cap, sigma)
        sides = {}
        for side, (a, b, idx, mask) in lines.items():
            inl = idx[mask]
            n = len(inl)
            if n < 4:
                continue
            X = pts_all[inl, 0]
            span = max(float(np.ptp(X)), 0.08)
            xb = float(X.mean())
            sp = 0.012 + 0.012 * xb * xb                      # zgomot punct (cuantizare pixeli creste cu distanta)
            s_slope = max(math.radians(1.5), sp * math.sqrt(12.0) / (span * math.sqrt(n)))
            s_a = math.sqrt(sp * sp / n + (xb * s_slope) ** 2 + 0.02 ** 2)
            d = line_distance(a, b)
            sides[side] = (d, -math.atan(b), s_slope, s_a, n)
            self._cam_side_d[side] = d
            self._last_cam_side[side] = per.t
        if self.outer_only:
            if len(sides) == 2 and min(sides["left"][4], sides["right"][4]) >= 8 and abs(sides["left"][1] + sides["right"][1]) < math.radians(30) \
                    and abs(0.5 * (sides["left"][1] + sides["right"][1])) < math.radians(15):
                self._w_votes.append(sides["left"][0] + sides["right"][0])
                self._w_votes = self._w_votes[-8:]
                if len(self._w_votes) >= cfg.W_VOTE_N and max(self._w_votes) - min(self._w_votes) < cfg.W_VOTE_SPREAD:
                    med = float(np.median(self._w_votes))
                    cls = min(cfg.OPEN_WIDTHS, key=lambda c: abs(c - med))
                    if abs(med - cls) <= cfg.W_VOTE_TOL:
                        keep = self.outer_pref
                        self.engage_width(cls)
                        W = cls
                        self.outer_pref = keep
            if self.outer_only:
                sides = {k: v for k, v in sides.items() if k == self.outer_only}
        if self.auto_width and not self.outer_only and len(sides) == 2 and sides["left"][4] >= 8 and sides["right"][4] >= 8:
            if abs(sides["left"][0] + sides["right"][0] - W) > 0.20:
                self.kf_incons += 1
                if self.kf_incons >= cfg.W_RELEASE_N:
                    self.release_width()
                    return
            elif abs(sides["left"][0] + sides["right"][0] - W) < 0.10:
                self.kf_incons = 0
        if len(sides) == 2 and abs(sides["left"][0] + sides["right"][0] - W) > 0.14:
            worse = max(sides, key=lambda k: sides[k][3])      # incoerent cu latimea: pastram linia mai precisa
            del sides[worse]
        self.lane_sides = len(sides)
        for side, (d, psi_l, s_slope, s_a, n) in sides.items():
            y_m = (W / 2.0 - d) if side == "left" else (d - W / 2.0)
            items.append(("psi", psi_l, s_slope))
            items.append(("y", y_m, s_a, psi_l))
        if psi_f is not None and span_f > 0.2:
            sp = 0.012 + 0.012 * xbar_f * xbar_f
            items.append(("psi", psi_f, max(math.radians(1.5), sp * math.sqrt(12.0) / (span_f * math.sqrt(max(nf, 1))))))
        if not items:
            return
        ok_any = False
        # intai psi (ca sa folosim psi cat mai bun pentru propagarea y), apoi y
        items.sort(key=lambda it: 0 if it[0] == "psi" else 1)
        for it in items:
            if it[0] == "psi":
                z = it[1] + dth
                R = it[2] ** 2
                if self._kf_fresh:
                    self.psi = z
                    self.P[1, 1] = R
                    self.P[0, 1] = self.P[1, 0] = 0.0
                    ok = True
                else:
                    ok = self._kf_scalar(1, z, R)
            else:
                y_m, psi_l = it[1], it[3]
                z = y_m + ds * math.sin(psi_l + 0.5 * dth)
                R = it[2] ** 2
                if self._kf_fresh:
                    self.y_off = z
                    self.P[0, 0] = R
                    self.P[0, 1] = self.P[1, 0] = 0.0
                    ok = True
                else:
                    ok = self._kf_scalar(0, z, R)
            ok_any = ok_any or ok
            if not ok:
                self._kf_rej += 1
                self.P += np.diag([2e-4, 1.5e-3])             # dezacord persistent => relaxam ca sa ne putem reface
        if ok_any:
            self._kf_fresh = False
            self._kf_rej = 0
            self.lane_t = per.t
        self.dl = W / 2.0 - self.y_off
        self.dr = W / 2.0 + self.y_off

    # ------------------------------------------------------------------ colturi
    def _opening(self, side, per, Xs, Ys, valid, line, t_now, delta):
        sign = 1.0 if side == "left" else -1.0
        az = per.az * sign                      # pozitiv spre partea respectiva
        st = per.state
        found = None
        if line is not None:
            a, b, idx, mask = line
            sb = np.where(az > 1.0)[0]
            order = sb[np.argsort(-az[sb])]     # de la marginea campului vizual spre centru
            cls = []
            for j in order:
                if st[j] == ST_OCCLUDED:
                    cls.append("o")
                elif st[j] == ST_NONE:
                    cls.append("n")
                else:
                    diff = sign * (Ys[j] - (a + b * Xs[j]))
                    cls.append("w" if abs(diff) <= 0.045 else ("b" if diff > cfg.OPEN_DY else "c"))
            # prima rulare de perete (>=2 coloane) urmata de >=2 coloane "dincolo"
            i = 0
            n = len(cls)
            while i < n and cls[i] in "no":
                i += 1
            nw = 0
            jw = None
            while i < n and cls[i] in "wo":
                if cls[i] == "w":
                    nw += 1
                    jw = i
                i += 1
            if nw >= 2 and i < n:
                nb = 0
                jb = None
                k = i
                while k < n and k < i + 5:
                    if cls[k] in "bn":
                        nb += 1
                        jb = k if jb is None else jb
                    elif cls[k] == "c":
                        nb -= 1
                    k += 1
                if nb >= 2 and jb is not None:
                    alpha = sign * math.radians(0.5 * (az[order[jw]] + az[order[jb]]))
                    H = cfg.REAR_TO_HEAD
                    den = math.sin(alpha) - b * math.cos(alpha)
                    if abs(den) > 1e-3:
                        sdist = (a + b * H) / den
                        if sdist > 0:
                            found = (H + sdist * math.cos(alpha), sdist * math.sin(alpha))
        if found is not None:
            dx, dy, dth = delta
            Xc, Yc = self._xform(found[0], found[1], dx, dy, dth)
            cur = self.corner[side]
            if cur is None or cur.src == "line":
                self.corner[side] = Track(Xc, Yc, "corner_" + side, t_now)
            else:
                # masuratoarea e cea mai buna cand coltul e aproape de marginea campului vizual
                beta = 0.6 if Xc < 1.4 else 0.35
                cur.X = (1 - beta) * cur.X + beta * Xc
                cur.Y = (1 - beta) * cur.Y + beta * Yc
                cur.n += 1
                cur.t_seen = t_now
            self.open_vis[side] = True
            self.open_t[side] = t_now
        else:
            # perete interior absent complet (colt deja foarte aproape / depasit)?
            n_wall = int(((az > 1.0) & valid).sum())
            had = self.corner[side] is not None
            if had and n_wall < 3:
                self.open_vis[side] = True
                self.open_t[side] = t_now
            elif line is not None and not had:
                self.open_vis[side] = False
        # coltul vechi (nevazut) expira
        c = self.corner[side]
        if c is not None and (c.X < -0.9 or (t_now - c.t_seen > 4.0 and c.X > 1.0)):
            self.corner[side] = None
            self.open_vis[side] = False

    def engage_width(self, W):
        """Latime clasificata (0.6 / 1.0): filtru Kalman cu ambii pereti."""
        self.W_fixed = W
        self.W = W
        self.outer_only = None
        self._kf_fresh = False
        self.kf_incons = 0
        self._w_votes = []

    def _enter_outer(self):
        self.outer_only = self.outer_pref
        self.W_fixed = cfg.OUTER_W
        self.W = cfg.OUTER_W
        self._w_votes = []
        self.kf_incons = 0

    def set_outer(self, side):
        """Open: dupa ce stim sensul, tinem masina la OUTER_W/2 de peretele exterior (nu mai depindem de latimea culoarului)
        pana cand clasificam latimea (0.6/1.0) din ambii pereti."""
        if self.outer_pref == side:
            return
        self.outer_pref = side
        self._enter_outer()
        self.P = np.diag([0.10 ** 2, 0.25 ** 2])
        self._kf_fresh = True

    def release_width(self):
        if self.outer_pref:
            self._enter_outer()
            return
        self.W_fixed = None
        self.W = None
        self._w_votes = []
        self.kf_incons = 0

    def reset_lane(self, psi=0.0, y_off=0.0, t=None):
        """Dupa un viraj: culoarul s-a schimbat; asteptam o masuratoare noua din camera."""
        if self.outer_pref:
            self._enter_outer()
        elif self.auto_width:
            self.release_width()
        self.psi, self.y_off = psi, y_off
        self.lane_t = -1e9 if t is None else t          # t dat => avem un prior bun: masuratorile se gateaza
        if t is None:
            self._kf_fresh = True
            self.P = np.diag([0.25 ** 2, 0.5 ** 2])
        else:
            self._kf_fresh = False
            self.P = np.diag([0.06 ** 2, 0.12 ** 2])
        self.lane_sides = 0
        self.dl = self.dr = None
        self.front_cam = self.front_sonar = self.obs_sonar = None
        self._nofit = {"left": 0, "right": 0}
        self._cam_side_d = {"left": None, "right": None}
        self.clear_corners()

    def _line_corner(self, per, t_now, delta, sc):
        """Liniile portocalie si albastre pornesc din coltul interior: intersectia lor = coltul."""
        o, b = per.lines.get("orange"), per.lines.get("blue")
        if not o or not b or o.get("P1") is None or b.get("P1") is None:
            return
        H = cfg.REAR_TO_HEAD

        def sc_pt(p):
            return np.array([H + (p[0] - H) * sc, p[1] * sc])
        po1, po2, pb1, pb2 = sc_pt(o["P1"]), sc_pt(o["P2"]), sc_pt(b["P1"]), sc_pt(b["P2"])
        do, db = po2 - po1, pb2 - pb1
        no, nb = np.linalg.norm(do), np.linalg.norm(db)
        if no < 1e-6 or nb < 1e-6:
            return
        do, db = do / no, db / nb
        ang = math.degrees(math.acos(min(1.0, abs(float(do @ db)))))
        if not (12.0 <= ang <= 55.0):
            return
        A = np.array([[do[0], -db[0]], [do[1], -db[1]]])
        try:
            su, sv = np.linalg.solve(A, pb1 - po1)
        except np.linalg.LinAlgError:
            return
        pt = po1 + su * do
        Xc, Yc = float(pt[0]), float(pt[1])
        if not (-0.4 < Xc < 3.0 and 0.12 < abs(Yc) < 0.95):
            return
        side = "left" if Yc > 0 else "right"
        dx, dy, dth = delta
        Xc, Yc = self._xform(Xc, Yc, dx, dy, dth)
        cur = self.corner[side]
        if cur is None:
            tr = Track(Xc, Yc, "corner_" + side, t_now)
            tr.src = "line"
            self.corner[side] = tr
        elif cur.src == "line":
            cur.X = 0.6 * cur.X + 0.4 * Xc
            cur.Y = 0.6 * cur.Y + 0.4 * Yc
            cur.n += 1
            cur.t_seen = t_now
        self.open_vis[side] = True
        self.open_t[side] = t_now

    def clear_corners(self):
        self.corner = {"left": None, "right": None}
        self.open_vis = {"left": False, "right": False}

    # ------------------------------------------------------------------ obiecte urmarite
    def _update_tracks(self, store, blobs, per, t_now, delta, sc):
        dx, dy, dth = delta
        H = cfg.REAR_TO_HEAD
        for b in blobs:
            X = H + (b.X - H) * sc
            Y = b.Y * sc
            X, Y = self._xform(X, Y, dx, dy, dth)
            best, bd = None, 0.28
            for tr in store:
                if tr.color != b.color:
                    continue
                d = math.hypot(tr.X - X, tr.Y - Y)
                if d < bd:
                    best, bd = tr, d
            if best is None:
                store.append(Track(X, Y, b.color, t_now, b.area))
            else:
                w = 0.6 if X < 1.0 else 0.4
                best.X = (1 - w) * best.X + w * X
                best.Y = (1 - w) * best.Y + w * Y
                best.n += 1
                best.t_seen = t_now
                best.area = b.area
        # dedupe: doua piste de aceeasi culoare foarte apropiate => una singura
        i = 0
        while i < len(store):
            j = i + 1
            while j < len(store):
                a, b = store[i], store[j]
                if a.color == b.color and math.hypot(a.X - b.X, a.Y - b.Y) < 0.22:
                    keep_a = a.n >= b.n
                    if keep_a:
                        a.t_seen = max(a.t_seen, b.t_seen)
                        del store[j]
                        continue
                    b.t_seen = max(a.t_seen, b.t_seen)
                    store[i] = b
                    del store[j]
                    a = b
                j += 1
            i += 1
        # dovada negativa: un obiect care ar trebui sa fie in campul vizual si nu mai e vazut dispare
        for tr in list(store):
            if 0.45 < tr.X < 1.9 and abs(math.degrees(math.atan2(tr.Y, max(tr.X - cfg.REAR_TO_HEAD, 0.05))) - per.pan) < 22 \
                    and t_now - tr.t_seen > 0.9:
                store.remove(tr)
        # curatenie
        keep = []
        for tr in store:
            if tr.X < -cfg.PILLAR_FORGET_BEHIND - 0.45:
                continue
            if t_now - tr.t_seen > 5.0:
                continue
            if tr.n < 2 and t_now - tr.t_seen > 0.5:
                continue
            keep.append(tr)
        store[:] = keep

    # ------------------------------------------------------------------ ultrasonic
    def ingest_sonar(self, r, pan_deg, t):
        """r: distanta (m) sau None. Capul trebuie sa fie stabilizat la pan_deg."""
        H = cfg.REAR_TO_HEAD
        if abs(pan_deg) < 5.0:
            if r is None or r > cfg.SONAR_MAX:
                self.obs_sonar = None
                self.front_sonar = None
                return
            Xs = H + r * math.cos(math.radians(pan_deg))
            self.front_sonar = (Xs, t)
            self.obs_sonar = (Xs, t)
            return
        if abs(abs(pan_deg) - cfg.PAN_PEEK_DEG) > 8.0 or r is None:
            return
        side = "left" if pan_deg > 0 else "right"
        P = math.radians(abs(pan_deg))
        psi = self.psi
        if side == "left":
            d_head = r * math.sin(P + psi)
            d_origin = d_head + H * math.sin(psi)
        else:
            d_head = r * math.sin(P - psi)
            d_origin = d_head - H * math.sin(psi)
        if d_origin <= 0.03 or d_origin > 1.6:
            return
        self.side_sonar[side] = (d_origin, t)
        cam_d = self._cam_side_d[side]
        override = False
        if cam_d is not None and t - self._last_cam_side[side] < 1.0 and abs(psi) < math.radians(20):
            if abs(d_origin - cam_d) > cfg.SONAR_OVERRIDE:
                self._cam_bad[side] = t
                override = True
            elif t - self._cam_bad[side] < cfg.CAM_BAD_HOLD and abs(d_origin - cam_d) < 0.5 * cfg.SONAR_OVERRIDE:
                self._cam_bad[side] = -1e9
        elif t - self._cam_bad[side] < cfg.CAM_BAD_HOLD:
            override = True
        # invatare scara camera
        cam_d = self._cam_side_d[side]
        if (cam_d is not None and t - self._last_cam_side[side] < 1.5 and cam_d > 0.15
                and abs(psi) < math.radians(20)):
            ratio = d_origin / cam_d
            if 0.6 < ratio < 1.6:
                self.scale = float(np.clip(self.scale * (1.0 + cfg.SCALE_ALPHA * (ratio - 1.0)), 0.7, 1.4))
        # daca vederea camerei lipseste, sonarul corecteaza pozitia laterala
        if t - self.lane_t > 0.6 or override:
            other = "right" if side == "left" else "left"
            o = self.side_sonar[other]
            W = self.W if self.W else cfg.CORRIDOR_W_NOMINAL
            if o is not None and t - o[1] < 2.5 and cfg.CORRIDOR_W_RANGE[0] < d_origin + o[0] < cfg.CORRIDOR_W_RANGE[1] + 0.2:
                W = d_origin + o[0]
                self.W = W
            y = (W / 2.0 - d_origin) if side == "left" else (d_origin - W / 2.0)
            self.y_off = 0.5 * self.y_off + 0.5 * y
            # unghiul din ultrasonic: doua masuratori pe aceeasi parte la distanta parcursa cunoscuta (peretele e drept)
            prev = self._sd_hist[side]
            if prev is not None:
                ds_ = self._path - prev[1]
                if 0.12 <= ds_ <= 1.0:
                    dd = d_origin - prev[0]
                    ps = math.atan(-dd / ds_) if side == "left" else math.atan(dd / ds_)
                    ps = max(-math.radians(30), min(math.radians(30), ps))
                    self.psi += 0.5 * (ps - self.psi)
            if prev is None or self._path - prev[1] >= 0.12:
                self._sd_hist[side] = (d_origin, self._path)

    # ------------------------------------------------------------------ rezultat
    def snapshot(self, t, head_free=True):
        w = World(t=t)
        age = t - self.lane_t
        w.lane_age = age
        w.y_off, w.psi, w.W = self.y_off, self.psi, self.W
        w.dl, w.dr = self.dl, self.dr
        w.lane_sides = self.lane_sides
        # perete in fata: din camera (fit), rafinat cu ultrasonicul cand sunt de acord; front_obs = orice obstacol
        fc = self.front_cam if self.front_cam and t - self.front_cam[1] < 0.6 else None
        fs = self.front_sonar if self.front_sonar and t - self.front_sonar[1] < 0.5 else None
        if fs is not None:
            w.front_obs = fs[0]
            w.front_age = t - fs[1]
        fv = self.front_sonar if self.front_sonar and t - self.front_sonar[1] < 1.0 else None   # veto: citire putin mai veche (compensata cu odometria)
        if fc is not None and fv is not None and abs(self.psi) < math.radians(25) and fv[0] - fc[0] > 0.30:
            # ultrasonicul (drept inainte) vede mult mai departe decat "peretele" din camera => nu e perete (stalp, picior, obiect colorat)
            self.front_veto = t
            fc = None
        if fc is not None:
            w.front = fc[0]
            if fs is None:
                w.front_age = t - fc[1]
        if fs is not None and abs(self.psi) < math.radians(25) and (fc is None or fs[0] < fc[0] + 0.30):
            w.front = fs[0]                     # ultrasonicul e precis la orice distanta; camera doar de aproape (CAM_MAX_X)
        w.corner = dict(self.corner)
        w.open_vis = dict(self.open_vis)
        w.near = dict(self.near)
        w.pillars = [p for p in self.pillars if p.n >= 2]
        w.markers = [m for m in self.markers if m.n >= 2]
        w.line_events = list(self._line_events)
        self._line_events = []
        w.last_line = dict(self.last_line)
        w.scale = self.scale
        w.cam_ok = self.cam_ok
        w.wall_pts = self.wall_pts
        w.sonar_side = dict(self.side_sonar)
        w.head_free = head_free
        return w

