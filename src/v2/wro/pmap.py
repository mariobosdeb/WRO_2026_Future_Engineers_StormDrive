"""Harta stalpilor in cadrul global: observatii din camera -> clustere -> "lipire" de cea mai apropiata pozitie permisa (seat).

Regulament: stalpii stau doar pe pozitiile (seat) din cele 4 sectiuni drepte: 3 coloane (0, 0.5, 1.0 m pe lungimea sectiunii)
x 2 randuri (0.4 / 0.6 m de peretele interior). Lipirea de seat elimina eroarea de masura (cativa cm) si e decisiva
pentru planificator (diferenta dintre randuri e doar 0.2 m).
"""
import math

import numpy as np

from . import config as cfg

SEATS = []
for _x in (1.0, 1.5, 2.0):
    for _y in (0.4, 0.6):
        SEATS.append((_x, _y, "B"))
    for _y in (2.4, 2.6):
        SEATS.append((_x, _y, "T"))
for _y in (1.0, 1.5, 2.0):
    for _x in (0.4, 0.6):
        SEATS.append((_x, _y, "L"))
    for _x in (2.4, 2.6):
        SEATS.append((_x, _y, "R"))
SEAT_XY = np.array([(s[0], s[1]) for s in SEATS])

# axa de mers (inainte) in fiecare sectiune pentru sens antiorar (+1); pentru orar se inverseaza
_AXIS_CCW = {"B": (1.0, 0.0), "R": (0.0, 1.0), "T": (-1.0, 0.0), "L": (0.0, -1.0)}


def lane_axis(direction, side):
    ax, ay = _AXIS_CCW[side]
    return (ax * direction, ay * direction)


class _Track:
    __slots__ = ("sw", "sx", "sy", "votes", "n", "near", "seat", "t", "first_r", "conf_r", "seq")

    def __init__(self):
        self.sw = 0.0; self.sx = 0.0; self.sy = 0.0
        self.votes = {"red": 0.0, "green": 0.0}
        self.n = 0
        self.near = 0.0                # cea mai mica distanta de observare
        self.seat = None
        self.t = 0.0
        self.first_r = None
        self.conf_r = None
        self.seq = None                # ordinea confirmarii (primul stalp confirmat are seq mic)

    @property
    def pos(self):
        return self.sx / self.sw, self.sy / self.sw


class PillarMap:
    def __init__(self, assoc=0.30, min_obs=3, max_range=2.3):
        self.tracks = []
        self.assoc = assoc
        self.min_obs = min_obs
        self.max_range = max_range
        self.version = 0
        self._sig = None
        self._seq = 0

    def add(self, blobs, pose, sigma_pose=0.03):
        """blobs: lista Blob (color, X, Y in cadrul masinii); pose: (x,y,th) global la captura."""
        x0, y0, th = pose
        c, s = math.cos(th), math.sin(th)
        for b in blobs:
            if b.color not in ("red", "green"):
                continue
            r = math.hypot(b.X, b.Y)
            if r > self.max_range or r < 0.30:              # era 0.45: aproape (cel mai precis) era ignorat
                continue
            W, H = cfg.CAM_SIZE
            if b.u - b.w_px / 2 < 3 or b.u + b.w_px / 2 > W - 3 or b.v_base > H - 4:
                continue                                     # stalp taiat de marginea imaginii: pozitia ar fi gresita
            gx = x0 + c * b.X - s * b.Y
            gy = y0 + s * b.X + c * b.Y
            if not (0.05 < gx < 2.95 and 0.05 < gy < 2.95):
                continue
            if 1.0 - 0.05 < gx < 2.0 + 0.05 and 1.0 - 0.05 < gy < 2.0 + 0.05:
                continue                                     # in interiorul peretelui interior: fals
            # asociere
            best, bd = None, min(self.assoc, 0.08 + 0.06 * r)
            for t in self.tracks:
                tx, ty = t.pos
                d = math.hypot(tx - gx, ty - gy)
                if d < bd:
                    best, bd = t, d
            if best is None:
                best = _Track(); self.tracks.append(best)
            sig = 0.025 + 0.045 * r + sigma_pose
            w = 1.0 / (sig * sig)
            best.sw += w; best.sx += w * gx; best.sy += w * gy
            best.votes[b.color] += w
            best.n += 1
            best.near = r if best.n == 1 else min(best.near, r)
            if best.n == 1:
                best.first_r = r
            if best.n == self.min_obs:
                best.conf_r = r
                best.seq = self._seq; self._seq += 1
        self._resnap()

    def _resnap(self):
        for t in self.tracks:
            if t.n < 1:
                continue
            x, y = t.pos
            d = np.hypot(SEAT_XY[:, 0] - x, SEAT_XY[:, 1] - y)
            k = int(np.argmin(d))
            t.seat = k if d[k] < 0.22 else None
        sig = tuple(sorted((p[0], p[1], p[2]) for p in self.pillars(1)))
        if sig != self._sig:
            self._sig = sig
            self.version += 1

    def confirmed(self, t):
        return t.n >= self.min_obs and t.seat is not None

    def pillars(self, direction):
        """Lista (x, y, col, ax, ay) pentru planificator (col 0 = rosu). O singura intrare per seat (cea cu cea mai multa greutate)."""
        out = {}
        for t in self.tracks:
            if not self.confirmed(t):
                continue
            if t.seat in out and out[t.seat][0] >= t.sw:
                continue
            col = 0 if t.votes["red"] >= t.votes["green"] else 1
            sx, sy, side = SEATS[t.seat]
            ax, ay = lane_axis(direction, side)
            out[t.seat] = (t.sw, (sx, sy, col, ax, ay), t.seq)
        # doi stalpi pe aceeasi coloana (randul interior + exterior, la 0.2 m) = de obicei acelasi stalp vazut de doua ori (eroarea de
        # pozitie pe masina e ~0.2 m), iar rosu+verde acolo nici nu se pot ocoli. Pastram unul: culoarea vazuta prima, pozitia cu
        # cele mai multe observatii.
        col = {}
        for k, (w, p, seq) in out.items():
            sx, sy, side = SEATS[k]
            col.setdefault((side, sx if side in "BT" else sy), []).append((seq, w, p))
        res = []
        for lst in col.values():
            c0 = min(lst, key=lambda e: e[0])[2][2]
            res.append(max((e for e in lst if e[2][2] == c0), key=lambda e: e[1])[2])
        return res

    def n_confirmed(self):
        return sum(1 for t in self.tracks if self.confirmed(t))

