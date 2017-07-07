from machine import UART,Pin
from time import sleep

Start_Byte=0x7E
Version_Byte=0xFF
Command_Length=0x06
Acknowledge=0x00
End_Byte=0xEF

def split(num):
    return num >> 8, num & 0xFF

class Dfplayer():
    def __init__(self, uart=None, busy_pin=None, config=True):
        if uart is None:
            self.uart = UART(1, 9600) # UART on 
            self.uart.init(9600, bits=8, parity=None, stop=1)
        else:
            self.uart = uart
        if busy_pin is not None:
            busy_pin.init(mode=Pin.IN)
        self.busy_pin = busy_pin
        if config:
            self.config()

    def config(self):
        self.execute(0x3F, 0x00, 0x00)

    def execute(self, CMD, Par1, Par2):
        Checksum = -(Version_Byte + Command_Length + CMD + Acknowledge + Par1 + Par2)
        HighByte, LowByte = split(Checksum)
        CommandLine = bytes([b & 0xFF for b in [Start_Byte, Version_Byte, Command_Length, CMD, Acknowledge,
            Par1, Par2, HighByte, LowByte, End_Byte
        ]])
        self.uart.write(CommandLine)

    def play(self, dirNum, fileNum):
        self.execute(0x0F,dirNum,fileNum)

    def volume(self, val=30):
        self.execute(0x06,0x00,val)  

    def playing(self):
        return self.busy_pin.value() == 0

def main():
    from machine import Pin
    from time import sleep
    from dfplayer import Dfplayer
    player = Dfplayer(busy_pin=Pin(0), config=False)
    player.config()
    sleep(0.1)
    #player.volume(30)
    folder = 1
    while True:
        for track in range(2, 7):
            print("Playing track {}".format(track))
            player.play(folder,track)
            sleep(0.2)
            while player.playing():
                sleep(0.05)


def scan():
    player = Dfplayer(busy_pin=Pin(0), config=False)
