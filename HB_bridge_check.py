# Pulse the pulser board
# i2c multiplexer bit 0x10 (same as RM 2, J18)
# i2c address 0x30, 11 bytes

# open channel with gui currently... read from J18

import client
import config
import counter
import sys

from optparse import OptionParser

# Raspberry Pi IP address
pi = config.ip_address
bus = client.webBus(pi, 0)

def pulse(cmd):
    counter.gpioReset()
    cmd = cmd2list(cmd)
    bus.write(config.ccm,[0x10])
    bus.read(0x30,11)
    #bus.write(0x30,[03,00,03,00,03,00,00,00,0xff,00,0xff])
    bus.write(0x30,cmd)
    bus.read(0x30,11)
    m = bus.sendBatch()
    print "Sent: {0}".format(cmd)
    print "Received: {0}".format(m)

def read_from_bridge(address):
    counter.gpioReset()
    bus.write(config.ccm,[0x01])
    bus.write(0x19, [address])
    bus.read(0x19, 4)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def write_to_bridge(address):
    counter.gpioReset()
    bus.write(config.ccm,[0x01])
    #bus.write(0x19, [0x0b, 03])
    bus.write(0x19, [address, 0xaa, 0xbb, 0xcc, 0xdd])
    #bus.read(0x19, 4)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def cmd2list(cmd):
    cmd_list = cmd.split(" ")
    return list(int(c, 16) for c in cmd_list)

if __name__ == "__main__":



    address = sys.argv[1]
    #message = sys.argv[2]
    #write_to_bridge(int(address, 16), int(message, 16))
    write_to_bridge(int(address, 16))
    read_from_bridge(int(address, 16))

