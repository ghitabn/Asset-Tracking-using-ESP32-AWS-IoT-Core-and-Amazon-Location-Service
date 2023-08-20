# boot.py -- run on boot-up
import time
import network
import config

print('Boot.py -> Start')
print("CONNECTING TO WIFI...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
while not wlan.isconnected():
    wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
    time.sleep(5)
print("WIFI CONNECTION SUCCESSFUL: {}".format(wlan.ifconfig()))
print('Boot.py -> End')
