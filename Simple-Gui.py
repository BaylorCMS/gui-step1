# Simple-Gui.py
#
# This is the Simple Graphical User Interface for communicating with QIE Cards
# using the ngCCM Emulator. It can be used to open GPIO for programming of 
# the Igloo FPGA. A computer running Microsemi Flash Pro must be connected
# to the ngCCM Emulator for Igloo FPGA programming.

# Developed with the help of many people.
# Originally based on User-Interface.py used at Fermilab.
# For CERN, Building 904, October 2016.

from Tkinter import *
from datetime import datetime
from initialClass import initialTests
from cardInfoClass import cardInformation
import igloo_test as it
import temp
import json
import client
import subprocess
import os
import platform
import config

class makeGui:
    def __init__(self, parent):
        # The Raspberry Pi IP address
        self.pi = config.ip_address

        # Windows Computer?
        windows = (platform.system() == 'Windows')

        if windows:
            self.ping = "ping -n 1 {0}".format(self.pi)
        else:
            self.ping = "ping -c 1 {0}".format(self.pi)

        # Ping Pi
        status = self.pingPi()
        #status = False

        # Create a webBus instance
        if status:
            self.myBus = client.webBus(self.pi,0)

        # Define i2c addresses
        self.gpio = config.gpio         # gpio i2c address
        self.fanout = config.fanout     # fanout i2c address
        self.ccm = config.ccm           # ngccm emulator i2c address
        self.address = 0x1c             # Qie Card in slot 4 i2c address (use for Toggle Igloo Power)
        self.fanoutStatus = 0           # 0 means don't use fanout board, 1 means use fanout board
        self.channels = config.channels # Fanout channels

        # Create an instance of initialTests
        self.initialTest = initialTests()

        # Create an instance of cardInformation
        self.cardInfo = cardInformation()

        # Read info from left side?
        self.readFromList = True

        # Has GPIO been selected?
        self.gpioSelected = False

        # Make an empty list that will eventually contain all of
        # the active card slots
        self.outSlotNumbers = []

        # Name the parent. This is mostly for bookkeeping purposes
        # and doesn't really get used too much.
        self.myParent = parent

        # Make a placeholder for the shortened unique ID
        self.uniqueIDPass = ""

        self.nameChoiceVar         =  StringVar()
        self.gpioChoiceVar         =  StringVar()
        self.infoCommentVar        =  StringVar()
        self.barcodeEntry          =  StringVar()
        self.uniqueIDEntry         =  StringVar()
        self.tempEntry             =  StringVar()
        self.firmwareVerEntry      =  StringVar()
        self.firmwareVerMinEntry   =  StringVar()
        self.firmwareVerOtherEntry =  StringVar()
        self.iglooToggleEntry      =  StringVar()
        self.iglooMajVerEntry      =  StringVar()
        self.iglooMinVerEntry      =  StringVar()
        self.overwriteVar          =  IntVar()

        # Place an all-encompassing frame in the parent window. All of the following
        # frames will be placed here (topMost_frame) and not in the parent window.
        self.topMost_frame = Frame(parent)
        self.topMost_frame.pack()

        #----- constants for controlling layout
        button_width = 6

        button_padx = "2m"
        button_pady = "1m"

        frame_padx = "3m"
        frame_pady = "2m"
        frame_ipadx = "3m"
        frame_ipady = "1m"
        #---------- end layout constants ------


        ##########################################
        ###                                    ###
        ###     BEGIN MAKING SUB-FRAMES        ###
        ###                                    ###
        ##########################################

        # Make a top half-frame
        self.topHalf_frame = Frame(self.topMost_frame)
        self.topHalf_frame.pack(side=TOP)

        # Make a frame for containing an experiment diagram
        self.experiment_frame = Frame(
            self.topHalf_frame,
            borderwidth=5, relief=RIDGE,
            height=580, width=300,
            background="white"
            )
        self.experiment_frame.pack_propagate=(False)
        self.experiment_frame.pack(
            side=RIGHT,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        ##########################################
        ###                                    ###
        ###     BEGIN MAKING WIDGETS           ###
        ###                                    ###
        ##########################################

        ######################################
        #####                            #####
        #####    Widgets in info frame   #####
        #####                            #####
        ######################################
        
        ######################################
        #####                            #####
        #####  Experiment Setup Frames   #####
        #####                            #####
        ######################################

        # Make a label for the entire left frame
        self.experi_subFrame_lbl = Label(self.experiment_frame,text="QIE Card Setup & Parameters")
        self.experi_subFrame_lbl.configure(
            padx=button_padx,
            pady=button_pady,
            background="white"
            )
        self.experi_subFrame_lbl.pack(side=TOP)

        # Make top 2_11 subframe
        self.experi_subTop2_11_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_11_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_7 subframe
        self.experi_subTop2_7_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_7_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_8 subframe
        self.experi_subTop2_8_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_8_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_9 subframe
        self.experi_subTop2_9_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_9_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_10 subframe
        self.experi_subTop2_10_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_10_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_6 subframe
        self.experi_subTop2_6_frame = Frame(self.experiment_frame, bg="white")
        self.experi_subTop2_6_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2 subframe
        self.experi_subTop2_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_0 subframe
        self.experi_subTop2_0_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_0_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_1 subframe
        self.experi_subTop2_1_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_1_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_2 subframe
        self.experi_subTop2_2_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_2_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_3 subframe
        self.experi_subTop2_3_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_3_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4 subframe
        self.experi_subTop2_4_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_4_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4_5 subframe
        self.experi_subTop2_4_5_frame = Frame(self.experiment_frame,background="white")
        self.experi_subTop2_4_5_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4_6 subframe
        self.experi_subTop_2_4_6_frame = Frame(self.experiment_frame, background="white")
        self.experi_subTop_2_4_6_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )


        ###################################
        ###                             ###
        ###   Subframes on right side   ###
        ###                             ###
        ###################################

        # Create variables for each manual check (16 placeholders for now)
        self.testPassList = [StringVar() for i in range(0,19)]
        self.testPassState = ("Pass","Fail")

        #################################
        ###                           ###
        ###       Info for Card       ###
        ###                           ###
        #################################

        # Make a label for the uniqueID entry
        self.experi_uniqueID_lbl = Label(self.experi_subTop2_frame, text="Unique ID: ")
        self.experi_uniqueID_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_uniqueID_lbl.pack(side=LEFT)

        # Make an entry box for the UniqueID
        # Make a entrybox for testing comments
        self.experi_uniqueID_entry = Entry(
            self.experi_subTop2_frame,
            textvariable=self.uniqueIDEntry,
            state="readonly"
            )
        self.experi_uniqueID_entry.pack(side=RIGHT)

        # Make a label for the temperature entry
        self.experi_temperature_lbl = Label(self.experi_subTop2_0_frame, text="Temperature: ")
        self.experi_temperature_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_temperature_lbl.pack(side=LEFT)

        # Make an entry box for the temperature
        # Make a entrybox for testing comments
        self.experi_temperature_entry = Entry(
            self.experi_subTop2_0_frame,
            textvariable=self.tempEntry,
            state="readonly"
            )
        self.experi_temperature_entry.pack(side=RIGHT)

        # Make a label for the main firmware ver entry
        self.experi_firmwareVer_lbl = Label(self.experi_subTop2_1_frame, text="Bridge Ver (Major): ")
        self.experi_firmwareVer_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVer_lbl.pack(side=LEFT)

        # Make an entry box for the main firmware ver
        # Make a entrybox for testing comments
        self.experi_firmwareVer_entry = Entry(
            self.experi_subTop2_1_frame,
            textvariable=self.firmwareVerEntry,
            state="readonly"
            )
        self.experi_firmwareVer_entry.pack(side=RIGHT)

        # Make a label for the minor firmware ver entry
        self.experi_firmwareVerMin_lbl = Label(self.experi_subTop2_2_frame, text="Bridge Ver (Minor): ")
        self.experi_firmwareVerMin_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVerMin_lbl.pack(side=LEFT)

        # Make an entry box for the minor firmware
        # Make a entrybox for testing comments
        self.experi_firmwareVerMin_entry = Entry(
            self.experi_subTop2_2_frame,
            textvariable=self.firmwareVerMinEntry,
            state="readonly"
            )
        self.experi_firmwareVerMin_entry.pack(side=RIGHT)

        # Make a label for the other firmware entry
        self.experi_firmwareVerOther_lbl = Label(self.experi_subTop2_3_frame, text="Bridge Ver (Other): ")
        self.experi_firmwareVerOther_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVerOther_lbl.pack(side=LEFT)

        # Make an entry box for the other firmware
        # Make a entrybox for testing comments
        self.experi_firmwareVerOther_entry = Entry(
            self.experi_subTop2_3_frame,
            textvariable=self.firmwareVerOtherEntry,
            state="readonly"
            )
        self.experi_firmwareVerOther_entry.pack(side=RIGHT)

        # Make a label for the major igloo firmware entry
        self.experi_iglooMajVer_lbl = Label(self.experi_subTop2_4_frame, text="Igloo Ver (Major): ")
        self.experi_iglooMajVer_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMajVer_lbl.pack(side=LEFT)

        # Make an entry box for the major firmware
        self.experi_iglooMajVer_entry = Entry(
            self.experi_subTop2_4_frame,
            textvariable=self.iglooMajVerEntry,
            state="readonly"
            )
        self.experi_iglooMajVer_entry.pack(side=RIGHT)


        # Make a label for the minor igloo firmware entry
        self.experi_iglooMinVer_lbl = Label(self.experi_subTop2_4_5_frame, text="Igloo Ver (Minor): ")
        self.experi_iglooMinVer_lbl.configure(
            background="white",
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMinVer_lbl.pack(side=LEFT)

        # Make an entry box for the minor firmware
        self.experi_iglooMinVer_entry = Entry(
            self.experi_subTop2_4_5_frame,
            textvariable=self.iglooMinVerEntry,
            state="readonly"
            )
        self.experi_iglooMinVer_entry.pack(side=RIGHT)

        # Make a label for the igloo toggle check
        self.iglooToggle_label = Label(self.experi_subTop_2_4_6_frame, text="Igloo Toggle Test: ")
        self.iglooToggle_label.configure(bg="white",padx=button_padx,pady=button_pady)
        self.iglooToggle_label.pack(side=LEFT)

        # Make an entry box for the minor firmware
        self.iglooToggle_entry = Entry(
            self.experi_subTop_2_4_6_frame,
            textvariable=self.iglooToggleEntry,
            state="readonly"
            )
        self.iglooToggle_entry.pack(side=RIGHT)

        # Make a line of hypens
        self.experi_hyphenLine = Label(self.experi_subTop2_6_frame, text="----------------------------------")
        self.experi_hyphenLine.configure(bg="white",padx=button_padx,pady=button_pady)
        self.experi_hyphenLine.pack()

        # Make a button to use Fanout Board
        self.useFanout_bttn = Button(self.experi_subTop2_11_frame, command=self.useFanout,
                          text="Use Fanout Board")
        self.useFanout_bttn.configure(bg="DeepSkyBlue3")
        self.useFanout_bttn.pack()

        # Make a label for the GPIO selection
        self.gpioSelect_label = Label(self.experi_subTop2_7_frame, text="Select GPIO Option: ")
        self.gpioSelect_label.configure(bg="white",padx=button_padx,pady=button_pady)
        self.gpioSelect_label.pack(side=LEFT)

        # Make a option menu for GPIO selection
        self.gpioSelect_box = OptionMenu(self.experi_subTop2_7_frame, self.gpioChoiceVar,
                          "J2 and J18","J3 and J19","J4 and J20","J5 and J21",
                          "J7 and J23","J8 and J24","J9 and J25","J10 and J26")
        self.gpioSelect_box.pack(side=LEFT)
        self.gpioChoiceVar.set("J2 and J18")

        # Make a button to submit GPIO option
        self.gpioSelect_bttn = Button(self.experi_subTop2_8_frame, command=self.gpioBttnPress,
                          text="Submit GPIO Choice")
        self.gpioSelect_bttn.configure(bg="CadetBlue1")
        self.gpioSelect_bttn.pack()

        # Make a button to read the unique ID & firmware from LEFT SIDE (RM 4 and 3)
        self.experi_uniqueID_left_get = Button(self.experi_subTop2_9_frame, text ="Read from Left (J2-J5 and J7-J10: RM 4 and 3)", command=self.getUniqueIDPress_left)
        self.experi_uniqueID_left_get.configure(bg="lemon chiffon")
        self.experi_uniqueID_left_get.pack(side=TOP)

        # Make a button to read the unique ID & firmware from RIGHT SIDE (RM 2 and 1)
        self.experi_uniqueID_right_get = Button(self.experi_subTop2_10_frame, text ="Read from Right (J18-J21 and J23-J26: RM 2 and 1)", command=self.getUniqueIDPress_right)
        self.experi_uniqueID_right_get.configure(bg="CadetBlue1")
        self.experi_uniqueID_right_get.pack(side=TOP)


    #################################
    ###                           ###
    ###  BEGIN MEMBER FUNCTIONS   ###
    ###                           ###
    #################################

    # Test Raspberry Pi Connection
    def pingPi(self):
        print "Pinging Raspberry Pi. Hold please!"
        status = os.system(self.ping)
        if status == 0:
            print "Raspberry Pi Connected: {0}".format(self.pi)
            return True
        else:
            print "Raspberry Pi Connection Error: {0}".format(self.pi)
            return False

    # This function is needed to make the json dumps print properly
    def jdefault(self,o):
        return o.__dict__

##########################################################################################

    # Dumps the results of the tests & inspections to a json file
    def initSubmitBttnPress(self):
        if (self.nameChoiceVar.get() == "Choose Name"):
            self.throwErrorBox()
            return None

        self.initialTest.User = self.nameChoiceVar.get()
        self.initialTest.TestComment = self.infoCommentVar.get()
        self.initialTest.Barcode     = self.barcodeEntry.get()
        self.initialTest.DateRun = str(datetime.now())

        if self.overwriteVar.get() == 1: self.initialTest.Overwrite = True
        if self.overwriteVar.get() == 0: self.initialTest.Overwrite = False

        for i in range(len(self.testPassList)):
            if self.testPassList[i].get() == "Pass":
                self.initialTest.testResults[self.testLabelList[i]] = True
            elif self.testPassList[i].get() == "Fail":
                self.initialTest.testResults[self.testLabelList[i]] = False
            else:
                self.initialTest.testResults[self.testLabelList[i]] = "na"

        self.initSubmitBttn.configure(state=DISABLED)

        fileString = self.barcodeEntry.get()+"_step1_raw.json"

        with open('/home/django/testing_database/uploader/temp_json/'+fileString,'w') as jsonFile:
#       with open(fileString,'w') as jsonFile:     # Uncomment this line for debugging
            json.dump(self.initialTest, jsonFile, default = self.jdefault)


        subprocess.call("/home/django/testing_database/uploader/step12.sh", shell=True)
        print "Preliminary step recorded. Thank you!"

##########################################################################################

    def throwErrorBox(self):
        self.top = Toplevel()
        self.top.title("Name Choice Error")
        self.top.config(height=50, width=360)
        self.top.pack_propagate(False)

        self.msg = Label(self.top, text="Please select a name before continuing.")
        self.msg.pack()

        self.button = Button(self.top, text="Sorry...", command=self.top.destroy)
        self.button.configure(bg="#ffbbbb")
        self.button.pack()

##########################################################################################

    def throwPassAllBox(self):
        self.passBox = Toplevel()
        self.passBox.title("Are you sure?")
        self.passBox.config(height=85, width=360)
        self.passBox.pack_propagate(False)

        self.passMsg = Label(self.passBox, text="Are you sure you want to pass all tests?")
        self.passMsg.pack()

        self.yesButton = Button(self.passBox, text="Yes", command=self.passAllSelected)
        self.yesButton.configure(bg="pale green")
        self.yesButton.pack()

        self.noButton = Button(self.passBox, text="No", command=self.passBox.destroy)
        self.noButton.configure(bg="salmon")
        self.noButton.pack()

    def passAllSelected(self):
        for i in range(len(self.testPassList)):
            self.testPassList[i].set("Pass")
        self.infoValChangeNonevent()
        self.passBox.destroy()

##########################################################################################

    # Dumps the card UID and firmware version to a json file
    def infoSubmitButtonPress(self):
        self.cardInfo.Barcode = self.barcodeEntry.get()
        self.cardInfo.Unique_ID = self.uniqueIDPass
        self.cardInfo.FirmwareMaj = self.firmwareVerEntry.get()
        self.cardInfo.FirmwareMin = self.firmwareVerMinEntry.get()
        self.cardInfo.FirmwareOth = self.firmwareVerOtherEntry.get()
        self.cardInfo.IglooMinVer = self.iglooMinVerEntry.get()
        self.cardInfo.IglooMajVer = self.iglooMajVerEntry.get()
        self.cardInfo.Igloo_FPGA_Control = self.iglooToggleEntry.get()
        self.cardInfo.User = self.nameChoiceVar.get()
        self.cardInfo.DateRun = str(datetime.now())

        fileString = self.barcodeEntry.get()+"_step2_raw.json"

        with open('/home/django/testing_database/uploader/temp_json/'+fileString,'w') as jsonFile:
            json.dump(self.cardInfo, jsonFile, default = self.jdefault)

        subprocess.call("/home/django/testing_database/uploader/step12.sh", shell=True)
        print "Secondary step recorded. Thank you!"

###########################################################################################

    def clearDataBttnPress(self):
        self.initSubmitBttn.configure(state=NORMAL)

        # Clear the data in the GUI displays:
        self.infoCommentVar.set("")
        self.barcodeEntry.set("")
        self.uniqueIDEntry.set("")
        self.tempEntry.set("")
        self.firmwareVerEntry.set("")
        self.firmwareVerMinEntry.set("")
        self.firmwareVerOtherEntry.set("")
        self.iglooMajVerEntry.set("")
        self.iglooMinVerEntry.set("")
        self.iglooToggleEntry.set("")
        self.overwriteVar.set(0)

        # On the gui, change all the tests to "N/A"
        for i in range(len(self.testPassList)):
            self.testPassList[i].set("N/A")

        # Now, clear the stored, behind-the-scenes entries
        self.initialTest.User = self.nameChoiceVar.get()
        self.initialTest.TestComment = self.infoCommentVar.get()
        self.initialTest.Barcode     = self.barcodeEntry.get()
        self.cardInfo.Barcode     = self.barcodeEntry.get()
        self.cardInfo.Unique_ID    = self.uniqueIDEntry.get()
        self.cardInfo.FirmwareMaj = self.firmwareVerEntry.get()
        self.cardInfo.FirmwareMin = self.firmwareVerMinEntry.get()
        self.cardInfo.FirmwareOth = self.firmwareVerOtherEntry.get()
        self.initialTest.DateRun     = str(datetime.now())
        self.cardInfo.User = self.nameChoiceVar.get()
        self.cardInfo.IglooMinVer = self.iglooMinVerEntry.get()
        self.cardInfo.IglooMajVer = self.iglooMajVerEntry.get()
        self.cardInfo.Igloo2_FPGA_Control = self.iglooToggleEntry.get()
        self.initialTest.Overwrite = False

        # Behind the scenes, change all the tests to "Fail"
        for i in range(len(self.testPassList)):
            if self.testPassList[i].get() == "Pass":
                self.initialTest.testResults[self.testLabelList[i-1]] = True
            else:
                self.initialTest.testResults[self.testLabelList[i-1]] = False

        # Change the buttons back to their red state
        self.infoValChangeNonevent()

###########################################################################################

    def reverseBytes(self, message):
        message_list = message.split()
        message_list.reverse()
        s = " "
        return s.join(message_list)

    def serialNum(self, message):
        message_list = message.split()
        message_list = message_list[1:-1]
        s = " "
        return s.join(message_list)

    # Converts decimal messages to Hex messages. Mostly used for UID
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

##############################################################################

    # A function that changes the menu colors depending on if a test passes
    # or fails. This function is for event cases (IE, changing a single menu value)
    def infoValChange(self,event):
        for i in range(len(self.testPassInfo)):
            if (self.testPassList[i].get() == "Fail"):
                self.testPassInfo[i].configure(bg="#ff5555")
            elif (self.testPassList[i].get() == "Pass"):
                self.testPassInfo[i].configure(bg="#70ff70")
            else:
                self.testPassInfo[i].configure(bg="#CCDDFF")

    # Duplicate of above function, but for non-event cases (IE hitting the "Clear" button)
    def infoValChangeNonevent(self):
        for i in range(len(self.testPassInfo)):
                         if (self.testPassList[i].get() == "Fail"):
                                 self.testPassInfo[i].configure(bg="#ff5555")
                         elif (self.testPassList[i].get() == "Pass"):
                                 self.testPassInfo[i].configure(bg="#70ff70")
                         else:
                                 self.testPassInfo[i].configure(bg="#CCDDFF")

#############################################################################

    def useFanout(self):
        self.fanoutStatus = (self.fanoutStatus + 1) % 2
        if self.fanoutStatus == 0:
            print "Fanout baord option disabled."
            self.useFanout_bttn.configure(bg="#ff3333")
        if self.fanoutStatus == 1:
            print "Fanout board option enabled."
            self.useFanout_bttn.configure(bg="#33ff33")

    # Opens the proper GPIO slot. Used for programming cards.
    def gpioBttnPress(self):
        # Defines GPIO values for Full Backplane.
        jSlotDict = {"J2 and J18" : 0x29, "J3 and J19" : 0x89, "J4 and J20" : 0xA9,
                    "J5 and J21" : 0x49, "J7 and J23" : 0x2A, "J8 and J24" : 0x8A,
                    "J9 and J25" : 0xAA, "J10 and J26" : 0x4A}

        dictStringToInts = {"J2 and J18" : [2, 18], "J3 and J19" : [3, 19],
                            "J4 and J20" : [4, 20], "J5 and J21" : [5, 21],
                            "J7 and J23" : [7, 23], "J8 and J24" : [8, 24],
                            "J9 and J25" : [9, 25], "J10 and J26" : [10, 26]}

        # define gpioVal, jslots and gpioSelected based on selection
        gpioVal = jSlotDict[self.gpioChoiceVar.get()]
        self.jslots = dictStringToInts[self.gpioChoiceVar.get()]
        self.gpioSelected = True

        # iterate through fanout board channels
        for ch in self.channels:
            self.myBus.write(self.fanout, [ch]) # write to fanout the value ch
            self.myBus.write(self.ccm, [0x08]) # PCA9538 is bit 3 on ngccm mux
            #power on and reset
                #register 3 is control reg for i/o modes
            self.myBus.write(self.gpio,[0x03,0x00]) # sets all GPIO pins to 'output' mode
            self.myBus.write(self.gpio,[0x01,0x08])
            self.myBus.write(self.gpio,[0x01,0x18]) # GPIO reset is 10
            self.myBus.write(self.gpio,[0x01,0x08])
        
            #jtag selectors finnagling for slot 26
            self.myBus.write(self.gpio,[0x01,gpioVal])
            self.myBus.read(self.gpio,0x01)
        
            batch = self.myBus.sendBatch()

            #print "GPIO Batch: {0}".format(batch)
            
            if (batch[-1] == "1 0"):
                print "GPIO I2C Error: {0}".format(self.gpioChoiceVar.get())
                self.gpioSelect_bttn.configure(bg="#ff3333")
            elif (batch[-1] == "0 "+str(gpioVal)):
                print 'GPIO selected: {0}'.format(self.gpioChoiceVar.get())
                self.gpioSelect_bttn.configure(bg="#33ff33")
            else:
                print 'GPIO Choice Error... unexpected communication error!'

##################################################################################

    def getUniqueIDPress_left(self):
        self.readFromLeft = True
        if self.gpioSelected:
            self.getUniqueIDPress()
        else:
            print 'GPIO not selected. Please select GPIO.'

##################################################################################

    def getUniqueIDPress_right(self):
        self.readFromLeft = False
        if self.gpioSelected:
            self.getUniqueIDPress()
        else:
            print 'GPIO not selected. Please select GPIO.'

##################################################################################

    def getUniqueIDPress(self):

        bridgeDict = {  2 : 0x19, 3 : 0x1A, 4 : 0x1B, 5 : 0x1C,
                        7 : 0x19, 8 : 0x1A, 9: 0x1B, 10: 0x1C,
                       18 : 0x19, 19 : 0x1A, 20: 0x1B, 21 : 0x1C,
                       23 : 0x19, 24 : 0x1A, 25: 0x1B, 26 : 0x1C}

        if self.readFromLeft:
            self.jslot = self.jslots[0]
            self.slot = bridgeDict[self.jslot]
            if self.fanoutStatus:
                self.myBus.write(self.fanout, [self.channels[1]])
            if self.jslot in [2,3,4,5]:
                self.myBus.write(self.ccm, [0x02^0x8])
            if self.jslot in [7,8,9,10]:
                self.myBus.write(self.ccm, [0x20^0x8])
        else:
            self.jslot = self.jslots[1]
            self.slot = bridgeDict[self.jslot]
            if self.fanoutStatus:
                self.myBus.write(self.fanout, [self.channels[0]])
            if self.jslot in [18,19,20,21]:
                self.myBus.write(self.ccm,[0x10^0x8])
            if self.jslot in [23,24,25,26]:
                self.myBus.write(self.ccm,[0x01^0x8])

        self.myBus.sendBatch()

        # slot = 0x19
        # Use self.slot, which is defined through gpioChoiceVar
        print 'Selected Slot: J'+str(self.jslot)

        # Getting unique ID
        # 0x05000000ea9c8b7000   <- From main gui
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.slot,[0x11,0x04,0,0,0])
        self.myBus.write(0x50,[0x00])
        self.myBus.read(0x50, 8)
        raw_bus = self.myBus.sendBatch()
        if raw_bus[-1][0] != '0':
            print 'Read Unique ID I2C Error!'
            return False
        cooked_bus = self.reverseBytes(raw_bus[-1])
        #cooked_bus = self.serialNum(cooked_bus)
        self.uniqueIDEntry.set(self.toHex(cooked_bus))
        self.uniqueIDPass = self.uniqueIDEntry.get()
        self.uniqueIDEntry.set("0x"+self.uniqueIDPass[4:(len(self.uniqueIDPass)-4)])
        print 'Full Unique ID: '+str(self.uniqueIDPass[:-2])

        # Getting bridge firmware
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.slot,[0x04])
        self.myBus.read(self.slot, 4)
        raw_data = self.myBus.sendBatch()[-1]
        med_rare_data = raw_data[2:]
        cooked_data = self.reverseBytes(med_rare_data)
        data_well_done = self.toHex(cooked_data)    # my apologies for the cooking references
        data_well_done = data_well_done[2:]
        print 'Bridge FPGA Firmware Version = 0x'+str(data_well_done)
        self.firmwareVerEntry.set("0x"+data_well_done[0:2])    #these are the worst (best?) variable names ever
        self.firmwareVerMinEntry.set("0x"+data_well_done[2:4])
        self.firmwareVerOtherEntry.set("0x"+data_well_done[4:8])

        # Getting temperature
        self.tempEntry.set(str(round(temp.readManyTemps(self.myBus, self.slot, 10, "Temperature", "nohold"),4)))

        # Getting IGLOO firmware info
        majorIglooVer = it.readIgloo(self.myBus, self.slot, 0x00)
        minorIglooVer = it.readIgloo(self.myBus, self.slot, 0x01)
        # Parse IGLOO firmware info
        majorIglooVer = self.toHex(self.reverseBytes(majorIglooVer))
        minorIglooVer = self.toHex(self.reverseBytes(minorIglooVer))
        # Trim the entries of their error codes
        majorIglooVer = majorIglooVer[0:-2]
        minorIglooVer = minorIglooVer[0:-2]
        # Display igloo FW info on gui
        self.iglooMajVerEntry.set(majorIglooVer)
        self.iglooMinVerEntry.set(minorIglooVer)
        print 'Igloo2 FPGA Major Firmware Version = '+str(majorIglooVer)
        print 'Igloo2 FPGA Minor Firmware Version = '+str(minorIglooVer)

        # Verify that the Igloo can be power toggled
        self.iglooToggleEntry.set(str(self.checkIglooToggle()))

##############################################################################################
#   Functions to check igloo toggle
##############################################################################################

    def checkIglooToggle(self):
        control_address = 0x22
        message = self.readBridge(control_address,4)

        ones_address = 0x02
        all_ones = '255 255 255 255'

        retval = False

        self.myBus.write(0x00,[0x06])
        self.myBus.sendBatch()

        register = self.readIgloo(ones_address, 4)
        if register != all_ones:
            retval = False

        # Turn Igloo Off
        self.toggleIgloo()
        register = self.detectIglooError(ones_address, 4)
        if register != '0':
            retval = True

        # Turn Igloo On
        self.toggleIgloo()
        register = self.readIgloo(ones_address, 4)
        if register != all_ones:
            retval = False

        if retval:
            print 'Toggle Igloo Power Success!'
        else:
            # confirm power on and card in slot J2, J7, J18, J23 to toggle dc-dc voltage
            print 'Toggle Igloo Power Fail!'
            print '\nPlease confirm that the power source is on.'
            print 'Please confirm that the card is in the selected slot.'
        return retval

    def toggleIgloo(self):
        iglooControl = 0x22
        message = self.readBridge(iglooControl,4)
        value = self.getValue(message)
        value = value ^ 0x400 # toggle igloo power!
        messageList = self.getMessageList(value,4)
        self.writeBridge(iglooControl,messageList)
        return self.readBridge(iglooControl,4)

    def writeBridge(self, regAddress,messageList):
        self.myBus.write(self.address, [regAddress]+messageList)
        return self.myBus.sendBatch()

    def readBridge(self, regAddress, num_bytes):
        self.myBus.write(0x00,[0x06])
        self.myBus.sendBatch()
        self.myBus.write(self.address,[regAddress])
        self.myBus.read(self.address, num_bytes)
        message = self.myBus.sendBatch()[-1]
        if message[0] != '0':
            print 'Bridge i2c error detected'
        return self.reverseBytes(message[2:])

    def readIgloo(self, regAddress, num_bytes):
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.address,[0x11,0x03,0,0,0])
        self.myBus.write(0x09,[regAddress])
        self.myBus.read(0x09, num_bytes)
        message = self.myBus.sendBatch()[-1]
        if message[0] != '0':
            print 'Igloo i2c error detected in readIgloo'
        return self.reverseBytes(message[2:])

    def detectIglooError(self, regAddress, num_bytes):
        self.myBus.write(0x00,[0x06])
        self.myBus.write(self.address,[0x11,0x03,0,0,0])
        self.myBus.write(0x09,[regAddress])
        self.myBus.read(0x09, num_bytes)
        message = self.myBus.sendBatch()[-1]
        return message[0]

    def getValue(self, message):
        hex_message = self.toHex(message)[2:]
        return int(hex_message,16)

    def getMessageList(self, value, num_bytes):
        hex_message = hex(value)[2:]
        length = len(hex_message)
        zeros = "".join(list('0' for i in xrange(8-length)))
        hex_message = zeros + hex_message
        mList = list(int(hex_message[a:a+2],16) for a in xrange(0,2*num_bytes,2))
        mList.reverse()
        return mList

###########################################################################################

root = Tk()
myapp = makeGui(root)
root.mainloop()
