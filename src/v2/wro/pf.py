"""Filtru de particule pentru localizarea in cadrul global al terenului Obstacle (pereti cunoscuti).

Cadrul global: terenul [0,3]^2, peretele interior [1,2]^2. Directia de mers e necunoscuta la start, deci fiecare particula
poarta o ipoteza de directie:
   +1 (antiorar): masina porneste in sectiunea de jos [1,2]x[0,1], orientata spre +x (peretele interior in stanga)
   -1 (orar)    : masina porneste in sectiunea de sus  [1,2]x[2,3], orientata spre +x (peretele interior in dreapta)
(terenul e simetric la rotatie cu 180 de grade, deci geometria peretilor e aceeasi; doar regula stalpilor/planul difera).
Masuratori: punctele de baza ale peretilor din camera (cadrul masinii, axa spate) + ultrasonicul frontal.
"""
import math

import numpy as np

S = 3.0
WALLS = np.array([(0, 0, S, 0), (S, 0, S, S), (S, S, 0, S), (0, S, 0, 0),
                  (1, 1, 2, 1), (2, 1, 2, 2), (2, 2, 1, 2), (1, 2, 1, 1)], float)
RES = 0.01


def _corner_lines():
    """Liniile de pe podea (aceeasi geometrie ca in sim.py): din fiecare colt al peretelui interior spre peretele exterior."""
    base = {"orange": (math.cos(math.radians(60)), math.sin(math.radians(60))),
            "blue": (math.cos(math.radians(30)), math.sin(math.radians(30)))}
    out = {"orange": [], "blue": []}
    for k, (px, py) in enumerate([(2.0, 2.0), (2.0, 1.0), (1.0, 1.0), (1.0, 2.0)]):
        for color, (dx, dy) in base.items():
            for _ in range(k):
                dx, dy = dy, -dx
            t = min([(S - px) / dx if dx > 1e-9 else 1e9, -px / dx if dx < -1e-9 else 1e9,
                     (S - py) / dy if dy > 1e-9 else 1e9, -py / dy if dy < -1e-9 else 1e9])
            out[color].append((px, py, px + t * dx, py + t * dy))
    return {c: np.array(v, float) for c, v in out.items()}


LINES = _corner_lines()


def _seg_dist(px, py, segs):
    x0, y0, x1, y1 = segs[:, 0], segs[:, 1], segs[:, 2], segs[:, 3]
    dx, dy = x1 - x0, y1 - y0
    den = dx * dx + dy * dy + 1e-12
    t = np.clip(((px[..., None] - x0) * dx + (py[..., None] - y0) * dy) / den, 0, 1)
    return np.hypot(px[..., None] - (x0 + t * dx), py[..., None] - (y0 + t * dy)).min(axis=-1)


class WallField:
    """Distanta pana la cel mai apropiat perete pe grila de 1 cm (in afara terenului: valoare mare)."""
    _cache = None

    def __init__(self):
        if WallField._cache is None:
            n = int(round(S / RES)) + 1
            xs = np.arange(n) * RES
            gx, gy = np.meshgrid(xs, xs, indexing="ij")
            WallField._cache = _seg_dist(gx, gy, WALLS).astype(np.float32)
        self.D = WallField._cache
        self.n = self.D.shape[0]

    def lookup(self, x, y):
        i = np.clip(np.rint(x / RES).astype(np.int32), 0, self.n - 1)
        j = np.clip(np.rint(y / RES).astype(np.int32), 0, self.n - 1)
        d = self.D[i, j]
        out = (x < -0.05) | (x > S + 0.05) | (y < -0.05) | (y > S + 0.05)
        return np.where(out, 0.6, d)

    def ray(self, ox, oy, th, rmax=2.5):
        """Distanta pana la perete pe raza (pasi de 1 cm, pentru ultrasonic). Vectorizat pe particule."""
        r = np.arange(0.05, rmax, 0.02)
        px = ox[:, None] + r[None, :] * np.cos(th)[:, None]
        py = oy[:, None] + r[None, :] * np.sin(th)[:, None]
        d = self.lookup(px, py)
        hit = d < 0.015
        k = hit.argmax(axis=1)
        any_ = hit.any(axis=1)
        return np.where(any_, r[k], rmax)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


class ParticleFilter:
    def __init__(self, n=320, seed=0, cam_scale_sigma=0.0):
        self.n = n
        self.rng = np.random.default_rng(seed)
        self.wf = WallField()
        self.x = np.zeros(n); self.y = np.zeros(n); self.th = np.zeros(n)
        self.dr = np.ones(n, np.int8)
        self.w = np.ones(n) / n
        self.frames = 0
        self._last_upd = None
        self.freeze_x = 1.3
        self.init_start()

    # ------------------------------------------------------------------
    def init_start(self):
        n = self.n
        h = n // 2
        self.dr[:h] = 1
        self.dr[h:] = -1
        self.x = self.rng.uniform(1.04, 1.96, n)
        y = self.rng.uniform(0.18, 0.82, n)
        self.y = np.where(self.dr > 0, y, 3.0 - y)         # sus: simetric (rotatie 180 grade a pozitiei)
        # la rotatie cu 180 de grade (x,y)->(3-x,3-y), heading +pi; dar in ipoteza orara masina priveste spre +x sus:
        self.y = np.where(self.dr > 0, y, 2.0 + y)
        self.th = self.rng.normal(0.0, math.radians(7.0), n)
        self.w[:] = 1.0 / n

    # ------------------------------------------------------------------
    def predict(self, ds, dth):
        n = self.n
        rng = self.rng
        dsn = ds * (1.0 + rng.normal(0, 0.08, n)) + rng.normal(0, 0.0008 + 0.012 * abs(ds), n)
        dthn = dth * (1.0 + rng.normal(0, 0.22, n)) + rng.normal(0, 0.0025, n)
        tm = self.th + 0.5 * dthn
        self.x += dsn * np.cos(tm)
        self.y += dsn * np.sin(tm)
        self.th = wrap(self.th + dthn)

    # ------------------------------------------------------------------
    def update_points(self, X, Y, delta=(0.0, 0.0, 0.0), temper=0.30, sigma0=0.04, sigma_r=0.035):
        """X, Y: puncte de perete in cadrul masinii DE LA CAPTURA; delta = miscarea masinii (dx,dy,dth) de la captura pana acum."""
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        if len(X) < 4:
            return
        # masina stationara: aceleasi masuratori repetate nu aduc informatie noua (ar face filtrul supraincrezator)
        if self._last_upd is not None:
            mv = math.hypot(self.x.mean() - self._last_upd[0], self.y.mean() - self._last_upd[1])
            if mv < 0.012 and abs(wrap(self.th.mean() - self._last_upd[2])) < 0.01:
                temper *= 0.12
        self._last_upd = (self.x.mean(), self.y.mean(), self.th.mean())
        if len(X) > 28:
            k = np.linspace(0, len(X) - 1, 28).astype(int)
            X, Y = X[k], Y[k]
        dx, dy, dth = delta
        c, s = math.cos(dth), math.sin(dth)
        px = c * (X - dx) + s * (Y - dy)                   # punct in cadrul curent = R(-dth)(p - d)
        py = -s * (X - dx) + c * (Y - dy)
        r = np.hypot(px, py)
        sig = sigma0 + sigma_r * r
        ct, st = np.cos(self.th)[:, None], np.sin(self.th)[:, None]
        gx = self.x[:, None] + ct * px[None, :] - st * py[None, :]
        gy = self.y[:, None] + st * px[None, :] + ct * py[None, :]
        d = self.wf.lookup(gx, gy)
        ll = np.log(0.10 + np.exp(-0.5 * (d / sig[None, :]) ** 2)).sum(axis=1)
        ll = ll * temper + self._impossible()
        self._apply(ll)
        self.frames += 1

    def update_line(self, color, pts, delta=(0.0, 0.0, 0.0), sigma=0.06, temper=0.5):
        """Puncte ale liniei colorate de pe podea (cadrul masinii de la captura): trebuie sa cada pe o linie de aceeasi culoare."""
        if len(pts) < 2:
            return
        P = np.asarray(pts, float)
        dx, dy, dth = delta
        c, s = math.cos(dth), math.sin(dth)
        px = c * (P[:, 0] - dx) + s * (P[:, 1] - dy)
        py = -s * (P[:, 0] - dx) + c * (P[:, 1] - dy)
        ct, st = np.cos(self.th)[:, None], np.sin(self.th)[:, None]
        gx = self.x[:, None] + ct * px[None, :] - st * py[None, :]
        gy = self.y[:, None] + st * px[None, :] + ct * py[None, :]
        d = _seg_dist(gx, gy, LINES[color])
        ll = np.log(0.10 + np.exp(-0.5 * (d / sigma) ** 2)).sum(axis=1)
        self._apply(ll * temper)

    def _impossible(self):
        """Penalizare pentru particule in interiorul peretelui interior sau in afara terenului (masina nu poate fi acolo)."""
        inner = (self.x > 1.0) & (self.x < 2.0) & (self.y > 1.0) & (self.y < 2.0)
        out = (self.x < 0.0) | (self.x > S) | (self.y < 0.0) | (self.y > S)
        near = self.wf.lookup(self.x, self.y) < 0.07          # centrul masinii nu poate fi la <7 cm de perete (latime 18 cm)
        return np.where(inner | out | near, -30.0, 0.0)

    def update_sonar(self, r, pan_deg=0.0, head_fwd=0.15, sigma=0.04):
        """Distanta frontala (ultrasonic pe cap): r in metri."""
        if r is None or r < 0.05 or r > 2.4:
            return
        a = self.th + math.radians(pan_deg)
        ox = self.x + head_fwd * np.cos(self.th)
        oy = self.y + head_fwd * np.sin(self.th)
        e = self.wf.ray(ox, oy, a, rmax=2.5)
        ll = -0.5 * ((e - r) / (sigma + 0.04 * r)) ** 2
        ll = np.maximum(ll, -4.0)
        self._apply(0.5 * ll)

    def _apply(self, ll):
        ll = ll - ll.max()
        w = self.w * np.exp(ll)
        sw = w.sum()
        if not np.isfinite(sw) or sw < 1e-300:
            w = np.ones(self.n)
            sw = self.n
        self.w = w / sw
        if self.freeze_x is not None and float((self.w * self.x).sum()) < self.freeze_x:
            # cele doua ipoteze sunt imagini in oglinda pana se vede capatul peretelui interior: diferentele de masa sunt zgomot
            # (deriva genetica / fluctuatii de potrivire), nu dovezi => le pastram egale
            for h in (1, -1):
                m = self.dr == h
                mh = float(self.w[m].sum())
                if mh > 1e-300:
                    self.w[m] *= 0.5 / mh
            self.w /= self.w.sum()
        neff = 1.0 / float((self.w ** 2).sum())
        if neff < 0.5 * self.n:
            self._resample()

    def _resample(self):
        """Resampling stratificat pe ipoteza de directie: fiecare ipoteza isi pastreaza numarul de particule (altfel una dintre ele
        poate disparea prin simpla deriva genetica, inainte sa existe dovezi), iar masa de probabilitate pe ipoteza se pastreaza."""
        n = self.n
        newx = np.empty(n); newy = np.empty(n); newth = np.empty(n); newdr = np.empty(n, np.int8); neww = np.empty(n)
        pos0 = 0
        for h in (1, -1):
            idx_h = np.flatnonzero(self.dr == h)
            if len(idx_h) == 0:
                continue
            mass = float(self.w[idx_h].sum())
            k = len(idx_h)
            if mass < 1e-300:
                wl = np.ones(k) / k
            else:
                wl = self.w[idx_h] / mass
            pos = (self.rng.random() + np.arange(k)) / k
            sel = idx_h[np.minimum(np.searchsorted(np.cumsum(wl), pos), k - 1)]
            sl = slice(pos0, pos0 + k)
            newx[sl] = self.x[sel] + self.rng.normal(0, 0.006, k)
            newy[sl] = self.y[sel] + self.rng.normal(0, 0.006, k)
            newth[sl] = wrap(self.th[sel] + self.rng.normal(0, 0.006, k))
            newdr[sl] = h
            neww[sl] = max(mass, 1e-12) / k
            # ~6% particule injectate in jurul grupului, mai larg (recuperare dupa deriva odometriei)
            m = max(2, k // 16)
            inj = self.rng.choice(k, size=m, replace=False)
            newx[pos0 + inj] += self.rng.normal(0, 0.12, m)
            newy[pos0 + inj] += self.rng.normal(0, 0.12, m)
            newth[pos0 + inj] = wrap(newth[pos0 + inj] + self.rng.normal(0, 0.12, m))
            pos0 += k
        self.x, self.y, self.th, self.dr = newx[:pos0], newy[:pos0], newth[:pos0], newdr[:pos0]
        w = neww[:pos0]
        self.w = w / w.sum()

    # ------------------------------------------------------------------
    def dir_prob(self):
        return float(self.w[self.dr > 0].sum())

    def estimate(self, direction=None):
        """Pozitie medie (x,y,th) pe ipoteza de directie data (sau cea mai probabila) + abateri standard."""
        if direction is None:
            direction = 1 if self.dir_prob() >= 0.5 else -1
        m = self.dr == direction
        w = self.w * m
        sw = w.sum()
        if sw < 1e-12:
            w = self.w
            sw = 1.0
        w = w / sw
        x = float((w * self.x).sum()); y = float((w * self.y).sum())
        th = math.atan2(float((w * np.sin(self.th)).sum()), float((w * np.cos(self.th)).sum()))
        sx = math.sqrt(float((w * (self.x - x) ** 2).sum()))
        sy = math.sqrt(float((w * (self.y - y) ** 2).sum()))
        sth = math.sqrt(float((w * wrap(self.th - th) ** 2).sum()))
        return (x, y, th), (sx, sy, sth), direction

    def force_direction(self, direction):
        """Directia stiuta din alta sursa (culoarea liniei): particulele ipotezei opuse se oglindesc fata de y=1.5
        (pista e simetrica; CCW: sectiunea de start jos, CW: sus, aceeasi orientare +x)."""
        m = self.dr != direction
        self.y[m] = 3.0 - self.y[m]
        self.th[m] = wrap(-self.th[m])
        self.dr[m] = direction

    def collapse(self, direction):
        """Dupa ce directia e sigura: pastram doar acea ipoteza."""
        m = self.dr == direction
        if m.sum() < 8:
            return
        idx = self.rng.choice(np.flatnonzero(m), size=self.n, p=self.w[m] / self.w[m].sum())
        self.x, self.y, self.th, self.dr = self.x[idx].copy(), self.y[idx].copy(), self.th[idx].copy(), self.dr[idx].copy()
        self.w[:] = 1.0 / self.n

