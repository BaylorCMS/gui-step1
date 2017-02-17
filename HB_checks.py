# Script is currently setup to use cards in RM4 (furthest from LV supply), bridge from card in slot J23

import client
import config
import counter
import sys

from optparse import OptionParser

# Raspberry Pi IP address
pi = config.ip_address
bus = client.webBus(pi, 0)

# I2C stuff
mux_ccm_emu = 0x01
bridge_addr = 0x19

def read_from_bridge(address, nbytes):
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    bus.write(bridge_addr, [address])
    bus.read(bridge_addr, 4)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def write_to_bridge(address, data):
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    to_write = [address]
    to_write.extend(data)
    bus.write(bridge_addr, to_write)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def read_from_igloo(address, nbytes, top=True):
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    if top:
        bus.write(bridge_addr, [0x11, 0x03, 0x00, 0x00, 0x00]) #put bridge multiplexer to igloo (top for HB)
    else:
        bus.write(bridge_addr, [0x11, 0x06, 0x00, 0x00, 0x00]) #put bridge multiplexer to bottom igloo for HB 
    bus.write(0x09, [address])
    bus.read(0x09, nbytes)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def write_to_igloo(address, data, top=True):
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    if top:
        bus.write(bridge_addr, [0x11, 0x03, 0x00, 0x00, 0x00]) #put bridge multiplexer to igloo 
    else:
        bus.write(bridge_addr, [0x11, 0x06, 0x00, 0x00, 0x00]) #put bridge multiplexer to igloo 
    to_write = [address]
    to_write.extend(data)
    bus.write(0x09, to_write)
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def read_unique_id():
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    bus.write(bridge_addr, [0x11, 0x04, 0x00, 0x00, 0x00]) #put bridge multiplexer (address 0x11) to unique id (switch option 4)
    bus.write(0x50, [0x00]) # unique id chip is at location 0x50, and we need to first write 0 to it before reading
    bus.read(0x50, 4) # actually read the unique id
    m = bus.sendBatch()
    print "Received: {0}".format(m)

def convert_temp_reading(data):
    data_list = data.split()
    data_MSB = data_list[1] 
    data_LSB = data_list[2]
    st = ((0xfc & int(data_LSB)) >> 2) + ((0xff & int(data_MSB)) << 6);
    temp = -46.85 + 175.72 * float(st) / float(1 << 14);
    return temp

def convert_humidity_reading(data):
    data_list = data.split()
    data_MSB = data_list[1] 
    data_LSB = data_list[2]
    shu = ((0xfc & int(data_LSB)) >> 2) + ((0xff & int(data_MSB)) << 6);
    humidity = -6.0 + 125.0 * float(shu) / float(1 << 14); 
    return humidity

def read_temperature():
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    bus.write(bridge_addr, [0x11, 0x05, 0x00, 0x00, 0x00]) # temperature sensor is at switch option 5
    bus.write(0x40, [0xf3])
    bus.read(0x40, 3)
    m = bus.sendBatch()
    print "Received: {0}".format(m)
    print "Temperature is ", convert_temp_reading(m[3])

def read_humidity():
    counter.gpioReset()
    bus.write(config.ccm,[mux_ccm_emu])
    bus.write(bridge_addr, [0x11, 0x05, 0x00, 0x00, 0x00]) # temperature sensor is at switch option 5
    bus.write(0x40, [0xf5])
    bus.read(0x40, 3)
    m = bus.sendBatch()
    print "Received: {0}".format(m)
    print "Humidity is ", convert_humidity_reading(m[3])

def cmd2list(cmd):
    cmd_list = cmd.split(" ")
    return list(int(c, 16) for c in cmd_list)

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--uniqueID", dest="uniqueID", default=False, 
                      action='store_true', help="Read the unique ID")
    parser.add_option("--temperature", dest="temperature", default=False, 
                      action='store_true', help="Read the temperature")
    parser.add_option("--humidity", dest="humidity", default=False, 
                      action='store_true', help="Read the relative humidity")
    parser.add_option("--igloo", dest="igloo", default=False, 
                      action='store_true', help="Communicate with igloo")
    parser.add_option("--bridge", dest="bridge", default=False, 
                      action='store_true', help="Communicate with bridge")
    parser.add_option("--read", dest="read", default=False, 
                      action='store_true', help="Perform read action")
    parser.add_option("--write", dest="write", default=False, 
                      action='store_true', help="Perform write action")
    parser.add_option("--register", dest="register",  
                      metavar="0xaa", help="Access which register")
    parser.add_option("--data", dest="data",  
                      metavar="0xaa 0xbb", help="Data to write (as string with spaces as separator)")
    parser.add_option("--nbytes", dest="nbytes", default=4,
                      help="How many bytes to read",type='int')
    (options, args) = parser.parse_args()


    if options.uniqueID:
        read_unique_id()

    if options.temperature:
        read_temperature()

    if options.humidity:
        read_humidity()

    if options.bridge:
        if options.read:
            print "Reading from bridge"
            read_from_bridge(int(options.register,16), options.nbytes)
        if options.write:
            print "Writing to bridge"
            data = [int(a,16) for a in options.data.split()]
            write_to_bridge(int(options.register,16), data)
            print "Reading back from bridge"
            read_from_bridge(int(options.register,16), len(data))

    if options.igloo:
        if options.read:
            print "Reading from igloo"
            read_from_igloo(int(options.register,16), options.nbytes)
        if options.write:
            print "Writing to igloo"
            data = [int(a,16) for a in options.data.split()]
            write_to_igloo(int(options.register,16), data)
            print "Reading back from igloo"
            read_from_igloo(int(options.register,16), len(data))
