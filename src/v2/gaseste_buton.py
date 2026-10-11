#!/usr/bin/env python3
"""Gaseste pe ce pin GPIO e legat butonul de start (nu misca motoarele).

    python3 gaseste_buton.py        # apoi apasa butonul de 3-4 ori in 20 de secunde

Pinii liberi sunt cititi o data cu pull-up (buton legat la GND), apoi cu pull-down (buton legat la 3.3 V).
"""
import time

import lgpio

LIBERI = (4, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21, 25, 26)     # fara I2C, sonar, senzor linie, faruri, UART


def asculta(h, flag, nume, sec):
    ok = []
    for p in LIBERI:
        try:
            lgpio.gpio_claim_input(h, p, flag)
            ok.append(p)
        except Exception:
            pass
    time.sleep(0.05)
    rep = {p: lgpio.gpio_read(h, p) for p in ok}
    schimbari = {p: 0 for p in ok}
    print("%s: apasa butonul de cateva ori (%d s)..." % (nume, sec), flush=True)
    end = time.time() + sec
    while time.time() < end:
        for p in ok:
            v = lgpio.gpio_read(h, p)
            if v != rep[p]:
                schimbari[p] += 1
                print("  GPIO%d -> %d" % (p, v), flush=True)
                rep[p] = v
        time.sleep(0.005)
    for p in ok:
        lgpio.gpio_free(h, p)
    return {p: n for p, n in schimbari.items() if n}


def main():
    h = lgpio.gpiochip_open(0)
    try:
        for flag, nume, leg in ((lgpio.SET_PULL_UP, "pull-up", "intre pin si GND"), (lgpio.SET_PULL_DOWN, "pull-down", "intre pin si 3.3 V")):
            r = asculta(h, flag, nume, 10)
            if r:
                p = max(r, key=r.get)
                print("\nGASIT: butonul e pe GPIO%d, legat %s (%d schimbari)" % (p, leg, r[p]))
                print("START_BUTTON_PIN = %d   START_BUTTON_PULL_UP = %s" % (p, flag == lgpio.SET_PULL_UP))
                return
        print("\nNu s-a schimbat niciun pin: butonul nu e legat la un pin liber sau firele nu fac contact.")
    finally:
        lgpio.gpiochip_close(h)


if __name__ == "__main__":
    main()

