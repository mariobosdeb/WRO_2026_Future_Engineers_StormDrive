#!/usr/bin/env python3
from gpiozero import TonalBuzzer
from time import sleep

tb = TonalBuzzer(18)
SONG = [
  ["E5",0.3],["Eb5",0.3], ["E5",0.3],["Eb5",0.3],["E5",0.3],["B4",0.3],["D5",0.3],["C5",0.3],
  ["A4",0.6],[None,0.1],["C4",0.3],["E4",0.3],["A4",0.3],
  ["B4",0.6],[None,0.1],["E4",0.3],["Ab4",0.3],["B4",0.3],
  ["C5",0.6],[None,0.1],["E4",0.3],["E5",0.3],["Eb5",0.3],
  ["E5",0.3],["Eb5",0.3],["E5",0.3],["B4",0.3],["D5",0.3],["C5",0.3],
  ["A4",0.6],[None,0.1],["C4",0.3],["E4",0.3],["A4",0.3],
  ["B4",0.6],[None,0.1],["E4",0.3],["C5",0.3],["B4",0.3],["A4",0.1]
]

def play(tune):
    for note, duration in tune:
        print(note)
        tb.play(note)
        sleep(float(duration))
    tb.stop()

if __name__ == "__main__":
    try:
        play(SONG)
    except KeyboardInterrupt:
        pass
