from gpiozero import PWMOutputDevice as PWM
import time

Left_R = 19
Left_G = 0
Left_B = 13
Right_R = 1
Right_G = 5
Right_B = 6
colors = [0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0xFF00FF, 0x00FFFF, 0X6F00D2, 0xFF5809]

def setup():
  global L_R, L_G, L_B, R_R, R_G, R_B
  L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
  L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
  L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)
  R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
  R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
  R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

def map(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def setAllColor(col):
  R_val = map((col & 0xff0000) >> 16, 0, 255, 0, 1.00)
  G_val = map((col & 0x00ff00) >> 8, 0, 255, 0, 1.00)
  B_val = map(col & 0x0000ff, 0, 255, 0, 1.00)
  for led_r, led_g, led_b in ((L_R,L_G,L_B),(R_R,R_G,R_B)):
    led_r.value = 1.0-R_val
    led_g.value = 1.0-G_val
    led_b.value = 1.0-B_val

def destroy():
  L_R.stop(); L_G.stop(); L_B.stop(); R_R.stop(); R_G.stop(); R_B.stop()

if __name__ == "__main__":
  setup()
  try:
    while True:
      for col in colors:
        setAllColor(col)
        time.sleep(0.5)
  except KeyboardInterrupt:
    destroy()
