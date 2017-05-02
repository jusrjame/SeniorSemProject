'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 *
 * File modified by Carter Crews for the SmartFridge project.
 */
 '''
### Fix for bug in SDK ###
import os
import sys
import AWSIoTPythonSDK
sys.path.insert(0,os.path.dirname(AWSIoTPythonSDK.__file__))
### End Fix ###
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
#import sys #uncomment when SDK is fixed.
import logging
import time
import getopt
import RPi.GPIO as io 

# Code to read data from sensors.
import glob
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
io.setmode(io.BCM) 

base_dir = '/sys/bus/w1/devices/'
device_folder_1 = glob.glob(base_dir + '28*')[0]
device_folder_2 = glob.glob(base_dir + '28*')[1]
device_file_1 = device_folder_1 + '/w1_slave'
device_file_2 = device_folder_2 + '/w1_slave'
doorPin1 = 17
doorPin2 = 18
door1StatusPrev = '2'
door2StatusPrev = '2'
tempLimit = 90 # Temp ceiling in Fahrenheit before sending a push notification.

io.setup(doorPin1, io.IN, pull_up_down=io.PUD_UP)
io.setup(doorPin2, io.IN, pull_up_down=io.PUD_UP)

def read_doors():
    ### A 1 means door is open, a 0 means door is closed. ###
    door1Status = io.input(doorPin1)
    door2Status = io.input(doorPin2)
    return{'door1':door1Status, 'door2':door2Status}

def read_temp_raw():
    f_1 = open(device_file_1, 'r')
    f_2 = open(device_file_2, 'r')
    lines_1 = f_1.readlines()
    lines_2 = f_2.readlines()
    f_1.close()
    f_2.close()
    return {'sensor1':lines_1, 'sensor2':lines_2}
 
def read_temp():
    raw_tmp = read_temp_raw()
    lines_1 = raw_tmp['sensor1']
    lines_2 = raw_tmp['sensor2']
    while lines_1[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        raw_tmp = read_temp_raw()
        lines_1 = raw_tmp['sensor1']
        lines_2 = raw_tmp['sensor2']
    equals_pos_1 = lines_1[1].find('t=')
    equals_pos_2 = lines_2[1].find('t=')
    if equals_pos_1 != -1:
        temp_string_1 = lines_1[1][equals_pos_1+2:]
        temp_c_1 = float(temp_string_1) / 1000.0
        temp_f_1 = temp_c_1 * 9.0 / 5.0 + 32.0
    else:
        temp_string_1 = -1
    if equals_pos_2 != -1:
        temp_string_2 = lines_2[1][equals_pos_2+2:]
        temp_c_2 = float(temp_string_2) / 1000.0
        temp_f_2 = temp_c_2 * 9.0 / 5.0 + 32.0
    else:
        temp_string_2 = -1
        print("Error reading temp sensor")

    if temp_string_1 == -1 or temp_string_2 == -1:
        sys.exit(0)
    else:
        return {'sensor1':temp_f_1, 'sensor2':temp_f_2}

# The rest of this code is used to connect and send the data to AWS.

# Custom MQTT message callback
#def customCallback(client, userdata, message):
#	print("Received a new message: ")
#	print(message.payload)
#	print("from topic: ")
#	print(message.topic)
#	print("--------------\n\n")

# Usage
usageInfo = """Usage:

Use certificate based mutual authentication:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>

Use MQTT over WebSocket:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w

Type "python basicPubSub.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-c, --cert
	Certificate file path
-k, --key
	Private key file path
-w, --websocket
	Use MQTT over WebSocket
-h, --help
	Help information


"""

# Read in command-line parameters
useWebsocket = False
host = "a3cnv91cxybtxo.iot.us-east-1.amazonaws.com"
rootCAPath = "root.crt"
certificatePath = "cert.crt"
privateKeyPath = "private.key"
#try:
#	opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:", ["help", "endpoint=", "key=","cert=","rootCA=", "websocket"])
#	if len(opts) == 0:
#		raise getopt.GetoptError("No input parameters!")
#	for opt, arg in opts:
#		if opt in ("-h", "--help"):
#			print(helpInfo)
#			exit(0)
#		if opt in ("-e", "--endpoint"):
#			host = arg
#		if opt in ("-r", "--rootCA"):
#			rootCAPath = arg
#		if opt in ("-c", "--cert"):
#			certificatePath = arg
#		if opt in ("-k", "--key"):
#			privateKeyPath = arg
#		if opt in ("-w", "--websocket"):
#			useWebsocket = True
#except getopt.GetoptError:
#	print(usageInfo)
#	exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
	print("Missing '-e' or '--endpoint'")
	missingConfiguration = True
if not rootCAPath:
	print("Missing '-r' or '--rootCA'")
	missingConfiguration = True
if not useWebsocket:
	if not certificatePath:
		print("Missing '-c' or '--cert'")
		missingConfiguration = True
	if not privateKeyPath:
		print("Missing '-k' or '--key'")
		missingConfiguration = True
if missingConfiguration:
	exit(2)

# Configure logging
logger = None
if sys.version_info[0] == 3:
	logger = logging.getLogger("core")  # Python 3
else:
	logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
logger.setLevel(logging.ERROR)
#logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("smartfridge", useWebsocket=True)
	myAWSIoTMQTTClient.configureEndpoint(host, 443)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("smartfridge")
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
time.sleep(2)

loopCount = 0
temp1Alarm = 0
temp2Alarm = 0
door1Alarm = 0
door2Alarm = 0
temp1AlarmTime = -1
temp2AlarmTime = -1
door1LastChange = -1
door2LastChange = -1

# Change the number in the strings below to a different number for each Pi.
while True:
    temps = read_temp()
    doors = read_doors()
    JSONPayload = '{"state":{"reported":{"temp1":' + str(temps['sensor1']) + ',"temp2":' + str(temps['sensor2'])

    # Temp sensor 1: Check for alarm state.
    if (temps['sensor1'] > tempLimit) and (temp1Alarm == 0):
        JSONPayload += ',"temp1Alarm":' + '"Temp 1 Alarm! Temp: ' + str(temps['sensor1']) + 'F"'
        if temp1AlarmTime == -1:
            temp1AlarmTime = loopCount
        temp1Alarm = 1
    elif (temps['sensor1'] < tempLimit) and (temp1Alarm == 1):
        JSONPayload += ',"temp1Alarm":' + '"Temp 1 Normal. Temp: ' + str(temps['sensor1']) + 'F"'
        temp1Alarm = 0
        temp1AlarmTime = -1

    # Temp sensor 2: Check for alarm state.
    if (temps['sensor2'] > tempLimit) and (temp2Alarm == 0):
        JSONPayload += ',"temp2Alarm":' + '"Temp 2 Alarm! Temp: ' + str(temps['sensor2']) + 'F"'
        if temp2AlarmTime == -1:
            temp2AlarmTime = loopCount
        temp2Alarm = 1
    elif (temps['sensor2'] < tempLimit) and (temp2Alarm == 1):
        JSONPayload += ',"temp2Alarm":' + '"Temp 2 Normal. Temp: ' + str(temps['sensor2']) + 'F"'
        temp2Alarm = 0
        temp2AlarmTime = -1
            
    if doors['door1'] != door1StatusPrev:
        JSONPayload += ',"door1":' + str(doors['door1'])
        door1StatusPrev = doors['door1']
        door1LastChange = loopCount
        if door1Alarm and (doors['door2'] == 0):
            JSONPayload += ',"door1Alarm":' + '"Door 1 Normal."'
            door1Alarm = 0
        
    if doors['door2'] != door2StatusPrev:
        JSONPayload += ',"door2":' + str(doors['door2'])
        door2StatusPrev = doors['door2']
        door2LastChange = loopCount
        if door2Alarm and (doors['door2'] == 0):
            JSONPayload += ',"door2Alarm":' + '"Door 2 Normal."'
            door2Alarm = 0

    # Door sensor 1: Check for alarm state.
    if (loopCount >= door1LastChange + 15) and ((loopCount - door1LastChange) % 5 == 0) and (doors['door1'] == 1):
        JSONPayload += ',"door1Alarm":' + '"Door 1 Alarm! Door 1 has been open for an extended period of time."'
        door1Alarm = 1

    # Door sensor 2: Check for alarm state.
    if (loopCount >= door2LastChange + 15) and ((loopCount - door2LastChange) % 5 == 0) and (doors['door2'] == 1):
        JSONPayload += ',"door2Alarm":' + '"Door 2 Alarm! Door 2 has been open for an extended period of time."'
        door2Alarm = 1
    
    JSONPayload += '}}}'

    # Send message to AWS.
    myAWSIoTMQTTClient.publish("$aws/things/raspberry-pi-1/shadow/update", JSONPayload, 1)

    loopCount += 1

    # Send another notification after a certain number of executions.
    if ((loopCount - temp1AlarmTime) % 15 == 0):
        temp1Alarm = 0
    if ((loopCount - temp2AlarmTime) % 15 == 0):
        temp2Alarm = 0
        
    #time.sleep(1)
