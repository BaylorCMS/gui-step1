# SimpleScripts to select GPIO and read from slots.

# CERN, Building 904
# October 2016

# Usage Notes:
# Please use your Raspberry Pi ip address (example 192.168.1.41)
# Configure your ethernet network manually 
# For example, ip address = 192.168.1.44, subnet mask = 255.255.255.0 

from datetime import datetime
import json
import client
import temp
import os
import sys
import platform
import config
import time

# Teststand class pings Raspberry Pi
class Teststand:
    def __init__(self, calibration=False, ip=config.ip_address):
        # Include calibraiton unit.
        self.calibrate = calibration
        
        # MyPi (ip address)
        self.pi = ip
        
        # Initialize Values
        self.gpioSelected = False       # Has GPIO been selected?
        self.piStatus     = False       # Can we ping the RaPi?
        self.busStatus    = False       # Can we connect a client websocket?
 
        # Define i2c addresses
        self.gpio           = config.gpio       # gpio i2c address
        self.fanout         = config.fanout     # fanout i2c address
        self.ccm            = config.ccm        # ngccm emulator i2c address
        self.address        = config.powerSlot  # Qie Card in slot 4 i2c address (use for Toggle Igloo Power)
        self.fanoutStatus   = config.board      # will a fanout board be used?
        self.channels       = config.channels   # Fanout channels
        
        self.active_slots = []          # Initialize with no active slots.

        # Is the OS Windows?
        windows = platform.system() == "Windows"

        # Use different count options to ping only 1 time.
        if windows:
            # Windows uses -n for ping count option. 
            self.ping = "ping -n 1 {0}".format(self.pi)
        else:
            # Linux and OSX use -c for ping count option. 
            self.ping = "ping -c 1 {0}".format(self.pi)

        # Ping Raspberry Pi and store result in self.piStatus
        self.pingPi()

        # Create a webBus instance
        if self.piStatus:
            try:
                self.myBus = client.webBus(self.pi,0)
            except:
                self.busStatus = False
                print 'Client Websocket Connection Error: No bus for you... sadness, it\'s true!'
                return

            # Client websocket connected sucessfully.
            self.busStatus = True

            # Set GPIO to output mode and reset GPIO
            self.gpioOutputMode()
            time.sleep(1)
            self.gpioReset()

            # Find active slots only if client websocket is connected.
            print "Finding active slots..."
            if self.calibrate:
                self.slot_list = [2,3,4,5,7,8,9,10,12]
            else:
                self.slot_list = [2,3,4,5,7,8,9,10,18,19,20,21,23,24,25,26]
            self.active_slots = self.findActiveSlots()
            print "Active J-Slots: {0}".format(self.active_slots)
        else:
            print "Raspberry Pi disconnected."

    #################################
    ###                           ###
    ###  BEGIN MEMBER FUNCTIONS   ###
    ###                           ###
    #################################


##################################################################################


    # Test Raspberry Pi Connection
    def pingPi(self):
        print "Pinging Raspberry Pi: {0}".format(self.ping)
        pingStatus = os.system(self.ping)
        if pingStatus == 0:
            print "Raspberry Pi Connected: {0}".format(self.pi)
            self.piStatus = True
        else:
            print "Raspberry Pi Connection Error: {0}".format(self.pi)
            self.piStatus = False

    def reverseBytes(self, message):
        message_list = message.split()
        message_list.reverse()
        s = " "
        return s.join(message_list)
    
    # Converts decimal messages to Hex messages.
    def toHex(self, message, colon=0):
        message_list = message.split()
        for byte in xrange(len(message_list)):
            message_list[byte] = hex(int(message_list[byte]))
            message_list[byte] = message_list[byte][2:]
            if len(message_list[byte]) == 1:
                message_list[byte] = '0' + message_list[byte]
        if colon == 2:
            s = ":"
            return s.join(message_list)
        if colon == 1:
            s = " "
            return s.join(message_list)
        s = ""
        return '0x' + s.join(message_list)
    
    # Parses Unique ID from message.
    def serialNum(self, message):
        message_list = message.split()
        # Remove error code, family name, checksum
        message_list = message_list[2:-1]
        s = " "
        return s.join(message_list)

    # Checks and removes error code.
    def errorCode(self, message):
        message_list = message.split()
        # Remove error code, family name, checksum
        error = message_list[0]
        if error == '1':
            print "I2C Error"
        message_list = message_list[1:]
        s = " "
        return s.join(message_list)
    
    def readBridge(self, regAddress, num_bytes):
        self.selectSlot(self.jslot)
        self.myBus.write(0x00,[0x06])
        self.myBus.sendBatch()
        self.myBus.write(self.slot,[regAddress])
        self.myBus.read(self.slot, num_bytes)
        message = self.myBus.sendBatch()[-1]
        #if message[0] != '0':
        #    print 'Bridge I2C Error'
        return self.toHex(self.reverseBytes(message[2:]))

    def readIgloo(self, regAddress, num_bytes):
        self.selectSlot(self.jslot)
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.slot,[0x11,0x03,0,0,0])
        self.myBus.write(0x09,[regAddress])
        self.myBus.read(0x09, num_bytes)
        message = self.myBus.sendBatch()[-1]
        #if message[0] != '0':
        #    print 'Igloo I2C Error'
        return self.toHex(self.reverseBytes(message[2:]))


##################################################################################

    def gpioReset(self):
        if self.board:          # Use fanout board
            for ch in self.channels:
                self.myBus.write(self.fanout, [ch])
                self.magicReset()
        else:                   # Without fanout board
            self.magicReset()

    # Reset gpio and set to output mode 
    def magicReset(self):
        # gpio reset
        #register 3 is control reg for i/o modes
        self.myBus.write(self.ccm,[0x08])
        self.myBus.write(self.gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
        self.myBus.write(self.gpio,[0x01,0x00]) # turn off reset
        self.myBus.write(self.gpio,[0x01,0x08]) # reset low
        self.myBus.write(self.gpio,[0x01,0x18]) # reset high: GPIO reset is 10
        batch = self.myBus.sendBatch()
        time.sleep(1)
        self.myBus.write(self.ccm,[0x08])
        self.myBus.write(self.gpio,[0x01,0x08]) # reset low (turn off reset)
        batch = self.myBus.sendBatch()
        error_code = batch[-1][0]
        if error_code == '1':
            print "GPIO reset fail"
            return False
        else:
            print "GPIO reset successful"
            return True

    
    def gpioOutputMode(self):
        if self.board:              # Use fanout board
            for ch in self.channels:
                self.myBus.write(self.fanout, [ch])
                self.outputMode()
        else:                       # Without fanout board
            self.outputMode()

    # Set gpio to output mode
    def outputMode(self):
        #register 3 is control reg for i/o modes
        self.myBus.write(self.ccm,[0x08])
        self.myBus.write(self.gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
        self.myBus.write(self.gpio,[0x01,0x00]) # turn off reset
        batch = self.myBus.sendBatch()
        error_code = batch[-1][0]
        if error_code == '1':
            print "Set GPIO output mode fail"
            return False
        else:
            print "Set GPIO output mode successful"
            return True

    # Select jslot, open channel on ngCCM Emulator.
    def selectSlot(self, jslot):
        self.jslot = jslot

        bridgeDict = {  2 : 0x19, 3 : 0x1A, 4 : 0x1B, 5 : 0x1C,
                        7 : 0x19, 8 : 0x1A, 9: 0x1B, 10: 0x1C,
                       18 : 0x19, 19 : 0x1A, 20: 0x1B, 21 : 0x1C,
                       23 : 0x19, 24 : 0x1A, 25: 0x1B, 26 : 0x1C,
                       12 : 0x19}

        # Fanout Board
        if self.board:
            if self.jslot in [18,19,20,21,23,24,25,26]:
                self.myBus.write(self.fanout, [self.channels[0]])   # RM 1 and 2
            if self.jslot in [2,3,4,5,7,8,9,10,12]:
                self.myBus.write(self.fanout, [self.channels[1]])   # RM 3 and 4 and CU

        self.slot = bridgeDict[self.jslot]
        if self.jslot in [23,24,25,26]:             # RM 1
            self.myBus.write(self.ccm, [0x01|0x8])
        if self.jslot in [12,18,19,20,21]:          # RM 2 and CU (12)
            self.myBus.write(self.ccm, [0x10|0x8])
        if self.jslot in [7,8,9,10]:                # RM 3
            self.myBus.write(self.ccm, [0x20|0x8])
        if self.jslot in [2,3,4,5]:                 # RM 4
            self.myBus.write(self.ccm, [0x02|0x8])

        # Don't send batch yet... wait until full command is assembled.
        #self.myBus.sendBatch()

    # Writes proper GPIO to ngCCM Emulator for given jslot.  Used for programming cards.
    def selectGpio(self, jslot):
        self.jslot = jslot
        # Defines GPIO values. Only used for reference.
        #jSlotDict = {"J2 and J18" : 0x29, "J3 and J19" : 0x89, "J4 and J20" : 0xA9,
        #            "J5 and J21" : 0x49, "J7 and J23" : 0x2A, "J8 and J24" : 0x8A,
        #            "J9 and J25" : 0xAA, "J10 and J26" : 0x4A}

        # Used to set GPIO for single slot.
        jSlotDict = {  2  : 0x29, 3  : 0x89, 4  : 0xA9, 5  : 0x49,
                       7  : 0x2A, 8  : 0x8A, 9  : 0xAA, 10 : 0x4A,
                       18 : 0x29, 19 : 0x89, 20 : 0xA9, 21 : 0x49,
                       23 : 0x2A, 24 : 0x8A, 25 : 0xAA, 26 : 0x4A,
                       12 : 0x2C}

        gpioVal = jSlotDict[self.jslot]
        self.gpioSelected = True

        # Reset GPIO and set GPIO output mode
        self.gpioReset()

        # Old magic reset commands
        #self.myBus.write(self.ccm,[0x08])
        #self.myBus.write(self.gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
        #self.myBus.write(self.gpio,[0x01,0x00])
        #self.myBus.write(self.gpio,[0x01,0x08])
        #self.myBus.write(self.gpio,[0x01,0x18]) # GPIO reset is 10
        #self.myBus.write(self.gpio,[0x01,0x08])
    
        #jtag selectors finnagling for slot 26
        self.myBus.write(self.gpio,[0x01,gpioVal])
    
        # myBus.write(self.gpio,[0x03,0x08])
        self.myBus.read(self.gpio,1)
        batch = self.myBus.sendBatch()
    
        if (batch[-1] == "1 0"):
            print "GPIO I2C Error: J{0}".format(self.jslot)
        elif (batch[-1] == "0 "+str(gpioVal)):
            print 'GPIO Selected: J{0}'.format(self.jslot)
    
        else:
            print 'GPIO Choice Error... state of confusion!'

##################################################################################
        
    # Read Unique ID and Firmware Versions from given jslot
    def readInfo(self, jslot):
        self.selectSlot(jslot)
        print 'Read Slot: J'+str(self.jslot)

        # Getting unique ID
        # 0x000000ea9c8b
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.slot,[0x11,0x04,0,0,0])
        self.myBus.write(0x50,[0x00])
        self.myBus.read(0x50, 8)
        raw_bus = self.myBus.sendBatch()
        raw_bus = raw_bus[-1]
        if raw_bus[0] != '0':
            print 'Read Unique ID I2C Error!'
            return False
        # Remove error code [0], family code [1] and checksum [-1]
        #salted_bus = self.errorCode(raw_bus)
        salted_bus = self.serialNum(raw_bus)
        cooked_bus = self.reverseBytes(salted_bus)
        self.unique_id = self.toHex(cooked_bus)
        print 'Unique ID: {0}'.format(self.unique_id)

        # Getting bridge firmware
        raw_data = self.readBridge(0x04, 4)
        data_well_done = raw_data[2:]
        print 'Bridge FW: 0x'+str(data_well_done)
        self.bridge_fw_maj = "0x"+data_well_done[0:2]    #these are the worst (best?) variable names ever
        self.bridge_fw_min = "0x"+data_well_done[2:4]
        self.bridge_fw_oth = "0x"+data_well_done[4:8]

        # Getting temperature
        self.temp = str(round(temp.readManyTemps(self.myBus, self.slot, 10, "Temperature", "nohold"),4))

        # Getting IGLOO firmware info
        self.igloo_fw_maj = self.readIgloo(0x00, 1)
        self.igloo_fw_min = self.readIgloo(0x01, 1)
        print 'Igloo FW: {0} {1}'.format(self.igloo_fw_maj, self.igloo_fw_min)

        # Return Dictionary
        return self.getInfo()


##################################################################################


    # Returns dictionary with unique id and firmware versions
    def getInfo(self):
        cardInfo = {}
        cardInfo["unique_id"]      = self.unique_id
        cardInfo["bridge_fw_maj"]  = self.bridge_fw_maj
        cardInfo["bridge_fw_min"]  = self.bridge_fw_min
        cardInfo["bridge_fw_oth"]  = self.bridge_fw_oth
        cardInfo["igloo_fw_maj"]   = self.igloo_fw_maj
        cardInfo["igloo_fw_min"]   = self.igloo_fw_min
        cardInfo["temperature"]    = self.temp
        cardInfo["date_time"]      = str(datetime.now())

        print "Card info recorded. Merci beaucoup!"
        return cardInfo

    # Tests for communication with Bridge.
    def hiDerBridge(self, jslot):
        self.jslot = jslot
        onesZeros = self.readBridge(0x0A, 4)
        value = '0xaaaaaaaa'
        #print "Bridge OnesZeros: {0}".format(onesZeros)
        if onesZeros == value:
            return True
        else:
            return False

    # Tests for communication with Igloo. 
    def hiDerIgloo(self, jslot):
        self.jslot = jslot
        igloo_fw_maj = self.readIgloo(0x00, 1)
        igloo_fw_min = self.readIgloo(0x01, 1)
        #print "Igloo FW: {0} {1}".format(igloo_fw_maj, igloo_fw_min)
        return "{0} {1}".format(igloo_fw_maj, igloo_fw_min)

    # Determine active jslots.
    def findActiveSlots(self):
        slots = []
        for slot in self.slot_list:
            hiB = self.hiDerBridge(slot)
            if hiB:
                hiI = self.hiDerIgloo(slot)
                print "J{0} : Igloo FW {1}".format(slot, hiI)
                slots.append(slot)
        return slots
            
    def readActiveSlots(self):
        info = []
        for slot in self.active_slots:
            info.append(self.readInfo(slot))
        return info

##################################################################################

slot_list = [2,3,4,5,7,8,9,10,12,18,19,20,21,23,24,25,26]

# Get information for specific slot.
# Enter J Slot as python argument.
# For example, for J2 (slot 2) run
# python scripts.py 2
# Windows True for Windows OS, False for Linux and OSX
# Pi Ip Address: default is 192.168.1.41
def runSlot():
    if len(sys.argv) != 2:
        print "Enter J-Slot to select and read"
    else:
        slot = int(sys.argv[1])
        if slot not in slot_list:
            print "Please select J-Slot from {0}".format(slot_list)
        else:
            ts = Teststand()
            if ts.piStatus and ts.busStatus:
                hiB = ts.hiDerBridge(slot)
                print "Hi Der Bridge: {0}".format(hiB)
                if hiB:
                    hiI = ts.hiDerIgloo(slot)
                    print "Hi Der Igloo: {0}".format(hiI)
                    ts.selectGpio(slot)
                    cardInfo = ts.readInfo(slot)
                    #print cardInfo

# Get information for all active slots.
# Windows True for Windows OS, False for Linux and OSX
# Pi Ip Address: default is 192.168.1.41
def runStand():
    ts = Teststand()
    if ts.piStatus and ts.busStatus:
        info = ts.readActiveSlots()
        #print info

# Only run if scripts.py is main... otherwise don't run (if imported as library).
if __name__ == '__main__':
    #runSlot()
    runStand()



