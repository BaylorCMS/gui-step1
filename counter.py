# Read CLock Counter, QIE Reset Counter and WTE Counter

import client
import time
import config

# Setup web bus and i2c addresses.
pi = config.ip_address
bus = client.webBus(pi, 0)
ccm = config.ccm
gpio = config.gpio
igloo = 0x09

# Bridge and Igloo Counters
# Clock Counter
#   address 0x12
#   size    4 bytes
# RES_QIE Counter
#   address 0x13
#   size    4 bytes
# WTE Counter
#   address 0x14
#   size    4 bytes

# Counter register addresses
counterDict = { "b_clock" : 0x12,
                "b_reset" : 0x13,
                "b_wte"   : 0x14,
                "i_clock" : 0x12,
                "i_reset" : 0x13,
                "i_wte"   : 0x14}
# Counter register size in bytes
size = 4

# RM 1, 2, 3, 4 i2c bus
rmBus   = [0x01, 0x10, 0x20, 0x02]
# Sipm Control 1, 2, 3, 4 i2c bus
sipmBus = [0x02, 0x20, 0x01, 0x04]
calBus = 0x10
# QIE Card i2c address
qieAddress = [0x19, 0x1a, 0x1b, 0x1c]

#########################################################

def getRmBus(rm):
    return rmBus[rm-1]

def getSipmBus(sipm):
    return sipmBus[sipm-1]

def getQieAddress(slot):
    return qieAddress[slot-1]

# Reverse Bytes
def reverseBytes(message):
    message_list = message.split()
    message_list.reverse()
    if message_list.pop() == '1':
        print "I2C ERROR"
    s = " "
    return s.join(message_list)

# Converts Message to Hex
def toHex(message,option=0):
    message_list = message.split()
    for byte in xrange(len(message_list)):
        message_list[byte] = hex(int(message_list[byte]))
        message_list[byte] = message_list[byte][2:]
        if len(message_list[byte]) == 1:
            message_list[byte] = '0' + message_list[byte]
    if option == 2:
        s = ":"
        return s.join(message_list)
    if option == 1:
        s = " "
        return s.join(message_list)
    s = ""
    return '0x' + s.join(message_list)

# Gets Value
def getValue(message):
    message = reverseBytes(message)
    hex_message = toHex(message)[2:]
    return int(hex_message,16)

#########################################################

# Reset qie card bridge fpga
def bridgeReset():
    bus.write(0x00, [0x06])
    m = bus.sendBatch()
    return m

# Reset gpio 
def gpioReset():
    # gpio reset
    #register 3 is control reg for i/o modes
    bus.write(ccm,[0x08])
    bus.write(gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
    bus.write(gpio,[0x01,0x00])
    bus.write(gpio,[0x01,0x08])
    bus.write(gpio,[0x01,0x18]) # GPIO reset is 10
    bus.write(gpio,[0x01,0x08])
    batch = bus.sendBatch()
    print 'GPIO Reset: {0}'.format(batch)

# Set gpio to output mode
def gpioOutputMode():
    #register 3 is control reg for i/o modes
    bus.write(ccm,[0x08])
    bus.write(gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
    batch = bus.sendBatch()
    error_code = batch[-1][0]
    if error_code == '1':
        print "Set GPIO output mode fail"
        return False
    else:
        print "Set GPIO output mode successful"
        return True

# Turns bits on (on=True) or off (on=False)
def reset(bit, on=False):
    bus.write(ccm,[0x08])
    bus.read(gpio,1)
    batch_1 = bus.sendBatch()
    value = getValue(batch_1[-1])
    bus.write(ccm,[0x08])
    if on == True:
        bus.write(gpio, [0x01, setBit(value, bit)])
    else:
        bus.write(gpio, [0x01, killBit(value, bit)])
    bus.read(gpio,1)
    batch_2 = bus.sendBatch()
    value_2 = getValue(batch_2[-1])

# Use value | bit operator to turn bits on
def setBit(value, bit):
    value = value | bit
    return value

# Use value & ~bit to turn bits off
def killBit(value, bit):
    value = value & ~bit
    return value

def powerReset():
    bus.write(ccm,[0x08])
    bus.write(gpio,[0x08,0])
    bus.sendBatch()


# Read counter from QIE card given RM (1-4) and Slot (1-4)
# Reads from Bridge or Igloo
def readCounter(rm, slot, counter):
    # Card is i2c address, register is register address 
    card = getQieAddress(slot)
    register = counterDict[counter]
    #bus.write(0x00,[0x06])
    bus.write(ccm, [getRmBus(rm)])
    # Read Bridge Counter
    if counter[0] == 'b':
        bus.write(card, [register])
        bus.read(card, size)
    # Read Igloo Counter
    else:
        bus.write(card, [0x11,0x03,0,0,0])
        bus.write(igloo, [register])
        bus.read(igloo, size)
    # Send the batch!
    m = bus.sendBatch()
    return m

def readCounters(rm_list, register_list, calibration=False):
    outputs = []
    for r in register_list:
        for rm in rm_list:
            for slot in [1,2,3,4]:
                # Read and print counter 
                m = readCounter(rm, slot, r)
                v = getValue(m[-1])
                outputs.append("{0}".format(v))
                #print "{0} : {1}".format(c,v)
        if calibration:
            # Read and print counter: calibration is "RM 2 Slot 1" address
            m = readCounter(2, 1, r)
            v = getValue(m[-1])
            outputs.append("{0}".format(v))
            #print "{0} : {1}".format(c,v)

    print "\t".join(outputs)
        
# bit = 0x10 is reset counter
# bit = 0x08 is counter enable
# reset high            turn bit = 0x10 on
# reset low             turn bit = 0x10 off
# read counters         counts = 0 after reset
# counter enable high   turn bit = 0x08 on
# wait a second         wait for t = 1 seconds
# counter enable low    turn bit = 0x08 off
# read counters         counts = 11000 after 1 second (11 kHz)
def count(rm_list, register_list, wait, iterations=1, calibration=False):
    # Set gpio output mode
    status = gpioOutputMode()

    # Gpio output mode succeeded
    if status:
        # Reset High and Low
        reset(0x10, True)
        reset(0x10, False)
        print "Reset Counters"
        # Read counters 
        readCounters(rm_list, register_list, calibration)

        for i in xrange(iterations):
            # Counter enable high, wait, counter enable low
            reset(0x08, True)
            time.sleep(wait)
            reset(0x08, False)

            # Read counters 
            readCounters(rm_list, register_list, calibration)

    else:
        print "Check power / connections."

#########################################################

def main():
    calibration = False
    rm_list = [3, 4]
    reg_list = ["b_reset", "i_reset", "b_wte", "i_wte"]
    #reg_list = ["b_clock", "i_clock"]
    wait = 1
    iterations = 20
    print "RM list: {0}".format(rm_list)
    print "Register list: {0}".format(reg_list)
    print "Calibration: {0}".format(calibration)
    print "Wait time: {0}".format(wait)
    print "Number iterations: {0}".format(iterations)
    count(rm_list, reg_list, wait, iterations, calibration)

if __name__ == "__main__":
    main()


