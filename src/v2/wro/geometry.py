"""Geometrie: model de camera (proiectie pe podea), RANSAC pe linii, utilitare unghi."""
import math

import numpy as np

from . import config as cfg


def wrap_pi(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class CameraModel:
    """Camera pinhole la inaltimea h, inclinata in jos cu `pitch`, in cadrul capului.

    Cadrul capului: X inainte, Y la stanga, origine = axa pan a capului.
    pixel_to_ground() intoarce punctul de pe podea; project() face invers (pentru simulator).
    """

    def __init__(self, size=None, hfov_deg=None, height=None, pitch_deg=None, fwd=None):
        w, h = size or cfg.CAM_SIZE
        self.w, self.h = w, h
        self.f = (w / 2.0) / math.tan(math.radians(hfov_deg or cfg.CAM_HFOV_DEG) / 2.0)
        self.cx, self.cy = w / 2.0, h / 2.0
        self.height = cfg.CAM_HEIGHT if height is None else height
        self.pitch = math.radians(cfg.CAM_PITCH_DEG if pitch_deg is None else pitch_deg)
        self.fwd = cfg.CAM_FWD_OFFSET if fwd is None else fwd
        self._sp, self._cp = math.sin(self.pitch), math.cos(self.pitch)

    def pixel_to_ground(self, u, v):
        """u, v: scalari sau array. Intoarce (X, Y, valid) in cadrul capului."""
        u = np.asarray(u, dtype=float)
        v = np.asarray(v, dtype=float)
        xc = (u - self.cx) / self.f
        yc = (v - self.cy) / self.f
        denom = self._sp + self._cp * yc
        valid = denom > 0.02
        t = np.where(valid, self.height / np.where(valid, denom, 1.0), 0.0)
        X = t * (self._cp - self._sp * yc) + self.fwd
        Y = -t * xc
        return X, Y, valid

    def project(self, X, Y, z):
        """Punct 3D (X inainte, Y stanga, z inaltime) in cadrul capului -> (u, v, adancime)."""
        X = np.asarray(X, dtype=float) - self.fwd
        Y = np.asarray(Y, dtype=float)
        dz = np.asarray(z, dtype=float) - self.height
        depth = X * self._cp - dz * self._sp
        down = -X * self._sp - dz * self._cp
        safe = np.where(depth > 1e-3, depth, np.nan)
        u = self.cx + self.f * (-Y) / safe
        v = self.cy + self.f * down / safe
        return u, v, depth

    def azimuth_deg(self, u):
        return np.degrees(np.arctan((self.cx - np.asarray(u, dtype=float)) / self.f))


def ransac_line(pts, inlier=None, max_angle_deg=None, min_points=None):
    """Linie Y = a + b*X prin RANSAC exhaustiv (puncte putine).

    pts: array (N,2) cu (X, Y). Intoarce (a, b, mask_inlieri) sau None.
    """
    inlier = cfg.FIT_INLIER if inlier is None else inlier
    max_b = math.tan(math.radians(cfg.FIT_MAX_ANGLE_DEG if max_angle_deg is None else max_angle_deg))
    min_points = cfg.FIT_MIN_POINTS if min_points is None else min_points
    pts = np.asarray(pts, dtype=float)
    n = len(pts)
    if n < min_points:
        return None
    X, Y = pts[:, 0], pts[:, 1]
    i, j = np.triu_indices(n, 1)
    dx = X[j] - X[i]
    ok = np.abs(dx) > 0.06
    if not ok.any():
        return None
    i, j, dx = i[ok], j[ok], dx[ok]
    b = (Y[j] - Y[i]) / dx
    good = np.abs(b) <= max_b
    if not good.any():
        return None
    i, j, b = i[good], j[good], b[good]
    a = Y[i] - b * X[i]
    resid = np.abs(Y[None, :] - (a[:, None] + b[:, None] * X[None, :]))
    inl = resid < inlier
    counts = inl.sum(axis=1)
    # preferam multe puncte; la egalitate panta mica
    score = counts - 0.01 * np.abs(b)
    k = int(np.argmax(score))
    if counts[k] < min_points:
        return None
    mask = inl[k]
    A = np.vstack([np.ones(mask.sum()), X[mask]]).T
    coef, *_ = np.linalg.lstsq(A, Y[mask], rcond=None)
    a2, b2 = float(coef[0]), float(coef[1])
    if abs(b2) > max_b:
        a2, b2 = float(a[k]), float(b[k])
    resid2 = np.abs(Y - (a2 + b2 * X))
    return a2, b2, resid2 < inlier * 1.3


def line_distance(a, b):
    """Distanta perpendiculara de la origine la linia Y = a + b X."""
    return abs(a) / math.sqrt(1.0 + b * b)

