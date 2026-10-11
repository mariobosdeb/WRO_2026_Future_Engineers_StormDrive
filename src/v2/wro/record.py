"""Inregistrarea senzorilor in cursa (RecHAL) si reluarea lor offline (ReplayHAL), ca un rosbag.

Pe masina: PathDriver primeste RecHAL(hw). Pentru fiecare pas al buclei (Brain.tick) se salveaza ce a citit Brain-ul
(sonar, pan, baterie, giroscop, cadrul procesat) plus starea capului si comenzile, in debug/rec_<ts>/rows.jsonl
si debug/rec_<ts>/f<NNNNN>.png (~80 KB/cadru).
Offline: replay.py reconstruieste Brain + filtrul de particule si le hraneste exact cu aceleasi date, deci se pot
testa schimbari in estimator/perceptie fara sa porneasca motoarele. Comenzile sunt cele inregistrate (bucla deschisa).
"""
import json
import os
import queue
import threading

# starea Brain-ului de care depinde ce citeste tick() (dupa _head_step)
STATE = ("steer_cmd", "speed_cmd", "pan_target", "head_ready_t", "base_pan", "hold_pan", "_peek_phase", "v_scale")


class RecHAL:
    def __init__(self, hal, out_dir):
        self.inner = hal
        self.dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.rows = []
        self.owner = None              # PathDriver (pentru .dir)
        self._cur = {}
        self._img = None
        self._nf = 0
        self._q = queue.Queue(maxsize=64)
        self._w = threading.Thread(target=self._writer, daemon=True)
        self._w.start()
        from . import config as cfg
        self.cfg = {k: getattr(cfg, k) for k in dir(cfg) if k.isupper() and isinstance(getattr(cfg, k), (int, float, str, bool, type(None), list, tuple))}

    def __getattr__(self, name):
        return getattr(self.inner, name)

    # citiri inregistrate
    def sonar(self):
        r = self.inner.sonar()
        self._cur["r"] = r
        return r

    def pan_now(self):
        p = self.inner.pan_now()
        self._cur["p"] = p
        return p

    def battery(self):
        b = self.inner.battery()
        self._cur["v"] = b[0]
        return b

    def yaw_rate(self):
        g = self.inner.yaw_rate()
        self._cur["g"] = g
        return g

    def frame(self):
        fr = self.inner.frame()
        self._img = fr
        return fr

    # apelate din Brain.tick
    def begin(self, brain, t):
        self._cur["t"] = t
        for k in STATE:
            self._cur[k] = getattr(brain, k)

    def end(self, brain):
        row = self._cur
        self._cur = {}
        row["dir"] = getattr(self.owner, "dir", 0)
        row["lp"] = getattr(self.owner, "pose", None)      # poza estimata in cursa (dupa pasul _sense precedent)
        if brain.frame_event is not None and self._img is not None:
            img, t_frame, _ = self._img
            row["tf"] = t_frame
            row["f"] = self._nf
            try:
                self._q.put_nowait((self._nf, img.copy()))
            except queue.Full:
                row["f"] = None                 # scrierea pe card nu tine pasul: cadrul se pierde (se vede la reluare)
            self._nf += 1
        self._img = None
        self.rows.append(row)

    def mark_sense(self):
        """Pasul curent a intrat si in filtrul de particule (PathDriver._sense)."""
        if self.rows:
            self.rows[-1]["s"] = 1

    def _writer(self):
        import cv2
        while True:
            item = self._q.get()
            if item is None:
                return
            n, img = item
            cv2.imwrite(os.path.join(self.dir, "f%05d.png" % n), img, [cv2.IMWRITE_PNG_COMPRESSION, 1])   # fara pierderi: reluarea e identica

    def close(self):
        self._q.put(None)
        self._w.join(timeout=10.0)
        with open(os.path.join(self.dir, "meta.json"), "w") as fh:
            json.dump({"seed": getattr(self.owner, "seed", 0), "cfg": self.cfg}, fh, indent=1, default=str)
        with open(os.path.join(self.dir, "rows.jsonl"), "w") as fh:
            for r in self.rows:
                fh.write(json.dumps(r, separators=(",", ":"), default=float) + "\n")
        return len(self.rows), self._nf


class ReplayHAL:
    """Serveste valorile unui singur pas inregistrat; replay.py avanseaza cu .load(row)."""

    def __init__(self, rec_dir):
        self.dir = rec_dir
        with open(os.path.join(rec_dir, "rows.jsonl")) as fh:
            self.rows = [json.loads(line) for line in fh]
        with open(os.path.join(rec_dir, "meta.json")) as fh:
            self.meta = json.load(fh)
        self.row = self.rows[0]
        self.missing = 0

    def load(self, row):
        self.row = row

    def now(self):
        return self.row["t"]

    def sleep(self, dt):
        pass

    def set_steer(self, deg):
        pass

    def set_speed(self, pct):
        pass

    def set_head(self, pan_deg, tilt_deg=None):
        pass

    def sonar(self):
        return self.row.get("r")

    def pan_now(self):
        return self.row.get("p", 0.0)

    def battery(self):
        return (self.row.get("v"), None, None, None)

    def yaw_rate(self):
        return self.row.get("g")

    def frame(self):
        n = self.row.get("f")
        if n is None:
            if "f" in self.row:
                self.missing += 1
            return None
        import cv2
        img = cv2.imread(os.path.join(self.dir, "f%05d.png" % n))
        if img is None:
            self.missing += 1
            return None
        return img, self.row["tf"], True

