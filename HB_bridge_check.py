# Pulse the pulser board
# i2c multiplexer bit 0x10 (same as RM 2, J18)
# i2c address 0x30, 11 bytes

# open channel with gui currently... read from J18

import client
import config
import counter

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

def send_to_bridge():
    counter.gpioReset()
    bus.write(config.ccm,[0x01])
    bus.read(0x04,32)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def cmd2list(cmd):
    cmd_list = cmd.split(" ")
    return list(int(c, 16) for c in cmd_list)

if __name__ == "__main__":

    address = sys.argv[1]
    send_to_bridge(int(address, 16))

