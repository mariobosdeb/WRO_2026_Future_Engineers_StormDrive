"""Brain: leaga hardware (HAL) + perceptie + estimator + odometrie + programarea capului.

IMPORTANT (montaj Adeept): camera SI ultrasonicul sunt pe ACELASI cap pan/tilt.
  - in conducere capul sta drept (camera vede inainte, ultrasonicul masoara frontal)
  - la intervale PEEK_PERIOD capul se uita scurt lateral (ultrasonic) ca sa calibreze scala
    camerei si sa verifice peretii; in acest timp cadrele camerei se ignora
"""
import math
from collections import deque

from . import config as cfg
from .estimator import Estimator
from .geometry import CameraModel
from .perception import Perceiver
from .autocal import PitchCal, SonarPitchCal, SpeedCal

CAM_LATENCY = 0.07


def settle_time(delta_deg):
    return cfg.PAN_SETTLE_BASE + cfg.PAN_SETTLE_PER_DEG * abs(delta_deg)


class Brain:
    def __init__(self, hal, use_est=True):
        self.hal = hal
        self.use_est = use_est
        self.frame_event = None              # (per, t_cap, delta(dx,dy,dth)) cand s-a procesat un cadru nou in acest tick
        self.sonar_event = None              # (r, pan, t)
        self.cam = CameraModel()
        self.perceiver = Perceiver(self.cam)
        self.est = Estimator()
        self.pitchcal = PitchCal(self.cam, self.perceiver) if cfg.AUTOCAL_PITCH else None
        self.sonarcal = SonarPitchCal(self.cam) if cfg.SONARCAL_PITCH else None
        self.speedcal = SpeedCal() if cfg.SPEEDCAL else None
        self.v_scale = 1.0                   # factor de corectie a vitezei reale fata de V_PER_PCT (invatat cu sonarul)
        self.steer_cmd = 0.0
        self.speed_cmd = 0.0
        self.v_est = 0.0
        self.delta_est = 0.0
        self.odo = deque(maxlen=200)         # (t, ds, dth)
        self.t_last = None
        self.yaw_acc = 0.0                   # rad, cumulat
        self.dist_acc = 0.0                  # m, cumulat (cu semn)
        self.path_acc = 0.0                  # m parcursi (valoare absoluta)
        # cap
        self.pan_target = 0.0
        self.head_ready_t = 0.0
        self.peek_ok = True
        self.hold_pan = None                 # daca nu e None, capul ramane la acest unghi
        self.base_pan = 0.0                  # unghiul "de lucru" al capului (privire spre peretele interior)
        self._peek_side = 1
        self._last_peek = -1e9
        self._peek_phase = None
        self._peek_until = 0.0
        self._peek_got = False
        self.peeks = self.peek_hits = 0      # statistica: priviri laterale / cu citire valida
        self.rec = hal if hasattr(hal, "begin") else None     # RecHAL (wro/record.py): inregistreaza senzorii
        self.last_img = None
        self.last_per = None
        self.frames = 0
        self.ticks = 0
        self._deadline = None

    # ------------------------------------------------------------------ comenzi
    def command(self, steer_deg, speed_pct, dt=None):
        """Seteaza directia (cu limitare de viteza) si puterea motorului."""
        t = self.hal.now()
        if dt is None:
            dt = 1.0 / cfg.LOOP_HZ
        maxd = cfg.STEER_SLEW_DPS * dt
        steer = max(-cfg.STEER_MAX_DEG, min(cfg.STEER_MAX_DEG, steer_deg))
        steer = self.steer_cmd + max(-maxd, min(maxd, steer - self.steer_cmd))
        self.steer_cmd = steer
        self.speed_cmd = speed_pct
        self.hal.set_steer(steer)
        self.hal.set_speed(speed_pct)

    def command_now(self, steer_deg, speed_pct):
        """Fara limitare de viteza a directiei (viraje, recuperare)."""
        steer = max(-cfg.STEER_MAX_DEG, min(cfg.STEER_MAX_DEG, steer_deg))
        self.steer_cmd = steer
        self.speed_cmd = speed_pct
        self.hal.set_steer(steer)
        self.hal.set_speed(speed_pct)

    def stop(self):
        self.speed_cmd = 0.0
        self.hal.set_speed(0.0)

    # ------------------------------------------------------------------ cap
    def set_pan(self, deg):
        if abs(deg - self.pan_target) < 0.5:
            return
        self.head_ready_t = self.hal.now() + settle_time(deg - self.pan_target) + 0.03
        self.pan_target = deg
        self.hal.set_head(deg)

    def start_scan(self, amp=65.0):
        """La start (masina stationara): capul priveste stanga, dreapta, apoi inapoi la centru; ultrasonicul masoara distantele laterale
        (se logheaza, pentru verificarea pozitiei de start) iar camera are timp sa vada tot. Intoarce (stanga, fata, dreapta) in m sau None."""
        hal = self.hal
        out = {}
        for name, a in (("st", amp), ("dr", -amp), ("fata", 0.0)):
            self.hold_pan = a                    # altfel _head_step readuce capul la base_pan la fiecare pas
            self.set_pan(a)
            end = hal.now() + settle_time(abs(a - self.pan_target)) + 0.35
            while hal.now() < end:
                self.tick()
                self.wait_period()
            vals = []
            for _ in range(4):
                s_ = hal.sonar()
                if s_ is not None:
                    vals.append(s_)
                self.tick()
                self.wait_period()
            out[name] = sorted(vals)[len(vals) // 2] if vals else None
        self.hold_pan = None
        self.set_pan(self.base_pan)
        f0 = self.frames
        end = hal.now() + 1.2
        while hal.now() < end and (self.frames - f0 < 4 or not self.head_straight):
            self.tick()
            self.wait_period()
        return out

    def request_peek(self, side=None):
        """side: +1 stanga, -1 dreapta, None = alterneaza."""
        if side is None:
            side = self._peek_side
            self._peek_side = -side
        self._peek_phase = "out"
        self._peek_side_now = side
        self.set_pan(side * cfg.PAN_PEEK_DEG)
        self._peek_until = self.head_ready_t + 0.10
        self._peek_got = False
        self.peeks += 1
        self._last_peek = self.hal.now()

    def _head_step(self, t):
        if self.hold_pan is not None:
            self.set_pan(self.hold_pan)
            return
        if self._peek_phase == "out":
            if (t >= self._peek_until and self._peek_got) or t >= self._peek_until + 0.3:
                self.peek_hits += self._peek_got
                self._peek_phase = "back"
                self.set_pan(self.base_pan)
        elif self._peek_phase == "back":
            if t >= self.head_ready_t:
                self._peek_phase = None
        else:
            if abs(self.pan_target - self.base_pan) > 0.5:
                self.set_pan(self.base_pan)
            elif (self.peek_ok and cfg.PEEK_ENABLED and t - self._last_peek >= (
                    cfg.PEEK_PERIOD_RESCUE if (self.use_est and t - self.est.lane_t > 0.8) else cfg.PEEK_PERIOD)):
                self.request_peek()

    @property
    def head_straight(self):
        return (abs(self.pan_target - self.base_pan) < 0.5 and self.hal.now() >= self.head_ready_t
                and self._peek_phase is None)

    # ------------------------------------------------------------------ odometrie
    def _odometry(self, t, dt):
        hal = self.hal
        batt = 1.0
        if cfg.BATT_COMP:
            try:
                v = hal.battery()[0]
                if v:
                    batt = max(0.7, min(1.0, v / cfg.BATTERY_FULL_VOLTAGE))
            except Exception:
                pass
        pct = self.speed_cmd
        v_cmd = 0.0 if abs(pct) < cfg.SPEED_MIN * 0.8 else cfg.V_PER_PCT * pct * batt * self.v_scale
        a = 1.0 - math.exp(-dt / 0.22)
        self.v_est += (v_cmd - self.v_est) * a
        tgt = math.radians(self.steer_cmd * cfg.WHEEL_PER_SERVO)
        maxd = math.radians(420.0) * dt
        self.delta_est += max(-maxd, min(maxd, tgt - self.delta_est))
        ds = self.v_est * dt
        dth = ds * math.tan(self.delta_est) / cfg.WHEELBASE
        gyro = hal.yaw_rate()
        if gyro is not None:
            dth = math.radians(gyro) * dt
        return ds, dth

    def pose_delta(self, t_cap):
        """Miscarea masinii (dx,dy,dth) in cadrul de la t_cap, pana acum."""
        x = y = th = 0.0
        for (t, ds, dth) in self.odo:
            if t <= t_cap:
                continue
            x += ds * math.cos(th + 0.5 * dth)
            y += ds * math.sin(th + 0.5 * dth)
            th += dth
        return x, y, th

    def reset_odometry(self):
        self.dist_acc = 0.0
        self.path_acc = 0.0
        self.yaw_acc = 0.0

    # ------------------------------------------------------------------ ciclu de simtire
    def tick(self):
        hal = self.hal
        t = hal.now()
        if self.t_last is None:
            self.t_last = t
        dt = max(1e-3, t - self.t_last)
        self.t_last = t
        ds, dth = self._odometry(t, dt)
        self.odo.append((t, ds, dth))
        self.yaw_acc += dth
        self.dist_acc += ds
        self.path_acc += abs(ds)
        if self.use_est:
            self.est.propagate(ds, dth)
        self.last_ds, self.last_dth = ds, dth
        self.frame_event = None
        self.sonar_event = None
        self._head_step(t)
        if self.rec is not None:
            self.rec.begin(self, t)

        # ultrasonic: doar daca capul s-a stabilizat
        if t >= self.head_ready_t:
            try:
                r = hal.sonar()
            except Exception:
                r = None
            pan = hal.pan_now() if abs(self.pan_target) > 0.5 else 0.0
            if abs(pan - self.pan_target) < 4.0:
                if self.use_est:
                    self.est.ingest_sonar(r, self.pan_target, t)
                self.sonar_event = (r, self.pan_target, t)
                if self._peek_phase == "out" and r is not None:
                    self._peek_got = True
                if self.use_est and self.speedcal is not None and abs(self.pan_target) < 2.0:
                    self.speedcal.update(self, r, self.est.psi, self.steer_cmd, self.speed_cmd, t)

        # camera: doar cand capul e drept de la o vreme
        fr = hal.frame()
        if fr is not None:
            img, t_frame, new = fr
            if new:
                t_cap = t_frame - CAM_LATENCY
                if self.hold_pan is None and abs(self.pan_target - self.base_pan) < 0.5 \
                        and t_cap >= self.head_ready_t and self._peek_phase is None:
                    per = self.perceiver.process(img, self.pan_target, t_cap)
                    self.frame_event = (per, t_cap, self.pose_delta(t_cap))
                    self.last_img = img
                    self._show_color(per)
                    if self.use_est and self.pitchcal is not None:
                        try:
                            self.pitchcal.update(self.perceiver.last_v, self.perceiver.last_has,
                                                 self.pan_target - self.base_pan, self.est.psi)
                        except Exception:
                            pass
                    if self.use_est:
                        self.est.ingest_camera(per, t, self.pose_delta(t_cap))
                    if self.use_est and self.sonarcal is not None:
                        self.sonarcal.update(self.est, self.pan_target - self.base_pan, t, self.steer_cmd)
                    self.last_img, self.last_per = img, per
                    self.frames += 1
                elif self.hold_pan is not None:
                    self.last_img = img
        if self.rec is not None:
            self.rec.end(self)
        world = self.est.snapshot(t, self.head_straight) if self.use_est else None
        self.ticks += 1
        return world

    def _show_color(self, per):
        """Farurile RGB: stalpul cel mai apropiat, altfel linia portocalie/albastra, altfel galben daca vede peretele."""
        lights = getattr(self.hal, "lights", None)
        if lights is None:
            return
        color = per.line_events[-1] if per.line_events else None
        if per.pillars:
            color = min(per.pillars, key=lambda b: b.X).color
        if color is None and (per.state == 1).sum() >= 0.3 * len(per.state):     # 1 = ST_WALL
            color = "wall"
        if color and color != lights.shown:
            lights.set_color(color)

    def wait_period(self):
        """Doarme pana la urmatorul pas al buclei (compenseaza timpul de calcul)."""
        period = 1.0 / cfg.LOOP_HZ
        now = self.hal.now()
        if self._deadline is None or now - self._deadline > 5 * period:
            self._deadline = now
        self._deadline += period
        self.hal.sleep(max(0.0, self._deadline - self.hal.now()))

