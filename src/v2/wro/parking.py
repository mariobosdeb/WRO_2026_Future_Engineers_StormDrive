"""Proba de parcare (separata de Obstacle, fara stalpi).

Locul (regulament WRO 2026, Fig. 4 / 8d): in sectiunea de start, langa peretele exterior, 20 cm latime, lungime
PARK_LOT_LEN = 1.5 x lungimea masinii; elementul magenta de la capatul sectiunii (in sens antiorar) e lipit de linia sectiunii.
In cadrul global al filtrului de particule (masina merge spre +x in sectiunea de start):
  antiorar: perete exterior y=0, locul la capatul de iesire  x in [2 - 0.02 - L, 2 - 0.02]
  orar:     perete exterior y=3, locul la capatul de intrare x in [1 + 0.02, 1 + 0.02 + L]

Fluxul: start + aflarea directiei (ca la Obstacle), apoi o cale calculata geometric: drept (inainte/inapoi) pana la punctul
de plecare, apoi S cu marsarierul in loc. Cu raza ~0.43 m un loc de 1.5 x lungime nu permite intrarea completa dintr-o
singura manevra (iar ~24 de manevre cu precizie de 1 cm nu sunt realiste fara encodere): tinta este parcarea PARTIALA
(7 puncte), cu spatele adanc in mijlocul locului si cea mai mare rezerva fata de elementele magenta.
"""
import math
import time

import numpy as np

from . import config as cfg
from .pathdrive import PathDriver, Tracker, _wrap

TH = 0.02                 # grosimea elementului magenta
DEPTH = 0.20              # latimea locului (adancimea elementelor)
SPD = 20.0
SIDE_PAN = 90.0           # privirea laterala, perpendicular pe perete: ultrasonicul da cel mai scurt ecou din con = distanta exacta
LOOK_HOLD = 0.5           # in manevra: cat sta capul pe fiecare directie dupa ce a ajuns [s]


def lot_lane(direction):
    """Intervalul liber al locului pe axa x (cadrul global)."""
    L = cfg.PARK_LOT_LEN
    return (2.0 - TH - L, 2.0 - TH) if direction > 0 else (1.0 + TH, 1.0 + TH + L)


def _to_global(direction, s, w, phi):
    """Cadrul culoarului (s inainte, w distanta de la peretele exterior, phi spre interior) -> global."""
    return (s, w, phi) if direction > 0 else (s, 3.0 - w, -phi)


def _footprint(s, w, phi, m=0.0):
    c, sn = math.cos(phi), math.sin(phi)
    hw = cfg.CAR_WIDTH / 2 + m
    return [(s + c * X - sn * Y, w + sn * X + c * Y)
            for X, Y in ((cfg.REAR_TO_FRONT + m, hw), (cfg.REAR_TO_FRONT + m, -hw), (-cfg.REAR_TO_BACK - m, -hw), (-cfg.REAR_TO_BACK - m, hw))]


def _overlap(poly, rect):
    """SAT: poligonul convex al masinii fata de dreptunghiul aliniat (x0,y0,x1,y1)."""
    x0, y0, x1, y1 = rect
    R = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    axes = [(1.0, 0.0), (0.0, 1.0)]
    for k in range(2):
        ex, ey = poly[k + 1][0] - poly[k][0], poly[k + 1][1] - poly[k][1]
        axes.append((-ey, ex))
    for ax, ay in axes:
        p = [q[0] * ax + q[1] * ay for q in poly]
        r = [q[0] * ax + q[1] * ay for q in R]
        if max(p) < min(r) or max(r) < min(p):
            return False
    return True


def _clear(path, direction, m):
    """Calea (in cadrul culoarului) nu atinge elementele magenta (marja m), peretele exterior / interior si marginile terenului."""
    a, b = lot_lane(direction)
    marks = [(b, -1.0, b + TH, DEPTH), (a - TH, -1.0, a, DEPTH)]
    for s, w, phi, g in path:
        poly = _footprint(s, w, phi)
        if any(_overlap(_footprint(s, w, phi, m), r) for r in marks):
            return False
        if any(q[1] < 0.01 or q[0] < 0.01 or q[0] > 2.99 for q in poly):        # perete exterior / capetele terenului
            return False
        if _overlap(poly, (1.0, 1.0, 2.0, 2.0)):                                # peretele interior (w = 1)
            return False
    return True


def _arc(p0, kap, length, gear, h=0.02):
    """Arc de curbura constanta in cadrul culoarului (kap > 0 = spre interior la mers inainte)."""
    s, w, phi = p0
    out = []
    n = max(1, int(math.ceil(abs(length) / h)))
    sg = -1.0 if gear else 1.0
    d = abs(length) / n
    for _ in range(n):
        dphi = sg * kap * d
        tm = phi + 0.5 * dphi
        s += sg * d * math.cos(tm)
        w += sg * d * math.sin(tm)
        phi += dphi
        out.append((s, w, phi, gear))
    return out


def _curve(p0, R, theta, frac):
    """Marsarier: arcul 1 (spatele spre perete, botul spre interior) pana la directia theta, apoi arcul 2 inapoi cu frac*theta."""
    a1 = _arc(p0, -1.0 / R, R * max(0.0, theta - p0[2]), 1)
    p1 = a1[-1][:3] if a1 else p0
    a2 = _arc(p1, 1.0 / R, R * frac * max(0.0, p1[2]), 1) if frac > 0 else []
    return a1 + a2


def _inset(direction, s, w, phi):
    """Cat de adanc e in loc cel mai adanc punct al masinii [m] (negativ = masina e complet afara)."""
    a, b = lot_lane(direction)
    best = -1.0
    for X in np.linspace(-cfg.REAR_TO_BACK, cfg.REAR_TO_FRONT, 7):
        for Y in np.linspace(-cfg.CAR_WIDTH / 2, cfg.CAR_WIDTH / 2, 5):
            ps = s + math.cos(phi) * X - math.sin(phi) * Y
            pw = w + math.sin(phi) * X + math.cos(phi) * Y
            best = max(best, min(ps - a, b - ps, DEPTH - pw))
    return best


MARGINS = (0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02)


def plan_park(direction, pose, rmin):
    """Calea de parcare din pozitia curenta (global): drept pana la punctul de plecare, apoi marsarier in loc.
    Alege manevra cu cea mai mare rezerva = min(distanta fata de elementele magenta, cat de adanc intra masina in loc), ca
    o eroare de pozitie de cativa cm sa nu duca nici la atingere, nici la masina complet afara (parcare partiala = 7 puncte).
    Intoarce (cale Nx4 global, rezerva [m], raza) sau (None, None, None)."""
    x, y, th = pose
    w0 = y if direction > 0 else 3.0 - y
    phi0 = th if direction > 0 else -th
    a, b = lot_lane(direction)
    best = None
    for R in (1.10 * rmin, 1.3 * rmin):
        for theta in np.radians(np.arange(10.0, 61.0, 5.0)):
            for frac in (0.0, 0.3, 0.6, 1.0):
                curve = _curve((0.0, w0, phi0), R, theta, frac)
                if not curve:
                    continue
                se, we, pe = curve[-1][:3]
                for st in np.linspace(a + 0.02, b - 0.06, 6):      # unde ajunge axa spate pe lungimea locului
                    ins = _inset(direction, st, we, pe)
                    if ins <= 0.02 or (best is not None and ins <= best[0]):
                        continue
                    s_start = st - se
                    g = 1 if s_start < x else 0
                    lead = _arc((x, w0, phi0), 0.0, abs(s_start - x) / max(0.5, math.cos(phi0)), g) if abs(s_start - x) > 0.01 else []
                    p_start = lead[-1][:3] if lead else (x, w0, phi0)
                    path = [(x, w0, phi0, g)] + lead + _curve(p_start, R, theta, frac)
                    for m in MARGINS:
                        if best is not None and min(m, ins) <= best[0]:
                            break
                        if _clear(path, direction, m):
                            best = (min(m, ins), path, R)
                            break
    if best is None:
        return None, None, None
    gp = np.array([(*_to_global(direction, s, w, phi), gear) for s, w, phi, gear in best[1]])
    return gp, best[0], best[2]


class ParkDriver(PathDriver):
    """Start + directie (ca la Obstacle, fara stalpi), apoi parcare paralela."""

    def _look(self, pan, dur):
        """Masina oprita, capul la `pan` [grade]; intoarce mediana citirilor ultrasonicului (m) sau None."""
        b = self.b
        b.base_pan = pan
        b.set_pan(pan)
        t_end = b.head_ready_t + dur
        rs = []
        while self.hal.now() < t_end:
            b.command_now(0.0, 0.0)
            self._sense()
            ev = b.sonar_event
            if ev is not None and ev[0] is not None and abs(ev[1] - pan) < 1.0 and ev[2] >= b.head_ready_t:
                rs.append(ev[0])
            b.wait_period()
        return float(np.median(rs)) if len(rs) >= 3 else None

    def _follow(self, path, t_start, max_time, side):
        """Urmareste calea (inainte/inapoi) pana la capat; capul alterneaza drept / lateral (ultrasonic pentru filtru)."""
        hal, b = self.hal, self.b
        trk = Tracker()
        trk.set(path)
        gear = int(path[1, 3])
        waiting = 0.0
        while True:
            if max_time is not None and hal.now() - t_start > max_time:
                self.reason = "timp"
                break
            if hal.now() >= b.head_ready_t + LOOK_HOLD:
                b.base_pan = 0.0 if b.base_pan != 0.0 else SIDE_PAN * side
                b.set_pan(b.base_pan)
            x, y, th = self._sense()
            servo, g, rem, err = trk.step(x, y, th)
            last = all(int(path[k, 3]) == g for k in range(trk.i + 1, len(path)))
            if g != gear:
                b.command_now(servo, 0.0)
                if abs(b.v_est) < 0.02:
                    waiting += 1.0 / cfg.LOOP_HZ
                    if waiting >= 0.25:
                        gear, waiting = g, 0.0
                b.wait_period()
                continue
            if last and rem < 0.015:
                break
            spd = SPD if rem > 0.15 else max(float(cfg.SPEED_MIN), SPD * rem / 0.15)
            b.command(servo, spd if g == 0 else -spd)
            self.trace.append((round(hal.now(), 2), self.state, round(err, 3), round(math.degrees(th), 1), round(servo, 1)))
            b.wait_period()
        b.command_now(0.0, 0.0)

    def _fix_pose(self, side):
        """Pozitia masinii direct din ultrasonic, inainte de manevra: drept inainte = peretele exterior de la capatul coltului
        urmator (x = 3), perpendicular spre peretele exterior = distanta laterala. Filtrul de particule se muta acolo."""
        x, y, th = self.pose
        phi = th if self.dir > 0 else -th
        dx = dy = 0.0
        rf = self._look(0.0, 1.0)
        if rf is not None and abs(phi) < math.radians(10):
            xm = 3.0 - rf - cfg.REAR_TO_HEAD * math.cos(phi)
            if abs(xm - x) < 0.7:
                dx = xm - x
        rs = self._look(SIDE_PAN * side, 0.8)
        if rs is not None and abs(phi) < math.radians(10) and rs < 0.9:
            wm = rs - cfg.REAR_TO_HEAD * math.sin(phi)
            w = y if self.dir > 0 else 3.0 - y
            if abs(wm - w) < 0.3:
                dy = (wm - w) * (1.0 if self.dir > 0 else -1.0)
        self.log("parcare: ultrasonic fata=%s lateral=%s => corectie pozitie dx=%+.2f dy=%+.2f m" % (
            "--" if rf is None else "%.2f" % rf, "--" if rs is None else "%.2f" % rs, dx, dy))
        self.pf.x += dx
        self.pf.y += dy
        self.pose = (x + dx, y + dy, th)

    def run(self, max_time=None):
        hal = self.hal
        t_start = hal.now()
        self.start()
        b = self.b
        if getattr(self, "aborted", False):
            self.reason = "nu e pe pista"
            return self.reason
        self._discover(t_start)
        b.command_now(0.0, 0.0)
        # In faza de start capul priveste in diagonala, iar filtrul ia ultrasonicul doar drept/lateral: pozitia pe lungimea
        # culoarului ramane nesigura (in simulator, eroare pana la 0.5 m). Ultrasonicul drept inainte vede peretele de la capatul
        # urmatorului colt (x), lateral peretele exterior (distanta fata de el).
        side = -1.0 if self.dir > 0 else 1.0                # capul spre peretele exterior (pan pozitiv = stanga)
        self._fix_pose(side)
        rmin = 1.0 / self._lat[self.dir].kmax
        a, bb = lot_lane(self.dir)
        self.state = "PARK"
        for attempt in range(2):
            t0 = time.time()
            path, rez, R = plan_park(self.dir, self.pose, rmin)
            self.log("parcare: loc x=[%.2f, %.2f], masina (%.2f,%.2f,%.0f)" % (a, bb, self.pose[0], self.pose[1], math.degrees(self.pose[2])))
            if path is None:
                self.reason = "parcare imposibila"
                self.log("parcare: nu exista manevra fara atingerea elementelor magenta")
                return self.reason
            self.log("parcare: manevra inapoi, raza %.2f m, rezerva %.1f cm (calculata in %.1f s)" % (R, 100 * rez, time.time() - t0))
            lead = int(np.argmax(path[1:, 2] != path[0, 2])) + 1 if np.any(path[1:, 2] != path[0, 2]) else len(path)
            if attempt == 0 and lead > 10:                 # drumul drept pana la punctul de plecare e lung: oprire, masurare, recalculare
                self._follow(path[:lead], t_start, max_time, side)
                if self.reason:
                    return self.reason
                self._fix_pose(side)
                continue
            self._follow(path, t_start, max_time, side)
            break
        b.command_now(0.0, 0.0)
        for _ in range(5):
            self._sense(); b.wait_period()
        if not self.reason:
            x, y, th = self.pose
            w = y if self.dir > 0 else 3.0 - y
            self.reason = "parcat"
            self.log("parcare: gata, axa spate x=%.2f, %.0f cm de perete, unghi %.0f grade, adancime in loc %.0f cm" % (
                x, 100 * w, math.degrees(th), 100 * _inset(self.dir, x, w, th if self.dir > 0 else -th)))
        self.state = "DONE"
        return self.reason

