==================================================
esp32-asset-tracker
==================================================

# 1. Description

# 2. AWS Architecture and schematics diagrams
- AWS architecture diagram: others\architecture.png
- Schematics: others\schematics.png

# 3. Hardware

- 1x DOIT ESP32 DEVKIT V1 (client devices) (https://www.amazon.ca/KeeYees-Development-Bluetooth-Microcontroller-ESP-WROOM-32/dp/B07QCP2451)
- 1x DHT11 (temperature and humidity sensor) (https://www.amazon.ca/dp/B078Y6323W)
- breadboard and wires

# 4. Steps

**Note.** The deployment has been tested in us-east-2 region, where all required AWS services are available.

## 4.1. Create an AWS IoT thing for the IoT device (ESP32) 

- Navigate to the AWS IoT console -> All devices -> Things and click Create things
- Select Create single thing and click Next
- Enter Thing name and click Next
	- thing name:	esp32-asset-01
- Select Auto-generate a new certificate and click Next
- Click Create policy
	- Name: esp32-asset-01-policy
	- Policy document -> select JSON and replace policy document with:

		```
		{
			"Version": "2012-10-17",
			"Statement": [
				{
					"Effect": "Allow",
					"Action": "iot:Connect",
					"Resource": "*"
				},
				{
					"Effect": "Allow",
					"Action": "iot:Publish",
					"Resource": "*"
				},
				{
					"Effect": "Allow",
					"Action": "iot:Receive",
					"Resource": "*"
				},
				{
					"Effect": "Allow",
					"Action": "iot:Subscribe",
					"Resource": "*"
				}
			]
		}
		```

	- click Create
- Return to the Create thing tab select the new created policy (esp32-asset-01-policy) and click Create thing
- Download certificates to the right folder and rename them:
	- Amazon root: esp32-asset-tracker/flash/AmazonRootCA1.pem
	- Device certificate: esp32-asset-tracker/flash/esp32-asset-01-certificate.pem.crt
	- Private key: esp32-asset-tracker/flash/esp32-asset-01-private.pem.key
	- Public key: esp32-asset-tracker/flash/esp32-asset-01-public.pem.key
- Click Done
		
## 4.2. Flash the ESP32 with MicroPython firmware
	
**Note.** The steps below are specific to a Windows local machine. Similar steps can be executed for Linux or MAC.

- Install CP210x USB to UART Bridge VCP Drivers on the local machine: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=overview
- Install Python 3.x: https://www.python.org/downloads/windows/
- Install esptool and MicroPython stubs (cmd or PowerShell): pip install esptool pip install -U micropython-esp32-stubs
- Download the latest MycroPython firmware from: https://micropython.org/download/esp32/ (i.e. esp32-20220618-v1.19.1.bin)
- Identify the COM port in use by the ESP32 board, using Device Manager (i.e. COM4)
- Erase the flash (cmd or PowerShell): python -m esptool --chip esp32 --port COM4 erase_flash
- Install the firmware (cmd or PowerShell): 
	python -m esptool --chip esp32 --port COM4 --baud 460800 
	write_flash -z 0x1000 esp32-20220618-v1.19.1.bin 
	Note. Depending on the ESP32 board, erasing/writing operations (steps 6 and 7 above) 
	might require to manually put the board Firmware Download boot mode by long pressing 
	the BOOT button. https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html

## 4.3. Configure the development environment on the local machine and upload the code to the IoT device (ESP32)

- Install VS Code and Pymakr to execute code on a EPS32, directly from a Visual Studio app: https://docs.pycom.io/gettingstarted/software/vscode/
- Update WIFI_SSID, WIFI_PASS and MQTT_HOST in the configuration file (esp32-asset-tracker/config.py)
	- MQTT topic: clients/esp32-asset-01/gps-01
- Upload the code to the IoT device (ESP32)
	References
		- NMEA sentences: https://www.rfwireless-world.com/Terminology/GPS-sentences-or-NMEA-sentences.html
		- Formatt coordinates: https://support.google.com/maps/answer/18539?hl=en&co=GENIE.Platform%3DDesktop

## 4.4. Test MQTT communication between the IoT device (ESP32) and AWS IoT Core
- Power on the IoT device (ESP32)
- Use putty to establish a serial connection to the IoT device
- Check messages in the serial console
- Use AWS IoT MQTT test client to test subscription to the configured topic (clients/esp32-asset-01/gps-01) - example: 

	```
	{
	  "deviceId": "esp32-asset-01",
	  "utctime": "23:56:46",
	  "latitude": "45.491667",
	  "longitude": -73.80668,
	  "satellites": "10"
	}
		```
## 4.5. Create an IoT rule to relay messages to Amazon Location

- Navigate to the AWS IoT core dashboard -> Message routing -> Rules
- Click on Create rule
- Rule name: esp32_asset_01_rule_01
- Click Next
- SQL Statement: SELECT * FROM 'clients/esp32-asset-01/gps-01'
- Rule actions: 
	- Action1: Location
- Create tracker: 
		- name: esp32-asset-01-tracker
		- position filtering method: Accuracy-based filtering
		- check Enable EventBridge events
	- DeviceId: esp32-asset-01
	- Latitude: ${latitude}
	- Longitude: ${longitude}
	- Timestamp value: ${timestamp()}
	- Timestamp units: MILLISECONDS
	- IAM role: 
		- Create new role:
			- name: esp32_asset_01_rule_01-role
	- Click Next
	- Click Create

## 4.6. Create a SNS topic and subscription

- Navigate to Amazon SNS -> Topics
- Click Create topic
	- Type: Standard
	- Name: esp32-asset-01-tracker-topic
- Click Create topic
- Click Create subscription
	- Select a protocol and an endpoint
- Click Create subscription
	
## 4.7. Create a geofence
### 4.7.1. Create a Geofence collection
- Navigate to Amazon Location -> Geofence collections -> click Create geofence collection
	- name: esp32-asset-01-geofencecolllection
	- EventBridge rule with CloudWatch as a target: No, do not create a rule
- Click Create geofence collection
- Navigate to Amazon Location -> Trackers -> esp32-asset-01-tracker
	- Click Link geofence collection -> select esp32-asset-01-geofencecollection

### 4.7.2. Create a geofence
- use https://geojson.io/ to create a GeoJSON file (or use the example esp32-asset-tracker/others/des-sources.json)
- Navigate to Amazon Location -> Geofence collections -> click esp32-asset-01-geofencecolllection -> click Add geofences -> drop a GeoJSON file -> click Add geofences

### 4.8. Create an EventBridge rule for Location Geofence events (Enter/Exit)
- Navigate to Amazon EventBridge
- Select EventBridge rule
- Click Create rule
- Name: esp32-asset-01-tracker-geofence-rule
- Type: rule with an event pattern
- Event source: AWS events or EventBridge partner events
- Creation method: Use pattern form
	- Event source: AWS services
	- AWS service: Amazon Location Service
	- Event type: Location Geofence Event
	- Event type Specification 1: Any type
- Click Next
- Target 1:
	- Type: AWS service
	- Select a target: SNS topic
	- Topic: esp32-asset-01-tracker-topic
- Click Next twice and click Create rule

### 4.9. Test geofence events notifications

- Use AWS IoT MQTT test client to test publish to the configured topic (clients/esp32-asset-01/gps-01):
	- topic: clients/esp32-asset-01/gps-01
	- Examples of dummy MQTT messages to force events:
		- Enter event (location inside the geofence):
			
			```
			{
				"deviceId": "esp32-asset-01",
				"utctime": "120000",
				"latitude": "45.491905",
				"longitude": "-73.806302",
				"satellites": "10"
			}
			```

		- Exit event (location outside the geofence):
			
			```
			{
				"deviceId": "esp32-asset-01",
				"utctime": "120000",
				"latitude": "45.492777",
				"longitude": "-73.804838",
				"satellites": "10"
			}
			```
				
**Note.** Useful commands for debugging/cleaning Location tracker data - use CloudShell from the Amazon Location (top right menu bar near the Region).

- get last position:

	```
	aws location get-device-position --device-id esp32-asset-01 --tracker-name esp32-asset-01-tracker
	```

- get history:

	```
	aws location get-device-position-history --device-id esp32-asset-01 --tracker-name esp32-asset-01-tracker
	```

- clear history:
	
	```
	aws location batch-delete-device-position-history --device-ids esp32-asset-01 --tracker-name esp32-asset-01-tracker 
	```