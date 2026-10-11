"""Driver Obstacle: localizare (filtru de particule pe pereti) + harta stalpilor + planificator lattice (inainte/inapoi) + urmarire de traseu.

Fluxul:
  WAIT      stam 0.8 s si lasam filtrul sa vada peretii
  DISCOVER  inaintam incet drept pana cand directia (CW/CCW) e sigura (geometria peretilor din fata)
  RUN       planificam traseul (orizont ~3.4 m) pe harta stalpilor vazuta pana acum, il urmarim cu feedforward + feedback,
            reluam planul cand se schimba harta / eroarea creste / ramane putin din traseu; la schimbarea sensului oprire completa
  FINISH    dupa 3 ture (progres de-a lungul turului) oprire in sectiunea de start

Totul e in cadrul global al terenului (vezi pf.py). Planificarea ruleaza intr-un fir separat pe masina reala.
"""
import math
import os
import threading
import time

import numpy as np

from . import config as cfg
from .pf import ParticleFilter
from .pmap import PillarMap
from .robot import Brain

LADDER = ((0.07, 0.13, 0.035), (0.045, 0.09, 0.035),   # marja stalp 13/9 cm (era 8/5): pe masina pozitia stalpului greseste ~10 cm
           (0.035, 0.04, 0.02), (0.025, 0.03, 0.01), (0.012, 0.012, 0.0), (0.005, 0.006, -0.02))
DPH = 3.4          # orizontul de planificare [m de progres pe tur]
EXT = 2.0          # cand raman mai putin de atat din traseu, il prelungim
KCL = 40.0         # cat de mult prefera planul distanta mare fata de stalpi (ocolire mai larga)
DISC_PAN = 26.0
DISC_END_X = 1.85     # fara linie colorata, filtrul decide sensul abia dupa ce masina trece de x (sectiunea de start: 1..2 m)
PAN_LOOK = 22.0       # cat priveste camera spre interior (grade)
SPD_F = 24.0          # incet (era 31): mai mult timp sa vada stalpii; x0.8 la evadare ramane peste SPEED_MIN=18
SPD_R = 23.0
COLOR_LOCK_S = 0.6        # cat timp tinem minte prima culoare dupa ce n-o mai vedem [s]
HEAD_SCAN_PERIOD = 2.0    # in cursa: cat sta capul pe directia normala intre doua priviri laterale [s]
HEAD_SCAN_DEG = 60.0      # privirea laterala (stanga, apoi dreapta) [grade]; ~perpendicular pe perete pentru ultrasonic
HEAD_SCAN_HOLD = 0.15     # cat priveste lateral dupa ce capul s-a oprit (camera + ultrasonic) [s]
PLAN_DEADLINE_S = 4.0     # planul care nu e gata in atat timp e abandonat (masina sta pe loc cat asteapta; pe Pi s-a ajuns la 21 s)
TURN_LINE_X = 0.0         # 0 = dezactivat (pe masina a pierdut pozitia; era 0.40). Coltul: cand prima linie de pe podea e la atat in fata, virajul se face direct (fara stalpi) [m]
TURN_GAP_M = 1.2          # distanta minima intre doua viraje la linie [m]
PLAN_PI_FACTOR = 3.0      # in simulator: cat de mult mai lent e Pi-ul fata de masina de dezvoltare (timp de planificare simulat)


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


# --------------------------------------------------------------------------------------------- planificare
def first_run(p):
    g = int(p[1, 3]); L = 0.0; k = 0
    while k + 1 < len(p) and int(p[k + 1, 3]) == g:
        L += math.hypot(p[k + 1, 0] - p[k, 0], p[k + 1, 1] - p[k, 1]); k += 1
    return g, L, k


def rev_len(p):
    L = 0.0
    for k in range(len(p) - 1):
        if int(p[k + 1, 3]) == 1:
            L += math.hypot(p[k + 1, 0] - p[k, 0], p[k + 1, 1] - p[k, 1])
    return L


def plan_ladder(lat, start, pill, g0, dP, use_rect, deadline=None):
    """Incearca planuri din ce in ce mai permisive (viraj maxim, marje, orizont). Intoarce (cale, parametri) sau (None, None)."""
    T, L1 = ((1.0, 0.12, 0.25), (1.0, 0.25, 0.4)), ((1.0, 0.25, 0.4),)
    if use_rect:
        stages = [(0.88, L1, 30000), (0.88, L1, 150000), (0.95, L1, 80000), (1.0, L1, 80000), (0.95, L1, 300000), (1.0, L1, 400000)]
    else:
        # fiecare treapta: (curbura maxima, tolerante terminale, buget de expansiuni, cate niveluri de margine se incearca).
        # Esecurile cele mai costisitoare sunt cele prin epuizarea bugetului (marginea conteaza putin): de aceea un singur salt direct la
        # un buget mare pe primele margini, in loc sa repetam bugete mici pe toata scara de margini.
        stages = [(0.88, T, 25000, 2), (0.88, T, 500000, 2), (0.95, L1, 60000, 5), (1.0, L1, 60000, 5), (0.95, L1, 400000, 3),
                  (1.0, L1, 500000, 5), (0.88, ((1.0, 0.25, 0.4), (1.4, 0.25, 0.4)), 800000, 5),
                  (0.97, ((0.6, 0.25, 0.4), (0.35, 0.25, 0.4)), 150000, 5)]
    for st in stages:
        kf, att, me = st[:3]
        nm = st[3] if len(st) > 3 else len(LADDER)
        for (mw, mp, ex) in LADDER[:nm]:
            for (f, um, hm) in att:
                if deadline is not None and time.time() > deadline:
                    return None, None
                path, c, e = lat.plan(start, pill, gear=g0, dP=max(0.25, dP * f), rev=1, rect=use_rect, kmax=lat.kmax * kf,
                                      mw=mw, mp=mp, extra=ex, maxexp=me, k_clear=KCL, umax=um, hmax=hm)
                if path is not None:
                    return path, (kf, mw, mp, ex)
    return None, None


def plan_ladder2(lat, start, pill, g0, dP, use_rect, deadline=None):
    p, m = plan_ladder(lat, start, pill, g0, dP, use_rect, deadline)
    if p is not None and len(p) > 2:
        g, L, k = first_run(p)
        if g == g0 and L < 0.13 and k + 1 < len(p):          # cuspa imediata si inutila: incercam cu sensul opus
            p2, m2 = plan_ladder(lat, start, pill, 1 - g0, dP, use_rect, deadline)
            if p2 is not None and int(p2[1, 3]) == 1 - g0:
                return p2, m2
    return p, m


# --------------------------------------------------------------------------------------------- urmarire
class Tracker:
    """Urmarire cu feedforward de curbura (din arcele laticei) + feedback pe eroarea laterala si de directie."""

    def __init__(self):
        self.path = None
        self.i = 0
        self.last_err = 0.0
        self._rec = False

    def set(self, path, keep_i=False):
        self.path = path
        if not keep_i:
            self.i = 0
        p = path
        n = len(p)
        kap = np.zeros(n)
        for k in range(n - 1):
            dth = _wrap(p[k + 1, 2] - p[k, 2])
            ds = math.hypot(p[k + 1, 0] - p[k, 0], p[k + 1, 1] - p[k, 1]) + 1e-9
            g = int(p[k + 1, 3])
            kap[k] = dth / ds if g == 0 else -dth / ds
        self.kap = kap

    def remaining_total(self):
        p = self.path
        L = 0.0
        for k in range(self.i, len(p) - 1):
            L += math.hypot(p[k + 1, 0] - p[k, 0], p[k + 1, 1] - p[k, 1])
        return L

    def step(self, x, y, th, ky=2.0, kth=1.0):
        p = self.path
        n = len(p)
        if n < 2:
            return 0.0, 0, 0.0, 0.0
        best, bj, bt = 1e9, self.i, 0.0
        for j in range(max(0, self.i - 1), min(n - 1, self.i + 10)):
            if j < self.i and int(p[j + 1, 3]) != int(p[self.i + 1, 3]):
                continue
            ax, ay = p[j, 0], p[j, 1]
            bx, by = p[j + 1, 0], p[j + 1, 1]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy + 1e-12
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
            d = math.hypot(x - (ax + t * dx), y - (ay + t * dy))
            if d < best - 1e-9:
                best, bj, bt = d, j, t
        self.i = bj
        gear = int(p[bj + 1, 3])
        ax, ay = p[bj, 0], p[bj, 1]
        bx, by = p[bj + 1, 0], p[bj + 1, 1]
        tx, ty = bx - ax, by - ay
        tn = math.hypot(tx, ty) + 1e-9
        tx /= tn; ty /= tn
        px_, py_ = ax + bt * (bx - ax), ay + bt * (by - ay)
        e_y = -(x - px_) * ty + (y - py_) * tx
        dth = _wrap(p[bj + 1, 2] - p[bj, 2])
        th_ref = p[bj, 2] + bt * dth
        e_th = _wrap(th - th_ref)
        delta_ff = math.atan(cfg.WHEELBASE * self.kap[bj])
        sgn = 1.0 if gear == 0 else -1.0
        delta = delta_ff - sgn * (ky * e_y + kth * e_th)
        servo = math.degrees(delta) / cfg.WHEEL_PER_SERVO
        remaining = 0.0
        kk = bj
        while kk + 1 < n and int(p[kk + 1, 3]) == gear:
            remaining += math.hypot(p[kk + 1, 0] - p[kk, 0], p[kk + 1, 1] - p[kk, 1]); kk += 1
        remaining = max(0.0, remaining - bt * tn)
        if remaining < 0.02 and kk + 1 < n and not self._rec:
            self.i = kk
            self._rec = True
            try:
                return self.step(x, y, th, ky, kth)
            finally:
                self._rec = False
        return servo, gear, remaining, abs(e_y)


# --------------------------------------------------------------------------------------------- driver
class PathDriver:
    def __init__(self, hal, mode="obstacle", verbose=True):
        self.hal = hal
        self.verbose = verbose
        self.b = Brain(hal, use_est=False)
        self.b.peek_ok = False
        self.pf = ParticleFilter(seed=int(time.time()) & 0xFFFF)
        self.map = PillarMap()
        self._disc_blobs = []
        self._map_logged = -1
        self._t_shot = -1e9
        self._scan_k = 0
        self._last_fwd_servo = 0.0
        self._front = []              # (t, dist_acc, distanta in fata din ultrasonic) cat merge inainte: detectie "blocat"
        self._scan_t = 0.0
        self._run_id = int(time.time())
        self._turn_d = -9.0
        self._stale = False
        self._lock = None             # (culoare, ultima data vazuta): prima culoare vazuta o ignora pe cealalta
        self._lat = {}
        self.dir = 0
        self.pose = None
        self.corners = 0
        self.T = 0.0
        self.trace = []
        self.laps = 0.0
        self.state = "WAIT"
        self.reason = ""
        self.n_plans = 0
        self.plan_time = 0.4          # estimare a duratei unui plan (s)
        self.events = []
        self.err_stats = []
        self._pend = None
        self._thread = None
        self._async = not hasattr(hal, "track")        # simulatorul are .track; masina reala ruleaza planificarea in fir
        self._load_lattices()

    # ------------------------------------------------------------------ utilitare
    def log(self, msg):
        if self.verbose:
            print("[%6.2f] %s" % (self.hal.now(), msg), flush=True)

    def _load_lattices(self):
        from .lattice import Lat
        t0 = time.time()
        for d in (1, -1):
            lat = Lat(d)
            lat.set_hw(2.0)
            lat.set_kdk(0.3)
            self._lat[d] = lat
        self.log("planificator incarcat (%.1fs)" % (time.time() - t0))

    def start(self, settle=0.7):
        self.hal.set_head(0.0)
        self.b.set_pan(0.0)
        t_end = self.hal.now() + settle
        while self.hal.now() < t_end:
            self._sense()
            self.b.wait_period()
        if getattr(cfg, "START_SCAN", True):
            try:
                sc = self.b.start_scan()
                self.log("scanare start (ultrasonic): stanga=%s fata=%s dreapta=%s" % tuple(
                    "--" if sc[k] is None else "%.0f cm" % (sc[k] * 100) for k in ("st", "fata", "dr")))
                if sc["st"] is not None and sc["dr"] is not None and sc["st"] > 1.3 and sc["dr"] > 1.3:
                    self.log("STOP: ultrasonicul nu vede nimic la stanga/dreapta pe 1.3 m => masina NU e intr-un culoar al pistei.")
                    self.aborted = True
                self.b.set_pan(0.0)
                for _ in range(6):
                    self._sense()
                    self.b.wait_period()
            except Exception as exc:
                self.log("scanarea de start a esuat: %s" % exc)

    # ------------------------------------------------------------------ simtire
    def _first_color(self, blobs):
        """Daca in cadru apar si rosu si verde, pastram doar culoarea vazuta prima (cat timp o mai vedem)."""
        cols = [q for q in blobs if q.color in ("red", "green")]
        if not cols:
            return blobs
        now = self.hal.now()
        if self._lock is None or now - self._lock[1] > COLOR_LOCK_S:
            self._lock = (min(cols, key=lambda q: math.hypot(q.X, q.Y)).color, now)
        col = self._lock[0]
        if any(q.color == col for q in cols):
            self._lock = (col, now)
        return [q for q in blobs if q.color == col]

    def _head_scan(self, now):
        """Capul: directia normala (PAN_LOOK spre interior) HEAD_SCAN_PERIOD s, apoi scurt stanga, scurt dreapta, inapoi."""
        b = self.b
        if self._scan_k == 0:
            done = now - self._scan_t >= HEAD_SCAN_PERIOD
        else:
            done = now >= b.head_ready_t + HEAD_SCAN_HOLD
        if done:
            self._scan_k = (self._scan_k + 1) % 3
            self._scan_t = now
            b.base_pan = (PAN_LOOK * self.dir, HEAD_SCAN_DEG, -HEAD_SCAN_DEG)[self._scan_k]
            b.set_pan(b.base_pan)

    def _save_pillar_frame(self, per, pose):
        """Doar pe masina reala: poza adnotata + linie in log cand se vad stalpi (max 2/s), ca sa vedem ce culori a vazut si unde."""
        if type(self.hal).__name__ != 'RealHW' or not per.pillars or self.hal.now() - self._t_shot < 0.5:
            return
        self._t_shot = self.hal.now()
        x0, y0, th = pose
        c, s = math.cos(th), math.sin(th)
        self.log('  vazut (masina %.2f,%.2f,%.0f): %s' % (x0, y0, math.degrees(th), ' '.join(
            '%s X=%.2f Y=%+.2f -> (%.2f,%.2f) %dpx' % ('R' if q.color == 'red' else 'V', q.X, q.Y,
                                                        x0 + c * q.X - s * q.Y, y0 + s * q.X + c * q.Y, q.area) for q in per.pillars)))
        try:
            import cv2
            from .perception import annotate
            d = os.path.join(cfg.DEBUG_DIR, 'frames_%d' % self._run_id)
            os.makedirs(d, exist_ok=True)
            cv2.imwrite(os.path.join(d, '%06.2f.jpg' % self._t_shot), annotate(self.b.last_img, per, self.b.perceiver.cam))
        except Exception as exc:
            self.log('  poza nesalvata: %s' % exc)

    def _sense(self):
        b = self.b
        b.tick()
        self.pf.predict(b.last_ds, b.last_dth)
        if b.sonar_event is not None:
            r, pan, t = b.sonar_event
            if r is not None and (abs(pan) < 2.0 or abs(pan) >= HEAD_SCAN_DEG - 2.0):     # fata sau privirea laterala
                self.pf.update_sonar(r, pan, cfg.REAR_TO_HEAD)
            if r is not None and abs(pan) <= PAN_LOOK + 3.0:
                self._front.append((t, b.dist_acc, r * math.cos(math.radians(pan))))
        if b.frame_event is not None:
            per, t_cap, delta = b.frame_event
            from .perception import ST_WALL
            m = per.state == ST_WALL
            self.pf.update_points(per.X[m], per.Y[m], delta)
            for color, info in (per.lines.items() if cfg.PF_USE_LINES else ()):   # liniile de pe podea, pentru localizare
                if info.get("P1") is not None:
                    (x1, y1), (x2, y2) = info["P1"], info["P2"]
                    self.pf.update_line(color, [(x1, y1), ((x1 + x2) / 2, (y1 + y2) / 2), (x2, y2)], delta)
            pose, sig, d = self.pf.estimate(self.dir or None)
            self._fresh_pose = pose
            # stalpi (doar dupa ce directia/pozitia sunt rezonabile)
            if sig[0] < 0.12 and sig[1] < 0.10 and (self.dir != 0 or self.pf.dir_prob() > 0.9 or self.pf.dir_prob() < 0.1):
                dx, dy, dth = delta
                th0 = pose[2] - dth
                c0, s0 = math.cos(pose[2] - dth), math.sin(pose[2] - dth)
                # pozitia masinii la captura = pozitia curenta minus miscarea (in cadrul capturii)
                x_cap = pose[0] - (c0 * dx - s0 * dy)
                y_cap = pose[1] - (s0 * dx + c0 * dy)
                self.map.add(per.pillars, (x_cap, y_cap, th0), sigma_pose=max(sig[0], sig[1]))
                self._save_pillar_frame(per, (x_cap, y_cap, th0))
        pose, sig, d = self.pf.estimate(self.dir or None)
        if self.pose is None:
            self.pose = pose
        else:
            a = 0.55
            self.pose = (self.pose[0] + a * (pose[0] - self.pose[0]), self.pose[1] + a * (pose[1] - self.pose[1]),
                         self.pose[2] + a * _wrap(pose[2] - self.pose[2]))
        self.sig = sig
        if hasattr(self, '_truth'):                         # doar simulator: eroarea de localizare fata de adevar
            tx, ty, tth = self._truth()
            self.err_stats.append((math.hypot(self.pose[0] - tx, self.pose[1] - ty), abs(_wrap(self.pose[2] - tth))))
        return self.pose

    # ------------------------------------------------------------------ planificare (sincron / fir)
    def _plan_job(self, lat, start, g0, pill, dP, use_rect, kind, j, t_submit):
        t0 = time.time()
        newp, m = plan_ladder2(lat, start, pill, g0, max(0.3, dP), use_rect, deadline=t0 + PLAN_DEADLINE_S)
        alt = None
        wall = time.time() - t0
        return dict(path=newp, m=m, kind=kind, j=j, t_submit=t_submit, wall=wall, start=start, g0=g0, rect_used=use_rect is not None)

    def _submit(self, lat, start, g0, pill, dP, use_rect, kind, j):
        args = (lat, start, g0, list(pill), dP, use_rect, kind, j, self.hal.now())
        self.n_plans += 1
        self.log('plan %s j=%d start=(%.2f,%.2f,%.0f) g0=%d dP=%.2f pillars=%d' % (kind, j, start[0], start[1], math.degrees(start[2]), g0, dP, len(pill)))
        if self.map.version != self._map_logged:
            self._map_logged = self.map.version
            self.log('  harta stalpi (sig poz %.2f,%.2f): %s' % (*getattr(self, 'sig', (0.0, 0.0))[:2], ' '.join(
                '%s(%.1f,%.1f)' % ('R' if p[2] == 0 else 'V', p[0], p[1]) for p in pill)))
        if self._async:
            self._res = None

            def run():
                self._res = self._plan_job(*args)
            self._thread = threading.Thread(target=run, daemon=True)
            self._thread.start()
            self._pend = dict(t_ready=None, kind=kind, j=j)
        else:
            res = self._plan_job(*args)
            delay = res["wall"] * PLAN_PI_FACTOR
            self._res = res
            self._pend = dict(t_ready=self.hal.now() + delay, kind=kind, j=j)

    def _poll(self):
        """Intoarce rezultatul planului daca e gata, altfel None."""
        if self._pend is None:
            return None
        if self._async:
            if self._thread is not None and self._thread.is_alive():
                return None
            res = self._res
        else:
            if self.hal.now() < self._pend["t_ready"]:
                return None
            res = self._res
        self._pend = None
        self._thread = None
        self._res = None
        if res is not None:
            self.log('  plan gata: %s %.2fs %s' % ('ok' if res['path'] is not None else 'ESUAT', res['wall'], res['m']))
            self.plan_time = max(0.15, 0.6 * self.plan_time + 0.4 * res["wall"] * (1.0 if self._async else PLAN_PI_FACTOR))
        return res

    def _escape(self, dist=0.30):
        """Planul nu exista (de obicei masina e lipita de un stalp/perete): ne retragem drept, in directia opusa stalpului cel mai apropiat."""
        b = self.b
        x, y, th = self.pose
        c, s_ = math.cos(th), math.sin(th)
        sgn = -1.0                                           # implicit: marsarier
        best = 9.0
        for (px, py, col, ax, ay) in self.map.pillars(self.dir):
            X = c * (px - x) + s_ * (py - y)
            Y = -s_ * (px - x) + c * (py - y)
            if abs(Y) < 0.30 and -0.45 < X < 0.60 and abs(X) < best:
                best = abs(X)
                sgn = -1.0 if X > 0 else 1.0
        # in marsarier virajul e invers: daca vrea la dreapta, roțile la stanga (botul se intoarce spre dreapta) si invers
        want = self._last_fwd_servo if abs(self._last_fwd_servo) > 3.0 else self.dir     # fara comanda recenta: sensul virajelor
        steer = -math.copysign(0.9 * cfg.STEER_MAX_DEG, want) if sgn < 0 else 0.0
        self.log("evadare: %s %.2f m%s" % ("inapoi" if sgn < 0 else "inainte", dist,
                                          "" if sgn > 0 else (", roti %s (vrea %s)" % ("stanga" if steer > 0 else "dreapta", "dreapta" if steer > 0 else "stanga"))))
        d0 = b.dist_acc
        t0 = self.hal.now()
        while abs(b.dist_acc - d0) < dist and self.hal.now() - t0 < 3.0:
            b.command(steer, (SPD_F if sgn > 0 else -SPD_R) * 0.8)
            self._sense()
            b.wait_period()
        b.command_now(0.0, 0.0)
        for _ in range(5):
            self._sense(); b.wait_period()

    def _stuck(self):
        """Odometria nu stie ca rotile patineaza: lipita de perete, masina "merge" doar in calcul. Blocata = in ultimele
        STUCK_TIME_S a "mers" >= STUCK_MIN_M inainte, dar ultrasonicul vede acelasi obiect aproape, la aceeasi distanta."""
        now = self.hal.now()
        self._front = [f for f in self._front if now - f[0] <= cfg.STUCK_TIME_S]
        h = self._front
        if len(h) < 4 or h[-1][0] - h[0][0] < 0.8 * cfg.STUCK_TIME_S:
            return False
        adv = h[-1][1] - h[0][1]
        d = [f[2] for f in h]
        if adv >= cfg.STUCK_MIN_M and max(d) < 0.45 and max(d) - min(d) < 0.06:
            self.log("BLOCAT: a 'mers' %.2f m, dar ultrasonicul vede %.0f cm tot timpul" % (adv, 100 * sum(d) / len(d)))
            self._front = []
            return True
        return False

    def _line_ahead(self):
        """Prima linie a coltului (orar: portocalie, antiorar: albastra) aproape in fata => X [m], altfel None."""
        fe = self.b.frame_event
        if fe is None or self.dir == 0:
            return None
        info = fe[0].lines.get("blue" if self.dir > 0 else "orange") or {}
        X = info.get("X")
        if info.get("px", 0) >= cfg.LINE_MIN_PIXELS and X is not None and 0.0 < X < TURN_LINE_X:
            return X
        return None

    def _corner_turn(self):
        """Coltul: intai virajul (dupa linia de pe podea), apoi stalpii. Viraj maxim spre interior pana la directia
        sectiunii urmatoare; planul vechi se arunca, harta se actualizeaza in continuare."""
        b = self.b
        th0 = self.pose[2]
        q = math.pi / 2
        th_t = round(th0 / q) * q + self.dir * q
        self.log("colt: linie %s => viraj %s" % ("albastra" if self.dir > 0 else "portocalie", "stanga" if self.dir > 0 else "dreapta"))
        b.base_pan = PAN_LOOK * self.dir
        b.set_pan(b.base_pan)
        d0 = b.dist_acc
        t0 = self.hal.now()
        steer = self.dir * 0.95 * cfg.STEER_MAX_DEG
        while self.dir * _wrap(self.pose[2] - th_t) < -0.20 and b.dist_acc - d0 < 1.2 and self.hal.now() - t0 < 4.0:
            b.command(steer, SPD_F * 0.8)
            self._sense()
            self._poll()                                 # rezultatul vechi (de dinainte de viraj) nu mai e bun
            b.wait_period()
        self._stale = self._pend is not None
        self._turn_d = b.dist_acc
        self._scan_k = 0
        self._scan_t = self.hal.now()
        self.log("colt: viraj gata (%.0f grade, %.2f m)" % (math.degrees(_wrap(self.pose[2] - th0)), b.dist_acc - d0))

    def _discover(self, t_start):
        """WAIT + DISCOVER: inaintam incet pana cand directia (CW/CCW) e sigura; la final filtrul e restrans pe directia aleasa."""
        hal = self.hal
        b = self.b
        self.state = "WAIT"
        # ---------------- DISCOVER: directia
        creep0 = None
        t_pan = hal.now(); pan_sgn = 1
        t_disc = hal.now()
        line_vote = 0                              # + = albastru (antiorar), - = portocaliu (orar); ca in Open
        while True:
            self._sense()
            if b.frame_event is not None and self.pose[0] < 2.5:
                ln = b.frame_event[0].lines
                o = (ln.get("orange") or {}).get("px", 0)
                bl = (ln.get("blue") or {}).get("px", 0)
                # linia e subtire: pe masina reala are 150..500 px (LINE_MIN_PIXELS=380 e pragul pentru viraj, nu pentru sens)
                if max(o, bl) >= 0.4 * cfg.LINE_MIN_PIXELS and max(o, bl) >= 2 * min(o, bl):
                    line_vote += 1 if bl > o else -1
                    self.log("A VAZUT LINIE %s pe podea (%d px)" % ("ALBASTRA" if bl > o else "PORTOCALIE", max(o, bl)))
                    if abs(line_vote) >= 2:
                        break
            pd = self.pf.dir_prob()
            moved = 0.0 if creep0 is None else (b.dist_acc - creep0)
            sure = pd > 0.99 or pd < 0.01
            tight = self.sig[0] < 0.08 and self.sig[1] < 0.07 and self.sig[2] < 0.06
            # Peretii exterior/interior arata la fel pana la capatul sectiunii: directia (oglindire) se vede abia cand
            # se vede unde se termina peretele interior => mergem inainte pana aproape de colt.
            # filtrul singur (fara linie) poate fi sigur pe ipoteza gresita (pe masina: p=0.000 pe sensul gresit) => decide
            # doar langa colt, unde linia ar fi trebuit deja vazuta
            seen_end = self.pose[0] > DISC_END_X
            if sure and tight and seen_end and moved > 0.25 and (line_vote == 0 or self.pose[0] > 2.3):    # o linie vazuta: asteptam confirmarea
                break
            if moved > 2.0 or hal.now() - t_start > 16.0:
                break
            if creep0 is None:
                creep0 = b.dist_acc
            self.state = "DISCOVER"
            # privim alternativ spre stanga/dreapta: capatul peretelui interior (ce diferentiaza CW de CCW) e la marginea campului
            # vizual cand privim drept inainte; cu capul intors el se vede din timp, pe partea unde chiar e peretele interior
            if hal.now() - t_pan > 0.9:
                t_pan = hal.now(); pan_sgn = -pan_sgn
            b.base_pan = DISC_PAN * pan_sgn
            b.set_pan(b.base_pan)
            # drept: tinem capul masinii pe directia culoarului (th=0 in cadrul global)
            ang = -0.9 * _wrap(self.pose[2]) - 0.4 * 0.0
            servo = math.degrees(math.atan(cfg.WHEELBASE * ang / 0.5)) / cfg.WHEEL_PER_SERVO
            # stalp in fata (independent de directie: rosu -> trecem pe dreapta lui, verde -> pe stanga): ocolire reactiva
            if b.frame_event is not None:
                nb = [(q.X, q.Y, q.color, b.dist_acc) for q in self._first_color(b.frame_event[0].pillars)
                      if q.color in ("red", "green") and 0.2 < q.X < 1.5]
                if nb:
                    self._disc_blobs = nb
            self._disc_blobs = [q for q in self._disc_blobs if q[0] - (b.dist_acc - q[3]) > -0.25]
            tgt = None
            for (X0, Y0, col, d0) in getattr(self, '_disc_blobs', []):
                X = X0 - (b.dist_acc - d0)
                if -0.1 < X < 1.4 and abs(Y0) < 0.40:
                    Yt = Y0 + (-0.30 if col == "red" else 0.30)
                    if tgt is None or X < tgt[0]:
                        tgt = (max(X, 0.12), Yt)
            if tgt is not None:
                kap = 2.0 * tgt[1] / (tgt[0] ** 2 + tgt[1] ** 2)
                servo = math.degrees(math.atan(cfg.WHEELBASE * kap)) / cfg.WHEEL_PER_SERVO
                servo = max(-0.95 * cfg.STEER_MAX_DEG, min(0.95 * cfg.STEER_MAX_DEG, servo))
            b.command(servo, 17.0)
            b.wait_period()
        b.command_now(0.0, 0.0)
        dir_pf = 1 if self.pf.dir_prob() >= 0.5 else -1
        self.dir = dir_pf
        forced = cfg.FORCE_DIRECTION in (1, -1)
        if forced or abs(line_vote) >= 2:          # sensul dat de operator / linia colorata sunt sigure; peretii (simetrici) pot pacali filtrul
            self.dir = cfg.FORCE_DIRECTION if forced else (1 if line_vote > 0 else -1)
            if self.dir != dir_pf:
                self.log("directie %s (%s), filtrul zicea %s -> corectez pozitia" % (
                    "data de operator" if forced else "din linie", "antiorar" if self.dir > 0 else "orar", "antiorar" if dir_pf > 0 else "orar"))
            self.pf.force_direction(self.dir)
        self.pf.collapse(self.dir)
        b.base_pan = PAN_LOOK * self.dir          # camera spre interior: vede stalpii din sectiunea urmatoare mai devreme
        b.set_pan(b.base_pan)
        self.log("directie: %s (p=%.3f), %.1fs" % ("antiorar" if self.dir > 0 else "orar", self.pf.dir_prob(), hal.now() - t_disc))
        for _ in range(4):
            self._sense(); b.wait_period()

    # ------------------------------------------------------------------ bucla principala
    def run(self, max_time=None):
        hal = self.hal
        t_start = hal.now()
        self.start()
        b = self.b
        if getattr(self, "aborted", False):
            self.reason = "nu e pe pista"
            return self.reason
        self._discover(t_start)
        lat = self._lat[self.dir]
        # sectiunea de start (in cadrul global): jos pentru antiorar, sus pentru orar
        sx0, sx1 = 1.0, 2.0
        sy0, sy1 = (0.0, 1.0) if self.dir > 0 else (2.0, 3.0)
        rect = (sx0 + 0.02, sy0 + 0.02, sx1 - 0.02, sy1 - 0.02)
        pose = self.pose
        last_P = lat.prog(pose[0], pose[1])
        lap_prog = 0.0
        trk = Tracker()
        gear = 0
        waiting = 0.0
        fin_planned = False
        replan_now = True
        last_map_v = -1
        last_replan = -9.0
        fails = 0
        self.state = "RUN"
        ended = False
        while True:
            now = hal.now()
            if max_time is not None and now - t_start > max_time:
                self.reason = "timp"
                break
            pose = self._sense()
            self._head_scan(now)
            x, y, th = pose
            P = lat.prog(x, y)
            dP_ = ((P - last_P) + lat.Ptot / 2) % lat.Ptot - lat.Ptot / 2
            lap_prog += dP_
            last_P = P
            self.laps = lap_prog / lat.Ptot
            self.corners = int(self.laps * 4 + 0.2)
            in_start = sx0 + 0.04 < x < sx1 - 0.04 and sy0 + 0.04 < y < sy1 - 0.04
            if self.laps >= 2.85 and in_start:
                b.command_now(0.0, 0.0)
                for _ in range(10):
                    self._sense(); b.wait_period()
                self.reason = "3 ture"
                self.corners = max(self.corners, 12)
                break
            finishing = self.laps > 2.80
            # ---- coltul: linia de pe podea => viraj direct, apoi plan nou pentru stalpi
            if b.dist_acc - self._turn_d > TURN_GAP_M and self._line_ahead() is not None:
                self._corner_turn()
                trk = Tracker()
                gear = 0
                replan_now = True
                continue
            # ---- rezultat plan in asteptare
            res = self._poll()
            if res is not None and self._stale:
                self._stale = False
                res = None
                replan_now = True
            if res is not None:
                if res["path"] is None:
                    fails += 1
                    self.events.append(("planfail", round(now, 1), res["kind"]))
                    self.log("plan esuat (%s)" % res["kind"])
                    replan_now = True
                    if fails in (3, 8, 13, 18):
                        self._escape()
                        last_P = lat.prog(self.pose[0], self.pose[1])
                    if fails > 25:
                        self.reason = "plan imposibil"
                        break
                else:
                    fails = 0
                    newp = res["path"]
                    if res["kind"] == "ext" and trk.path is not None:
                        j = res["j"]
                        if trk.i < j - 1 and j < len(trk.path):
                            newp = np.vstack([trk.path[:j], newp])
                            trk.set(newp, keep_i=True)
                        else:
                            replan_now = True               # prea tarziu: planul pornea dintr-un punct deja depasit
                    else:
                        trk.set(newp)
                    if finishing and res.get("rect_used"):
                        fin_planned = True
            # ---- decizie de planificare
            if self._pend is None:
                kind = None
                start = None
                g0 = gear
                j = 0
                if trk.path is None or replan_now:
                    kind = "actual"; start = (x, y, th)
                elif trk.last_err > 0.06:
                    kind = "actual"; start = (x, y, th)
                else:
                    rem_all = trk.remaining_total()
                    n = len(trk.path)
                    v = max(0.15, 0.30)
                    ahead = int(max(0.45, (self.plan_time * 1.3 + 0.25) * v) / 0.05)
                    map_changed = self.map.version != last_map_v and now - last_replan > 0.6
                    if (rem_all < EXT and not fin_planned) or map_changed:
                        jj = min(n - 1, trk.i + max(3, ahead))
                        if rem_all < EXT and not fin_planned:
                            jj = max(jj, min(n - 1, n - 1 - int(0.5 / 0.05)))
                        if jj > trk.i + 1 and jj < n - 1:
                            kind = "ext"; j = jj
                            start = (trk.path[j, 0], trk.path[j, 1], trk.path[j, 2]); g0 = int(trk.path[j, 3])
                        elif rem_all < EXT and not fin_planned:
                            kind = "actual"; start = (x, y, th)
                if kind is not None:
                    pill = self.map.pillars(self.dir)
                    dP = DPH
                    use_rect = None
                    if finishing:
                        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
                        Pg = lat.prog(cx, cy)
                        Pst = lat.prog(start[0], start[1])
                        dPf = (Pg - Pst) % lat.Ptot
                        dP = min(dPf, DPH) if dPf > 0.3 else DPH
                        use_rect = rect if dPf <= DPH else None
                    last_map_v = self.map.version
                    last_replan = now
                    replan_now = False
                    self._submit(lat, start, g0, pill, dP, use_rect, kind, j)
                    if use_rect is not None:
                        self._rect_pending = True
            if trk.path is None:
                b.command_now(0.0, 0.0)
                b.wait_period()
                continue
            # ---- urmarire
            servo, g, rem, err = trk.step(x, y, th)
            trk.last_err = err
            if g != gear:
                b.command_now(servo, 0.0)
                if abs(b.v_est) < 0.02:
                    waiting += 1.0 / cfg.LOOP_HZ
                    if waiting >= 0.25:
                        gear = g
                        waiting = 0.0
                b.wait_period()
                continue
            spd = SPD_F if g == 0 else SPD_R
            if rem < 0.20:
                spd = max(float(cfg.SPEED_MIN), spd * rem / 0.20)     # sub SPEED_MIN motorul nu mai invarte rotile (mai ales cu rotile virate)
            if rem < 0.035:
                spd = 0.0
            if self._pend is not None and self._pend["kind"] == "actual":
                spd = 0.0 if err > 0.06 else min(spd, 18.0)
            if g == 0 and spd > 0:
                self._last_fwd_servo = servo
            else:
                self._front = []
            if cfg.STUCK_TIME_S and self._stuck():
                self.events.append(("blocat", round(now, 1)))
                self._escape()
                last_P = lat.prog(self.pose[0], self.pose[1])
                trk = Tracker()
                gear = 0
                replan_now = True
                continue
            b.command(servo, spd if g == 0 else -spd)
            self.trace.append((round(now, 2), self.state, round(err, 3), round(math.degrees(th), 1), round(servo, 1)))
            b.wait_period()
        b.command_now(0.0, 0.0)
        self.state = "DONE"
        return self.reason

