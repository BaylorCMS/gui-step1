#!/usr/bin/bash
# uploadIgloo.sh
# script to run on Windows machine (hcaldaq-pc)
# 1. copy json file to Linux machine (cmshcal11)
# 2. combine flashpro log files 
# 3. copy directory of log files to Linux machine (cmshcal11)
# 4. upload results to database

###################################################
#               Set Initial Data                  #
###################################################
echo "Setting initial data"

# use explicit ip address because Windows machine does not resolve host aliases
remoteHost=hep@192.168.1.11
remoteDatabase=/home/django/testing_database_hb
remoteJson=$remoteDatabase/uploader/temp_json
remoteScript=$remoteDatabase/uploader/step123.sh
jsonLoc=temp_json
jsonTag=step3_raw.json
logLoc=$1
remoteLog=$remoteDatabase/uploader/temp_logs

echo "Initial data set"
echo ""

# Note: $? is the error code of the last command executed
# Use $? to check if the last command was successful

# 1. copy json file to Linux machine (cmshcal11)
echo "    Copying json file to $remoteHost"
scp $jsonLoc/*$jsonTag $remoteHost:$remoteJson
if [ $? -eq 0 ]
then
    echo "    Successfully copied json file to $remoteHost"
else
    echo "    ERROR: Failed to copy json file to $remoteHost"
    echo "ERROR: No json file uploaded to database"
    exit 1
fi

# 2. combine flashpro log files 
flashproLog=$logLoc/igloo_flashpro.log
echo "Igloo FlashPro Programming Log" > $flashproLog
echo "" > $flashproLog

# igloos should be top and bot to match file names
declare -a igloos=("top" "bot")
for igloo in "${igloos[@]}"
do
    if ls $logLoc/"$igloo"_igloo_flashpro.log &> /dev/null; then
        echo "$igloo igloo flashpro programming log" >> $flashproLog
        echo "" >> $flashproLog
        cat $logLoc/"$igloo"_igloo_flashpro.log >> $flashproLog
        echo "" >> $flashproLog
    else
        echo "The flashpro log file $logLoc/"$igloo"_igloo_flashpro.log does not exist"
    fi
done

# 3. copy directory of log files to Linux machine (cmshcal11)
echo "    Copying directory of log files to $remoteHost"
scp -r $logLoc $remoteHost:$remoteLog
if [ $? -eq 0 ]
then
    echo "    Successfully copied directory of log files to $remoteHost"
else
    echo "    ERROR: Failed to copy directory of logs files to $remoteHost"
    echo "ERROR: No log files uploaded to database"
    exit 1
fi

# remote json files if copying was successful
rm $jsonLoc/*$jsonTag

# 4. upload results to database
# include option -w for no color
ssh $remoteHost $remoteScript -w

if [ $? -eq 0 ]
then
    echo "    Successfully uploaded results to database"
else
    echo "    ERROR: Failed to upload results to database"
    echo "ERROR: No information uploaded to database"
    exit 1
fi

echo "Successfully uploaded results to database"

echo "Finished"


