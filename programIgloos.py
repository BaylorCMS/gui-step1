from optparse import OptionParser
from datetime import datetime
from scripts import Teststand
from scripts import writeToLog
import os
import subprocess as sp
import json

def writeTCLFile(programFile):
    flashproLog = "flashpro.log"
    with open("program_igloo.tcl", "w") as file:
        file.write("# Microsemi Tcl Script\n")
        file.write("# flashpro\n")
        file.write("# Date: Tue Oct 11 09:37:47 2016\n")
        file.write("# Directory C:\Users\hcaldaq\gui-step1\n")
        file.write("# File C:\Users\hcaldaq\gui-step1\program_igloo.tcl\n")
        file.write("open_project -project {%s} -connect_programmers 1\n"%(os.path.abspath("HB_igloo/HB_igloo.pro").replace("\\","/")))
        file.write("enable_prg_type -prg_type FP4 -enable FALSE\n")
        file.write("enable_prg -name 86103 -enable TRUE\n")
        file.write("set_programming_file -file {%s}\n"%os.path.abspath(programFile).replace("\\","/"))
        #file.write("remove_prg -name 84830\n")
        file.write("set_programming_action -action PROGRAM\n")
        file.write("set_main_log_file -file {0}\n".format(flashproLog))
        file.write("run_selected_actions\n")
        file.write("save_log -file {0}\n".format(flashproLog))
        file.write("close_project\n")

# remove finalLog if it exists, then move initialLog to finalLog        
def moveLog(initialLog, finalLog):
    if os.path.isfile(initialLog):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        if os.path.isfile(finalLog):
            os.remove(finalLog)
        os.rename(initialLog, finalLog)
    else:
        print "Cannot move log file '{0}' because it does not exist.".format(initialLog)

if __name__ ==  "__main__":
    # define log file for teststand
    logFile = "teststand.log"  
    begin_time = datetime.now()
    writeToLog(logFile, "Begin time is: {0}".format(begin_time))
    parser = OptionParser()
    parser.add_option("-f", "--file",               dest="filename",        default="HB_igloo/fixed_HB_RM_v1_03.stp", help="Firmware programming file")
    parser.add_option("-i", "--ip",                 dest="ip",              help="ip address of Raspberry Pi")
    parser.add_option("-s", "--slot",               dest="slot",            default = -2,   help="Specify a single slot")
    parser.add_option("-b", "--no_fanout_board",    dest="no_fanout_board", action="store_true",  default=False, help="Do not use fanout board")
    parser.add_option("-t", "--stop",               dest="stop",            action="store_true",  default=False, help="Stop after checking active slots")
    parser.add_option("-c", "--calibration",        dest="calibration",     action="store_true",  default=False, help="Include calibration unit")

    (options, args) = parser.parse_args()

    writeTCLFile(options.filename)
    # use_fanout_board is True if you are using a fanout board
    use_fanout_board = not(options.no_fanout_board)
    if options.ip:
        ts = Teststand(use_fanout_board, calibration=options.calibration, ip=options.ip)
    else:
        ts = Teststand(use_fanout_board, calibration=options.calibration)

    if options.stop:
        exit()
    
    slots = []
    if options.slot >0:
        slot = int(options.slot)
        if slot in ts.active_slots:
            slots = [slot]
        else:
            writeToLog(logFile, "Invalid Slot")
            exit()
    else:
        slots = ts.active_slots

    if not ts.active_slots:
        writeToLog(logFile, "ERROR: No active slots found. Check that QIE cards are inserted in the backplane and powered on.")
        exit(1)
    
    # define log files
    flashproLog = "flashpro.log"
    tempLog = "card.log"
    
    # program top and bottom igloos
    igloos = ["top","bot"]
    iglooData = []
    if ts.piStatus and ts.busStatus:
        logFile = tempLog
        for slot in slots:
            ts.setLogFile(tempLog)
            Igloos_Programmed=False
            # We should not read from Igloos before programming
            #data = ts.readInfo(slot)
            #writeToLog(logFile, "time: ", data["DateRun"])
            #writeToLog(logFile, "temp: ", data["temperature"])
            for igloo in igloos:
                writeToLog(logFile, "")
                writeToLog(logFile, "Initiated Programing of SpecifiedSlot: {0} {1} Igloo FPGA".format(slot,igloo))
                writeToLog(logFile, "")

                ts.selectGpio(slot,igloo)

                writeToLog(logFile, "Starting Flashpro batch programming mode")
                # Please include the correct Microsemi path here 
                #sp.check_output("C:\\Microsemi\\Program_Debug_v11.7\\bin\\flashpro.exe script:C:\\Users\\pastika\\Desktop\\program_igloo.tcl console_mode:brief", shell=True)
                try:
                    output = sp.check_output("C:\\Microsemi\\Program_Debug_v11.7\\bin\\flashpro.exe script:%s console_mode:brief"%os.path.abspath("program_igloo.tcl"), shell=True)
                    writeToLog(logFile, "Success Programing: {0} {1} Igloo FPGA".format(slot,igloo) )
                    Igloos_Programmed=True
                    finalLog = "logs/{0}_igloo_{1}".format(igloo, flashproLog)
                    moveLog(flashproLog, finalLog)
                except:
                    writeToLog(logFile, "Error: Failed Programing: {0} {1} Igloo FPGA".format(slot,igloo) )
                    Igloos_Programmed=False
                    finalLog = "logs/{0}_igloo_{1}".format(igloo, flashproLog)
                    moveLog(flashproLog, finalLog)
                    break
                # Used this to pause if you want to program using flashpro GUI
                # raw_input("press enter to continue")

            data = ts.readInfo(slot)
            if Igloos_Programmed:
                data["Igloos_Programmed"]="Passed"
            else:
                data["Igloos_Programmed"]="Failed"

            writeToLog(logFile, "time: {0}".format(data["DateRun"]))
            writeToLog(logFile, "temp: {0}".format(data["temperature"]))
            iglooData.append(data)
            jsonFile = "temp_json/{0}_step3_raw.json".format(data["Unique_ID"])
            with open(jsonFile, 'w') as jf:
                json.dump(data, jf)
            
        
        for datum in iglooData:
            # create log directory using unique id
            unique_id = data["Unique_ID"]
            card_dir = "logs/{0}".format(unique_id)
            if not os.path.exists(card_dir):
                os.makedirs(card_dir)
            
            for igloo in igloos:
                initialLog = "logs/{0}_igloo_{1}".format(igloo, flashproLog)
                finalLog = "{0}/{1}_igloo_{2}".format(card_dir, igloo, flashproLog)
                moveLog(initialLog, finalLog)
            writeToLog(logFile, "Unique ID: {0}".format(unique_id))
            writeToLog(logFile, "Top Igloo FW: {0} {1}".format(datum["IglooMajVerT"], datum["IglooMinVerT"]))
            writeToLog(logFile, "Bottom Igloo FW: {0} {1}".format(datum["IglooMajVerB"], datum["IglooMinVerB"]))
            # move log files to unique id directory
            finalLog = "{0}/{1}".format(card_dir, tempLog)
            moveLog(tempLog, finalLog)
            # do not log after this point
            # the script uploadIgloo.sh moves the log file to cmshcal11
            print ""
            print "Uploading results to database"
            print ""
            try:
                output = sp.check_output("bash uploadIgloo.sh logs/{0}".format(datum["Unique_ID"]), shell=True)
                print ""
                print "uploadIgloo.sh output:"
                print ""
                print output
            except:
                print "ERROR: Unable to upload results to the database. It is possible that the step3 json file does not exist in the temp_json directory."
            
        
    
    else:
        logFile = "teststand.log"  
        writeToLog(logFile, "Failed Raspberry Pi and/or Websocket status.")
        writeToLog(logFile, "    1. Did you turn on the Raspberry Pi?")
        writeToLog(logFile, "    2. Did you start the server?")
        writeToLog(logFile, "    3. Did you plug in the ethernet cable?")
        writeToLog(logFile, "    4. Did you use the correct ip address?")
        writeToLog(logFile, "    5. Did you have coffee today?")
    
    logFile = "teststand.log" 
    end_time = datetime.now()
    writeToLog(logFile, "End time is: {0}".format(end_time))
    total_time = end_time-begin_time
    writeToLog(logFile, "total run time is: {0}".format(total_time))



