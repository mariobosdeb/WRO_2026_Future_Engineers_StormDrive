"""Stratul hardware real (Adeept Robot HAT + PCA9685, HC-SR04, Picamera2).

Are exact aceeasi interfata ca SimHW (vezi sim.py), deci Driver/Brain ruleaza neschimbat:
    now, sleep, set_steer(deg +stanga), set_speed(%), set_head(pan_deg +stanga), pan_now,
    sonar() -> metri | None, frame() -> (bgr, t, nou) | None, ir(), battery(), yaw_rate()
Camera si ultrasonicul sunt pe ACELASI cap pan/tilt.
"""
import statistics
import threading
import time

from . import config as cfg
from .battery import BatteryMonitor
from .lights import AdeeptLights


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


class _LgSonar:
    """HC-SR04 prin lgpio: durata ecoului din timestamp-urile hardware ale fronturilor
    (gpiozero masura in Python si dadea "no echo" cand CPU era incarcat). read() -> metri | None."""

    def __init__(self, trig, echo, max_m):
        import lgpio
        self._lg = lgpio
        self._max = max_m
        self._h = lgpio.gpiochip_open(0)           # Pi 5: gpiochip0 = pinctrl-rp1
        lgpio.gpio_claim_output(self._h, trig, 0)
        lgpio.gpio_claim_alert(self._h, echo, lgpio.BOTH_EDGES)
        self._trig = trig
        self._rise = None
        self._dur = None
        self._done = threading.Event()
        self._cb = lgpio.callback(self._h, echo, lgpio.BOTH_EDGES, self._edge)

    def _edge(self, chip, gpio, level, tick):
        if level == 1:
            self._rise = tick
        elif level == 0 and self._rise is not None:
            self._dur = (tick - self._rise) * 1e-9
            self._rise = None
            self._done.set()

    def read(self):
        self._rise = self._dur = None
        self._done.clear()
        self._lg.gpio_write(self._h, self._trig, 1)
        t = time.perf_counter() + 12e-6
        while time.perf_counter() < t:
            pass
        self._lg.gpio_write(self._h, self._trig, 0)
        if not self._done.wait(2.2 * self._max / 343.0 + 0.01):
            return None
        d = self._dur * 343.0 / 2.0
        return d if 0.02 < d < self._max * 0.98 else None


class RealHW:
    def __init__(self, use_camera=True):
        import busio
        from board import SCL, SDA
        from adafruit_pca9685 import PCA9685
        from adafruit_motor import motor as am, servo as asv

        self._lock = threading.Lock()
        self.pca = PCA9685(busio.I2C(SCL, SDA), address=cfg.PCA_ADDRESS)
        self.pca.frequency = cfg.PCA_FREQUENCY
        self._servo = {ch: asv.Servo(self.pca.channels[ch], min_pulse=cfg.SERVO_MIN_PULSE,
                                     max_pulse=cfg.SERVO_MAX_PULSE, actuation_range=180)
                       for ch in (cfg.STEER_CH, cfg.PAN_CH, cfg.TILT_CH)}
        self.motor = am.DCMotor(self.pca.channels[cfg.MOTOR_IN1], self.pca.channels[cfg.MOTOR_IN2])
        self.motor.decay_mode = am.SLOW_DECAY
        try:
            self._ultra = _LgSonar(cfg.ULTRA_TRIGGER, cfg.ULTRA_ECHO, cfg.SONAR_MAX)
            print("ultrasonic: lgpio (timestamp hardware)")
        except Exception as exc:
            from gpiozero import DistanceSensor
            print("ultrasonic: gpiozero (lgpio indisponibil: %s)" % exc)
            self._ultra = DistanceSensor(echo=cfg.ULTRA_ECHO, trigger=cfg.ULTRA_TRIGGER,
                                         max_distance=cfg.SONAR_MAX, queue_len=2, partial=True)
        self.lights = AdeeptLights()
        self.battery_mon = BatteryMonitor()
        self.battery_mon.start()
        self._t0 = time.monotonic()
        self._pan_from = self._pan_to = 0.0
        self._pan_t0 = -1e9
        self._pan_dur = 0.0
        self._pan_set_t = -1e9
        self._sonar = (None, -1e9)
        self._frame = None
        self._frame_n = 0
        self._frame_seen = 0
        self._cam_error = None
        self._gyro = None
        self.running = True
        self.set_steer(0.0)
        self._write_pan(0.0)
        self._set_servo(cfg.TILT_CH, cfg.TILT_SERVO_DEG)
        threading.Thread(target=self._sonar_loop, daemon=True).start()
        if use_camera:
            self._start_camera()
        if cfg.IMU_ENABLED:
            self._start_gyro()

    # ------------------------------------------------------------------ timp
    def now(self):
        return time.monotonic() - self._t0

    def sleep(self, dt):
        if dt > 0:
            time.sleep(dt)

    # ------------------------------------------------------------------ servo / motor
    def _set_servo(self, ch, deflection_deg):
        with self._lock:
            self._servo[ch].angle = clamp(cfg.SERVO_CENTRE + deflection_deg, 0.0, 180.0)

    def set_steer(self, deg):
        deg = clamp(deg, -cfg.STEER_MAX_DEG, cfg.STEER_MAX_DEG)
        self._set_servo(cfg.STEER_CH, cfg.STEER_SIGN * (deg + cfg.STEER_TRIM_DEG))

    def _write_pan(self, deg):
        self._set_servo(cfg.PAN_CH, cfg.PAN_SIGN * (deg + cfg.PAN_TRIM_DEG))

    def set_tilt(self, deg):
        """Inclinarea capului (servo tilt), folosita la calibrare."""
        cfg.TILT_SERVO_DEG = float(deg)
        self._set_servo(cfg.TILT_CH, cfg.TILT_SERVO_DEG)

    def set_head(self, pan_deg, tilt_deg=None):
        pan_deg = clamp(pan_deg, -90.0, 90.0)
        now = self.now()
        cur = self.pan_now()
        self._pan_from, self._pan_to, self._pan_t0 = cur, pan_deg, now
        self._pan_dur = cfg.PAN_SETTLE_BASE + cfg.PAN_SETTLE_PER_DEG * abs(pan_deg - cur)
        self._pan_set_t = now
        self._write_pan(pan_deg)

    def pan_now(self):
        t = self.now() - self._pan_t0
        if t >= self._pan_dur:
            return self._pan_to
        return self._pan_from + (self._pan_to - self._pan_from) * (t / max(1e-3, self._pan_dur))

    def set_speed(self, pct):
        pct = clamp(pct, -100.0, 100.0)
        with self._lock:
            self.motor.throttle = cfg.MOTOR_DIRECTION * pct / 100.0

    def stop(self):
        self.set_speed(0.0)

    # ------------------------------------------------------------------ ultrasonic (fir propriu)
    def _sonar_loop(self):
        while self.running:
            try:
                if isinstance(self._ultra, _LgSonar):
                    val = self._ultra.read()
                    t = self.now()
                else:
                    d = self._ultra.value      # proportie 0..1 din max_distance (NU .distance, care e deja in metri)
                    t = self.now()
                    val = None if (d is None or d >= 0.98 or d <= 0.02) else float(d) * cfg.SONAR_MAX
                self._sonar = (val, t)
            except Exception:
                self._sonar = (None, self.now())
            time.sleep(0.045)

    def sonar(self):
        """Metri de la axa pan a capului (ca in simulator); None daca citirea e veche sau facuta inainte ca servo-ul sa ajunga."""
        val, t = self._sonar
        if self.now() - t > 0.15 or t < self._pan_set_t + self._pan_dur or val is None:
            return None
        return val + cfg.SONAR_FWD

    # ------------------------------------------------------------------ camera
    def _start_camera(self):
        try:
            import libcamera
            from picamera2 import Picamera2
            self._picam = Picamera2()
            conf = self._picam.create_preview_configuration(main={"size": cfg.CAM_SIZE, "format": "RGB888"})
            conf["transform"] = libcamera.Transform(hflip=cfg.CAM_HFLIP, vflip=cfg.CAM_VFLIP)
            self._picam.configure(conf)
            self._picam.start()
            time.sleep(0.8)
        except Exception as exc:
            self._cam_error = exc
            print("CAMERA INDISPONIBILA: %s" % exc)
            return
        threading.Thread(target=self._camera_loop, daemon=True).start()

    def _camera_loop(self):
        while self.running:
            try:
                img = self._picam.capture_array()       # RGB888 = ordine B,G,R (OpenCV)
            except Exception as exc:
                self._cam_error = exc
                return
            self._frame = (img, self.now())
            self._frame_n += 1

    @property
    def camera_ok(self):
        return self._frame is not None and self._cam_error is None

    def frame(self):
        f = self._frame
        if f is None:
            return None
        new = self._frame_n != self._frame_seen
        self._frame_seen = self._frame_n
        return f[0], f[1], new

    # ------------------------------------------------------------------ diverse
    def ir(self):
        try:
            from gpiozero import InputDevice
            if not hasattr(self, "_ir"):
                self._ir = [InputDevice(pin=p) for p in cfg.IR_PINS]
            return tuple(int(d.value) for d in self._ir)
        except Exception:
            return (None, None, None)

    def battery(self):
        return self.battery_mon.snapshot()

    def _start_gyro(self):
        try:
            import smbus
            bus = smbus.SMBus(1)
            bus.write_byte_data(cfg.IMU_ADDRESS, 0x6B, 0x00)
            bus.write_byte_data(cfg.IMU_ADDRESS, 0x1B, 0x00)

            def gz():
                d = bus.read_i2c_block_data(cfg.IMU_ADDRESS, 0x47, 2)
                r = (d[0] << 8) | d[1]
                return (r - 65536 if r >= 0x8000 else r) / 131.0
            time.sleep(0.2)
            bias = statistics.mean(gz() for _ in range(200))
            self._gyro = 0.0

            def loop():
                while self.running:
                    try:
                        r = cfg.IMU_SIGN * (gz() - bias)
                        self._gyro = 0.0 if abs(r) < 0.25 else r
                    except Exception:
                        self._gyro = None
                        return
                    time.sleep(0.005)
            threading.Thread(target=loop, daemon=True).start()
        except Exception as exc:
            print("IMU indisponibil (%s) - continui fara" % exc)
            self._gyro = None

    def yaw_rate(self):
        return self._gyro            # grade/s (+stanga) sau None

    def shutdown(self):
        self.running = False
        try:
            self.stop()
            self.set_steer(0.0)
            self._write_pan(0.0)
        finally:
            try:
                self._ultra.close()
            except Exception:
                pass
            try:
                self._picam.stop()
            except Exception:
                pass
            self.battery_mon.stop()
            try:
                self.lights.shutdown()
            except Exception:
                pass

