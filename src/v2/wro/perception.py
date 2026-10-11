"""Perceptie din imaginea camerei (Picamera2 RGB888 = pixeli B,G,R => BGR2HSV).

Din fiecare cadru scoatem:
  * baza peretelui negru pe fiecare dintr-un set de coloane (puncte pe podea, in cadrul masinii)
  * liniile portocalii / albastre de pe podea (+ evenimente "linie noua")
  * stalpi rosii / verzi (pozitie pe podea) si markerii magenta ai parcarii

Peretii sunt NEGRI si podeaua ALBA (regulament 13.2-13.6), deci segmentarea e simpla si
nu depinde de culori exacte: prag adaptiv pe luminozitate (relativ la podeaua alba).
"""
import math
from dataclasses import dataclass, field

import cv2
import numpy as np

from . import config as cfg
from .geometry import CameraModel

ST_NONE, ST_WALL, ST_OCCLUDED, ST_TOUCH = 0, 1, 2, 3


@dataclass
class Blob:
    color: str
    X: float                # cadrul masinii (axa spate), inainte
    Y: float                # stanga
    area: float
    u: float
    v_base: float
    w_px: float
    h_px: float


@dataclass
class Perception:
    t: float
    pan: float
    ok: bool
    az: np.ndarray          # azimut (grade, + stanga) fata de directia masinii
    X: np.ndarray           # puncte de baza ale peretelui (cadrul masinii)
    Y: np.ndarray
    state: np.ndarray       # ST_*
    lines: dict = field(default_factory=dict)       # culoare -> {"px","X","Y"}
    line_events: list = field(default_factory=list)
    pillars: list = field(default_factory=list)
    markers: list = field(default_factory=list)
    bright: float = 0.0
    dark_thr: float = 0.0


class Perceiver:
    def __init__(self, camera=None):
        self.cam = camera or CameraModel()
        self._active = {"orange": False, "blue": False}
        self._last_event = {"orange": -1e9, "blue": -1e9}
        self._k3 = np.ones((3, 3), np.uint8)
        w = self.cam.w
        self.bins = cfg.WALL_BINS
        self.bw = w // self.bins
        self.u_bin = (np.arange(self.bins) + 0.5) * self.bw + (w - self.bins * self.bw) / 2.0
        self.az_bin = self.cam.azimuth_deg(self.u_bin)

    # ------------------------------------------------------------------
    def _to_car(self, Xh, Yh, pan_deg):
        th = math.radians(pan_deg)
        c, s = math.cos(th), math.sin(th)
        Xc = Xh * c - Yh * s + cfg.REAR_TO_HEAD
        Yc = Xh * s + Yh * c
        return Xc, Yc

    @staticmethod
    def _mask(hsv, lo, hi):
        return cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))

    def process(self, bgr, pan_deg, t):
        h, w = bgr.shape[:2]
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        V = hsv[:, :, 2]
        p90 = float(np.percentile(V[::4, ::4], 90))
        thr = float(np.clip(cfg.DARK_FRAC * p90, cfg.DARK_V_MIN, cfg.DARK_V_MAX))
        ok = p90 > 60.0

        # ---------------- baza peretelui pe fiecare bin
        dark = V < thr
        r0, r1 = int(h * cfg.CAM_ROI_TOP), int(h * cfg.CAM_ROI_BOTTOM)
        rows = r1 - r0
        nb, bw = self.bins, self.bw
        c0 = (w - nb * bw) // 2
        sub = dark[r0:r1, c0:c0 + nb * bw].reshape(rows, nb, bw).mean(axis=2) > cfg.BIN_DARK_FRAC
        K = cfg.WALL_RUN_MIN
        cs = np.vstack([np.zeros((1, nb), np.int32), np.cumsum(sub, axis=0, dtype=np.int32)])
        run_ok = (cs[K:] - cs[:-K]) == K                       # (rows-K+1, nb)
        has = run_ok.any(axis=0)
        idx_from_bottom = np.argmax(run_ok[::-1], axis=0)
        end_row = rows - 1 - idx_from_bottom                    # indice in ROI
        v_base = r0 + end_row + 1.0
        self.last_v, self.last_has = v_base, has        # (pentru calibrate.py)
        touch = has & (end_row >= rows - 2)

        # ---------------- culori (liniile doar pe podea, sub baza peretelui: obiectele colorate de dupa perete nu conteaza)
        top = np.where(has, v_base - cfg.LINE_WALL_TOL, 0.0).astype(np.int32)
        top_col = np.repeat(top, bw)
        top_col = np.concatenate([np.full(c0, top_col[0]), top_col, np.full(w - c0 - nb * bw, top_col[-1])])
        lines, events = self._lines(hsv, h, w, pan_deg, t, top_col)
        pillars = self._blobs_pillar(hsv, pan_deg)
        markers = self._blobs_marker(hsv, pan_deg)

        state = np.where(has, ST_WALL, ST_NONE).astype(np.int8)
        state[touch] = ST_TOUCH
        # coloane acoperite de stalpi / markere => necunoscute
        for b in pillars + markers:
            u0 = b.u - b.w_px / 2.0 - 3
            u1 = b.u + b.w_px / 2.0 + 3
            hit = (self.u_bin + bw / 2.0 > u0) & (self.u_bin - bw / 2.0 < u1)
            state[hit & (state != ST_NONE) & (b.v_base >= v_base - 3.0)] = ST_OCCLUDED   # doar daca stalpul e mai aproape decat peretele

        Xh, Yh, valid = self.cam.pixel_to_ground(self.u_bin, v_base)
        state[~valid & (state == ST_WALL)] = ST_NONE
        Xc, Yc = self._to_car(Xh, Yh, pan_deg)
        return Perception(t=t, pan=pan_deg, ok=ok, az=self.az_bin + pan_deg, X=Xc, Y=Yc,
                          state=state, lines=lines, line_events=events, pillars=pillars,
                          markers=markers, bright=p90, dark_thr=thr)

    # ------------------------------------------------------------------
    def _lines(self, hsv, h, w, pan_deg, t, top_col=None):
        y0 = int(h * cfg.LINE_ROI_TOP)
        y0r = float(y0)
        roi = hsv[y0:, :]
        floor = None
        if top_col is not None:
            floor = ((np.arange(y0, h)[:, None] >= top_col[None, :]).astype(np.uint8)) * 255
        out, events = {}, []
        for name, (lo, hi) in (("orange", cfg.ORANGE), ("blue", cfg.BLUE)):
            m = self._mask(roi, lo, hi)
            if floor is not None:
                m = cv2.bitwise_and(m, floor)
            px = int(cv2.countNonZero(m))
            info = {"px": px, "X": None, "Y": None, "P1": None, "P2": None}
            if px >= cfg.LINE_FIT_PIXELS:
                pts = cv2.findNonZero(m)
                if pts is not None and len(pts) >= 20:
                    vx, vy, x0, y0 = [float(v) for v in cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01).ravel()]
                    P = pts.reshape(-1, 2).astype(np.float64)
                    tt = (P[:, 0] - x0) * vx + (P[:, 1] - y0) * vy
                    t1, t2 = np.percentile(tt, 3), np.percentile(tt, 97)
                    g = []
                    for tq in (t1, t2):
                        u_, v_ = x0 + vx * tq, y0 + vy * tq + y0r
                        Xh_, Yh_, ok_ = self.cam.pixel_to_ground(u_, v_)
                        if bool(ok_):
                            g.append(self._to_car(float(Xh_), float(Yh_), pan_deg))
                    if len(g) == 2 and math.hypot(g[1][0] - g[0][0], g[1][1] - g[0][1]) > 0.08:
                        info["P1"], info["P2"] = g
            if px >= cfg.LINE_CLEAR_PIXELS:
                mom = cv2.moments(m, binaryImage=True)
                if mom["m00"] > 0:
                    uc = mom["m10"] / mom["m00"]
                    vc = mom["m01"] / mom["m00"] + y0
                    Xh, Yh, ok = self.cam.pixel_to_ground(uc, vc)
                    if bool(ok):
                        Xc, Yc = self._to_car(float(Xh), float(Yh), pan_deg)
                        info["X"], info["Y"] = Xc, Yc
            out[name] = info
            if px >= cfg.LINE_MIN_PIXELS:
                if not self._active[name] and t - self._last_event[name] >= cfg.LINE_EVENT_GAP:
                    events.append(name)
                    self._last_event[name] = t
                self._active[name] = True
            elif px < cfg.LINE_CLEAR_PIXELS:
                self._active[name] = False
        return out, events

    def _contours(self, mask):
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._k3)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return cnts

    def _make_blob(self, color, cnt, pan_deg, pillar, img_w=None):
        area = cv2.contourArea(cnt)
        x, y, bw, bh = cv2.boundingRect(cnt)
        if pillar:
            if area < cfg.PILLAR_MIN_AREA or bh < 1.0 * bw * 0.85 or bh < 5:
                return None
            # marginile imaginii: peretele negru apare rosiatic (umbrirea lentilei) => "stalpi" falsi; un stalp real reapare mai la centru
            if img_w is not None and (x <= 1 or x + bw >= img_w - 1):
                return None
        elif area < cfg.MARKER_MIN_AREA:
            return None
        u = x + bw / 2.0
        vb = y + bh
        Xh, Yh, ok = self.cam.pixel_to_ground(u, vb)
        if not bool(ok):
            return None
        Xh, Yh = float(Xh), float(Yh)
        if pillar:                      # centrul stalpului e putin dupa fata vizibila
            r = math.hypot(Xh, Yh)
            if r > 1e-3:
                Xh += cfg.PILLAR_HALF * Xh / r
                Yh += cfg.PILLAR_HALF * Yh / r
        Xc, Yc = self._to_car(Xh, Yh, pan_deg)
        return Blob(color, Xc, Yc, float(area), u, float(vb), float(bw), float(bh))

    def _blobs_pillar(self, hsv, pan_deg):
        out = []
        red = cv2.bitwise_or(self._mask(hsv, *cfg.RED[0]), self._mask(hsv, *cfg.RED[1]))
        green = self._mask(hsv, *cfg.GREEN)
        for name, m in (("red", red), ("green", green)):
            for cnt in self._contours(m):
                b = self._make_blob(name, cnt, pan_deg, True, hsv.shape[1])
                if b is not None:
                    out.append(b)
        out.sort(key=lambda b: b.X)
        return out[:6]

    def _blobs_marker(self, hsv, pan_deg):
        out = []
        m = self._mask(hsv, *cfg.MAGENTA)
        for cnt in self._contours(m):
            b = self._make_blob("magenta", cnt, pan_deg, False)
            if b is not None:
                out.append(b)
        out.sort(key=lambda b: b.X)
        return out[:4]


def annotate(bgr, per, cam):
    """Imagine de debug cu puncte de perete, stalpi si markere."""
    img = bgr.copy()
    for j in range(len(per.state)):
        if per.state[j] == ST_NONE:
            continue
        col = (0, 255, 255) if per.state[j] == ST_WALL else (0, 128, 255)
        u = int(cam.cx - cam.f * math.tan(math.radians(per.az[j] - per.pan)))
        cv2.circle(img, (u, 5 + 6 * (j % 2)), 2, col, -1)
    for b in per.pillars + per.markers:
        cv2.rectangle(img, (int(b.u - b.w_px / 2), int(b.v_base - b.h_px)),
                      (int(b.u + b.w_px / 2), int(b.v_base)), (255, 255, 255), 1)
        cv2.putText(img, "%s %.2f,%.2f" % (b.color[0], b.X, b.Y), (int(b.u) - 20, int(b.v_base) + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    return img

