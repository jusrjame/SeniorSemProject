import os
import glob
import time
 
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
	
while True:
    temps = read_temp()
    print("tmp1: ",temps['sensor1']," F")
    print("tmp2: ",temps['sensor2']," F")
    time.sleep(1)
