from machine import UART, Pin
from utime import sleep_ms, ticks_ms, ticks_diff

Start_Byte = 0x7E
Version_Byte = 0xFF
Command_Length = 0x06
Acknowledge = 0x00
End_Byte = 0xEF

# inherent delays in DFPlayer
CONFIG_LATENCY = 1000
PLAY_LATENCY =   500
VOLUME_LATENCY = 500

def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))

def split(num):
    return num >> 8, num & 0xFF

def kill_time(stamp_ms, kill_ms):
    diff_ms = ticks_diff(ticks_ms(), stamp_ms)
    if diff_ms < kill_ms:
        snooze_ms = kill_ms - diff_ms
        sleep_ms(snooze_ms)
        return snooze_ms
    else:
        return 0

class Player():
    def __init__(self, uart=None, busy_pin=None, config=True, volume=0.5):
        self._volume = None
        if uart is None:
            self.uart = UART(1, 9600) # UART on 
            self.uart.init(9600, bits=8, parity=None, stop=1)
        else:
            self.uart = uart
        if busy_pin is not None:
            busy_pin.init(mode=Pin.IN, pull=Pin.PULL_UP)
        self.busy_pin = busy_pin
        if config:
            self.config()
        if volume is not None:
            self.volume(volume)

    def command(self, CMD, Par1, Par2):
        self.awaitconfig()
        Checksum = -(Version_Byte + Command_Length + CMD + Acknowledge + Par1 + Par2)
        HighByte, LowByte = split(Checksum)
        CommandLine = bytes([b & 0xFF for b in [
            Start_Byte, Version_Byte, Command_Length, CMD, Acknowledge,
            Par1, Par2, HighByte, LowByte, End_Byte
        ]])
        self.uart.write(CommandLine)

    def config(self):
        self.configtime = ticks_ms()
        #self.reset()
        self.command(0x3F, 0x00, 0x00)

    def play(self, folderNum, trackNum):
        self.awaitconfig()
        self.playtime = ticks_ms()
        self.command(0x0F, folderNum, trackNum)

    def finish(self, folderNum, trackNum):
        self.play(folderNum, trackNum)
        while self.playing():
            sleep_ms(50)

    def playing(self):
        if self.busy_pin is not None:
            self.awaitplay()
            return self.busy_pin.value() == 0
        else:
            raise AssertionError("No busy pin provided, cannot detect play status")

    def awaitconfig(self):
        if self.configtime is not None:
            kill_time(self.configtime, CONFIG_LATENCY)
        self.configtime = None

    def awaitplay(self):
        if self.playtime is not None: # handle delay between playing and registering
            kill_time(self.playtime, PLAY_LATENCY)
        self.playtime = None

    def awaitvolume(self):
        if self.volumetime is not None: # handle delay between playing and registering
            kill_time(self.volumetime, VOLUME_LATENCY)
        self.volumetime = None

    def repeat(self, repeat=True):
        self.awaitconfig()
        val = 1 if repeat else 0
        self.command(0x11, 0, val)

    def _gain(self, gain=1.0):
        self.awaitconfig()
        gain = float(clamp(gain, 0, 1.0))
        val = int(30.0 * gain)
        self.command(0x10,0 ,val)  

    def volume(self, volume=None):
        self.awaitconfig()
        if volume is None:
            return self._volume
        else:
            self._volume = float(clamp(volume, 0, 1.0))
            val = int(30.0 * self._volume)
            self.command(0x06,0 ,val)
            self.volumetime = ticks_ms()

    def standby(self):
        self.awaitconfig()
        self.command(0x0A, 0x00, 0x00)

    def wake(self):
        self.awaitconfig()
        self.command(0x0B, 0x00, 0x00)

    def reset(self):
        self.awaitconfig()
        self.command(0x0C, 0x00, 0x00)

def main():
    from time import sleep
    player = Player(busy_pin=Pin(0))
    player.volume(0.5)
    player.awaitvolume()
    for folder in range(0,3):
        for track in range(0, 2):
            player.play(folder, track)
            while player.playing():
                sleep(0.01)