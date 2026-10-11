"""Simulator WRO Future Engineers: teren 3x3 m, cinematica Ackermann, ultrasonic ray-cast,
camera RANDATA (aceeasi imagine pe care o proceseaza codul real) si metrici de scor.

Implementeaza aceeasi interfata ca hardware.RealHAL, deci intreg codul de decizie ruleaza
neschimbat in simulare.  Valorile fizice (viteza, raza de viraj, camera) pot fi perturbate
fata de config ca sa verificam robustetea la calibrare imperfecta.
"""
import math
import random
from dataclasses import dataclass, field

import numpy as np

from . import config as cfg
from .geometry import CameraModel

S = 3.0                     # latura interioara a terenului (m)
WALL_H = 0.10
PILLAR_H = 0.10
BGR = {
    "floor": (238, 238, 238), "wall": (22, 22, 22), "sky": (150, 140, 135),
    "orange": (0, 102, 255), "blue": (255, 51, 0),
    "red": (55, 39, 238), "green": (44, 214, 68), "magenta": (255, 0, 255),
}


@dataclass
class Track:
    widths: dict                       # 'L','R','B','T' latimea culoarului (m)
    direction: int                     # +1 CCW, -1 CW
    start_side: str                    # 'B','R','T','L' sectiunea dreapta de start
    pillars: list = field(default_factory=list)       # (x, y, 'red'|'green')
    markers: list = field(default_factory=list)       # (x0,y0,x1,y1) blocuri magenta
    lot: tuple = None                  # (cx, cy, along, depth) informativ
    ix0: float = 0.0
    ix1: float = 0.0
    iy0: float = 0.0
    iy1: float = 0.0

    def __post_init__(self):
        self.ix0, self.ix1 = self.widths["L"], S - self.widths["R"]
        self.iy0, self.iy1 = self.widths["B"], S - self.widths["T"]

    # segmente de perete (x0,y0,x1,y1)
    def walls(self):
        o = [(0, 0, S, 0), (S, 0, S, S), (S, S, 0, S), (0, S, 0, 0)]
        i = [(self.ix0, self.iy0, self.ix1, self.iy0), (self.ix1, self.iy0, self.ix1, self.iy1),
             (self.ix1, self.iy1, self.ix0, self.iy1), (self.ix0, self.iy1, self.ix0, self.iy0)]
        return o + i

    def corner_lines(self):
        """Linii orange/blue din colturile interioare spre colturile exterioare (rotite CW)."""
        base = {"orange": (math.cos(math.radians(60)), math.sin(math.radians(60))),
                "blue": (math.cos(math.radians(30)), math.sin(math.radians(30)))}
        pts = [(self.ix1, self.iy1), (self.ix1, self.iy0), (self.ix0, self.iy0), (self.ix0, self.iy1)]
        segs = []
        for k, (px, py) in enumerate(pts):
            for color, (dx, dy) in base.items():
                for _ in range(k):                 # rotatie CW 90 grade: (x,y)->(y,-x)
                    dx, dy = dy, -dx
                # lungime pana la peretele exterior
                tmax = 1e9
                if dx > 1e-9:
                    tmax = min(tmax, (S - px) / dx)
                if dx < -1e-9:
                    tmax = min(tmax, (0 - px) / dx)
                if dy > 1e-9:
                    tmax = min(tmax, (S - py) / dy)
                if dy < -1e-9:
                    tmax = min(tmax, (0 - py) / dy)
                segs.append((color, px, py, px + dx * tmax, py + dy * tmax))
        return segs

    def sections(self):
        """Dreptunghiuri ale celor 4 sectiuni drepte: nume -> (x0,y0,x1,y1)."""
        return {"B": (self.ix0, 0, self.ix1, self.iy0), "R": (self.ix1, self.iy0, S, self.iy1),
                "T": (self.ix0, self.iy1, self.ix1, S), "L": (0, self.iy0, self.ix0, self.iy1)}


def lane_axis(track, side):
    """Pentru sectiunea dreapta `side` intoarce (centru_lateral, directia de mers unitar) pentru
    sensul de mers al pistei."""
    d = track.direction
    # CCW: B->dreapta(+x), R->sus(+y), T->stanga(-x), L->jos(-y). CW invers.
    dirs = {"B": (1, 0), "R": (0, 1), "T": (-1, 0), "L": (0, -1)}
    dx, dy = dirs[side]
    return (dx * d, dy * d)


def random_track(rng, mode="open", direction=None, widths=None, start_side=None, parking=False):
    direction = direction or rng.choice([+1, -1])
    if widths is None:
        if mode == "open":
            widths = {k: rng.choice([0.6, 1.0]) for k in "LRBT"}
        else:
            widths = {k: 1.0 for k in "LRBT"}
    start_side = start_side or rng.choice("BRTL")
    t = Track(widths=widths, direction=direction, start_side=start_side)
    if mode == "obstacle":
        _place_pillars(t, rng, parking)
    return t


# 36 carduri din regulament (Fig. 8c): lista de (coloana, rand, culoare); coloana 0=capatul de intrare, 1=mijloc, 2=capatul de iesire;
# rand 0 = aproape de peretele interior (0.4 m de el), 1 = spre peretele exterior (0.6 m)
_CARDS = [
    [(0, 0, 'g')], [(0, 0, 'r')], [(1, 0, 'g')], [(1, 0, 'r')], [(2, 0, 'g')],
    [(2, 0, 'r')], [(0, 1, 'g')], [(0, 1, 'r')], [(1, 1, 'g')], [(1, 1, 'r')],
    [(2, 0, 'g')], [(2, 0, 'r')], [(0, 1, 'g'), (2, 0, 'g')], [(0, 1, 'g'), (2, 0, 'r')], [(0, 1, 'r'), (2, 0, 'g')],
    [(0, 1, 'g'), (2, 0, 'r')], [(0, 1, 'r'), (2, 0, 'g')], [(0, 1, 'r'), (2, 0, 'r')], [(0, 0, 'g'), (2, 1, 'g')], [(0, 0, 'g'), (2, 1, 'r')],
    [(0, 0, 'r'), (2, 1, 'g')], [(0, 0, 'g'), (2, 1, 'r')], [(0, 0, 'r'), (2, 1, 'g')], [(0, 0, 'r'), (2, 1, 'r')], [(0, 0, 'g'), (2, 0, 'g')],
    [(0, 0, 'g'), (2, 0, 'r')], [(0, 0, 'r'), (2, 0, 'g')], [(0, 0, 'g'), (2, 0, 'r')], [(0, 0, 'r'), (2, 0, 'g')], [(0, 0, 'r'), (2, 0, 'r')],
    [(0, 1, 'g'), (2, 1, 'g')], [(0, 1, 'g'), (2, 1, 'r')], [(0, 1, 'r'), (2, 1, 'g')], [(0, 1, 'g'), (2, 1, 'r')], [(0, 1, 'r'), (2, 1, 'g')],
    [(0, 1, 'r'), (2, 1, 'r')],
]


def _place_pillars(t, rng, parking):
    """Amplasarea din regulament: o sectiune cu un singur semn (loc mijloc/rand exterior, culoare la sorti), celelalte trei
    sectiuni (in sens orar dupa ea) primesc cate un card tras din cele 35 ramase. Semnele stau EXACT pe locurile lor (granita sectiunii)."""
    secs = t.sections()
    order = ['T', 'R', 'B', 'L']                       # sens orar
    s0 = rng.choice(order)
    c0 = rng.choice(['g', 'r'])
    pool = [c for i, c in enumerate(_CARDS) if i != (8 if c0 == 'g' else 9)]
    rng.shuffle(pool)
    plan = {s0: [(1, 1, c0)]}
    k = order.index(s0)
    for j in range(1, 4):
        plan[order[(k + j) % 4]] = list(pool[j - 1])
    flip = rng.random() < 0.5                          # orientarea cardului fata de sensul de mers
    for side, (x0, y0, x1, y1) in secs.items():
        dx, dy = lane_axis(t, side)
        horizontal = side in "BT"
        for (col, row, ch) in plan[side]:
            c = [0.0, 0.5, 1.0][col]
            if flip:
                c = 1.0 - c
            rr = 0.4 if (parking and side == t.start_side) else [0.4, 0.6][row]   # cu parcare: rand interior
            color = 'green' if ch == 'g' else 'red'
            if horizontal:
                inner_y = y1 if side == "B" else y0
                outer_dir = -1 if side == "B" else 1
                py = inner_y + outer_dir * rr * abs(y1 - y0)
                px = (x0 + c * (x1 - x0)) if dx > 0 else (x1 - c * (x1 - x0))
            else:
                inner_x = x0 if side == "R" else x1
                outer_dir = 1 if side == "R" else -1
                px = inner_x + outer_dir * rr * abs(x1 - x0)
                py = (y0 + c * (y1 - y0)) if dy > 0 else (y1 - c * (y1 - y0))
            t.pillars.append((px, py, color))
    if parking:
        _place_lot(t, rng)


def _place_lot(t, rng):
    """Parcarea (regulament 2026, Fig. 4 si 8d): langa peretele exterior al sectiunii de start, la capatul ei din sensul
    antiorar; elementul magenta de la capat e lipit de linia sectiunii. Doua blocuri 20x2 cm, loc liber 1.5 x lungimea masinii."""
    side = t.start_side
    x0, y0, x1, y1 = t.sections()[side]
    L = 1.5 * cfg.CAR_LENGTH
    th, dp = 0.02, 0.20
    if side == "B":
        blocks = [(x1 - th, 0.0, x1, dp), (x1 - 2 * th - L, 0.0, x1 - th - L, dp)]
        t.lot = (x1 - th - L / 2, 0.0, L, dp, "B")
    elif side == "R":
        blocks = [(S - dp, y1 - th, S, y1), (S - dp, y1 - 2 * th - L, S, y1 - th - L)]
        t.lot = (S, y1 - th - L / 2, L, dp, "R")
    elif side == "T":
        blocks = [(x0, S - dp, x0 + th, S), (x0 + th + L, S - dp, x0 + 2 * th + L, S)]
        t.lot = (x0 + th + L / 2, S, L, dp, "T")
    else:
        blocks = [(0.0, y0, dp, y0 + th), (0.0, y0 + th + L, dp, y0 + 2 * th + L)]
        t.lot = (0.0, y0 + th + L / 2, L, dp, "L")
    t.markers = blocks


def lot_free(track):
    """Dreptunghiul liber al parcarii (x0,y0,x1,y1), sau None."""
    if not track.markers:
        return None
    (a0, b0, a1, b1), (c0, d0, c1, d1) = track.markers
    return (min(a1, c1), min(b0, d0), max(a0, c0), max(b1, d1)) if track.start_side in "BT" else \
        (min(a0, c0), min(b1, d1), max(a1, c1), max(b0, d0))


# --------------------------------------------------------------------------- geometrie 2D
def _ray_seg(ox, oy, ex, ey, x0, y0, x1, y1):
    """Intersectie raza (o + s*e) cu segmentul; intoarce s (inf daca nu)."""
    sx, sy = x1 - x0, y1 - y0
    den = ex * sy - ey * sx
    with np.errstate(all="ignore"):
        wx, wy = x0 - ox, y0 - oy
        s = (wx * sy - wy * sx) / den
        k = (wx * ey - wy * ex) / den
    ok = (np.abs(den) > 1e-12) & (s > 1e-4) & (k >= 0.0) & (k <= 1.0)
    return np.where(ok, s, np.inf)


def _rect_edges(x0, y0, x1, y1):
    return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]


def _poly_seg_intersect(poly, seg):
    ax, ay, bx, by = seg
    n = len(poly)
    for i in range(n):
        cx, cy = poly[i]
        dx, dy = poly[(i + 1) % n]
        d1 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        d2 = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax)
        d3 = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx)
        d4 = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx)
        if d1 * d2 < 0 and d3 * d4 < 0:
            return True
    return False


def _point_in_poly(poly, p):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


@dataclass
class SimParams:
    """Realitatea fizica (poate diferi de ce crede codul)."""
    wheelbase: float = None
    v_per_pct: float = None
    steer_gain: float = 1.0          # unghi roata / unghi servo
    steer_trim_deg: float = 0.0
    cam_pitch_deg: float = None
    cam_height: float = None
    cam_hfov_deg: float = None
    speed_tau: float = 0.22
    steer_rate_dps: float = 420.0
    cam_latency: float = 0.07
    cam_fps: float = 15.0
    light: float = 1.0               # factor luminozitate
    noise: float = 4.0
    sonar_noise: float = 0.012
    sonar_dropout: float = 0.03
    pan_deg_per_s: float = 520.0
    slip: float = 1.0                # factor de viteza unghiulara (alunecare)


class SimHW:
    """Interfata HAL simulata."""

    def __init__(self, track, params=None, seed=0, start_pose=None, dt=0.01):
        self.track = track
        self.p = params or SimParams()
        self.rng = random.Random(seed)
        self.nrng = np.random.default_rng(seed)
        self.dt = dt
        self.t = 0.0
        L = self.p.wheelbase or cfg.WHEELBASE
        self.L = L
        self.vk = self.p.v_per_pct or cfg.V_PER_PCT
        self.wps = cfg.WHEEL_PER_SERVO          # adevarul fizic (codul isi poate corecta cfg.WHEEL_PER_SERVO in timpul rularii)
        self.x, self.y, self.th = start_pose if start_pose else (1.5, 0.5, 0.0)
        self.v = 0.0
        self.delta = 0.0                       # unghi real al rotii (rad)
        self.steer_cmd = 0.0                   # grade servo comandate (cu semnul din cfg tratat in HAL)
        self.speed_cmd = 0.0
        self.pan_cmd = 0.0
        self.pan_act = 0.0
        self.tilt_cmd = cfg.TILT_SERVO_DEG
        self.cam = CameraModel(hfov_deg=self.p.cam_hfov_deg, height=self.p.cam_height,
                               pitch_deg=self.p.cam_pitch_deg)
        self._hist = []
        self._frame = None
        self._frame_t = -1.0
        self.collisions = 0
        self.pillar_hits = 0
        self.marker_hits = 0
        self.stalled = False
        self.distance = 0.0
        self.angle_acc = 0.0                   # unghi acumulat in jurul centrului
        self._last_ang = math.atan2(self.y - S / 2, self.x - S / 2)
        self.started = False
        self.log = []
        self._walls = track.walls()
        self._pillar_boxes = [(px - 0.025, py - 0.025, px + 0.025, py + 0.025, c) for px, py, c in track.pillars]
        self._marker_boxes = list(track.markers)
        self._lines = track.corner_lines()
        self.battery_v = 8.2
        self.lights_color = None
        self.finished_stop_t = None
        self._hit_pillars = set()

    # ------------------------------------------------------------- timp
    def now(self):
        return self.t

    def sleep(self, dt):
        end = self.t + dt
        while self.t < end - 1e-9:
            self._step(min(self.dt, end - self.t))

    # ------------------------------------------------------------- actuatori
    def set_steer(self, deg):
        self.steer_cmd = max(-cfg.STEER_MAX_DEG, min(cfg.STEER_MAX_DEG, deg))

    def set_speed(self, pct):
        self.speed_cmd = max(-100.0, min(100.0, pct))

    def set_head(self, pan_deg, tilt_deg=None):
        self.pan_cmd = max(-90.0, min(90.0, pan_deg))

    def pan_now(self):
        return self.pan_act

    # ------------------------------------------------------------- fizica
    def _step(self, dt):
        # servo directie: viteza limitata
        target = math.radians(self.steer_cmd * self.p.steer_gain + self.p.steer_trim_deg) * self.wps
        maxd = math.radians(self.p.steer_rate_dps) * dt
        self.delta += max(-maxd, min(maxd, target - self.delta))
        # pan
        mp = self.p.pan_deg_per_s * dt
        self.pan_act += max(-mp, min(mp, self.pan_cmd - self.pan_act))
        # motor
        pct = self.speed_cmd
        v_tar = 0.0 if abs(pct) < cfg.SPEED_MIN * 0.8 else self.vk * pct * (self.battery_v / 8.4)
        self.v += (v_tar - self.v) * min(1.0, dt / self.p.speed_tau)
        old = (self.x, self.y, self.th)
        w = self.v * math.tan(self.delta) / self.L * self.p.slip
        self.th += w * dt
        self.x += self.v * math.cos(self.th) * dt
        self.y += self.v * math.sin(self.th) * dt
        self.t += dt
        hit = self._collides()
        if hit:
            self.x, self.y, self.th = old
            self.v = 0.0
            self.stalled = True
        else:
            self.stalled = False
        self.distance += abs(self.v) * dt
        ang = math.atan2(self.y - S / 2, self.x - S / 2)
        d = (ang - self._last_ang + math.pi) % (2 * math.pi) - math.pi
        self.angle_acc += d
        self._last_ang = ang
        self._hist.append((self.t, self.x, self.y, self.th, self.pan_act))
        if len(self._hist) > 60:
            self._hist.pop(0)

    def footprint(self, x=None, y=None, th=None, inflate=0.0):
        x = self.x if x is None else x
        y = self.y if y is None else y
        th = self.th if th is None else th
        c, s = math.cos(th), math.sin(th)
        hw = cfg.CAR_WIDTH / 2 + inflate
        pts = [(cfg.REAR_TO_FRONT + inflate, hw), (cfg.REAR_TO_FRONT + inflate, -hw),
               (-cfg.REAR_TO_BACK - inflate, -hw), (-cfg.REAR_TO_BACK - inflate, hw)]
        return [(x + a * c - b * s, y + a * s + b * c) for a, b in pts]

    def _collides(self):
        poly = self.footprint()
        hit = False
        for w in self._walls:
            if _poly_seg_intersect(poly, w) or any(
                    _seg_point_dist(w, p) < 0.004 for p in poly):
                if not self.stalled:
                    self.collisions += 1
                    self.log.append(("coll", round(self.t, 2), round(self.x, 2), round(self.y, 2), round(math.degrees(self.th))))
                hit = True
                break
        for i, (x0, y0, x1, y1, c) in enumerate(self._pillar_boxes):
            if any(_poly_seg_intersect(poly, e) for e in _rect_edges(x0, y0, x1, y1)) or \
                    _point_in_poly(poly, ((x0 + x1) / 2, (y0 + y1) / 2)):
                if i not in self._hit_pillars:
                    self._hit_pillars.add(i)
                    self.pillar_hits += 1
                    self.log.append(("pill", round(self.t, 2), round(self.x, 2), round(self.y, 2), round(math.degrees(self.th)), i))
                hit = True
        for (x0, y0, x1, y1) in self._marker_boxes:
            if any(_poly_seg_intersect(poly, e) for e in _rect_edges(x0, y0, x1, y1)):
                self.marker_hits += 1
                hit = True
        return hit

    # ------------------------------------------------------------- senzori
    def head_pose(self, x=None, y=None, th=None, pan=None):
        x = self.x if x is None else x
        y = self.y if y is None else y
        th = self.th if th is None else th
        pan = self.pan_act if pan is None else pan
        hx = x + cfg.REAR_TO_HEAD * math.cos(th)
        hy = y + cfg.REAR_TO_HEAD * math.sin(th)
        return hx, hy, th + math.radians(pan)

    def sonar(self):
        """Distanta (m) pe directia capului sau None."""
        if self.rng.random() < self.p.sonar_dropout:
            return None
        hx, hy, yaw = self.head_pose()
        best = np.inf
        for off in (-12, -6, 0, 6, 12):
            a = yaw + math.radians(off)
            ex, ey = math.cos(a), math.sin(a)
            d, nx, ny = self._cast(hx, hy, ex, ey)
            if not math.isfinite(d):
                continue
            inc = math.acos(max(-1.0, min(1.0, -(ex * nx + ey * ny))))
            if inc > math.radians(62):
                continue                         # ecou pierdut (incidenta razanta)
            best = min(best, d)
        if not math.isfinite(best) or best > cfg.SONAR_MAX:
            return None
        return max(0.03, best + self.nrng.normal(0, self.p.sonar_noise) + 0.005 * best * self.nrng.normal())

    def _cast(self, ox, oy, ex, ey):
        """Prima intersectie (2D) cu orice obstacol; intoarce (s, nx, ny) normala spre emitator."""
        best, bn = math.inf, (0.0, 0.0)
        segs = list(self._walls)
        for (x0, y0, x1, y1, _c) in self._pillar_boxes:
            segs += _rect_edges(x0, y0, x1, y1)
        for b in self._marker_boxes:
            segs += _rect_edges(*b)
        for (x0, y0, x1, y1) in segs:
            s = float(_ray_seg(ox, oy, ex, ey, x0, y0, x1, y1))
            if s < best:
                best = s
                sx, sy = x1 - x0, y1 - y0
                n = math.hypot(sx, sy)
                nx, ny = -sy / n, sx / n
                if nx * ex + ny * ey > 0:
                    nx, ny = -nx, -ny
                bn = (nx, ny)
        return best, bn[0], bn[1]

    def frame(self):
        """Ultimul cadru (bgr, t_captura) la cel mult cam_fps; None daca nu e nou."""
        if self.t - self._frame_t < 1.0 / self.p.cam_fps - 1e-9 and self._frame is not None:
            return self._frame, self._frame_t, False
        t_cap = self.t - self.p.cam_latency
        pose = None
        for h in reversed(self._hist):
            if h[0] <= t_cap:
                pose = h
                break
        if pose is None:
            pose = (self.t, self.x, self.y, self.th, self.pan_act)
        img = self.render(pose[1], pose[2], pose[3], pose[4])
        self._frame, self._frame_t = img, self.t
        return img, self.t, True

    def ir(self):
        return (1, 1, 1)

    def battery(self):
        return (self.battery_v, 80, False, False)

    def yaw_rate(self):
        return None

    # ------------------------------------------------------------- randare
    def render(self, x, y, th, pan_deg):
        """Randare la jumatate de rezolutie (rapid), apoi marire la rezolutia camerei."""
        import cv2
        cam = self.cam
        w, h = cam.w, cam.h
        st = 2
        hx, hy, yaw = self.head_pose(x, y, th, pan_deg)
        cx0 = hx + cam.fwd * math.cos(yaw)
        cy0 = hy + cam.fwd * math.sin(yaw)
        u, v = np.meshgrid(np.arange(0, w, st, dtype=np.float32) + st / 2.0,
                           np.arange(0, h, st, dtype=np.float32) + st / 2.0)
        rx = (u - cam.cx) / cam.f
        ry = (v - cam.cy) / cam.f
        sp, cp = math.sin(cam.pitch), math.cos(cam.pitch)
        r_f = cp - sp * ry
        r_up = -sp - cp * ry
        r_left = -rx
        c, s = math.cos(yaw), math.sin(yaw)
        dx = r_f * c - r_left * s
        dy = r_f * s + r_left * c
        hn = np.hypot(dx, dy)
        ex, ey = dx / hn, dy / hn
        slope = r_up / hn
        H = cam.height
        with np.errstate(all="ignore"):
            s_floor = np.where(slope < 0, H / np.maximum(-slope, 1e-9), np.float32(1e9))
            s_best = np.full(u.shape, np.inf, np.float32)
            col = np.zeros(u.shape + (3,), np.float32)
            col[:] = BGR["sky"]

            def consider(segs, color, height):
                nonlocal s_best, col
                for (x0, y0, x1, y1) in segs:
                    sd = _ray_seg(cx0, cy0, ex, ey, x0, y0, x1, y1)
                    z = H + slope * sd
                    ok = np.isfinite(sd) & (z >= 0) & (z <= height) & (sd < s_best)
                    if ok.any():
                        s_best = np.where(ok, sd, s_best)
                        col[ok] = color

            consider(self._walls, BGR["wall"], WALL_H)
            for (x0, y0, x1, y1, cname) in self._pillar_boxes:
                if (x0 - cx0) ** 2 + (y0 - cy0) ** 2 > 9.0:
                    continue
                consider(_rect_edges(x0, y0, x1, y1), BGR[cname], PILLAR_H)
            for b in self._marker_boxes:
                consider(_rect_edges(*b), BGR["magenta"], 0.10)
            floor_vis = (s_floor < 1e8) & (s_floor < s_best)
            if floor_vis.any():
                sf = np.where(floor_vis, s_floor, 0.0)
                gx = cx0 + ex * sf
                gy = cy0 + ey * sf
                floor_col = np.empty(u.shape + (3,), np.float32)
                floor_col[:] = BGR["floor"]
                for (name, ax, ay, bx, by) in self._lines:
                    d = _pt_seg_dist(gx, gy, ax, ay, bx, by)
                    floor_col[d < 0.010] = BGR[name]
                col = np.where(floor_vis[..., None], floor_col, col)
        img = cv2.resize(col, (w, h), interpolation=cv2.INTER_LINEAR)
        shade = (1.0 - 0.10 * (np.arange(h, dtype=np.float32) / h))[:, None, None]
        img = img * shade * self.p.light
        img += self.nrng.normal(0, self.p.noise, img.shape).astype(np.float32)
        return np.clip(img, 0, 255).astype(np.uint8)

    # ------------------------------------------------------------- evaluare
    def in_section(self, side, margin=0.0):
        """True daca proiectia masinii e complet in sectiunea dreapta `side`."""
        x0, y0, x1, y1 = self.track.sections()[side]
        for (px, py) in self.footprint():
            if not (x0 - margin <= px <= x1 + margin and y0 - margin <= py <= y1 + margin):
                return False
        return True

    def laps(self):
        return abs(self.angle_acc) / (2 * math.pi)


def _seg_point_dist(seg, p):
    x0, y0, x1, y1 = seg
    px, py = p
    dx, dy = x1 - x0, y1 - y0
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy + 1e-12)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _pt_seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy + 1e-12), 0.0, 1.0)
    return np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def start_pose_for(track, rng, side=None, frac=None):
    """Pozitie de start in sectiunea dreapta de start, orientata in sensul de mers."""
    side = side or track.start_side
    x0, y0, x1, y1 = track.sections()[side]
    dx, dy = lane_axis(track, side)
    frac = rng.uniform(0.15, 0.55) if frac is None else frac
    if side in "BT":
        length = x1 - x0
        px = x0 + frac * length if dx > 0 else x1 - frac * length
        py = (y0 + y1) / 2 + rng.uniform(-0.12, 0.12) * min(1.0, (y1 - y0))
    else:
        length = y1 - y0
        py = y0 + frac * length if dy > 0 else y1 - frac * length
        px = (x0 + x1) / 2 + rng.uniform(-0.12, 0.12) * min(1.0, (x1 - x0))
    th = math.atan2(dy, dx) + math.radians(rng.uniform(-4, 4))
    # axa spate: pozitia masinii este axa spate
    return px, py, th

