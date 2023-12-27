import fcntl, os, time
import struct


# Small program to communicate with I2C devices via
# Linux kernel IOCTL, this program asl specifically supports
# ADS1115 ADC, PCA9685 Servo driver and LTC2497 ADC


# ltc2487.pdf
# 16 bit 16 chan ADC @ 5V
# This ADC is integrade with the PCA9685 servo driver
# in order to measure current of each servo channel
# in this applciation we want signle-ended mode inorder
# to utilize 12 channels for each of the 12 motors
class LTC2497:
    MODE_SINGLE = 0xb0
    DATASIZE = 0x3

    def __init__(self, i2c, addr):
        self.i2c = I2CDevice(i2c, addr)
        self.mode = MODE_SINGLE

    def read_voltage(self, raw) -> float:
        volts = (raw * 5.0) / 32767
        return votls

    def read_chan(self, chan):
        command = self.MODE_SINGLE | (chan & 0xf)
        self.i2c.write(command)
        time.delay(.01)
        data = self.i2c.read(3)
        val = (data[0] & 0x3f << 10) | data[1] << 2 | (data[2]) >> 6
        return val

    def write_register(self, addr, val): 
        self.i2c.write(buf)
    
    def read_register(self, reg):
        data = self.i2c.read(3)
        return data



# ads1115.pdf
# 16 bit ADC @ ~5V Datasheet states input range is set by
# gains, gains are listed in range dict
class ADS1115:
    ADS1X15_RANGE = {"default": 6.144, "1": 4.096, "2": 2.048, "4": 1.024, 
                     "8": 0.512, "16": 0.256}
    # Operating modes, values are masked for setting
    # Config Register
    MODE_CONTINUOUS = 0x000
    MODE_SINGLE = 0x0100

    def __init__(self, i2c, addr):
        self.mode = MODE_CONTINUOUS
        self.gain = ADS1X15_RANGE["default"]
        self.i2c = I2CDevice(i2c, addr)

    def get_voltage(self, raw_val) -> float:
        volts = (raw_val * ADS1X15_RANGE["default"]) / 32767
        return volts

    def write_register(self, reg, value):
        buf = []
        buf[0] = reg
        buf[1] = (value >> 8) & 0xFF
        but[2] = value & 0xFF

        self.i2c.write(buf)

    def read_register(self, reg) -> int:
        data = self.i2c.read(2)
        val = struct.unpack(">h", data.to_bytes(2, "big"))[0]
        print("ADS1115 read: {val}")
        return val


class PCA9685ServoDriver:
    PCA9685_MODE1 = 0x0
    PCA9685_MODE2 = 0x1
    PCA9685_PRESCALE = 0xFE 
    MODE1_RESTART = 0x80
    MODE1_SLEEP = 0x10
    MODE1_EXTCLK = 0x40
    MODE1_AI = 0x20
    FREQUENCY_OSCILLATOR = 25000000
    PCA9685_PRESCALE_MIN = 0x3
    PCA9685_PRESCALE_MAX = 0xFF

    def __init__(self, i2c, addr):
        self.i2c = I2CDevice(i2c, addr)
        self.reset()
        self.set_pwm_frequency(1000)
 
    def reset(self):
        buf = struct.pack('>BB', self.PCA9685_MODE1, self.MODE1_RESTART)
        print(f"Servo RESET bytes {buf}")
        self.write(buf)
        time.delay(0.01)

    def set_ext_clock(self, clock):
        print("Servo EXT Clock")
        ext_clock = clock | self.MODE1_EXTCLK
        self.write(self.PCA9685_MODE1, ext_clock)

    def set_pwm_frequency(self, freq):
        if freq < 1:
            freq = 1
        elif freq > 3500: 
            freq = 3500

        print("Setting PWM frequency")
        prescale = (self.FREQUENCY_OSCILLATOR / (freq * 4096.0)) + 0.5 - 1
        old = self.read(self.PCA9685)
        mode = (old & ~self.MODE1_RESTART) | self.MODE1_SLEEP
        self.write(self.PCA9685_MODE1, mode)
        self.write(self.PCA9685_PRESCALE, prescale)
        self.write(self.PCA9685_MODE1, old)
        time.delay(0.01)
        self.write(self.PCA9685_MODE1, old | self.MODE1_RESTART | self.MODE1_AI)

    def read(self, addr):
        self.i2c.write(addr)
        return self.i2c.read(1)

    def write(self, addr, val):
        buf = struct.pack('>BB', addr, val)
        print(f"Servo Writing bytes: {buf}")
        self.i2c.write(buf)

    def sleep(self):
        print("Servo Sleep")
        wake = self.read(PCA9685_MODE1)
        sleep = wake | MODE1_SLEEP
        self.write(PCA9685_MODE1, sleep)
    
    def wake(self):
        print("Servro Wake")
        sleep = self.read(PCA9685_MODE1)
        wakeup = sleep & ~MODE1_SLEEP
        self.write(PCA9685_MODE1, wakeup)

    def set_output_mode(self):
        pass

    def get_pwm(self):
        pass
    
    def set_pwm(self):
        pass
    
    def set_pin(self):
        pass

    def write_micro_seconds(self):
        pass



# Basic IOCTL interface for i2c
class I2CDevice:
    I2C_SLAVE = 0x0703

    def __init__(self, bus, address):
        self.file = ""
        self.address = address
        self.bus = bus

        self.open_device(bus, address) 

    def read(self, length):
        return self.file.read(length)

    def write(self, data):
        self.file.write(data)

    def open_device(self, bus, address):
        print(f"Opening /dev/i2c-{bus} addr --> {address:X}")
        self.file = open("/dev/i2c-{bus}", 'rb+', buffering=0)
        fcntl.ioctl(file, I2C_SLAVE, address)

    def convert(self, raw_adc):
        byte1, byte2 = struck.unpack(">BB", raw_adc)
        return byte1, byte2

    def close(self):
        self.file.close()



ADS1115_ADDR = 0x48    # ADC (default)
PCA9685_ADDR = 0x40    # Servo Driver (Hardware select)
LTC2497_ADDR = 0x14    # Servo Driver ADC (Hardware select)

adc = I2CDevice(1, ADS1115_ADDR)

BITS = 32767
VOLTS = 6.144

data = adc.read(2)

byte1, byte2 = struct.unpack(">BB", data)
print(f"Byte1 {byte1} Byte2 {byte2}")

value = struct.unpack(">h", data.to_bytes(2, "big"))[0]
print(f"Value {value}")

# ADC calculation 
data = (data & b'00001111') << 8
data = data * VOLTS / BITS
channel = (data & b'00110000') >> 4

print("Volts: {} Channel: {}".format(data, channel))

# Test Writing
register = bytes.fromhex(10)
adc.write_adc(register)
