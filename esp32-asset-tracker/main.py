print('Main.py -> Start')
import sys
import config
import os
import random
import ujson
import esp32
import machine
from umqtt.simple import MQTTClient

from machine import UART

import utime

print('Main.py -> Init')

# IoT configuration
info = os.uname()
with open("/flash/" + config.THING_PRIVATE_KEY, 'r') as f:
    key = f.read()
with open("/flash/" + config.THING_CLIENT_CERT, 'r') as f:
    cert = f.read()
device_id = config.THING_ID
topic_pub = "clients/" + device_id + "/gps-01"
aws_endpoint = config.MQTT_HOST
ssl_params = {"key":key, "cert":cert, "server_side":False}

# GPS configuration
gpsModule = UART(2, baudrate=9600)
print(gpsModule)
buff = bytearray(255)
FIX_STATUS = False

latitude = ""
longitude = ""
utctime = ""
satellites = ""

def getGPS(gpsModule):
    global FIX_STATUS, latitude, longitude, utctime, satellites
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parts = buff.split(',')
        
        # print("(" + buff + ")")
        
        if (parts[0] == "b'$GNGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                # https://www.rfwireless-world.com/Terminology/GPS-sentences-or-NMEA-sentences.html  
                print("NMEA sentence: " + buff[1:-5])
                utctime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]             
                latitude = convertToDegree(parts[2])
                if (parts[3] == 'S'):
                    latitude = -float(latitude)
                longitude = convertToDegree(parts[4])
                if (parts[5] == 'W'):
                    longitude = -float(longitude)
                satellites = parts[7]
                FIX_STATUS = True
                break
        utime.sleep_ms(200)

# https://support.google.com/maps/answer/18539?hl=en&co=GENIE.Platform%3DDesktop        
def convertToDegree(RawDegrees):
    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)

def mqtt_connect(client=device_id, endpoint=aws_endpoint, sslp=ssl_params):
    print("CONNECTING TO MQTT BROKER...")
    mqtt = MQTTClient(
        client_id=client,
        server=endpoint,
        port=8883,
        keepalive=4000,
        ssl=True,
        ssl_params=sslp)
    try:
        mqtt.connect()
        print("MQTT BROKER CONNECTION SUCCESSFUL: ", endpoint)
    except Exception as e:
        print("MQTT CONNECTION FAILED: {}".format(e))
        machine.reset()
    return mqtt

def mqtt_publish(client, topic=topic_pub, message='{"message": "esp32"}'):
    client.publish(topic, message)
    print("PUBLISHING MESSAGE: {} TO TOPIC: {}".format(message, topic))

print('Main.py -> Setup')
mqtt = mqtt_connect()

print('Main.py -> Loop')
startTime = utime.ticks_ms() - 10000 # try an initial read right away
while True:
    try:
        endTime = utime.ticks_ms()
        getGPS(gpsModule)
        timeDiff = endTime - startTime

        if(FIX_STATUS == True) and (timeDiff >= 10000):
            msg = ujson.dumps({
            "deviceId": device_id,
            "utctime": utctime,
            "latitude": latitude,
            "longitude": longitude,
            "satellites": satellites
            })
            mqtt_publish(client=mqtt, message=msg)
            startTime = utime.ticks_ms()
            FIX_STATUS = False
       
    except OSError as e:
        print("RECONNECT TO MQTT BROKER")
        mqtt = mqtt_connect()

    except Exception as e:
        print("A GENERAL ERROR HAS OCCURRED: {}".format(e))
        machine.reset()