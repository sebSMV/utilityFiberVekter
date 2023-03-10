import re
import serial
from time import sleep
from plc_connector import Connector
from datetime import datetime

configFilePath = '/home/pi/utilityFiberVekter/conf.txt'
#configFilePath = 'conf.txt'

def is_valid_ip(ip):
    pattern = r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    if re.match(pattern, ip):
        return True
    return False


def read_ip_from_config():
    with open(configFilePath, 'r') as f:
        for line in f:
            if line.startswith('PLCIP:'):
                ip = line.split(':')[1].strip()
                if is_valid_ip(ip):
                    return ip
    return None


def read_config(prefix):
    with open(configFilePath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(prefix):
                key, value = line.split(':', 1)
                return value
    return None


def readLine(port, eol='\r\n'):
    string = ""
    while True:
        data = port.read(1).decode()
        string += str(data)
        if eol in string:
            return string.strip('- ?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\r\n')


if __name__ == '__main__':
    #Read config file
    IP = read_ip_from_config()
    portName1 = read_config('P1')
    portName2 = read_config('P2')
    print("PLCIP: " + IP)
    print("Port 1: " + portName1)
    print("Port 2: " + portName2)

    #init port
    port1 = serial.Serial(portName1)
    port2 = serial.Serial(portName2)

    rawdataA = 0
    rawdataB = 0
    weightA = 0.0
    weightB = 0.0
    lastWeightA = 0.0
    lastWeightB = 0.0
    offsetA = 0.0
    offsetB = 0.0

    lastSecs = 0

    if IP is None or portName1 is None or portName2 is None:
        raise IOError('File not found or invalid config')

    print('Connecting to PLC at: ' + IP)
    with Connector(IP) as plc:
        print('Connected to PLC')
        while True:
            try:
                ts = datetime.now()
                if ts.second != lastSecs:
                    lastSecs = ts.second
                    plc.write("TS_Heartbeat", not bool(plc.read("TS_Heartbeat")))


                if plc.read("TS_ZeroWeightA"):
                    print("Resetting Weight A")
                    offsetA = abs(rawdataA)
                    plc.write("TS_ZeroWeightA", False)

                if plc.read("TS_ZeroWeightB"):
                    print("Resetting Weight B")
                    offsetB = abs(rawdataB)
                    plc.write("TS_ZeroWeightB", False)

                readData = False
                if port1.inWaiting() > 1:
                    rawdataA = float(readLine(port1, '\r'))
                    readData = True

                if port2.inWaiting() > 1:
                    rawdataB = float(readLine(port2, '\r'))
                    readData = True

                if readData:
                    print(f"Weight A: Raw: {rawdataA} Act: {weightA}, Weight B: Raw: {rawdataB} Act: {weightB}")

                weightA = abs(rawdataA - offsetA)
                weightB = abs(rawdataB - offsetB)

                try:
                    if weightA != lastWeightA:
                        plc.write("FS_VektA", weightA)
                        lastWeightA = weightA

                    if weightB != lastWeightB:
                        plc.write("FS_VektB", weightB)
                        lastWeightB = weightB
                except Exception as e:
                    print("Writing tags may have failed:")
                    print(e)
                finally:
                    pass
            except Exception as e:
                print('An error occured')
                print(e)
                sleep(10)
