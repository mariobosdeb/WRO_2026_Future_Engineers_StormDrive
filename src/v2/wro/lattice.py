"""Planificator lattice (C++ prin ctypes) pentru Obstacle: cale cu inainte/inapoi printre pereti si stalpi.

lattice.cpp se compileaza automat la prima utilizare (necesita g++:  sudo apt install -y g++).
Terenul: [0,3]^2 cu peretele interior [1,2]^2. Campul de referinta (progres P, deplasare laterala U, directie H) e calculat
pe grila de 2 cm si salvat in cache (debug/field_<dir>.npz).
"""
import ctypes
import hashlib
import math
import os
import shutil
import subprocess
import tempfile

import numpy as np

from . import config as cfg

S = 3.0
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "lattice.cpp")
_lib = None


def _build():
    """Compileaza lattice.cpp (daca nu exista deja un .so pentru continutul curent) si il incarca."""
    global _lib
    if _lib is not None:
        return _lib
    with open(_SRC, "rb") as fh:
        h = hashlib.md5(fh.read()).hexdigest()[:10]
    cands = [os.path.join(_HERE, "_lattice_%s.so" % h), os.path.join(tempfile.gettempdir(), "_wro_lattice_%s.so" % h)]
    path = next((p for p in cands if os.path.exists(p)), None)
    if path is None:
        cxx = shutil.which("g++") or shutil.which("c++") or shutil.which("clang++")
        if cxx is None:
            raise RuntimeError("Lipseste compilatorul C++ (sudo apt install -y g++)")
        last = None
        for p in cands:
            try:
                subprocess.run([cxx, "-O2", "-std=c++17", "-shared", "-fPIC", "-o", p, _SRC], check=True,
                               capture_output=True, timeout=300)
                path = p
                break
            except Exception as exc:                      # director fara drept de scriere etc.
                last = exc
        if path is None:
            raise RuntimeError("Compilarea lattice.cpp a esuat: %s" % last)
    lib = ctypes.CDLL(path)
    D, I = ctypes.c_double, ctypes.c_int
    PD, PF, PI = ctypes.POINTER(D), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(I)
    lib.plan_path.argtypes = [I, PD, D, D, D, I, PF, PF, PF, I, D, D, D, D, D, D, D, D, D, D, D, D, I, D, D, D, D, D, I, D, D, D, D,
                              I, PD, I, PI, PD, PI]
    lib.plan_path.restype = I
    lib.set_hw.argtypes = [D]
    lib.set_kdk.argtypes = [D]
    _lib = lib
    return lib


def ref_loop(direction, r=0.5, c=0.5, n_arc=40):
    """polilinie inchisa (centrul culoarului cu colturi rotunjite), in sensul de mers."""
    V=[(S-c,c),(S-c,S-c),(c,S-c),(c,c)]            # CCW incepand (2.5,0.5)
    # CCW: de la (c,c) -> (S-c,c) -> (S-c,S-c) -> (c,S-c) -> (c,c)
    P=[(c,c),(S-c,c),(S-c,S-c),(c,S-c)]
    pts=[]
    for k in range(4):
        a=np.array(P[k]); b=np.array(P[(k+1)%4]); z=np.array(P[(k+2)%4])
        d1=(b-a)/np.linalg.norm(b-a); d2=(z-b)/np.linalg.norm(z-b)
        p_in=b-d1*r; p_out=b+d2*r
        pts.append(p_in)
        # arc cu centrul la p_in + n*r, n=normala stanga a d1
        n=np.array([-d1[1],d1[0]])
        cen=p_in+n*r
        a0=math.atan2(p_in[1]-cen[1],p_in[0]-cen[0])
        for i in range(1,n_arc):
            t=a0+ (math.pi/2)*i/n_arc
            pts.append(cen+r*np.array([math.cos(t),math.sin(t)]))
        pts.append(p_out)
    pts=np.array(pts)
    if direction<0:
        pts=pts[::-1]
    return pts

class Field:
    def __init__(self, direction, res=0.02, r=0.5):
        self.res=res; self.dir=direction
        self.n=int(round(S/res))+1
        pts=ref_loop(direction,r=r)
        # densificare
        dense=[]
        for i in range(len(pts)):
            a=pts[i]; b=pts[(i+1)%len(pts)]
            L=np.linalg.norm(b-a); m=max(1,int(L/0.01))
            for j in range(m): dense.append(a+(b-a)*j/m)
        dense=np.array(dense)
        seg=np.roll(dense,-1,axis=0)-dense
        sl=np.linalg.norm(seg,axis=1)
        tang=np.arctan2(seg[:,1],seg[:,0])
        prog=np.concatenate([[0],np.cumsum(sl)[:-1]])
        self.total=float(sl.sum())
        xs=np.arange(self.n)*res
        gx,gy=np.meshgrid(xs,xs,indexing='ij')
        G=np.stack([gx.ravel(),gy.ravel()],axis=1)
        U=np.empty(len(G)); H=np.empty(len(G)); P=np.empty(len(G))
        for s in range(0,len(G),2000):
            g=G[s:s+2000]
            d=np.hypot(g[:,None,0]-dense[None,:,0],g[:,None,1]-dense[None,:,1])
            k=d.argmin(axis=1)
            dx=g[:,0]-dense[k,0]; dy=g[:,1]-dense[k,1]
            tx=np.cos(tang[k]); ty=np.sin(tang[k])
            U[s:s+2000]=-dx*ty+dy*tx      # stanga +
            H[s:s+2000]=tang[k]
            P[s:s+2000]=prog[k]
        self.U=U.reshape(self.n,self.n); self.H=H.reshape(self.n,self.n); self.P=P.reshape(self.n,self.n)
    def look(self,arr,x,y):
        i=np.clip(np.rint(x/self.res).astype(int),0,self.n-1); j=np.clip(np.rint(y/self.res).astype(int),0,self.n-1)
        return arr[i,j]



def _field_cached(direction, fillet):
    path = os.path.join(cfg.DEBUG_DIR, "field_%d_%03d.npz" % (direction, int(round(fillet * 100))))
    try:
        z = np.load(path)
        f = Field.__new__(Field)
        f.res = float(z["res"]); f.dir = direction; f.n = int(z["n"]); f.total = float(z["total"])
        f.U, f.H, f.P = z["U"], z["H"], z["P"]
        return f
    except Exception:
        pass
    f = Field(direction, r=fillet)
    try:
        os.makedirs(cfg.DEBUG_DIR, exist_ok=True)
        np.savez(path, res=f.res, n=f.n, total=f.total, U=f.U, H=f.H, P=f.P)
    except Exception:
        pass
    return f


class Lat:
    """Planificator pentru un sens de mers (+1 antiorar, -1 orar)."""

    def __init__(self, direction, fillet=0.65):
        self.lib = _build()
        self.dir = direction
        self.F = _field_cached(direction, fillet)
        self.P = np.ascontiguousarray(self.F.P, dtype=np.float32)
        self.U = np.ascontiguousarray(self.F.U, dtype=np.float32)
        self.H = np.ascontiguousarray(self.F.H, dtype=np.float32)
        self.NT, self.TR, self.Ptot = self.F.n, self.F.res, self.F.total
        self.kmax = math.tan(math.radians(cfg.STEER_MAX_DEG * cfg.WHEEL_PER_SERVO)) / cfg.WHEELBASE
        self.out = np.zeros(4 * 400)

    def set_hw(self, w):
        self.lib.set_hw(w)

    def set_kdk(self, w):
        self.lib.set_kdk(w)

    def prog(self, x, y):
        return float(self.F.look(self.F.P, np.array([x]), np.array([y]))[0])

    def lateral(self, x, y):
        return float(self.F.look(self.F.U, np.array([x]), np.array([y]))[0])

    def plan(self, pose, pills, gear=0, dP=1.6, umax=0.3, hmax=0.5, mw=0.03, mp=0.035, extra=0.02, win=(-0.12, 0.08), rev=1,
             revc=2.5, gearc=0.5, k_clear=10.0, k_u=1.5, k_h=0.8, rect=None, maxexp=250000, ds=0.05, kmax=None):
        """pills: lista (x, y, col, ax, ay), col 0 = rosu (ocolit pe dreapta), 1 = verde. Intoarce (cale Nx4 [x,y,th,gear] | None, cost, expansiuni)."""
        D, I = ctypes.c_double, ctypes.c_int
        PD, PF = ctypes.POINTER(D), ctypes.POINTER(ctypes.c_float)
        n = len(pills)
        pa = np.ascontiguousarray(np.array(pills, dtype=np.float64).reshape(-1, 5)) if n else np.zeros(5)
        nout, cost, exp = I(0), D(0), I(0)
        r = rect or (0, 0, 0, 0)
        ok = self.lib.plan_path(n, pa.ctypes.data_as(PD), pose[0], pose[1], pose[2], gear,
                                self.P.ctypes.data_as(PF), self.U.ctypes.data_as(PF), self.H.ctypes.data_as(PF), self.NT, self.TR,
                                self.Ptot, dP, umax, hmax, (kmax or self.kmax), ds, mw, mp, extra, win[0], win[1], rev, revc, gearc,
                                k_clear, k_u, k_h, 1 if rect else 0, r[0], r[1], r[2], r[3], maxexp,
                                self.out.ctypes.data_as(PD), 400, ctypes.byref(nout), ctypes.byref(cost), ctypes.byref(exp))
        if ok != 1:
            return None, ok, exp.value
        return self.out[:4 * nout.value].reshape(-1, 4).copy(), cost.value, exp.value

