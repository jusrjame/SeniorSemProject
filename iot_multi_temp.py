
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

# Code to read data from sensors.
import glob
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder_1 = glob.glob(base_dir + '28*')[0]
device_folder_2 = glob.glob(base_dir + '28*')[1]
device_file_1 = device_folder_1 + '/w1_slave'
device_file_2 = device_folder_2 + '/w1_slave'
 
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

# Publish to the same topic in a loop forever
loopCount = 0
# Change the number in the strings below to a different number for each Pi.
while True:
    temps = read_temp()
    myAWSIoTMQTTClient.publish("pi/001/temp1", str(temps['sensor1']), 1)
    myAWSIoTMQTTClient.publish("pi/001/temp2", str(temps['sensor2']), 1)
    #myAWSIoTMQTTClient.publish("pi/001/door1", str(loopCount % 2), 1)
    #myAWSIoTMQTTClient.publish("pi/001/door2", str((loopCount +1) % 2), 1)
    loopCount += 1
    time.sleep(1)
### END AWS CODE ###
