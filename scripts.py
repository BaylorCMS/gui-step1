# Teststand class to select GPIO and read from slots.
# Used to program Igloo FPGAs
# Used to read from QIE cards

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

def writeToLog(logFile, line): 
    timeStamp = datetime.now()
    line = "{0} {1}".format(timeStamp, line)
    print line
    with open(logFile, 'a') as f:
        print >> f, line

# Teststand class pings Raspberry Pi
class Teststand:
    def __init__(self, board=True, calibration=False, ip=config.ip_address):
        self.logFile = "teststand.log"
        # Include calibraiton unit.
        self.calibrate = calibration
        # Use fanout board with channels.
        self.board = board
        self.channels = config.channels
        # MyPi (ip address)
        self.pi = ip
        
        # Initialize Values
        self.gpioSelected = False       # Has GPIO been selected?
        self.piStatus     = False       # Can we ping the RaPi?
        self.busStatus    = False       # Can we connect a client websocket?

        # Define i2c addresses
        self.gpio = config.gpio         # gpio i2c address
        self.fanout = config.fanout     # fanout i2c address
        self.ccm = config.ccm           # ngccm emulator i2c address
        self.address = 0x19             # Qie Card in slot 1 i2c address (use for Toggle Igloo Power)
        self.iglooAddress = 0x09        # igloo i2c address
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
                writeToLog(self.logFile, 'Client Websocket Connection Error: No bus for you... sadness, it\'s true!')
                return

            # Client websocket connected sucessfully.
            self.busStatus = True

            # Set GPIO to output mode and reset GPIO
            self.gpioOutputMode()
            time.sleep(1)
            self.gpioReset()

            # Find active slots only if client websocket is connected.
            writeToLog(self.logFile, "Finding active slots...")
            if self.calibrate:
                self.slot_list = [2,3,4,5,7,8,9,10,12]
            else:
                self.slot_list = [2,3,4,5,7,8,9,10,18,19,20,21,23,24,25,26]
            self.active_slots = self.findActiveSlots()
            writeToLog(self.logFile, "Active J-Slots: {0}".format(self.active_slots))
        else:
            writeToLog(self.logFile, "Raspberry Pi disconnected.")

    #################################
    ###                           ###
    ###  BEGIN MEMBER FUNCTIONS   ###
    ###                           ###
    #################################


##################################################################################

    def setLogFile(self, logFile):
        self.logFile = logFile

    # Test Raspberry Pi Connection
    def pingPi(self):
        writeToLog(self.logFile, "Pinging Raspberry Pi: {0}".format(self.ping))
        pingStatus = os.system(self.ping)
        if pingStatus == 0:
            writeToLog(self.logFile, "Raspberry Pi Connected: {0}".format(self.pi))
            self.piStatus = True
        else:
            writeToLog(self.logFile, "Raspberry Pi Connection Error: {0}".format(self.pi))
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
    
    # getValue(): input hex value and output corresponding integer value in decimal
    def getValue(self, hex_message):
        #hex_message = self.toHex(message)[2:]
        return int(hex_message,16)

    # getMessageList(): input value and number of bytes; output message as list
    def getMessageList(self, value, num_bytes):
        total_length = 2 * num_bytes
        hex_message = hex(value)[2:]
        hex_message = hex_message.zfill(total_length)
        mList = list(int(hex_message[a:a+2],16) for a in xrange(0,total_length,2))
        mList.reverse()
        return mList
 
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
            writeToLog(self.logFile, "I2C_ERROR")
        message_list = message_list[1:]
        s = " "
        return s.join(message_list)
    
    def readBridge(self, registerAddress, num_bytes):
        self.selectSlot(self.jslot) # does multiplex
        self.myBus.write(0x00,[0x06])
        self.myBus.sendBatch()
        self.myBus.write(self.card_i2c_address,[registerAddress])
        self.myBus.read(self.card_i2c_address, num_bytes)
        message = self.myBus.sendBatch()[-1]
        #if message[0] != '0':
        #    writeToLog(self.logFile, 'Bridge I2C_ERROR')
        return self.toHex(self.reverseBytes(message[2:]))

    # Function to write to Bridge FPGA
    def writeBridge(self, registerAddress,messageList):
        self.selectSlot(self.jslot) # does multiplex
        self.myBus.write(self.card_i2c_address, [registerAddress]+messageList)
        return self.myBus.sendBatch()

    # Function to read from Igloo FPGA (top or bot)
    def readIgloo(self, igloo, registerAddress, num_bytes=1):
        i2cSelectValue = -1
        iglooSelectDictionary = {"top":0x03, "bot":0x06}
        try:
            i2cSelectValue = iglooSelectDictionary[igloo]
        except KeyError:
            writeToLog(self.logFile, "In readIgloo(): igloo = {0} which is not 'top' or 'bot'".format(igloo))
            writeToLog(self.logFile, "In readIgloo(): i2cSelectValue = {0} (should be 0x03 or 0x06, -1 is the default if not set)".format(i2cSelectValue))
            sys.exit(1)
        self.myBus.write(0x00,[0x06])
        self.selectSlot(self.jslot) # does multiplex
        #self.multiplex()
        self.myBus.write(self.card_i2c_address,[0x11,i2cSelectValue,0,0,0])
        self.myBus.write(self.iglooAddress, [registerAddress])
        self.myBus.read(self.iglooAddress, num_bytes)
        message = self.myBus.sendBatch()[-1]
        if message[0] != '0':
            writeToLog(self.logFile, 'In readIgloo(): Igloo I2C_ERROR')
        writeToLog(self.logFile, "In readIgloo(): Reading {0} Igloo; message = {1}".format(igloo, message))
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
            writeToLog(self.logFile, "GPIO reset fail")
            return False
        else:
            writeToLog(self.logFile, "GPIO reset successful")
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
            writeToLog(self.logFile, "outputMode(): Set GPIO output mode ERROR")
            return False
        else:
            writeToLog(self.logFile, "outputMode(): Set GPIO output mode SUCCESS")
            return True

    # Select jslot, open channel on ngCCM Emulator.
    def selectSlot(self, jslot):
        self.jslot = jslot

        # RMs and CU slots
        bridgeDict = {  2 : 0x19, 3  : 0x1A, 4  : 0x1B,  5 : 0x1C,
                        7 : 0x19, 8  : 0x1A, 9  : 0x1B, 10 : 0x1C,
                       18 : 0x19, 19 : 0x1A, 20 : 0x1B, 21 : 0x1C,
                       23 : 0x19, 24 : 0x1A, 25 : 0x1B, 26 : 0x1C,
                       12 : 0x19}

        # Fanout Board
        if self.board:
            if self.jslot in [18,19,20,21,23,24,25,26]:
                self.myBus.write(self.fanout, [self.channels[0]])   # RM 1 and 2
            if self.jslot in [2,3,4,5,7,8,9,10,12]:
                self.myBus.write(self.fanout, [self.channels[1]])   # RM 3 and 4 and CU

        self.card_i2c_address = bridgeDict[self.jslot]
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
    # Use for programming top or bottom igloo. 
    def selectGpio(self,jslot,igloo):
        gpioValueDict = {  2  : 0x29, 3  : 0x89, 4  : 0xA9, 5  : 0x49,
                           7  : 0x2A, 8  : 0x8A, 9  : 0xAA, 10 : 0x4A,
                           18 : 0x29, 19 : 0x89, 20 : 0xA9, 21 : 0x49,
                           23 : 0x2A, 24 : 0x8A, 25 : 0xAA, 26 : 0x4A,
                           12 : 0x2C}

        self.jslot = jslot
        gpioVal = gpioValueDict[self.jslot] 
        # Fanout Board
        if self.board:
            if self.jslot in [18,19,20,21,23,24,25,26]:
                self.myBus.write(self.fanout, [self.channels[0]])   # RM 1 and 2
            if self.jslot in [2,3,4,5,7,8,9,10,12]:
                self.myBus.write(self.fanout, [self.channels[1]])   # RM 3 and 4 and CU
        
        # it is better to sendBatch() at the end so that full multiplexing happens
        #batch = self.myBus.sendBatch() # verified that sendbatch is not needed here
        
        self.myBus.write(0x74, [0x08]) # PCA9538 is bit 3 on ngccm mux
        # myBus.write(0x70,[0x01,0x00]) # GPIO PwrEn is register 3
        #backplane power enable and backplane reset
        #register 3 is control reg for i/o modes
        self.myBus.write(0x70,[0x03,0x00]) # sets all GPIO pins to 'output' mode
        self.myBus.write(0x70,[0x01,0x08]) # GPIO value 0x08: bakplane power enable 1
        self.myBus.write(0x70,[0x01,0x18]) # GPIO reset 0x18: backplane reset 1
        self.myBus.write(0x70,[0x01,0x08]) # GPIO reset 0x08: backplane reset 0
    
        #jtag selectors finnagling for slot 26
        self.myBus.write(0x70,[0x01,gpioVal])
    
        # myBus.write(0x70,[0x03,0x08])
        self.myBus.read(0x70,1)
        batch = self.myBus.sendBatch()
        message = batch[-1]
        writeToLog(self.logFile, "GPIO Batch = "+str(batch))
    
        if (message == "1 0"):
            writeToLog(self.logFile, "In gpioBttnPress(): GPIO I2C_ERROR")
            writeToLog(self.logFile, self.I2C_ERROR_HELP)
            return
        elif (message == "0 "+str(gpioVal)):
            writeToLog(self.logFile, "GPIO Success: message is {0}".format(message))
    
        else:
            writeToLog(self.logFile, "GPIO Error: unexpected message is {0}".format(message))

        
        # select JTAG to program top/bottom igloo using Bridge register BRDG_ADDR_IGLO_CONTROL: 0x22
        iglooControl = 0x22
        message = self.readBridge(iglooControl,4)
        writeToLog(self.logFile, "Reading from BRDG_ADDR_IGLO_CONTROL before selecting JTAG: message = {0}".format(message))
        value = self.getValue(message)
        # select top (0) or bottom (1) igloo to program; maintain settings for other bits
        if igloo == "top":
            value = value & 0xFFE
        elif igloo == "bot":
            value = value | 0x001
        else:
            writeToLog(self.logFile, "In selectGpio(): ERROR; Igloo is '{0}' which is not top or bot".format(igloo))
        messageList = self.getMessageList(value,4)
        self.writeBridge(iglooControl,messageList)
        message = self.readBridge(iglooControl,4)
        writeToLog(self.logFile, "Reading from BRDG_ADDR_IGLO_CONTROL after selecting JTAG: message = {0}".format(message))
        
        writeToLog(self.logFile, "Ready to program {0} igloo".format(igloo))



##################################################################################
        
    # Read Unique ID and Firmware Versions from given jslot
    def readInfo(self, jslot):
        self.selectSlot(jslot)
        writeToLog(self.logFile, 'Read Slot: J'+str(self.jslot))

        # Getting unique ID
        # 0x000000ea9c8b
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.card_i2c_address,[0x11,0x04,0,0,0])
        self.myBus.write(0x50,[0x00])
        self.myBus.read(0x50, 8)
        raw_bus = self.myBus.sendBatch()
        raw_bus = raw_bus[-1]
        if raw_bus[0] != '0':
            writeToLog(self.logFile, 'Read Unique ID I2C_ERROR!')
            return False
        # Remove error code [0], family code [1] and checksum [-1]
        salted_bus = self.errorCode(raw_bus)
        #salted_bus = self.serialNum(raw_bus)
        cooked_bus = self.reverseBytes(salted_bus)
        self.unique_id = self.toHex(cooked_bus)
        writeToLog(self.logFile, 'Unique ID: {0}'.format(self.unique_id))

        # Getting bridge firmware
        raw_data = self.readBridge(0x04, 4)
        data_well_done = raw_data[2:]
        writeToLog(self.logFile, 'Bridge FW: 0x'+str(data_well_done))
        self.bridge_fw_maj = "0x"+data_well_done[0:2]    #these are the worst (best?) variable names ever
        self.bridge_fw_min = "0x"+data_well_done[2:4]
        self.bridge_fw_oth = "0x"+data_well_done[4:8]

        # Getting temperature
        self.temp = str(round(temp.readManyTemps(self.myBus, self.card_i2c_address, 10, "Temperature", "nohold"),4))

        # Getting IGLOO firmware info
        self.top_igloo_fw_maj = self.readIgloo("top", 0x00)
        self.top_igloo_fw_min = self.readIgloo("top", 0x01)
        self.bot_igloo_fw_maj = self.readIgloo("bot", 0x00)
        self.bot_igloo_fw_min = self.readIgloo("bot", 0x01)
        writeToLog(self.logFile, 'Top Igloo FW: {0} {1}'.format(self.top_igloo_fw_maj, self.top_igloo_fw_min))
        writeToLog(self.logFile, 'Bottom Igloo FW: {0} {1}'.format(self.bot_igloo_fw_maj, self.bot_igloo_fw_min))

        # Return Dictionary
        return self.getInfo()


##################################################################################


    # Returns dictionary with unique id and firmware versions
    def getInfo(self):
        cardInfo = {}
        cardInfo["Barcode"]             = ""
        cardInfo["Unique_ID"]           = self.unique_id
        cardInfo["FirmwareMaj"]         = self.bridge_fw_maj
        cardInfo["FirmwareMin"]         = self.bridge_fw_min
        cardInfo["FirmwareOth"]         = self.bridge_fw_oth
        cardInfo["IglooMajVerT"]        = self.top_igloo_fw_maj
        cardInfo["IglooMinVerT"]        = self.top_igloo_fw_min
        cardInfo["IglooMajVerB"]        = self.bot_igloo_fw_maj
        cardInfo["IglooMinVerB"]        = self.bot_igloo_fw_min
        cardInfo["temperature"]         = self.temp
        cardInfo["DateRun"]             = str(datetime.now())

        #writeToLog(self.logFile, "Card info recorded. Merci beaucoup!")
        return cardInfo

    # Tests for communication with Bridge.
    def hiDerBridge(self, jslot):
        self.jslot = jslot
        onesZeros = self.readBridge(0x0A, 4)
        value = '0xaaaaaaaa'
        #writeToLog(self.logFile, "Bridge OnesZeros: {0}".format(onesZeros))
        if onesZeros == value:
            return True
        else:
            return False

    # Tests for communication with Igloo. 
    def hiDerIgloo(self, jslot):
        self.jslot = jslot
        self.top_igloo_fw_maj = self.readIgloo("top", 0x00)
        self.top_igloo_fw_min = self.readIgloo("top", 0x01)
        self.bot_igloo_fw_maj = self.readIgloo("bot", 0x00)
        self.bot_igloo_fw_min = self.readIgloo("bot", 0x01)
        #writeToLog(self.logFile, "Igloo FW: {0} {1}".format(igloo_fw_maj, igloo_fw_min))
        return "top: {0} {1} bot: {2} {3}".format(self.top_igloo_fw_maj, self.top_igloo_fw_min,
                                                  self.bot_igloo_fw_maj, self.bot_igloo_fw_min)

    # Determine active jslots.
    def findActiveSlots(self):
        slots = []
        for slot in self.slot_list:
            hiB = self.hiDerBridge(slot)
            if hiB:
                # we should not read from Igloos before they are programmed.
                #hiI = self.hiDerIgloo(slot)
                #writeToLog(self.logFile, "J{0} : Igloo FW {1}".format(slot, hiI))
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
        writeToLog(self.logFile, "Enter J-Slot to select and read")
    else:
        slot = int(sys.argv[1])
        if slot not in slot_list:
            writeToLog(self.logFile, "Please select J-Slot from {0}".format(slot_list))
        else:
            ts = Teststand()
            if ts.piStatus and ts.busStatus:
                hiB = ts.hiDerBridge(slot)
                writeToLog(self.logFile, "Hi Der Bridge: {0}".format(hiB))
                if hiB:
                    hiI = ts.hiDerIgloo(slot)
                    writeToLog(self.logFile, "Hi Der Igloo: {0}".format(hiI))
                    ts.selectGpio(slot)
                    cardInfo = ts.readInfo(slot)
                    #writeToLog(self.logFile, cardInfo)

# Get information for all active slots.
# Windows True for Windows OS, False for Linux and OSX
# Pi Ip Address: default is 192.168.1.41
def runStand():
    ts = Teststand()
    if ts.piStatus and ts.busStatus:
        info = ts.readActiveSlots()
        #writeToLog(self.logFile, info)

# Only run if scripts.py is main... otherwise don't run (if imported as library).
if __name__ == '__main__':
    runSlot()
    #runStand()



