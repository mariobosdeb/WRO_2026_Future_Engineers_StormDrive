"""Driver: masina de stari a misiunii (Open + Obstacle).

Stari:  LANE (centrare pe culoar)  ->  TURN (viraj de colt)  ->  LANE ...  ->  FINISH / PARK
        RECOVER (marsarier cand ceva e prea aproape in fata)

Coltul se detecteaza GEOMETRIC: peretele interior se termina (deschidere) si peretele exterior
din fata da latimea culoarului urmator.  Centrul culoarului urmator e la x* = (X_front + X_colt)/2
(cadrul masinii).  Cu raza de viraj R, virajul la directie maxima incepe cand x* - R <= margine.
"""
import math

from . import config as cfg
from .robot import Brain
from .plan import Planner, build_obstacles


def sgn(x):
    return 1.0 if x >= 0 else -1.0


class Driver:
    def __init__(self, hal, mode=None, verbose=None):
        self.hal = hal
        self.mode = mode or cfg.MODE
        self.verbose = cfg.VERBOSE if verbose is None else verbose
        self.b = Brain(hal)
        if (mode or cfg.MODE) == "obstacle":
            self.b.est.W_fixed = 1.0
        self.dir = cfg.FORCE_DIRECTION         # +1 CCW (interior stanga), -1 CW
        self.dir_src = "forta" if cfg.FORCE_DIRECTION else ""
        self.state = "LANE"
        self.corners = 0
        self.path_last_turn = -1.0
        self.turn_same = False
        self.turn_target = cfg.TURN_HANDOFF_YAW
        self.yaw0 = 0.0
        self.turn_sgn = 1.0
        self.turn_t0 = 0.0
        self.I = 0.0
        self.T = 0.0
        self.done = False
        self.reason = ""
        self.t0 = None
        self.finish_path0 = None
        self.start_path0 = 0.0
        self.gain_n = 0
        self.gain_ref = None
        self.p_start = None         # cat a mers de la start pana la primul viraj
        self.p_sec = None           # cat dureaza sectiunea de start intre viraj 4 si viraj 5
        self.finish_dist = cfg.FINISH_TRAVEL
        self._prog = None
        self._looked = -1           # indexul coltului pentru care am facut deja "oprire si privire"
        self.look_t0 = 0.0
        self.look_f0 = 0
        self._vs_logged = 1.0
        self.f0_samples = []        # distanta frontala (sonar) la start: referinta pentru oprirea finala
        self.dir_score = 0.0        # vot directie: + = CCW (stanga), - = CW (dreapta)
        self.dir_why = []
        self._dsum0 = []            # stanga+dreapta (ultrasonic) la inceput = latimea culoarului
        self._dlast = {}            # ultima citire laterala pe fiecare parte (+1 stanga, -1 dreapta)
        self._dnone = {1: 0, -1: 0}
        self.f0 = None
        self.rec_path0 = None
        self.rec_steer = 0.0
        self.trace = []
        self.events = []
        if self.mode == 'open' and cfg.OPEN_KF:
            self.b.est.auto_width = True
        if self.dir:
            self._on_dir()                     # sensul dat (--cw/--ccw): acelasi mod ca dupa descoperirea sensului
        self._seen_pillars = set()
        self._last_status = -1e9
        self.park = None                       # setat de parking.py (Obstacle)
        self.planner = Planner() if self.mode == "obstacle" else None
        self.turn_due_path = None
        self.turn_steer = cfg.TURN_STEER_DEG
        self.plan_info = {}
        self.u_target = 0.0
        self.constraint = False
        self.w = None
        self._last_blind = -1e9

    # ------------------------------------------------------------------ utilitare
    def log(self, msg):
        self.events.append((round(self.hal.now(), 2), msg))
        if self.verbose:
            print("[%6.2f] %s" % (self.hal.now(), msg), flush=True)

    @property
    def turn_side(self):
        if self.dir is None:
            return None
        return "left" if self.dir > 0 else "right"

    def half_free(self, w):
        W = w.W or cfg.CORRIDOR_W_NOMINAL
        return W / 2.0 - cfg.CAR_WIDTH / 2.0

    # ------------------------------------------------------------------ pornire
    def start(self, settle=0.7):
        b = self.b
        self.t0 = self.hal.now()
        b.command_now(0.0, 0.0)
        end = self.hal.now() + settle
        while self.hal.now() < end:
            b.tick()
            b.wait_period()
        if hasattr(self.hal, "camera_ok"):
            self._save_start_photo()
        if getattr(cfg, "START_SCAN", True):
            try:
                sc = b.start_scan()
                self.log("scanare start (ultrasonic): stanga=%s fata=%s dreapta=%s" % tuple(
                    "--" if sc[k] is None else "%.0f cm" % (sc[k] * 100) for k in ("st", "fata", "dr")))
                if sc["st"] is not None and sc["dr"] is not None and sc["st"] > 1.3 and sc["dr"] > 1.3:
                    self.log("STOP: ultrasonicul nu vede nimic la stanga/dreapta pe 1.3 m => masina NU e intr-un culoar al pistei. Pune-o intre pereti si porneste din nou.")
                    self.done = True
                    self.reason = "nu e pe pista"
            except Exception as exc:
                self.log("scanarea de start a esuat: %s" % exc)
        b.reset_odometry()
        self.start_path0 = b.path_acc
        self.path_last_turn = b.path_acc - 0.2     # permitem primul colt aproape imediat
        self.log("start (directie %s)" % {None: "necunoscuta", 1: "CCW", -1: "CW"}[self.dir])

    def _save_start_photo(self):
        """debug/start_<timp>.jpg: stanga ce vede camera, dreapta ce detecteaza (portocaliu/albastru/negru-perete)."""
        img = self.b.last_img
        if img is None:
            self.log("poza de start: camera nu a dat niciun cadru")
            return
        try:
            import os
            import time
            import cv2
            import numpy as np
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            ann = (img // 3).copy()
            y0 = int(img.shape[0] * cfg.LINE_ROI_TOP)
            cnt = {}
            for name, (lo, hi), col in (("orange", cfg.ORANGE, (0, 140, 255)), ("blue", cfg.BLUE, (255, 80, 0))):
                m = cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
                m[:y0] = 0
                ann[m > 0] = col
                cnt[name] = int(cv2.countNonZero(m))
            per = self.b.last_per
            if per is not None and getattr(per, "dark_thr", None) is not None:
                ann[(hsv[:, :, 2] < per.dark_thr) & (ann.sum(axis=2) < 200)] = (0, 0, 120)
            cv2.line(ann, (0, y0), (ann.shape[1], y0), (255, 255, 255), 1)
            cv2.putText(ann, "portocaliu %d  albastru %d" % (cnt["orange"], cnt["blue"]), (4, 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            path = os.path.join(cfg.DEBUG_DIR, "start_%d.jpg" % int(time.time()))
            cv2.imwrite(path, np.hstack([img, ann]))
            self.log("poza de start: %s (pixeli portocaliu=%d albastru=%d)" % (path, cnt["orange"], cnt["blue"]))
        except Exception as exc:
            self.log("poza de start nesalvata: %s" % exc)

    def run(self, max_time=None, on_tick=None):
        hal, b = self.hal, self.b
        if self.t0 is None:
            self.start()
        limit = cfg.ROUND_TIME_LIMIT if max_time is None else max_time
        while not self.done:
            w = b.tick()
            self.w = w
            self.step(w)
            if on_tick is not None:
                on_tick(self, w)
            if hal.now() - self.t0 > limit:
                self.reason = "timeout"
                self.log("timp limita")
                break
            b.wait_period()
        b.stop()
        return self.reason

    # ------------------------------------------------------------------ pas
    def _on_dir(self):
        if self.mode == "open" and cfg.OPEN_OUTER:
            self.b.est.set_outer("right" if self.dir > 0 else "left")

    def report(self, w):
        """Mesaje pentru operator: ce a vazut (linii, stalpi) si starea curenta."""
        if not self.verbose:
            return
        RO = {"orange": "PORTOCALIE", "blue": "ALBASTRA", "red": "ROSU", "green": "VERDE"}
        for c in w.line_events:
            self.log("A VAZUT LINIE %s pe podea" % RO.get(c, c))
        for p in w.pillars:
            key = (p.color, round(p.X, 1), round(p.Y, 1))
            if id(p) not in self._seen_pillars:
                self._seen_pillars.add(id(p))
                self.log("A VAZUT STALP %s la %.2f m in fata, %s (%.2f m)" % (
                    RO.get(p.color, p.color), p.X, "stanga" if p.Y > 0 else "dreapta", abs(p.Y)))
        t = self.hal.now()
        if t - self._last_status >= cfg.STATUS_PERIOD_S:
            self._last_status = t
            f = lambda v: "--" if v is None else "%.2f" % v
            pil = ",".join("%s@%.1f" % (RO.get(p.color, p.color)[0], p.X) for p in w.pillars[:3])
            print("[%6.1f] %-7s fata=%s | st=%s dr=%s | y=%+.2f psi=%+3.0f | colt_st=%s colt_dr=%s | stalpi:%s | volan=%+.0f" % (
                t, self.state, f(w.front_obs if w.front_obs is not None else w.front), f(w.dl), f(w.dr),
                w.y_off or 0.0, math.degrees(w.psi or 0.0),
                f(None if w.corner.get("left") is None else w.corner["left"].X),
                f(None if w.corner.get("right") is None else w.corner["right"].X),
                pil or "-", self.b.steer_cmd), flush=True)

    # ------------------------------------------------------------------ oprire si privire inainte de colt (Obstacle)
    def begin_look(self, why):
        """Stalpii din culoarul urmator, aproape de colt, sunt ascunsi dupa peretele interior pana foarte aproape: oprim, intoarcem
        capul spre noul culoar si memoram stalpii inainte sa intram in viraj."""
        b = self.b
        self.state = "LOOK"
        self.look_t0 = self.hal.now()
        self.look_f0 = b.frames
        b.base_pan = self.dir * cfg.CORNER_LOOK_PAN
        b.stop()
        self.log("OPRESC si ma uit spre noul culoar (stalpi dupa colt) - motiv viraj: %s" % why)

    def look_step(self, w):
        b = self.b
        b.base_pan = self.dir * cfg.CORNER_LOOK_PAN
        b.stop()
        t = self.hal.now() - self.look_t0
        if (b.frames - self.look_f0 >= cfg.CORNER_LOOK_FRAMES and t > 0.25) or t > cfg.CORNER_LOOK_MAX_S:
            self._looked = self.corners
            b.base_pan = 0.0
            self.state = "LANE"

    def _front_ref(self, w):
        """Distanta frontala folosita ca referinta la oprirea finala: Open = sonar (nu sunt stalpi), Obstacle = doar peretele."""
        fo = w.front_obs
        if self.mode == "open" or fo is None:
            return fo
        for p in w.pillars:                       # un stalp in fata ar fi luat drept perete
            if abs(p.Y) < 0.30 and 0.0 < p.X < fo + 0.12:
                return None
        return fo

    def stuck_check(self, w):
        """Odometria nu stie ca rotile patineaza: masina agatata de un stalp/perete "inainteaza" doar in calcul.
        Verificam cu senzorii: in ~STUCK_TIME_S masina a "mers" >= STUCK_MIN_M dar distanta frontala (sonar) sau stalpul cel mai
        apropiat nu s-au apropiat deloc, iar y si psi (vedere) nu s-au schimbat => blocata."""
        b = self.b
        t = self.hal.now()
        ok = b.speed_cmd > 0 and self.state == "LANE" and w.front_obs is not None or \
            (b.speed_cmd > 0 and self.state == "LANE" and bool(w.pillars))
        if not ok:
            self._prog = None
            return False
        pillX = min((p.X for p in w.pillars if abs(p.Y) < 0.45 and p.X > -0.05), default=None)
        cur = (t, b.path_acc, w.front_obs if w.front_age < 0.3 else None, pillX, w.y_off or 0.0, w.psi or 0.0)
        if self._prog is None:
            self._prog = cur
            return False
        t0, p0, f0, x0, y0, s0 = self._prog
        if t - t0 < cfg.STUCK_TIME_S:
            return False
        adv = b.path_acc - p0
        self._prog = cur
        if adv < cfg.STUCK_MIN_M:
            return False
        closer = []
        if f0 is not None and cur[2] is not None:
            closer.append(f0 - cur[2])
        if x0 is not None and cur[3] is not None:
            closer.append(x0 - cur[3])
        if not closer:
            return False
        if max(closer) < 0.25 * adv and abs(cur[4] - y0) < 0.06 and abs(cur[5] - s0) < math.radians(12):
            self.log("BLOCAT: a 'mers' %.2f m dar nu s-a apropiat de nimic" % adv)
            self.begin_recover(w, "blocat (nu inainteaza)")
            return True
        return False

    def step(self, w):
        self.report(w)
        if w.lane_age > 1.0 and self.hal.now() - self._last_blind > 2.0:
            self._last_blind = self.hal.now()
            ss = self.b.est.side_sonar
            f = lambda v: "--" if v is None or self.hal.now() - v[1] > 3.0 else "%.0f cm" % (v[0] * 100)
            self.log("CAMERA NU VEDE PERETII de %.1f s -> ma bazez pe ultrasonic: stanga=%s dreapta=%s fata=%s | cap=%+.0f priviri laterale %d/%d" % (
                min(w.lane_age, 99.0), f(ss["left"]), f(ss["right"]),
                "--" if w.front_obs is None else "%.0f cm" % ((w.front_obs - cfg.REAR_TO_HEAD) * 100),
                self.b.pan_target, self.b.peek_hits, self.b.peeks))
        if cfg.STUCK_TIME_S and self.stuck_check(w):
            return
        st = self.state
        if st == "LANE":
            self.lane_step(w)
        elif st == "TURN":
            self.turn_step(w)
        elif st == "FINISH":
            self.finish_step(w)
        elif st == "RECOVER":
            self.recover_step(w)
        elif st == "LOOK":
            self.look_step(w)
        elif st == "PARK" and self.park is not None:
            self.park.step(self, w)
        if len(self.trace) < 20000:
            self.trace.append((round(w.t, 2), self.state, round(w.y_off or 0, 3), round(math.degrees(w.psi or 0), 1),
                               round(self.b.steer_cmd, 1)))

    # ------------------------------------------------------------------ control culoar
    def lane_command(self, w, u_t=0.0, speed=None, ky_scale=1.0):
        b = self.b
        W = w.W or cfg.CORRIDOR_W_NOMINAL
        lim = max(0.0, W / 2.0 - cfg.CAR_WIDTH / 2.0 - cfg.MARGIN_WALL)
        u_t = max(-lim, min(lim, u_t))
        y = w.y_off if w.y_off is not None else 0.0
        psi = math.degrees(w.psi) if w.psi is not None else 0.0
        eo = b.est.outer_only
        if eo and self.mode == "open":
            # latimea necunoscuta: acceptam orice pozitie intre [OUTER_BAND] fata de peretele exterior (nu impingem spre perete)
            lo, hi = (-cfg.OUTER_BAND_NEAR, cfg.OUTER_BAND_FAR) if eo == "right" else (-cfg.OUTER_BAND_FAR, cfg.OUTER_BAND_NEAR)
            u_t = max(lo, min(hi, y))
        err = y - u_t
        dt = 1.0 / cfg.LOOP_HZ
        self.I = max(-cfg.I_CLAMP_M * cfg.KY_I, min(cfg.I_CLAMP_M * cfg.KY_I, self.I + err * dt * cfg.KY_I))
        if abs(psi) > 25.0:
            self.I = 0.0
        psi_des = -max(-cfg.PSI_APPROACH_MAX, min(cfg.PSI_APPROACH_MAX, cfg.KY_DEG_PER_M * ky_scale * err / cfg.KPSI))
        if cfg.TRIM_LEARN and abs(psi) < 5.0 and w.lane_age < 0.5 and b.path_acc - self.path_last_turn > 0.6 and self.state == 'LANE':
            self.T = max(-cfg.TRIM_CLAMP, min(cfg.TRIM_CLAMP, self.T + cfg.TRIM_KI * (psi - psi_des) * dt))
        steer = -cfg.KPSI * (psi - psi_des) - self.I - self.T
        # siguranta: prea aproape de un perete => impinge spre centru
        if w.dl is not None and w.dr is not None and w.lane_age < 0.5:
            gl = w.dl - cfg.CAR_WIDTH / 2.0
            gr = w.dr - cfg.CAR_WIDTH / 2.0
            if gl < cfg.MARGIN_WALL and eo != "right":      # in modul "perete exterior" nu stim distanta pana la peretele interior
                steer -= 220.0 * (cfg.MARGIN_WALL - gl)
            if gr < cfg.MARGIN_WALL and eo != "left":
                steer += 220.0 * (cfg.MARGIN_WALL - gr)
        # castigurile sunt acordate in grade de ROATA (nu de servo): impartim la raportul roata/servo, ca bucla sa ramana la fel
        steer = steer * cfg.NOMINAL_WPS / max(0.15, cfg.WHEEL_PER_SERVO) if cfg.NORMALIZE_STEER else steer
        if speed is None:
            speed = cfg.SPEED_STRAIGHT
        if w.lane_age > cfg.HOLD_ESTIMATE_S:
            speed = min(speed, cfg.SPEED_CAUTIOUS)
        b.command(steer, speed)

    # ------------------------------------------------------------------ colturi
    def corner_x_star(self, w, side):
        """Centrul culoarului urmator pe axa X (cadrul masinii) sau None."""
        Wn = w.W or cfg.CORRIDOR_W_NOMINAL
        c = w.corner.get(side)
        Xf = w.front
        if self.mode == "open" and cfg.TURN_BY_FRONT and Xf is not None and self.dir is not None and w.front_age < 0.5:
            # peretele din fata e masurat precis (sonar+camera): dupa viraj masina trebuie sa fie la ~0.5*OUTER_W de peretele
            # exterior (cel din fata), deci arcul incepe cand Xf = R + 0.5*OUTER_W, indiferent de latimea culoarului urmator.
            xs_w = Xf - 0.5 * cfg.OUTER_W
            xs_c, why_c = self._corner_xs_corner(w, side, Wn, c, Xf)
            if xs_c is None or xs_w <= xs_c:
                return xs_w, "perete"
            return xs_c, why_c
        return self._corner_xs_corner(w, side, Wn, c, Xf)

    def _corner_xs_corner(self, w, side, Wn, c, Xf):
        if c is not None and w.open_vis.get(side):
            Xc = c.X
            if Xf is not None and 0.40 < Xf - Xc < 1.35:
                return 0.5 * (Xf + Xc), "colt+perete"
            return Xc + 0.5 * Wn, "colt"
        if Xf is not None and self.dir is not None:
            return Xf - 0.5 * Wn, "perete"
        return None, ""

    def _dir_vote(self, v, why):
        self.dir_score += v
        self.dir_why.append(why)

    def discover_direction(self, w):
        """Vot din trei surse; decide cand |scor| >= DIR_DECIDE (culoarea singura are nevoie de 2 cadre)."""
        b = self.b
        # 1) linia colorata de pe podea, doar cat timp prima linie e inca in fata (perete fata departe)
        fe = b.frame_event
        far = w.front is not None and w.front_age < 0.5 and w.front > cfg.DIR_COLOR_MIN_FRONT
        if fe is not None and far:
            o = (fe[0].lines.get("orange") or {}).get("px", 0)
            bl = (fe[0].lines.get("blue") or {}).get("px", 0)
            if max(o, bl) >= cfg.LINE_MIN_PIXELS and max(o, bl) >= 2 * min(o, bl):
                self._dir_vote(-1 if o > bl else +1, "%s %d px" % ("portocaliu" if o > bl else "albastru", max(o, bl)))
        # 2) coltul vazut de camera (geometria peretilor)
        for s_ in ("left", "right"):
            c = w.corner.get(s_)
            if c is not None and w.open_vis.get(s_) and (c.n >= 2 or c.src == "line") and c.X > 0.2:
                self._dir_vote(2 if s_ == "left" else -2, "colt %s la %.2f m" % ("stanga" if s_ == "left" else "dreapta", c.X))
                break
        # 3) ultrasonic lateral: peretele interior se termina => gol (fara ecou sau culoar brusc mai lat)
        se = b.sonar_event
        if se is not None and abs(se[1]) >= 45.0:
            side = 1 if se[1] > 0 else -1
            r = se[0]
            if r is None:
                self._dnone[side] += 1
                if self._dnone[side] >= 3 and self._dlast.get(-side) is not None:
                    self._dir_vote(2 * side, "ultrasonic %s fara ecou" % ("stanga" if side > 0 else "dreapta"))
                    self._dnone[side] = 0
            else:
                self._dnone[side] = 0
                self._dlast[side] = r
                other = self._dlast.get(-side)
                if other is not None:
                    tot = r + other
                    if len(self._dsum0) < 4:
                        self._dsum0.append(tot)
                    elif tot > sorted(self._dsum0)[len(self._dsum0) // 2] + cfg.DIR_SONAR_JUMP:
                        self._dir_vote(2 * side, "ultrasonic %s %.2f m (culoar mai lat)" % ("stanga" if side > 0 else "dreapta", r))
        if abs(self.dir_score) >= cfg.DIR_DECIDE:
            self.dir = +1 if self.dir_score > 0 else -1
            self._on_dir()
            self.log("directie: %s (scor %+.0f: %s)" % ("CCW, stanga" if self.dir > 0 else "CW, dreapta",
                                                        self.dir_score, "; ".join(self.dir_why[-4:])))

    def lane_step(self, w):
        b = self.b
        if b.speedcal is not None and abs(b.v_scale - self._vs_logged) > 0.04:
            self._vs_logged = b.v_scale
            self.log("viteza reala / V_PER_PCT = %.2f (calibrata cu sonarul, ultima masuratoare %.2f)" % (b.v_scale, b.speedcal.last_ratio or 0.0))
        fref = self._front_ref(w)
        if self.corners == 0 and self.f0 is None and b.path_acc - self.start_path0 < 0.40 and fref is not None \
                and w.front_age < 0.3 and abs(w.psi or 0.0) < math.radians(8):
            self.f0_samples.append(fref)
            if len(self.f0_samples) >= cfg.FINISH_F0_N:
                self.f0 = sorted(self.f0_samples)[len(self.f0_samples) // 2]
                self.log("referinta frontala la start: %.2f m" % self.f0)
        self.check_gain(w)
        if self.dir is None:
            self.discover_direction(w)
        side = self.turn_side
        look = (self.mode == "open" and self.dir and cfg.PAN_LOOK_DEG
                and w.corner.get(side) is None and b.path_acc - self.path_last_turn >= 0.6 and w.lane_age < 0.8)
        b.base_pan = (self.dir * cfg.PAN_LOOK_DEG) if look else 0.0
        R = cfg.turn_radius()
        if self.ktm():
            R = cfg.KT_R_TRIGGER
        approach = False
        if side is not None and b.path_acc - self.path_last_turn >= cfg.CORNER_LOCKOUT_M:
            xs, why = self.corner_x_star(w, side)
            if xs is not None:
                d_geo = xs - R - cfg.TURN_MARGIN
                if d_geo <= (cfg.EARLY_TURN_M if self.mode == "obstacle" else 0.0):
                    if self.mode == "obstacle" and cfg.CORNER_LOOK and self._looked != self.corners and self.dir:
                        self.begin_look(why)
                        return
                    if self.turn_allowed(w, d_geo):
                        self.begin_turn(w, why)
                        return
                else:
                    self.turn_due_path = None
                approach = xs - R < 0.45
                if self.mode == "obstacle" and d_geo < cfg.OBS_LOOK_DIST:
                    b.base_pan = self.dir * cfg.OBS_LOOK_DEG      # vedem stalpii de dupa colt (ascunsi dupa peretele interior)
            if w.front is not None and w.front <= cfg.FRONT_FORCE and abs(w.psi or 0.0) < math.radians(25):
                self.begin_turn(w, "perete aproape")
                return
        elif side is None and w.front is not None and w.front <= cfg.FRONT_FORCE + 0.05:
            # nicio informatie despre colt: alege partea mai libera
            dl, dr = (w.dl or 0.0), (w.dr or 0.0)
            self.dir = (+1 if self.dir_score > 0 else -1) if self.dir_score else (+1 if dl >= dr else -1)
            self._on_dir()
            self.log("directie (fortat): %s" % ("CCW" if self.dir > 0 else "CW"))
            self.begin_turn(w, "perete aproape")
            return
        # siguranta frontala
        gap = (w.front_obs - cfg.REAR_TO_FRONT) if w.front_obs is not None else None
        if gap is not None and gap < cfg.FRONT_STOP_GAP and w.front_age < 0.4 and b.speed_cmd > 0:
            self.begin_recover(w, "obstacol/perete la %.0f cm in fata" % (gap * 100))
            return
        speed = cfg.SPEED_STRAIGHT
        if approach:
            speed = cfg.SPEED_CORNER
        if self.mode == "obstacle":
            self.plan_command(w, min(speed, cfg.SPEED_OBSTACLE))
        else:
            self.lane_command(w, 0.0, speed)

    # ------------------------------------------------------------------ planificator (Obstacle)
    def make_obstacles(self, w, next_pillars=False):
        side = self.turn_side
        W = w.W if w.W else (1.0 if self.mode == "obstacle" else cfg.CORRIDOR_W_NOMINAL)
        W = max(0.8, min(1.15, W)) if self.mode == "obstacle" else W
        corner = None
        if side is not None:
            c = w.corner.get(side)
            if c is not None and w.open_vis.get(side):
                corner = (c.X, c.Y)
        psi, y0 = (w.psi or 0.0), (w.y_off or 0.0)
        sp, cp = math.sin(psi), math.cos(psi)
        cs = None
        if corner is not None:
            cs = corner[0] * math.cos(psi) - corner[1] * sp          # s al coltului in cadrul culoarului
        sg = float(self.dir) if self.dir else 0.0
        pil = []
        for p in w.pillars:
            if not (-0.35 < p.X < 2.6 and abs(p.Y) < 1.3):
                continue
            s_ = p.X * cp - p.Y * sp
            u_ = y0 + p.X * sp + p.Y * cp
            if abs(u_) < W / 2.0 - 0.06:
                pil.append(p)
            elif next_pillars and cs is not None and sg and s_ > cs - 0.05 and s_ < cs + W + 0.1 and sg * u_ > W / 2.0 - 0.05:
                pil.append(p)                                       # stalp din sectiunea de dupa colt
        obs, s_c, s_f = build_obstacles(w, self.dir, W, w.psi or 0.0, w.y_off or 0.0, corner, w.front, pil)
        return obs, W, s_c, s_f

    def plan_command(self, w, speed):
        obs, W, s_c, s_f = self.make_obstacles(w)
        steer, info = self.planner.plan(w.y_off or 0.0, w.psi or 0.0, obs)
        self.plan_info = info
        if w.lane_age > cfg.HOLD_ESTIMATE_S:
            speed = min(speed, cfg.SPEED_CAUTIOUS)
        self.b.command(steer, speed)

    def turn_allowed(self, w, d_geo):
        """Obstacle: alege momentul virajului (inainte de punctul geometric daca asa se evita un stalp,
        sau intarziat pana la o limita) simuland arcul + 0.5 m dupa colt cu peretii si stalpii cunoscuti."""
        if self.mode != "obstacle" or self.planner is None:
            return True
        b = self.b
        if d_geo <= 0 and self.turn_due_path is None:
            self.turn_due_path = b.path_acc
        waited = (b.path_acc - self.turn_due_path) if self.turn_due_path is not None else 0.0
        d_max = max(0.05, 0.5 - 0.15)
        o_hi = max(0.0, d_geo) + max(0.0, d_max - waited) if d_geo > 0 else max(0.0, d_max - waited)
        if d_geo <= 0:
            o_hi = max(0.0, d_max - waited)
            d_geo_eff = 0.0
        else:
            d_geo_eff = d_geo
            o_hi = d_geo + d_max
        obs, W, s_c, s_f = self.make_obstacles(w, next_pillars=True)
        off, st, pen0, penb = self.planner.best_turn_offset(w.y_off or 0.0, w.psi or 0.0, self.dir, obs,
                                                             o_hi, d_pref=d_geo_eff)
        self.turn_steer = st
        ok = off <= 1e-6
        if not ok:
            self.plan_info = {"turn_pen": pen0, "turn_best": penb, "turn_off": off}
        return ok

    def begin_turn(self, w, why):
        b = self.b
        if self.mode != "obstacle":
            self.turn_steer = cfg.TURN_STEER_DEG
        self.state = "TURN"
        self.turn_due_path = None
        b.base_pan = 0.0
        self.turn_sgn = +1.0 if self.dir > 0 else -1.0
        self.yaw0 = b.yaw_acc
        self.psi0_est = b.est.psi
        self.turn_t0 = self.hal.now()
        self.turn_ref = self._turn_reference(w)
        self.kt_phase = 'f'
        self.kt_n = 0
        self.turn_same = self.corners > 0 and b.path_acc - self.path_last_turn < cfg.CORNER_SAME_M
        self.turn_target = cfg.TURN_HANDOFF_YAW
        if self.turn_same:
            self.turn_target = max(25.0, min(45.0, math.degrees(w.psi or 0.0) * self.turn_sgn))   # cat lipseste pana la aliniere
            self.log("CONTINUI virajul (colt %d, la %.2f m dupa virajul anterior) - motiv: %s | perete fata la %s m" % (
                self.corners, b.path_acc - self.path_last_turn, why, None if w.front is None else round(w.front, 2)))
            self.turn_step(w)
            return
        if self.corners == 0 and self.p_start is None:
            self.p_start = b.path_acc - self.start_path0
        elif self.corners == 4 and self.p_sec is None:
            self.p_sec = b.path_acc - self.path_last_turn
        self.log("VIREZ (colt %d/%d) - motiv: %s | colt la %s m, perete fata la %s m" % (self.corners + 1, cfg.TOTAL_CORNERS, why,
                 None if w.corner[self.turn_side] is None else round(w.corner[self.turn_side].X, 2),
                 None if w.front is None else round(w.front, 2)))
        self.turn_step(w)

    def ktm(self):
        """True daca raza reala e prea mare pentru un colt dintr-o miscare -> viraj in mai multe miscari."""
        return cfg.turn_radius() > cfg.KT_R_MIN

    def learn_gain(self, turned_vis, psi_new):
        """Dupa viraj notam rotatia; peste ~0.8 s camera ne spune unde suntem de fapt (check_gain)."""
        if not cfg.LEARN_GAIN or self.gain_n >= cfg.LEARN_GAIN_MAX_TURNS:
            return
        b = self.b
        if cfg.SPEEDCAL and b.speedcal is not None and b.speedcal.n_updates < cfg.LEARN_GAIN_MIN_SPEEDCAL:
            return                          # fara viteza calibrata, rotatia observata ar fi atribuita gresit rotilor
        odo = math.degrees(b.yaw_acc - self.yaw0) * self.turn_sgn
        self.gain_ref = dict(turned=turned_vis, odo=odo, psi_new=psi_new, yaw_end=b.yaw_acc, t=self.hal.now())

    def check_gain(self, w):
        g = self.gain_ref
        if g is None:
            return
        b = self.b
        now = self.hal.now()
        if now - g["t"] < cfg.LEARN_GAIN_DELAY:
            return
        self.gain_ref = None
        if w.lane_age > 0.25 or w.lane_sides < 1 or b.est._kf_fresh:
            return
        delta = b.yaw_acc - g["yaw_end"]
        resid = w.psi - (g["psi_new"] + delta)
        if abs(math.degrees(resid)) > 40.0:
            return
        true_turn = g["turned"] + self.turn_sgn * math.degrees(resid)
        odo = g["odo"]
        if odo < 25.0 or true_turn < 25.0:
            return
        r = true_turn / odo
        a = cfg.LEARN_GAIN_RATE if self.gain_n > 0 else 1.0
        k = max(0.8, min(1.25, 1.0 + a * (r - 1.0)))
        new = max(cfg.WHEEL_PER_SERVO_MIN, min(cfg.WHEEL_PER_SERVO_MAX, cfg.WHEEL_PER_SERVO * k))
        self.gain_n += 1
        self.log("invatare roata/servo: rotatie reala %.0f / odometrie %.0f => WHEEL_PER_SERVO %.3f -> %.3f (raza %.2f m)" % (
            true_turn, odo, cfg.WHEEL_PER_SERVO, new, cfg.turn_radius()))
        cfg.WHEEL_PER_SERVO = new

    def turned_deg(self):
        """Cat s-a rotit in viraj: estimarea (odometrie + corectii din camera) sau doar odometria."""
        b = self.b
        odo = math.degrees(b.yaw_acc - self.yaw0) * self.turn_sgn
        if cfg.TURN_VISION_YAW:
            vis = math.degrees(b.est.psi - self.psi0_est) * self.turn_sgn
            if abs(vis - odo) < 40.0:
                return vis
        return odo

    def turn_step(self, w):
        b = self.b
        turned = self.turned_deg()
        if turned >= self.turn_target or self.hal.now() - self.turn_t0 > (cfg.KT_MAX_TIME if self.ktm() else cfg.TURN_MAX_TIME):
            self.end_turn(turned)
            return
        gap = (w.front_obs - cfg.REAR_TO_FRONT) if w.front_obs is not None else None
        if self.ktm():
            if self.kt_phase == 'f':
                if gap is not None and gap < cfg.KT_FRONT_GAP and w.front_age < 0.3:
                    self.kt_phase = 'r'
                    self.kt_path0 = b.path_acc
                    self.kt_n += 1
                    b.stop()
                    return
                b.command_now(self.turn_sgn * cfg.TURN_STEER_DEG, cfg.SPEED_CORNER)
            else:
                if b.path_acc - self.kt_path0 >= cfg.KT_REV_M or self.kt_n > 6:
                    self.kt_phase = 'f'
                    b.stop()
                    return
                b.command_now(-self.turn_sgn * cfg.TURN_STEER_DEG, -cfg.SPEED_REVERSE)
            return
        if gap is not None and gap < cfg.FRONT_STOP_GAP and turned < 40 and w.front_age < 0.3:
            self.begin_recover(w, "perete la %.0f cm in fata in timpul virajului" % (gap * 100))
            return
        b.command_now(self.turn_sgn * self.turn_steer, cfg.SPEED_CORNER)

    def _turn_reference(self, w):
        """Pozitia coltului in cadrul culoarului vechi (ca sa stim unde suntem in culoarul nou)."""
        psi, y0 = (w.psi or 0.0), (w.y_off or 0.0)
        W = w.W if w.W else (1.0 if self.mode == "obstacle" else cfg.CORRIDOR_W_NOMINAL)
        xc = []
        c = w.corner.get(self.turn_side) if self.turn_side else None
        if c is not None:
            xc.append(c.X * math.cos(psi) - c.Y * math.sin(psi) + W / 2.0)
        if w.front is not None and w.front_age < 0.5:
            xc.append(w.front * math.cos(psi) - W / 2.0)
        return dict(psi=psi, y=y0, xc=(sum(xc) / len(xc) if xc else None))

    def end_turn(self, turned):
        b = self.b
        if self.turn_same:                      # acelasi colt, acelasi culoar: nu numaram, nu resetam culoarul
            self.path_last_turn = b.path_acc
            self.turn_steer = cfg.TURN_STEER_DEG
            self.I = 0.0
            self.log("continuare viraj terminata (colt %d) la %.0f grade" % (self.corners, turned))
            self.state = "FINISH" if self.corners >= cfg.TOTAL_CORNERS else "LANE"
            return
        self.corners += 1
        y_new = 0.0
        ref = getattr(self, "turn_ref", None)
        psi0 = ref["psi"] if ref else 0.0
        psi_new = psi0 + math.radians(turned - 90.0) * self.turn_sgn
        psi_new = max(-1.0, min(1.0, psi_new))
        if ref and ref["xc"] is not None and self.mode == "obstacle":
            dx, dy, dth = b.pose_delta(self.turn_t0)
            p0 = ref["psi"]
            x_l = dx * math.cos(p0) - dy * math.sin(p0)
            u_new = -self.turn_sgn * (x_l - ref["xc"])
            y_new = max(-0.4, min(0.4, u_new))
        b.est.reset_lane(psi=psi_new, y_off=y_new,
                         t=(self.hal.now() if (ref and ref["xc"] is not None and self.mode == "obstacle") else None))
        self.path_last_turn = b.path_acc
        self.turn_steer = cfg.TURN_STEER_DEG
        self.I = 0.0
        self.finish_path0 = b.path_acc
        if self.corners >= cfg.TOTAL_CORNERS and self.p_start is not None and self.p_sec is not None:
            self.finish_dist = max(0.15, min(2.0, self.p_sec - self.p_start - cfg.FINISH_MARGIN))
            self.log("oprire planificata la %.2f m dupa ultimul viraj (sectiune %.2f, start %.2f)" % (self.finish_dist, self.p_sec, self.p_start))
        self.learn_gain(turned, psi_new)
        self.log("viraj terminat (%d/%d) la %.0f grade" % (self.corners, cfg.TOTAL_CORNERS, turned))
        if self.corners >= cfg.TOTAL_CORNERS:
            self.state = "FINISH"
        else:
            self.state = "LANE"

    # ------------------------------------------------------------------ final
    def finish_step(self, w):
        b = self.b
        trav = b.path_acc - self.finish_path0
        by_front = False
        fref = self._front_ref(w)
        if cfg.FINISH_BY_FRONT and self.f0 is not None and fref is not None \
                and w.front_age < 0.3 and abs(w.psi or 0.0) < math.radians(8) and abs(trav - self.finish_dist) < 0.35 and trav > 0.5 * self.finish_dist:
            by_front = fref <= self.f0 - cfg.FINISH_F_MARGIN
            if by_front:
                self.log("oprire dupa distanta frontala: %.2f m (la start %.2f m)" % (fref, self.f0))
        if by_front or trav >= self.finish_dist + (cfg.FINISH_ODO_EXTRA if (cfg.FINISH_BY_FRONT and self.f0 is not None) else 0.0):
            b.stop()
            if self.mode == "obstacle" and cfg.PARKING_ENABLED and self.park is not None:
                self.state = "PARK"
                self.park.begin(self, w)
                return
            self.done = True
            self.reason = "finish"
            self.log("oprit in sectiunea de start")
            return
        u_t = 0.0
        speed = cfg.SPEED_CAUTIOUS
        if self.mode == "obstacle":
            self.plan_command(w, speed)
        else:
            self.lane_command(w, u_t, speed)
        if w.front is not None and w.front < 0.33:
            b.stop()
            self.done = True
            self.reason = "finish"

    # ------------------------------------------------------------------ recuperare
    def begin_recover(self, w, why="obstacol aproape in fata"):
        b = self.b
        self.log("DAU CU SPATELE: %s" % why)
        self.state = "RECOVER"
        self.rec_path0 = b.path_acc
        self.rec_steer = -sgn(b.steer_cmd) * cfg.STEER_MAX_DEG * 0.5 if abs(b.steer_cmd) > 3 else 0.0
        b.stop()

    def recover_step(self, w):
        b = self.b
        if b.path_acc - self.rec_path0 >= cfg.RECOVER_REVERSE_M:
            b.stop()
            self.state = "LANE"
            return
        b.command_now(self.rec_steer, -cfg.SPEED_REVERSE)

    # ------------------------------------------------------------------ stalpi (Obstacle)
    def plan_pillars(self, w):
        """Intoarce (u_tinta, factor_ky, viteza) din stalpii urmariti.

        Roșu: stalpul ramane in STANGA masinii (treci prin dreapta lui).  Verde: stalpul ramane in DREAPTA.
        """
        self.constraint = False
        psi = w.psi or 0.0
        y = w.y_off or 0.0
        need = cfg.PILLAR_HALF + cfg.PASS_CLEAR + cfg.CAR_WIDTH / 2.0
        c, s = math.cos(psi), math.sin(psi)
        cand = []
        for p in w.pillars:
            if p.X < -0.10 or p.X > cfg.PILLAR_LOOKAHEAD + 0.5 or abs(p.Y) > cfg.PILLAR_REGISTER_Y + 0.3:
                continue
            u_p = y + p.X * s + p.Y * c
            cand.append((p.X, u_p, p.color))
        if not cand:
            self.u_target = 0.0
            return 0.0, 1.0, None
        cand.sort()
        Xn = cand[0][0]
        lo, hi = -9.0, 9.0
        for X, u_p, color in cand:
            if X > Xn + 0.75:
                break
            if color == "red":
                hi = min(hi, u_p - need - 0.02)
            else:
                lo = max(lo, u_p + need + 0.02)
        if lo > hi:                                    # nu se pot satisface ambele: doar cel mai apropiat
            X, u_p, color = cand[0]
            if color == "red":
                lo, hi = -9.0, u_p - need - 0.02
            else:
                lo, hi = u_p + need + 0.02, 9.0
        u_t = max(lo, min(hi, 0.0))
        self.constraint = True
        self.u_target = u_t
        near = Xn < 1.0
        return u_t, (1.5 if near else 1.2), cfg.SPEED_OBSTACLE

