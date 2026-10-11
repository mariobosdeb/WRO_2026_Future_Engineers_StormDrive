#!/usr/bin/env python3
"""Non-invasive Adeept ADS7830 battery monitor with safety filtering."""
import statistics
import threading
import time
from collections import deque

from . import config as cfg


class BatteryMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.available = False
        self.voltage = None
        self.percent = None
        self.critical = False
        self.disconnected = True
        self._values = deque(maxlen=cfg.BATTERY_SAMPLES)
        self._lock = threading.Lock()
        self.adc = None
        try:
            import smbus
            self.bus = smbus.SMBus(1)
            self.available = True
        except Exception as exc:
            self.bus = None
            print("Battery ADC unavailable: %s" % exc)

    def read_adc(self, channel=0):
        cmd = 0x84
        return self.bus.read_byte_data(
            cfg.BATTERY_I2C_ADDRESS,
            cmd | ((((channel << 2) | (channel >> 1)) & 0x07) << 4))

    def read_voltage(self):
        raw = self.read_adc(cfg.BATTERY_ADC_CHANNEL)
        a0 = raw / 255.0 * cfg.BATTERY_ADC_VREF
        return a0 / cfg.BATTERY_DIVISION_RATIO

    def update_once(self):
        voltage = self.read_voltage()
        with self._lock:
            self._values.append(voltage)
            median = statistics.median(self._values)
            filtered = [v for v in self._values if abs(v - median) < 1.0]
            if not filtered:
                return
            value = sum(filtered) / len(filtered)
            self.voltage = value
            self.disconnected = value < cfg.BATTERY_MIN_VALID_VOLTAGE
            self.critical = (not self.disconnected and
                             value < cfg.BATTERY_WARNING_VOLTAGE)
            pct = ((value - cfg.BATTERY_WARNING_VOLTAGE) /
                   (cfg.BATTERY_FULL_VOLTAGE - cfg.BATTERY_WARNING_VOLTAGE) * 100.0)
            self.percent = max(0, min(100, int(pct)))

    def run(self):
        if not self.available:
            return
        while self.running:
            try:
                self.update_once()
            except Exception as exc:
                print("Battery read error: %s" % exc)
                self.available = False
                return
            time.sleep(0.1)

    def snapshot(self):
        with self._lock:
            return self.voltage, self.percent, self.critical, self.disconnected

    def stop(self):
        self.running = False
        try:
            if self.bus:
                self.bus.close()
        except Exception:
            pass

