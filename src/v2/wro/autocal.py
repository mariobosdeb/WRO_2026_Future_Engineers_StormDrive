"""Autocalibrare online a inclinarii camerei.

Peretii culoarului sunt paraleli. Daca inclinarea (pitch) presupusa e gresita, cei doi pereti apar convergenti/divergenti
(pantele lor in cadrul masinii difera). Cautam corectia de pitch care egaleaza pantele si o aplicam lent.
"""
import math

import numpy as np

from . import config as cfg
from .geometry import CameraModel


def _slope(X, Y):
    xm, ym = X.mean(), Y.mean()
    dx = X - xm
    den = float((dx * dx).sum())
    if den < 1e-9:
        return None
    return float((dx * (Y - ym)).sum() / den)


class PitchCal:
    def __init__(self, cam, perceiver):
        self.cam = cam
        self.perceiver = perceiver
        self.grid = np.arange(-cfg.AUTOCAL_RANGE_DEG, cfg.AUTOCAL_RANGE_DEG + 0.01, 1.0)
        self.votes = []
        self.applied = 0.0             # corectie totala aplicata (grade)
        self.n_frames = 0

    def _models(self):
        base = math.degrees(self.cam.pitch)
        out = []
        for d in self.grid:
            m = CameraModel(pitch_deg=base + d, height=self.cam.height, fwd=self.cam.fwd)
            out.append(m)
        return out

    def estimate(self, v_base, has):
        """Intoarce corectia de pitch (grade, se adauga la pitch-ul curent) sau None."""
        az = self.perceiver.az_bin
        u = self.perceiver.u_bin
        left = has & (az > 3.0)
        right = has & (az < -3.0)
        if left.sum() < 8 or right.sum() < 8:
            return None
        mism = []
        for d, m in zip(self.grid, self._models()):
            X, Y, valid = m.pixel_to_ground(u, v_base)
            X = X + 0.0
            res = []
            for sel in (left, right):
                s = sel & valid & (X < cfg.AUTOCAL_XMAX) & (X > 0.15)
                if s.sum() < 8 or np.ptp(X[s]) < 0.35:
                    res.append(None)
                    continue
                res.append(_slope(X[s], Y[s]))
            if res[0] is None or res[1] is None:
                mism.append(np.nan)
            else:
                mism.append(res[0] - res[1])
        mism = np.array(mism)
        ok = ~np.isnan(mism)
        if ok.sum() < 4:
            return None
        g, mm = self.grid[ok], mism[ok]
        # peretele stang are panta (Y creste) ; la pitch corect pantele sunt egale => mism = 0. Cautam trecerea prin zero.
        sg = np.sign(mm)
        cross = np.where(sg[:-1] * sg[1:] < 0)[0]
        if len(cross) != 1:
            return None
        i = int(cross[0])
        d0 = g[i] + (0 - mm[i]) * (g[i + 1] - g[i]) / (mm[i + 1] - mm[i])
        return float(d0)

    def update(self, v_base, has, pan_deg, psi):
        if abs(pan_deg) > 2.0 or abs(psi) > math.radians(cfg.AUTOCAL_PSI_MAX):
            return
        d = self.estimate(v_base, has)
        if d is None or abs(d) > cfg.AUTOCAL_RANGE_DEG - 0.5:
            return
        self.n_frames += 1
        self.votes.append(d)
        self.votes = self.votes[-cfg.AUTOCAL_VOTES:]
        if len(self.votes) >= cfg.AUTOCAL_VOTES:
            med = float(np.median(self.votes))
            if abs(med) > cfg.AUTOCAL_DEADBAND_DEG:
                step = max(-1.0, min(1.0, cfg.AUTOCAL_RATE * med))
                self.apply(step)
            self.votes = []

    def apply(self, d_deg):
        self.applied += d_deg
        self.cam.pitch = self.cam.pitch + math.radians(d_deg)
        self.cam._sp, self.cam._cp = math.sin(self.cam.pitch), math.cos(self.cam.pitch)


class SonarPitchCal:
    """Calibreaza inclinarea camerei cu ultrasonicul: peretele din fata e vazut de camera la X_v si masurat de sonar la X_s.
    Unghiul razei spre podea: phi = atan(h / X). Corectia de pitch = phi(X_s) - phi(X_v). Mediana pe mai multe perechi."""

    def __init__(self, cam):
        self.cam = cam
        self.votes = []
        self.applied = 0.0
        self.n_pairs = 0
        self._last = (None, None)

    def update(self, est, pan_deg, t, steer=0.0):
        if abs(steer) > cfg.SONARCAL_STEER_MAX:
            return
        fc, fs = est.front_cam, est.front_sonar
        if fc is None or fs is None or abs(pan_deg) > 2.0:
            return
        if (fc[1], fs[1]) == self._last:
            return
        self._last = (fc[1], fs[1])
        if abs(fc[1] - fs[1]) > 0.25 or t - fs[1] > 0.3:
            return
        if abs(est.psi) > math.radians(cfg.SONARCAL_PSI_MAX):
            return
        H = cfg.REAR_TO_HEAD
        xv, xs = fc[0] - H - self.cam.fwd, fs[0] - H - self.cam.fwd
        if not (cfg.SONARCAL_XMIN < fs[0] < cfg.SONARCAL_XMAX) or xv <= 0.05 or xs <= 0.05:
            return
        if abs(xs - xv) > 0.6:
            return
        h = self.cam.height
        d = math.degrees(math.atan2(h, xs) - math.atan2(h, xv))
        self.n_pairs += 1
        self.votes.append(d)
        self.votes = self.votes[-int(cfg.SONARCAL_VOTES):]
        if len(self.votes) >= int(cfg.SONARCAL_VOTES):
            med = float(np.median(self.votes))
            if abs(med) > cfg.SONARCAL_DEADBAND and abs(self.applied + med) < cfg.AUTOCAL_RANGE_DEG:
                step = max(-cfg.SONARCAL_CAP, min(cfg.SONARCAL_CAP, cfg.SONARCAL_RATE * med))
                self.applied += step
                self.cam.pitch += math.radians(step)
                self.cam._sp, self.cam._cp = math.sin(self.cam.pitch), math.cos(self.cam.pitch)
            self.votes = []


class SpeedCal:
    """Calibreaza viteza reala (V_PER_PCT efectiv) cu ultrasonicul: pe o dreapta spre perete, scaderea distantei frontale = drumul real.
    Regresie liniara f(dist_odometrie) pe o fereastra cu viteza stabila; scale = -panta. Se aplica odometriei (robot.v_scale)."""

    def __init__(self):
        self.d = []
        self.f = []
        self.n_updates = 0
        self.last_ratio = None
        self._spd = None
        self._spd_t = 0.0

    def reset(self):
        self.d, self.f = [], []

    def update(self, brain, front, psi, steer, speed_cmd, t):
        if self._spd is None or abs(speed_cmd - self._spd) > 1.5:
            self._spd, self._spd_t = speed_cmd, t
            self.reset()
        steady = (t - self._spd_t) >= cfg.SPEEDCAL_SETTLE_S
        ok = steady and speed_cmd > 0 and abs(steer) < cfg.SPEEDCAL_STEER_MAX and abs(psi) < math.radians(10) \
            and front is not None and cfg.SPEEDCAL_FMIN < front < cfg.SPEEDCAL_FMAX
        if not ok:
            self.reset()
            return
        if self.f and abs(front - self.f[-1]) > 0.15:       # salt: alta suprafata
            self.reset()
        self.d.append(brain.dist_acc)
        self.f.append(front)
        if brain.dist_acc - self.d[0] < cfg.SPEEDCAL_WINDOW_M or len(self.d) < 6:
            return
        d = np.array(self.d)
        f = np.array(self.f)
        A = np.vstack([d - d.mean(), np.ones_like(d)]).T
        (slope, _), *_ = np.linalg.lstsq(A, f, rcond=None)
        res = f - A @ np.array([slope, f.mean()])
        self.reset()
        if float(res.std()) > cfg.SPEEDCAL_RES_MAX:
            return
        ratio = -float(slope)
        if 0.5 < ratio < 1.8:
            self.last_ratio = ratio
            k = 1.0 + cfg.SPEEDCAL_RATE * (ratio - 1.0)
            brain.v_scale = max(cfg.SPEEDCAL_MIN, min(cfg.SPEEDCAL_MAX, brain.v_scale * k))
            self.n_updates += 1

