# User-Interface.py
#
# This is the main Graphical User Interface for for Teststand 1. 
# A server runs on a RaspberryPi, which connects to the Fanout.
# The Fanout connects to the ngCCM Emulator.
# QIE cards can be inserted into any QIE card backplane slot.
#
# Developed with the help of many people
# For Baylor University, Summer 2016 (HE) and Summer 2018 (HB).

from Tkinter import *
from datetime import datetime
from initialClass import initialTests
from cardInfoClass import cardInformation
from functools import partial
from Tools import Tools
from checksumClass import Checksum
import temp
import json
import client
import subprocess
import argparse
import time

#toggles between lists and three-state buttons for Pass/Fail switches
listbuttons=0

#initalizes the global hotkey lockout variable. Setting this to '2' will disable hotkeys
lockout=0

class makeGui(Tools):
    def __init__(self, parent, color_themes, color_theme="bright"):
        # color themes
        self.color_themes = color_themes
        self.color_theme = color_theme
        # Default color_theme is "bright"
        if self.color_theme not in self.color_themes:
            self.color_theme = "bright"
        # set color theme
        self.setColorTheme()

        # full base path for database
        self.databasePath = "/home/django/testing_database_hb"
        # Create a webBus instance
        #self.myBus = client.webBus("192.168.1.41",0)
        self.myBus = client.webBus("192.168.1.26",0)

        # Create a permanent I2C address of QCard (slot 1)
        self.card_i2c_address = 0x19
        
        # Permanent I2C address of Igloo FPGA
        self.iglooAddress = 0x09
        
        # Standard help message for I2C_ERROR
        self.I2C_ERROR_HELP = "Please confirm that the card is in the selected slot.\nPlease confirm that the power source is on."

        # Create an instance of initialTests
        self.initialTest = initialTests()

        # Create an instance of cardInformation
        self.cardInfo = cardInformation()

        # Read info from left side?
        self.readFromList = True

        # Make an empty list that will eventually contain all of
        # the active card slots
        self.outSlotNumbers = []

        # Name the parent. This is mostly for bookkeeping purposes
        # and doesn't really get used too much... as in not at all!
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
        self.iglooMajVerEntryT     =  StringVar()
        self.iglooMajVerEntryB     =  StringVar()
        self.iglooMinVerEntryT     =  StringVar()
        self.iglooMinVerEntryB     =  StringVar()
        self.check                 =  StringVar()
        self.overwriteVar          =  IntVar()
        self.iglooArmed            =  IntVar()

        # Place an all-encompassing frame in the parent window. All of the following
        # frames will be placed here (topMost_frame) and not in the parent window.
        self.topMost_frame = Frame(parent)
        self.topMost_frame.pack()
        self.topMost_frame.configure(bg=self.backc)
        #----- constants for controlling layout
        button_width = 6

        button_padx = "2m"
        button_pady = "1m"

        frame_padx = "3m"
        frame_pady = "2m"
        frame_ipadx = "3m"
        frame_ipady = "1m"
        #---------- end layout constants ------
        # Creates hotkey bindings for Pass/Fail buttons
        if (not listbuttons) and (lockout is not 2):
            hotkeys = ['1','2','3','4','5','q','w','e','r','t','a','s','d','f','g','z','x','o','p']
            for i in range(len(hotkeys)):
                parent.bind(hotkeys[i], partial(self.togglepstate,i))

        def lockon (self,event=None):
            global lockout
            lockout=1
        def lockoff (self,event=None):
            global lockout
            lockout=0
                                                                                              

        ##########################################
        ###                                    ###
        ###     BEGIN MAKING SUB-FRAMES        ###
        ###                                    ###
        ##########################################

        # Make and pack a sub-frame within topMost_frame that will contain
        # all of the controls for non-hardware related test information
        # (i.e. name of tester)
        self.info_frame = Frame(
            self.topMost_frame,
            borderwidth=5, relief=RIDGE,
            height=50,
            background=self.topc,
            )
        self.info_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make a top half-frame
        self.topHalf_frame = Frame(self.topMost_frame)
        self.topHalf_frame.configure(bg=self.backc)
        self.topHalf_frame.pack(side=TOP)

        # Make a frame for containing an experiment diagram
        self.experiment_frame = Frame(
            self.topHalf_frame,
            borderwidth=5, relief=RIDGE,
            height=580, width=300,
            background=self.rightc
            )
        self.experiment_frame.pack_propagate=(False)
        self.experiment_frame.pack(
            side=RIGHT,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make a label for the entire right frame
        self.experi_rightFrame = Frame(
            self.topHalf_frame,
            borderwidth=5, relief=RIDGE,
            height=580, width=300,
            background=self.midc
            )
        self.experi_rightFrame.pack_propagatte=(False)
        self.experi_rightFrame.pack(
            side=LEFT,
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

        # Make and pack a text label for name selector
        self.info_Label = Label(self.info_frame, text="Testing Information/Parameters")
        self.info_Label.configure(
            padx=button_padx,
            pady=button_pady,
            background=self.topc,
            foreground=self.fontc
            )
        self.info_Label.pack(side=TOP)

        # Make a sub-sub-frame within the frame to hold another label and a dropdown box
        self.info_subTop_frame = Frame(self.info_frame,background=self.topc)
        self.info_subTop_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make a sub-sub-frame within the frame to hold comment box
        self.info_subBot_frame = Frame(self.info_frame,background=self.topc)
        self.info_subBot_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make a label for the name drop-down:
        self.info_nameLabel = Label(self.info_subTop_frame, text="Tester Name: ")
        self.info_nameLabel.configure(
            padx=button_padx,
            pady=button_pady,
            background=self.topc,
            foreground=self.fontc
            )
        self.info_nameLabel.pack(side=LEFT)

        # Make and pack a listbox to pick which QIE card to talk to:
        self.info_nameBox = OptionMenu(self.info_subTop_frame, self.nameChoiceVar, "Bryan Caraway", "Grace Cummings", "Zach Eckert", "Loriza Hasa", "Frank Jensen", "Kamal Lamichhane", "Nesta Lenhert", "Chris Madrid", "Brooks McMaster", "Danny \"HF\" Noonan", "Joe Pastika", "Ian McAlister", "Mark Saunders", "Sezen Sekmen", "Zach Shelton", "Caleb Smith", "Nadja Strobbe")
        self.info_nameBox.pack(side=LEFT)
        self.info_nameBox.configure(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
        self.info_nameBox["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
        self.nameChoiceVar.set("Choose Name") # initializes the OptionMenu
        # Make a label for the name drop-down:
        self.info_commentLabel = Label(self.info_subBot_frame, text="User Testing Comments: ")
        self.info_commentLabel.configure(
            padx=button_padx,
            pady=button_pady,
            background=self.topc,
            foreground=self.fontc
            )
        self.info_commentLabel.pack(side=LEFT)

        # Make a entrybox for testing comments
        self.info_commentBox = Entry(
            self.info_subBot_frame,
            textvariable=self.infoCommentVar
            )
        self.info_commentBox.pack(side=LEFT)
        self.info_commentBox.configure(bg=self.topc,fg=self.fontc)
        self.info_commentBox.bind("<FocusIn>",lockon)
        self.info_commentBox.bind("<FocusOut>",lockoff)
        
        ######################################
        #####                            #####
        #####  Experiment Setup Frames   #####
        #####                            #####
        ######################################

        self.testLabelList = ["BPL-GND","1.2-GND","1.5-GND","2.5-GND",  
                              "3.3-GND","5.0-GND","1.2-1.5","1.2-2.5","1.2-3.3",
                              "1.2-AVCC","1.5-2.5","1.5-3.3","1.5-AVCC", "2.5-3.3",
                              "2.5-AVCC", "3.3-AVCC", "Vis", "SuplCur","Program"]
        

        # Make a label for the entire left frame
        self.experi_subFrame_lbl = Label(self.experiment_frame,text="QIE Card Setup & Parameters")
        self.experi_subFrame_lbl.configure(
            padx=button_padx,
            pady=button_pady,
            background=self.rightc,
            foreground=self.fontc
            )
        self.experi_subFrame_lbl.pack(side=TOP)

        # Make top 2_7 subframe
        self.experi_subTop2_7_frame = Frame(self.experiment_frame, bg=self.rightc)
        self.experi_subTop2_7_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_8 subframe
        self.experi_subTop2_8_frame = Frame(self.experiment_frame, bg=self.rightc)
        self.experi_subTop2_8_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        # Make top 2_6 subframe
        self.experi_subTop2_6_frame = Frame(self.experiment_frame, bg=self.rightc)
        self.experi_subTop2_6_frame.pack(
            side=TOP,
            ipadx=frame_ipadx, padx=frame_padx,
            ipady=frame_ipady, pady=frame_pady,
            )

        self.experi_subTop2_6_fText = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_6_fText.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            )

        # Make top 2 subframe
        self.experi_subTop2_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_0 subframe
        self.experi_subTop2_0_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_0_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_1 subframe
        self.experi_subTop2_1_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_1_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_2 subframe
        self.experi_subTop2_2_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_2_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_3 subframe
        self.experi_subTop2_3_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_3_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4 subframe
        self.experi_subTop2_4_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_4_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4_5 subframe
        self.experi_subTop2_4_5_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_4_5_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 2_4_6 subframe
        self.experi_subTop_2_4_6_frame = Frame(self.experiment_frame, background=self.rightc)
        self.experi_subTop_2_4_6_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            pady=frame_pady
            )


        # Make top 2_5 subframe
        self.experi_subTop2_5_frame = Frame(self.experiment_frame,background=self.rightc)
        self.experi_subTop2_5_frame.pack(
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

        # Make a buffer frame
        self.experi_subTopBuffer_frame = Frame(self.experi_rightFrame,bg=self.midc)
        self.experi_subTopBuffer_frame.pack(
            side=TOP,
            ipady=frame_ipady,
            ipadx=frame_ipadx,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make an "inspections and tests" label
        self.experi_inspections_label = Label(self.experi_subTopBuffer_frame,
                        text="Inspections and Tests",fg=self.fontc)
        self.experi_inspections_label.configure(bg=self.midc)
        self.experi_inspections_label.pack()

        # Make a subframe for the barcode box
        self.experi_barcode_frame = Frame(self.experi_rightFrame, bg=self.midc)
        self.experi_barcode_frame.pack(
            side=TOP,
            ipady=frame_ipady,
            ipadx=frame_ipadx,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make a label for the Barcode entry
        self.experi_barcode_lbl = Label(self.experi_barcode_frame, text="Barcode: ")
        self.experi_barcode_lbl.configure(
            background=self.midc,
            padx=button_padx,
            pady=button_pady,
            foreground=self.fontc
            )
        self.experi_barcode_lbl.pack(side=LEFT)

        # Make an entry box for the barcode
        # Make a entrybox for testing comments
        self.experi_barcode_entry = Entry(
            self.experi_barcode_frame,
            textvariable=self.barcodeEntry
            )
        self.experi_barcode_entry.pack(side=RIGHT)
        self.experi_barcode_entry.configure(bg=self.midc,fg=self.fontc,width=7)
        self.experi_barcode_entry.bind("<FocusIn>",lockon)
        self.experi_barcode_entry.bind("<FocusOut>",lockoff)

        # Make another buffer frame
        self.experi_subTopBuffer2_frame = Frame(self.experi_rightFrame,bg=self.midc)
        self.experi_subTopBuffer2_frame.pack(
            side=TOP,
            ipady=frame_ipady,
            ipadx=frame_ipadx,
            padx=frame_padx,
            pady=frame_pady
            )

        # Make top 3 subframe
        self.experi_subTop3_frame = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop3_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            )

        # Make top 3 subframe for text
        self.experi_subTop3_fText = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop3_fText.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            padx=frame_padx,
            )

        # Make top 4 subframe
        self.experi_subTop4_frame = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop4_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 4 subframe for text
        self.experi_subTop4_fText = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop4_fText.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 5 subframe
        self.experi_subTop5_frame = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop5_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 5 subframe for text
        self.experi_subTop5_fText = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop5_fText.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 6 subframe
        self.experi_subTop6_frame = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop6_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 6 subframe for text
        self.experi_subTop6_fText = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop6_fText.pack(
            side=TOP,
            ipadx=frame_ipadx,
            padx=frame_padx,
            )

        # Make top 7 subframe
        self.experi_subTop7_frame = Frame(self.experi_rightFrame,background=self.midc)
        self.experi_subTop7_frame.pack(
            side=TOP,
            ipadx=frame_ipadx,
            ipady=frame_ipady,
            pady=frame_pady,
            padx=frame_padx,
            )


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
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady
            )
        self.experi_uniqueID_lbl.pack(side=LEFT)

        # Make an entry box for the UniqueID
        # Make a entrybox for testing comments
        self.experi_uniqueID_entry = Entry(
            self.experi_subTop2_frame,
            textvariable=self.uniqueIDEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=21
            )
        self.experi_uniqueID_entry.pack(side=LEFT)

        self.experi_uniqueID_lbl = Label(self.experi_subTop2_frame, text="Checksum: ")
        self.experi_uniqueID_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady
            )
        self.experi_uniqueID_lbl.pack(side=LEFT)
       
        # Make an entry box for the Checksum
        # Make a entrybox for results
        self.experi_uniqueID_entry = Entry(
            self.experi_subTop2_frame,
            textvariable=self.check,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=6
            )
        self.experi_uniqueID_entry.pack(side=LEFT)

        # Make a label for the temperature entry
        self.experi_temperature_lbl = Label(self.experi_subTop2_0_frame, text="Temperature: ")
        self.experi_temperature_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_temperature_lbl.pack(side=LEFT)

        # Make an entry box for the temperature
        # Make a entrybox for testing comments
        self.experi_temperature_entry = Entry(
            self.experi_subTop2_0_frame,
            textvariable=self.tempEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc
            )
        self.experi_temperature_entry.configure(bg=self.rightc,fg=self.fontc)
        self.experi_temperature_entry.pack(side=RIGHT)

        # Make a label for the main firmware ver entry
        self.experi_firmwareVer_lbl = Label(self.experi_subTop2_1_frame, text="Bridge Ver (Major): ")
        self.experi_firmwareVer_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVer_lbl.pack(side=LEFT)

        # Make an entry box for the main firmware ver
        # Make a entrybox for testing comments
        self.experi_firmwareVer_entry = Entry(
            self.experi_subTop2_1_frame,
            textvariable=self.firmwareVerEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc
            )
        self.experi_firmwareVer_entry.pack(side=RIGHT)

        # Make a label for the minor firmware ver entry
        self.experi_firmwareVerMin_lbl = Label(self.experi_subTop2_2_frame, text="Bridge Ver (Minor): ")
        self.experi_firmwareVerMin_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVerMin_lbl.pack(side=LEFT)

        # Make an entry box for the minor firmware
        # Make a entrybox for testing comments
        self.experi_firmwareVerMin_entry = Entry(
            self.experi_subTop2_2_frame,
            textvariable=self.firmwareVerMinEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc
            )
        self.experi_firmwareVerMin_entry.pack(side=RIGHT)

        # Make a label for the other firmware entry
        self.experi_firmwareVerOther_lbl = Label(self.experi_subTop2_3_frame, text="Bridge Ver (Other): ")
        self.experi_firmwareVerOther_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_firmwareVerOther_lbl.pack(side=LEFT)

        # Make an entry box for the other firmware
        # Make a entrybox for testing comments
        self.experi_firmwareVerOther_entry = Entry(
            self.experi_subTop2_3_frame,
            textvariable=self.firmwareVerOtherEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc
            )
        self.experi_firmwareVerOther_entry.pack(side=RIGHT)

        # Make a label for the major top igloo firmware entry
        self.experi_iglooMajVerT_lbl = Label(self.experi_subTop2_4_frame, text="Top Igloo Ver (Major): ")
        self.experi_iglooMajVerT_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMajVerT_lbl.pack(side=LEFT)

        # Make an entry box for the major top firmware
        self.experi_iglooMajVerT_entry = Entry(
            self.experi_subTop2_4_frame,
            textvariable=self.iglooMajVerEntryT,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=4
            )
        self.experi_iglooMajVerT_entry.pack(side=LEFT)

        # Make an entry box for the minor top# firmware
        self.experi_iglooMinVerT_entry = Entry(
            self.experi_subTop2_4_frame,
            textvariable=self.iglooMinVerEntryT,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=4
            )
        self.experi_iglooMinVerT_entry.pack(side=RIGHT)

        # Make a label for the minor top igloo firmware entry
        self.experi_iglooMinVerT_lbl = Label(self.experi_subTop2_4_frame, text="(Minor): ")
        self.experi_iglooMinVerT_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMinVerT_lbl.pack(side=RIGHT)


        # Make a label for the major bottom igloo firmware entry
        self.experi_iglooMajVerB_lbl = Label(self.experi_subTop2_4_5_frame, text="Bottom Igloo Ver (Major): ")
        self.experi_iglooMajVerB_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMajVerB_lbl.pack(side=LEFT)

        # Make an entry box for the major bottom# firmware
        self.experi_iglooMajVerB_entry = Entry(
            self.experi_subTop2_4_5_frame,
            textvariable=self.iglooMajVerEntryB,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=4
            )
        self.experi_iglooMajVerB_entry.pack(side=LEFT)

        # Make an entry box for the minor bottom firmware
        self.experi_iglooMinVerB_entry = Entry(
            self.experi_subTop2_4_5_frame,
            textvariable=self.iglooMinVerEntryB,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=4
            )
        self.experi_iglooMinVerB_entry.pack(side=RIGHT)
          

        # Make a label for the minor bottom igloo firmware entry
        self.experi_iglooMinVerB_lbl = Label(self.experi_subTop2_4_5_frame, text="(Minor): ")
        self.experi_iglooMinVerB_lbl.configure(
            background=self.rightc,
            foreground=self.fontc,
            padx=button_padx,
            pady=button_pady,
            )
        self.experi_iglooMinVerB_lbl.pack(side=RIGHT)
 
        # Make a label for the igloo toggle check
        self.iglooToggle_label = Label(self.experi_subTop_2_4_6_frame, text="Igloo Toggle Test: ")
        self.iglooToggle_label.configure(bg=self.rightc,fg=self.fontc,padx=button_padx,pady=button_pady)
        self.iglooToggle_label.pack(side=LEFT)

        # Make an entry box for the minor firmware
        self.iglooToggle_entry = Entry(
            self.experi_subTop_2_4_6_frame,
            textvariable=self.iglooToggleEntry,
            state="readonly",
            readonlybackground=self.rightc,
            foreground=self.fontc,
            width=6
            )
        self.iglooToggle_entry.pack(side=RIGHT)


        # Make a button to read the unique ID & firmware LEFT SIDE
        self.experi_uniqueID_left_get = Button(self.experi_subTop2_5_frame, text ="Get Unique ID & Firmware Ver. from Left", command=self.getUniqueIDPress_left)
        self.experi_uniqueID_left_get.configure(bg=self.buttonsc[0],fg=self.fontc,activebackground=self.dimbuttonsc[0],activeforeground=self.fontc)
        self.experi_uniqueID_left_get.pack(side=TOP)

        # Make a button to read the unique ID & firmware RIGHT SIDE
        self.experi_uniqueID_right_get = Button(self.experi_subTop2_5_frame, text ="Get Unique ID & Firmware Ver. from Right", command=self.getUniqueIDPress_right)
        self.experi_uniqueID_right_get.configure(bg=self.buttonsc[1],fg=self.fontc,activebackground=self.dimbuttonsc[1],activeforeground=self.fontc)
        self.experi_uniqueID_right_get.pack(side=TOP)

        # Make a button to submit the unique ID & firmware
        self.experi_uniqueID_give = Button(self.experi_subTop2_5_frame, text ="Upload Unique ID & Firmware Ver.", command=self.infoSubmitButtonPress)
        self.experi_uniqueID_give.configure(bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
        self.experi_uniqueID_give.pack(side=TOP)

        # Make a line of hypens
        #self.experi_hyphenLine = Label(self.experi_subTop2_6_frame, text="----------------------------------")
        #self.experi_hyphenLine.configure(bg=self.rightc,fg=self.fontc,padx=button_padx,pady=button_pady)
        #self.experi_hyphenLine.pack()



        # Make a label for the GPIO selection
        self.gpioSelect_label = Label(self.experi_subTop2_7_frame, text="Select GPIO Option: ")
        self.gpioSelect_label.configure(bg=self.rightc,fg=self.fontc,padx=button_padx,pady=button_pady)
        self.gpioSelect_label.pack(side=LEFT)

        # Make a option menu for GPIO selection
        self.gpioSelect_box = OptionMenu(self.experi_subTop2_7_frame, self.gpioChoiceVar,
                          "J2 and J21","J3 and J20","J4 and J19","J5 and J18",
                          "J7 and J26","J8 and J25","J9 and J24","J10 and J23", command=self.gpioBttnPress)
        self.gpioSelect_box.configure(bg=self.rightc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
        self.gpioSelect_box.pack(side=LEFT)
        self.gpioSelect_box["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
        self.gpioChoiceVar.set("J2 and J21")

        # Make a checkbox to overwrite/not overwrite pre-existing data
        self.overwriteBox = Checkbutton(self.experi_subTop2_7_frame, text="Igloo Arming Switch", variable=self.iglooArmed)
        self.overwriteBox.configure(bg=self.buttonsc[5],fg=self.fontc,activebackground=self.dimbuttonsc[5],activeforeground=self.fontc,selectcolor=self.checkc)
        self.overwriteBox.pack(side=LEFT,
                       padx = button_padx,
                       pady = button_pady,
                       ipady = button_pady,
                       ipadx = button_padx)

        # Make a button to submit GPIO option
        self.gpioSelect_bttn = Button(self.experi_subTop2_8_frame, command=self.gpioBttnPress,
                          text="Submit GPIO Choice")
        self.gpioSelect_bttn.configure(bg=self.buttonsc[0],fg=self.fontc,activebackground=self.dimbuttonsc[0],activeforeground=self.fontc)
        self.gpioSelect_bttn.pack()

        ################################
        ###                          ###
        ###     Visual Tests         ###
        ###                          ###
        ################################

        self.testDescDict = {"BPL-GND" : "  Bkpln to GND", "1.2-GND" : "1.2V to GND", "1.5-GND" : "1.5V to GND",
                     "2.5-GND" : "2.5V to GND", "3.3-GND" : "3.3V to GND  ", "5.0-GND" : "  5.0V to GND",
                     "1.2-1.5" : "1.2V to 1.5V", "1.2-2.5" : "1.2V to 2.5V", "1.2-3.3" : "1.2V to 3.3V", "1.2-AVCC" : "1.2V to AVCC  ",
                     "1.5-2.5" : "  1.5V to 2.5V", "1.5-3.3" : "1.5V to 3.3V", "1.5-AVCC" : "1.5V to AVCC", "2.5-3.3" : "2.5V to 3.3V",
                     "2.5-AVCC" : "2.5V to AVCC  ", "3.3-AVCC" : "  3.3V to AVCC", "Vis" : "Visual Inspec.  ", "SuplCur" : "  Supply Current","Program" : "Bridge Programming OK  "}


#       self.testPassList = [StringVar() for i in range(0,19)]

#       self.testLabelList = ["Res_1","Res_2","Res_3","Res_4",
#                         "Res_5","Res_6","Res_7","Res_8",
#                     "Res_9","Res_10","Res_11", "Res_12",
#                     "Res_13", "Res_14", "Res_15", "SuplCur", "Vis", "Program",
#                     "Res_16"]

        self.testPassInfo = []

        for i in range(0,5):
            if (listbuttons):
                self.testPassInfo.append(OptionMenu(self.experi_subTop3_frame,self.testPassList[i],"Fail","Pass","N/A",command=self.infoValChange))
                self.testPassInfo[i]["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
            else: 
                self.testPassInfo.append(Button(self.experi_subTop3_frame,text="N/A",command=partial(self.togglepstate,i)))
            self.testPassInfo[i].configure(width=11,bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            self.testPassInfo[i].pack(side=LEFT)
            self.testPassList[i].set("N/A")

            self.testPassLabel=Label(self.experi_subTop3_fText, text=self.testDescDict[self.testLabelList[i]]+"\n",bg=self.midc,fg=self.fontc)
            self.testPassLabel.configure(width=15)
            self.testPassLabel.pack(side=LEFT)

        for i in range(5,10):
            if (listbuttons):
                self.testPassInfo.append(OptionMenu(self.experi_subTop4_frame,self.testPassList[i],"Fail","Pass","N/A",command=self.infoValChange))
                self.testPassInfo[i]["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
            else:
                self.testPassInfo.append(Button(self.experi_subTop4_frame,text="N/A",command=partial(self.togglepstate,i)))
            self.testPassInfo[i].configure(width=11, bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            self.testPassInfo[i].pack(side=LEFT)
            self.testPassList[i].set("N/A")
    
            self.testPassLabel=Label(self.experi_subTop4_fText, text=self.testDescDict[self.testLabelList[i]]+"\n", bg=self.midc,fg=self.fontc)
            self.testPassLabel.configure(width=15)
            self.testPassLabel.pack(side=LEFT)

        for i in range(10,15):
            if (listbuttons):
                self.testPassInfo.append(OptionMenu(self.experi_subTop5_frame,self.testPassList[i],"Fail","Pass","N/A",command=self.infoValChange))
                self.testPassInfo[i]["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
            else:
                self.testPassInfo.append(Button(self.experi_subTop5_frame,text="N/A",command=partial(self.togglepstate,i)))
            self.testPassInfo[i].configure(width=11,bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            self.testPassInfo[i].pack(side=LEFT)
            self.testPassList[i].set("N/A")

            self.testPassLabel=Label(self.experi_subTop5_fText, text=self.testDescDict[self.testLabelList[i]]+"\n", bg=self.midc,fg=self.fontc)
            self.testPassLabel.configure(width=15)
            self.testPassLabel.pack(side=LEFT)

        for i in range(15,17):
            if (listbuttons):
                self.testPassInfo.append(OptionMenu(self.experi_subTop6_frame,self.testPassList[i],"Fail","Pass","N/A",command=self.infoValChange))
                self.testPassInfo[i]["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
            else: 
                self.testPassInfo.append(Button(self.experi_subTop6_frame,text="N/A",command=partial(self.togglepstate,i)))
            self.testPassInfo[i].configure(width=15,bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            self.testPassInfo[i].pack(side=LEFT)
            self.testPassList[i].set("N/A")

            self.testPassLabel=Label(self.experi_subTop6_fText, text=self.testDescDict[self.testLabelList[i]]+"\n", bg=self.midc,fg=self.fontc)
            self.testPassLabel.configure(width=20)
            self.testPassLabel.pack(side=LEFT)

     
        for i in range(17,19):
            if (listbuttons):
                self.testPassInfo.append(OptionMenu(self.experi_subTop2_6_frame,self.testPassList[i],"Fail","Pass","N/A",command=self.infoValChange))
                self.testPassInfo[i]["menu"].config(bg=self.topc,fg=self.fontc,activebackground=self.dimc,activeforeground=self.fontc)
                self.testPassList[i].set("N/A")
            else:
                self.testPassInfo.append(Button(self.experi_subTop2_6_frame,text="N/A",command=partial(self.togglepstate,i)))
            self.testPassInfo[i].configure(width=16,bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            self.testPassInfo[i].pack(side=LEFT)
            self.testPassList[i].set("N/A")
     
            self.testPassLabel=Label(self.experi_subTop2_6_fText, text=self.testDescDict[self.testLabelList[i]]+"\n",bg=self.midc,fg=self.fontc)
            self.testPassLabel.configure(width=20)
            self.testPassLabel.pack(side=LEFT)

        # Make a checkbox to overwrite/not overwrite pre-existing data
        self.overwriteBox = Checkbutton(self.experi_subTop7_frame, text="Overwrite existing QIE Card data (if applicable)?", variable=self.overwriteVar)
        self.overwriteBox.configure(bg=self.buttonsc[1],fg=self.fontc,activebackground=self.dimbuttonsc[1],activeforeground=self.fontc,selectcolor=self.checkc)
        self.overwriteBox.pack(side=TOP,
                       padx = button_padx,
                       pady = button_pady,
                       ipady = button_pady*2,
                       ipadx = button_padx*2)

        # Make a button to submit tests and information
        self.passAllTestsBttn = Button(self.experi_subTop7_frame, text="Pass All Tests", command=self.throwPassAllBox)
        self.passAllTestsBttn.configure(bg=self.buttonsc[4], fg=self.fontc, width=40, activebackground=self.dimbuttonsc[4], activeforeground=self.fontc)
        self.passAllTestsBttn.pack(side=TOP)

        # Make a button to submit tests and information
        self.initSubmitBttn = Button(self.experi_subTop7_frame, text="Submit Inspections & Tests", command=self.initSubmitBttnPress)
        self.initSubmitBttn.configure(bg=self.buttonsc[5], fg=self.fontc, width=40, activebackground=self.dimbuttonsc[5], activeforeground=self.fontc)
        self.initSubmitBttn.pack(side=TOP)

        # Make a button to clear all results
        self.clearDataBttn = Button(self.experi_subTop7_frame, text="Clear Inspections, Tests, & Info", command=self.clearDataBttnPress)
        self.clearDataBttn.configure(bg=self.buttonsc[6], fg=self.fontc, width=40, activebackground=self.dimbuttonsc[6], activeforeground=self.fontc)
        self.clearDataBttn.pack(side=TOP)



    #################################
    ###                           ###
    ###  BEGIN MEMBER FUNCTIONS   ###
    ###                           ###
    #################################

    # This function is needed to make the json dumps print properly
    def jdefault(self,o):
        return o.__dict__

##########################################################################################

    # Controls the three-state button behavior (when enabled) for Pass/Fail buttons
    def togglepstate(self,i,event=None):
        if ((event is not None) and lockout):
            return
        for o in range(1):#len(self.testPassInfo)):
            if(self.testPassList[i].get() == "Pass"):
                self.testPassInfo[i].configure(text="Fail",bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
                self.testPassList[i].set("Fail")
            elif(self.testPassList[i].get() == "Fail"):
                self.testPassList[i].set("N/A")
                self.testPassInfo[i].configure(text="N/A",bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)
            else:
                self.testPassList[i].set("Pass")
                self.testPassInfo[i].configure(text="Pass",bg=self.buttonsc[8],fg=self.fontc,activebackground=self.dimbuttonsc[8],activeforeground=self.fontc)


#########################################################################################

    def barcodeErrorBox(self):
         self.top = Toplevel()
         self.top.title("Barcode Entry Error")
         self.top.config(height=50, width=360, bg=self.backc)
         self.top.pack_propagate(False)
 
         self.msg = Label(self.top, text="Your barcode must be exactly 7 characters",fg=self.fontc, bg=self.backc)
         self.msg.pack()
 
         self.button = Button(self.top, text="Ok", command=self.top.destroy)
         self.button.configure(bg=self.buttonsc[7],fg=self.fontc,activebackground=self.dimbuttonsc[7],activeforeground=self.fontc)
         self.button.pack()


    # Dumps the results of the tests & inspections to a json file
    def initSubmitBttnPress(self):
        if (self.nameChoiceVar.get() == "Choose Name"):
            self.throwErrorBox()
            return None
        if (len(self.barcodeEntry.get()) != 7):
            self.barcodeErrorBox()
            return None
        self.initialTest.User = self.nameChoiceVar.get()
        self.initialTest.TestComment = self.infoCommentVar.get()
        self.initialTest.Barcode     = self.barcodeEntry.get()
        print self.initialTest.Barcode 
        self.initialTest.DateRun = str(datetime.now())

        if self.overwriteVar.get() == 1: self.initialTest.Overwrite = True
        if self.overwriteVar.get() == 0: self.initialTest.Overwrite = False

        for i in range(len(self.testPassList)-2):       #Last two are part of the firmware check
            print(self.testLabelList[i])
            print(self.testPassList[i].get())
            if self.testPassList[i].get() == "Pass":
                self.initialTest.testResults[self.testLabelList[i]] = True
            elif self.testPassList[i].get() == "Fail":
                self.initialTest.testResults[self.testLabelList[i]] = False
            else:
                self.initialTest.testResults[self.testLabelList[i]] = "na"

        self.initSubmitBttn.configure(state=DISABLED)

        fileString = self.barcodeEntry.get()+"_step1_raw.json"

        with open(self.databasePath+'/uploader/temp_json/'+fileString,'w') as jsonFile:
#       with open(fileString,'w') as jsonFile:     # Uncomment this line for debugging
            json.dump(self.initialTest, jsonFile, default = self.jdefault)


        # use -l for linux (must be first argument)
        # use 1 for step 1 (must be second argument)
        subprocess.call(self.databasePath+"/uploader/step123.sh -l 1", shell=True)
        print "Preliminary step recorded. Thank you!"

##########################################################################################

    def throwErrorBox(self):
        self.top = Toplevel()
        self.top.title("Name Choice Error")
        self.top.config(height=50, width=360, bg=self.backc)
        self.top.pack_propagate(False)

        self.msg = Label(self.top, text="Please select a name before continuing.",fg=self.fontc,bg=self.backc)
        self.msg.pack()

        self.button = Button(self.top, text="Sorry...", command=self.top.destroy)
        self.button.configure(bg=self.buttonsc[7],fg=self.fontc,activebackground=self.dimbuttonsc[7],activeforeground=self.fontc)
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
        self.yesButton.configure(bg=self.buttonsc[8],fg=self.fontc,activebackground=self.dimbuttonsc[8],activeforeground=self.fontc)
        self.yesButton.pack()

        self.noButton = Button(self.passBox, text="No", command=self.passBox.destroy)
        self.noButton.configure(bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
        self.noButton.pack()

    def passAllSelected(self):
        for i in range(len(self.testPassList)-2):
            self.testPassList[i].set("Pass")
            self.testPassInfo[i].configure(text="Pass")
        self.infoValChangeNonevent()
        self.passBox.destroy()

##########################################################################################

    # Dumps the card UID and firmware version to a json file
    def infoSubmitButtonPress(self):
        if (len(self.barcodeEntry.get()) != 7):
             self.barcodeErrorBox()
             return None
        self.cardInfo.Barcode = self.barcodeEntry.get()
        self.cardInfo.Unique_ID = self.uniqueIDPass
        self.cardInfo.FirmwareMaj = self.firmwareVerEntry.get()
        self.cardInfo.FirmwareMin = self.firmwareVerMinEntry.get()
        self.cardInfo.FirmwareOth = self.firmwareVerOtherEntry.get()
        if (self.iglooArmed.get()):
            self.cardInfo.IglooMinVerT = self.iglooMinVerEntryT.get()
            self.cardInfo.IglooMajVerT = self.iglooMajVerEntryT.get()
            self.cardInfo.IglooMinVerB = self.iglooMinVerEntryB.get()
            self.cardInfo.IglooMajVerB = self.iglooMajVerEntryB.get()
            self.cardInfo.Igloo_FPGA_Control = self.iglooToggleEntry.get()
        self.cardInfo.User = self.nameChoiceVar.get()
        self.cardInfo.DateRun = str(datetime.now())
        self.cardInfo.Checksum = self.check.get()
        self.cardInfo.SupplyI = self.testPassList[17].get() + "ed"
        self.cardInfo.PrgmChk = self.testPassList[18].get() + "ed"

        fileString = self.barcodeEntry.get()+"_step2_raw.json"

        with open(self.databasePath+'/uploader/temp_json/'+fileString,'w') as jsonFile:
            json.dump(self.cardInfo, jsonFile, default = self.jdefault)

        # use -l for linux (must be first argument)
        # use 2 for step 2 (must be second argument)
        subprocess.call(self.databasePath+"/uploader/step123.sh -l 2", shell=True)
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
        self.iglooMajVerEntryT.set("")
        self.iglooMinVerEntryT.set("")
        self.iglooMajVerEntryB.set("")
        self.iglooMinVerEntryB.set("")
        self.iglooToggleEntry.set("")
        self.check.set("")
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
        self.cardInfo.IglooMinVerT = self.iglooMinVerEntryT.get()
        self.cardInfo.IglooMajVerT = self.iglooMajVerEntryT.get()
        self.cardInfo.IglooMinVerB = self.iglooMinVerEntryB.get()
        self.cardInfo.IglooMajVerB = self.iglooMajVerEntryB.get()
        self.cardInfo.Igloo2_FPGA_Control = self.iglooToggleEntry.get()
        self.initialTest.Overwrite = False

        # Behind the scenes, change all the tests to "Fail"
        for i in range(len(self.testPassList)-2):
            if self.testPassList[i].get() == "Pass":
                self.initialTest.testResults[self.testLabelList[i]] = True
            else:
                self.initialTest.testResults[self.testLabelList[i]] = False

        # Change the buttons back to their red state
        self.infoValChangeNonevent()

###########################################################################################

    # A function that changes the menu colors depending on if a test passes
    # or fails. This function is for event cases (IE, changing a single menu value)
    def infoValChange(self,event):
        for i in range(len(self.testPassInfo)):
            if (self.testPassList[i].get() == "Fail"):
                self.testPassInfo[i].configure(bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
            elif (self.testPassList[i].get() == "Pass"):
                self.testPassInfo[i].configure(bg=self.buttonsc[8],fg=self.fontc,activebackground=self.dimbuttonsc[8],activeforeground=self.fontc)
            else:
                self.testPassInfo[i].configure(bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)

    # Duplicate of above function, but for non-event cases (IE hitting the "Clear" button)
    def infoValChangeNonevent(self):
        for i in range(len(self.testPassInfo)):
            if (self.testPassList[i].get() == "Fail"):
                self.testPassInfo[i].configure(bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
            elif (self.testPassList[i].get() == "Pass"):
                self.testPassInfo[i].configure(bg=self.buttonsc[8],fg=self.fontc,activebackground=self.dimbuttonsc[8],activeforeground=self.fontc)
            else:
                self.testPassInfo[i].configure(bg=self.buttonsc[3],fg=self.fontc,activebackground=self.dimbuttonsc[3],activeforeground=self.fontc)

#############################################################################

    # Opens the proper GPIO slot. Used for programming cards.
    def gpioBttnPress(self,*args):
        jSlotDict = {"J2 and J18" : 0x29, "J3 and J19" : 0x89, "J4 and J20" : 0xA9,
                     "J5 and J21" : 0x49, "J7 and J23" : 0x2A, "J8 and J24" : 0x8A,
                     "J9 and J25" : 0xAA, "J10 and J26" : 0x4A}


        # Full Backplane Functionality
        newJSlotDict = {"J2 and J21" : [0x29,0x49], "J3 and J20" : [0x89,0xA9],
                        "J4 and J19" : [0xA9,0x89], "J5 and J18" : [0x49,0x29],
                        "J7 and J26" : [0x2A,0x4A], "J8 and J25" : [0x8A,0xAA],
                        "J9 and J24" : [0xAA,0x8A], "J10 and J23" : [0x4A,0x2A]}

        dictStringToInts = {"J2 and J21" : [2, 21], "J3 and J20" : [3, 20],
                            "J4 and J19" : [4, 19], "J5 and J18" : [5, 18],
                            "J7 and J26" : [7, 26], "J8 and J25" : [8, 25],
                            "J9 and J24" : [9, 24], "J10 and J23" : [10, 23]}

        gpioVals = newJSlotDict[self.gpioChoiceVar.get()]
        self.jslots = dictStringToInts[self.gpioChoiceVar.get()]
        print 'GPIO '+self.gpioChoiceVar.get()+' values = '+str(gpioVals)

        for gpioValsIndex in xrange(len(gpioVals)):
            self.jslot = self.jslots[gpioValsIndex]
            gpioVal = gpioVals[gpioValsIndex]
            if gpioValsIndex == 0: # right side, J2-10
                self.myBus.write(0x72, [0x02])
            else: # left side, J18-26
                self.myBus.write(0x72, [0x01])
            batch = self.myBus.sendBatch()
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
            print "GPIO Batch = "+str(batch)
    
            if (batch[-1] == "1 0"):
                print "In gpioBttnPress(): GPIO I2C_ERROR"
                self.gpioSelect_bttn.configure(bg=self.buttonsc[2],fg=self.fontc,activebackground=self.dimbuttonsc[2],activeforeground=self.fontc)
                print self.I2C_ERROR_HELP
                return
            elif (batch[-1] == "0 "+str(gpioVal)):
                print "GPIO " + str(newJSlotDict[self.gpioChoiceVar.get()]) + " communication SUCCESS"
                self.gpioSelect_bttn.configure(bg=self.buttonsc[8],fg=self.fontc,activebackground=self.dimbuttonsc[8],activeforeground=self.fontc)
    
            else:
                print "GPIO Error: unexpected message is {0}".format(message)

            
            # select JTAG to program top/bottom igloo using Bridge register BRDG_ADDR_IGLO_CONTROL: 0x22
            igloo = "top"
            iglooControl = 0x22
            message = self.readBridge(iglooControl,4)
            print "Reading from BRDG_ADDR_IGLO_CONTROL before selecting JTAG: message = {0}".format(message)
            value = self.getValue(message)
            # select top (0) or bottom (1) igloo to program; maintain settings for other bits
            if igloo == "top":
                value = value & 0xFFE
            if igloo == "bottom":
                value = value | 0x001
            messageList = self.getMessageList(value,4)
            self.writeBridge(iglooControl,messageList)
            message = self.readBridge(iglooControl,4)
            print "Reading from BRDG_ADDR_IGLO_CONTROL after selecting JTAG: message = {0}".format(message)
            
            print "Ready to program {0} igloo".format(igloo)

##################################################################################

    def getUniqueIDPress_left(self):
        self.readFromLeft = True
        self.getUniqueIDPress()

##################################################################################

    def getUniqueIDPress_right(self):
        self.readFromLeft = False
        self.getUniqueIDPress()

##################################################################################

    # Read UniqueID, Bridge and Igloo Firmware Versions
    def getUniqueIDPress(self):
        
        """
        bridgeDict = { 18 : 0x19, 19 : 0x1A, 20 : 0x1B, 21 : 0x1C,
                       23 : 0x19, 24 : 0x1A, 25 : 0x1B, 26 : 0x1C,
                        2 : 0x19,  3 : 0x1A,  4 : 0x1B,  5 : 0x1C,
                        7 : 0x19,  8 : 0x1A,  9 : 0x1B, 10 : 0x1C }

        if self.readFromLeft:
            self.jslot = self.jslots[1]
            self.card_i2c_address = bridgeDict[self.jslot]
            if self.jslot in [18,19,20,21]:
                self.myBus.write(0x72, [0x01])
                self.myBus.write(0x74,[0x18])
            if self.jslot in [23,24,25,26]:
                self.myBus.write(0x72, [0x01])
                self.myBus.write(0x74,[0x09])
        else:
            self.jslot = self.jslots[0]
            self.card_i2c_address = bridgeDict[self.jslot]
            if self.jslot in [2,3,4,5]:
               self.myBus.write(0x72, [0x02])
               self.myBus.write(0x74, [0x0A])
            if self.jslot in [7,8,9,10]:
               self.myBus.write(0x72, [0x02])
               self.myBus.write(0x74, [0x28])
        """

        if self.readFromLeft:
            self.jslot = self.jslots[1]
        else:
            self.jslot = self.jslots[0]
        self.multiplex()
        self.myBus.sendBatch()
        
        bridgeDict = { 18 : 0x19, 19 : 0x1A, 20 : 0x1B, 21 : 0x1C,
                       23 : 0x19, 24 : 0x1A, 25 : 0x1B, 26 : 0x1C,
                        2 : 0x19,  3 : 0x1A,  4 : 0x1B,  5 : 0x1C,
                        7 : 0x19,  8 : 0x1A,  9 : 0x1B, 10 : 0x1C }
        self.card_i2c_address = bridgeDict[self.jslot]

        print "Reading Unique ID and Firmware versions."
        print "JSlot = {0} ; I2C_Address = 0x{1:02x}".format(self.jslot, self.card_i2c_address)

        # Getting unique ID
        # 0x05000000ea9c8b7000   <- From main gui
        self.myBus.write(0x00,[0x06])
        self.multiplex()
        self.myBus.write(self.card_i2c_address,[0x11,0x04,0,0,0])
        self.myBus.write(0x50,[0x00])
        self.myBus.read(0x50, 8)
        
        # raw_bus is list of strings (list of messages)
        # the last entry in raw_bus is the message string containing the unique id
        raw_bus = self.myBus.sendBatch()
        
        # Verify checksum
        selfcheck = Checksum(raw_bus[-1],0).result
        if selfcheck is 0: # passed checksum test
            self.check.set("Passed")
            print "UniqueID checksum test passed"
        else:               # failed checksum test
            self.check.set("Failed")
            print "UniqueID checksum test failed"            
        
        # I2C_ERROR
        if raw_bus[-1][0] != '0':
            print 'In getUniqueIDPress(): I2C_ERROR when reading Unique ID'
            print self.I2C_ERROR_HELP
            return
        
        cooked_bus = self.reverseBytes(raw_bus[-1])
        #cooked_bus = self.serialNum(cooked_bus)
        self.uniqueIDEntry.set(self.toHex(cooked_bus))
        self.uniqueIDPass = self.uniqueIDEntry.get()
        self.uniqueIDEntry.set("0x" + self.uniqueIDPass[2:10].upper() + "_0x" + self.uniqueIDPass[10:18].upper())

        # Getting bridge firmware
        #self.myBus.write(0x00,[0x06])
        #self.myBus.write(self.card_i2c_address,[0x04])
        #self.myBus.read(self.card_i2c_address, 4)
        #raw_data = self.myBus.sendBatch()[-1]
        #med_rare_data = raw_data[2:]
        #cooked_data = self.reverseBytes(med_rare_data)
        bridge_fw_message = self.readBridge(0x04,4)
        bridge_fw = self.toHex(bridge_fw_message)    # my apologies for the cooking references
        bridge_fw = bridge_fw[2:]
        print 'Bridge FPGA Firmware Version = 0x'+str(bridge_fw)
        self.firmwareVerEntry.set("0x"+bridge_fw[0:2])    #these are the worst (best?) variable names ever
        self.firmwareVerMinEntry.set("0x"+bridge_fw[2:4])
        self.firmwareVerOtherEntry.set("0x"+bridge_fw[4:8])

        # Getting temperature
        self.multiplex()
        self.tempEntry.set(str(round(temp.readManyTemps(self.myBus, self.card_i2c_address, 10, "Temperature", "nohold"),4)))

        if (self.iglooArmed.get()):
            # Getting IGLOO firmware info
            majorIglooVerT = self.readIgloo("top",0x00)
            minorIglooVerT = self.readIgloo("top",0x01)
            majorIglooVerB = self.readIgloo("bottom",0x00)
            minorIglooVerB = self.readIgloo("bottom",0x01)
            # Write IGLOO firmware in hex
            majorIglooVerT = self.toHex(majorIglooVerT)
            minorIglooVerT = self.toHex(minorIglooVerT)
            majorIglooVerB = self.toHex(majorIglooVerB)
            minorIglooVerB = self.toHex(minorIglooVerB)
            # Display igloo FW info on gui
            self.iglooMajVerEntryT.set(majorIglooVerT)
            self.iglooMinVerEntryT.set(minorIglooVerT)
            self.iglooMajVerEntryB.set(majorIglooVerB)
            self.iglooMinVerEntryB.set(minorIglooVerB)
            print "Top Igloo2 FPGA Major Firmware Version = {0}".format(majorIglooVerT)
            print "Top Igloo2 FPGA Minor Firmware Version = {0}".format(minorIglooVerT)
            print "Bottom Igloo2 FPGA Major Firmware Version = {0}".format(majorIglooVerB)
            print "Bottom Igloo2 FPGA Minor Firmware Version = {0}".format(minorIglooVerB)

            # Verify that the Igloo can be power toggled
            self.iglooToggleEntry.set(self.checkIglooToggle())
        else:
            self.iglooMajVerEntryT.set("")
            self.iglooMinVerEntryT.set("")
            self.iglooMajVerEntryB.set("")
            self.iglooMinVerEntryB.set("")  
            self.iglooToggleEntry.set("") 
#########################################
#   Functions to check igloo toggle     #
#########################################

    def checkIglooToggle(self):
        print '\n--- Begin Toggle Igloo2 Power Test'
        control_address = 0x22
        message = self.readBridge(control_address,4)
        print 'Igloo Powered on Bridge Control Igloos = '+str(message)

        igloos = ("top","bottom")
        ones_address = 0x02
        all_ones = '255 255 255 255'
        all_zeros = '0 0 0 0'  

        self.myBus.write(0x00,[0x06])
        self.myBus.sendBatch()
        # check that igloos are powered on  
        for igloo in igloos:

            register = self.readIgloo(igloo,ones_address, 4)
            if register != all_ones:
                print 'Toggle Igloo Power Fail!'
                return "Failed"
            # print 'Igloo Ones = '+str(register)

        # Turn Igloo Off
        message = self.toggleIgloo()
        time.sleep(2) 
        print 'Igloo Powered off Bridge Control Igloos = '+str(message)
        # check that igloos are powered off  
        for igloo in igloos:

            register = self.readIgloo(igloo,ones_address, 4)
            if register != all_zeros:
                print 'Toggle Igloo Power Fail!'
                return "Failed"
            # print 'Igloo Ones = '+str(register)

        # Turn Igloo On
        message=self.toggleIgloo()
        print 'Igloo Powered on Bridge Control Igloos = '+str(message)
        time.sleep(2) 
        # check that igloos are powered on  
        for igloo in igloos:

            register = self.readIgloo(igloo,ones_address, 4)
            if register != all_ones:
                print 'Toggle Igloo Power Fail!'
                return "Failed"
            # print 'Igloo Ones = '+str(register)

        print 'Toggle Igloo Power Success!'
        return "Passed"

    # turning igloo on and off using bridge vdd enable register
    def toggleIgloo(self):
        iglooControl = 0x22
        message = self.readBridge(iglooControl,4)
        value = self.getValue(message)
        value = value ^ 0x400 # toggle igloo power: Igloo2 VDD Enable
        messageList = self.getMessageList(value,4)
        self.writeBridge(iglooControl,messageList)
        return self.readBridge(iglooControl,4)


###########################################################################################

# Main
def main():
    # Choose a color theme from the list (or add your own)
    color_themes = ["bright", "dark", "sunrise", "nightfall"]

    # command line options
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--color_theme", "-c", default="bright",        help="color theme of GUI")
    parser.add_argument("--list_colors", "-l", action="store_true",     help="list available color themes")
    options = parser.parse_args()
    color_theme = options.color_theme
    list_colors = options.list_colors

    # print color themes and exit
    if list_colors:
        sys.exit("color themes: {0}".format(" ".join(color_themes)))

    root = Tk()
    myapp = makeGui(root, color_themes, color_theme)
    root.mainloop()

if __name__ == "__main__":
    main()


