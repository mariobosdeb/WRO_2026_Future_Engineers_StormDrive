import time
import smbus

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus = smbus.SMBus(1)
        self.address = 0x48

    def analogRead(self, chn):
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value

if __name__ == "__main__":
    adc = ADS7830()
    while True:
        adc_value = adc.analogRead(1)
        print(f"Light Tracking Value: {adc_value}")
        time.sleep(0.5)
