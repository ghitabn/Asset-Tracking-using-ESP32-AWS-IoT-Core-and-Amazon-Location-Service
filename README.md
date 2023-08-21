# 1. Description
Esp32-asset-tracker is an implementation of an asset tracker using physical devices (a GPS module connected to an ESP32 development board), AWS IoT Core and Amazon Location Service
Esp32-asset-tracker-viewer (optional): a web application to display current and historical device locations on a map, built using AWS Amplify 

# 2. AWS Architecture and schematics
- AWS architecture diagram: others\architecture.png
- Schematics: others\schematics.png

# 3. Hardware

- 1x DOIT ESP32 DEVKIT V1 (client devices) (https://www.amazon.ca/KeeYees-Development-Bluetooth-Microcontroller-ESP-WROOM-32/dp/B07QCP2451)
- 1x DHT11 (temperature and humidity sensor) (https://www.amazon.ca/dp/B078Y6323W)
- breadboard and wires

# 4. Esp32-asset-tracker step by step

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
	
# 5. Esp32-asset-tracker-viewer (optional) step by step

## 5.1. Deploy a backend environment on AWS Amplify

**Note.** Before you begin, make sure you have the following installed:

	- Node.js v14.x or later
	- npm v6.14.4 or later

- from a command prompt, get in the application folder

	```
	cd esp32-asset-tracker-viewer
	```
	
- install dependencies
	
	```
	npm install
	```
	
- install Amplify CLI
	
	```
	npm install -g @aws-amplify/cli
	```

- initialize the Amplify environment
	
	```
	amplify init

		Project information
		| Name: esp32assettrackview
		| Environment: dev
		| Default editor: Visual Studio Code
		| App type: javascript
		| Javascript framework: react
		| Source Directory Path: src
		| Distribution Directory Path: build
		| Build Command: npm.cmd run-script build
		| Start Command: npm.cmd run-script start

		? Initialize the project with the above configuration? Yes
		Using default provider  awscloudformation
		? Select the authentication method you want to use: AWS profile

		For more information on AWS Profiles, see:
		https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html

		? Please choose the profile you want to use ghitabn-poc
		Adding backend environment dev to AWS Amplify app: d1csrdcbrqaj48

		Deployment completed.
		Deployed root stack esp32assettrackview [ ======================================== ] 4/4
				amplify-esp32assettrackview-d… AWS::CloudFormation::Stack     CREATE_COMPLETE                Sat Aug 19 2023 22:08:35…
				DeploymentBucket               AWS::S3::Bucket                CREATE_COMPLETE                Sat Aug 19 2023 22:08:34…
				AuthRole                       AWS::IAM::Role                 CREATE_COMPLETE                Sat Aug 19 2023 22:08:25…
				UnauthRole                     AWS::IAM::Role                 CREATE_COMPLETE                Sat Aug 19 2023 22:08:25…

		√ Help improve Amplify CLI by sharing non sensitive configurations on failures (y/N) · no
		Deployment state saved successfully.
		√ Initialized provider successfully.
		✅ Initialized your environment successfully.

		Your project has been successfully initialized and connected to the cloud!

		Some next steps:
		"amplify status" will show you what you've added already and if it's locally configured or deployed
		"amplify add <category>" will allow you to add features like user login or a backend API
		"amplify push" will build all your local backend resources and provision it in the cloud
		"amplify console" to open the Amplify Console and view your project status
		"amplify publish" will build all your local backend and frontend resources (if you have hosting category added) and provision it in the cloud

		Pro tip:
		Try "amplify add api" to create a backend API and then "amplify push" to deploy everything
	```
	
- add Amazon Location Service resources

	```
	amplify add geo
	
		? Select which capability you want to add: Map (visualize the geospatial data)
		√ geo category resources require auth (Amazon Cognito). Do you want to add auth now? (Y/n) · yes
		Using service: Cognito, provided by: awscloudformation

		 The current configured provider is Amazon Cognito.

		 Do you want to use the default authentication and security configuration? Default configuration
		 Warning: you will not be able to edit these selections.
		 How do you want users to be able to sign in? Username
		 Do you want to configure advanced settings? No, I am done.
		✅ Successfully added auth resource esp32assettrackview0e231fc2 locally

		✅ Some next steps:
		"amplify push" will build all your local backend resources and provision it in the cloud
		"amplify publish" will build all your local backend and frontend resources (if you have hosting category added) and provision it in the cloud

		√ Provide a name for the Map: · esp32assettrackmap
		√ Who can access this Map? · Authorized and Guest users
		Available advanced settings:
		- Map style & Map data provider (default: Streets provided by Esri)

		√ Do you want to configure advanced settings? (y/N) · yes
		√ Specify the map style. Refer https://docs.aws.amazon.com/location-maps/latest/APIReference/API_MapConfiguration.html · Explore (data provided by HERE)
		⚠️ Specified resource configuration requires Cognito Identity Provider unauthenticated access but it is not enabled.
		✅ Successfully updated auth resource locally.
		✅ Successfully added resource esp32assettrackmap locally.

		✅ Next steps:
		"amplify push" builds all of your local backend resources and provisions them in the cloud
		"amplify publish" builds all of your local backend and front-end resources (if you added hosting category) and provisions them in the cloud
	```
	
- allow application to work with Amazon Location Service Trackers:
	
	```
	amplify override project
	
		✅ Successfully generated "override.ts" folder at C:\Users\ghitabn\Documents\esp\Projects\platformio\esp32-asset-tracker\esp32-asset-tracker-viewer\amplify\backend\awscloudformation
		√ Do you want to edit override.ts file now? (Y/n) · yes
		Edit the file in your editor: C:\Users\ghitabn\Documents\esp\Projects\platformio\esp32-asset-tracker\esp32-asset-tracker-viewer\amplify\backend\awscloudformation\override.ts
		? Press enter to continue
	```
	
	- update and save the policy used by Amazon Cognito to display the tracker position on the map by replacing the content of iot-asset-tracking-app\amplify\backend\awscloudformation\override.ts with:
	
		```
		import { AmplifyRootStackTemplate } from "@aws-amplify/cli-extensibility-helper";

		export function override(resources: AmplifyRootStackTemplate) {
		  resources.unauthRole.addOverride("Properties.Policies", [
			{
			  PolicyName: "trackerPolicy",
			  PolicyDocument: {
				Version: "2012-10-17",
				Statement: [
				  {
					Effect: "Allow",
					Action: ["geo:GetDevicePositionHistory"],
					Resource: {
					  "Fn::Sub":
						"arn:aws:geo:${AWS::Region}:${AWS::AccountId}:tracker/esp32-asset-01-tracker",
					},
				  },
				],
			  },
			},
		  ]);
		}
		```
	
- push Amplify configuration and create resources in the cloud
	
	```
	amplify push
	
		√ Successfully pulled backend environment dev from the cloud.

			Current Environment: dev

		┌──────────┬─────────────────────────────┬───────────┬───────────────────┐
		│ Category │ Resource name               │ Operation │ Provider plugin   │
		├──────────┼─────────────────────────────┼───────────┼───────────────────┤
		│ Auth     │ esp32assettrackview0e231fc2 │ Create    │ awscloudformation │
		├──────────┼─────────────────────────────┼───────────┼───────────────────┤
		│ Geo      │ esp32assettrackmap          │ Create    │ awscloudformation │
		└──────────┴─────────────────────────────┴───────────┴───────────────────┘
		√ Are you sure you want to continue? (Y/n) · yes

		Deployment completed.
		Deploying root stack esp32assettrackview [ =============--------------------------- ] 1/3
				amplify-esp32assettrackview-d… AWS::CloudFormation::Stack     UPDATE_IN_PROGRESS             Sat Aug 19 2023 22:20:23…
				authesp32assettrackview0e231f… AWS::CloudFormation::Stack     CREATE_COMPLETE                Sat Aug 19 2023 22:21:01…
				geoesp32assettrackmap          AWS::CloudFormation::Stack     CREATE_IN_PROGRESS             Sat Aug 19 2023 22:21:02…
		Deployed auth esp32assettrackview0e231fc2 [ ======================================== ] 6/6
				UserPoolClientRole             AWS::IAM::Role                 CREATE_IN_PROGRESS             Sat Aug 19 2023 22:20:43…
				UserPool                       AWS::Cognito::UserPool         CREATE_IN_PROGRESS             Sat Aug 19 2023 22:20:44…
		Deploying geo esp32assettrackmap [ ================================-------- ] 4/5
				CustomMapLambdaServiceRole4EE… AWS::IAM::Role                 CREATE_COMPLETE                Sat Aug 19 2023 22:21:17…
				CustomMapLambdaServiceRoleDef… AWS::IAM::Policy               CREATE_COMPLETE                Sat Aug 19 2023 22:21:35…
				CustomMapLambda51D5D430        AWS::Lambda::Function          CREATE_COMPLETE                Sat Aug 19 2023 22:21:50…
				CustomMap                      Custom::LambdaCallout          CREATE_COMPLETE                Sat Aug 19 2023 22:21:54…
				MapPolicy                      AWS::IAM::Policy               CREATE_IN_PROGRESS             Sat Aug 19 2023 22:21:55…

		Deployment state saved successfully.
	```
	
- launch the application
	
	```
	npm start
	```
	
- browse http://localhost:8080/

- add hosting

	```
	amplify hosting add
	
		√ Select the plugin module to execute · Amazon CloudFront and S3
		√ hosting bucket name · esp32assettrackview-20230819222706-hostingbucket
		Static webhosting is disabled for the hosting bucket when CloudFront Distribution is enabled.
		  Amazon CloudFront and S3
		You can now publish your app using the following command:
		Command: amplify publish
	

	amplify configure project
		Project information
		| Name: esp32assettrackview
		| Environment: dev
		| Default editor: Visual Studio Code
		| App type: javascript
		| Javascript framework: react
		| Source Directory Path: src
		| Distribution Directory Path: build
		| Build Command: npm.cmd run-script build
		| Start Command: npm.cmd run-script start

		AWS Profile setting
		| Selected profile: ghitabn-poc

		Advanced: Container-based deployments
		| Leverage container-based deployments: No

		? Which setting do you want to configure? Project information
		? Enter a name for the project esp32assettrackview
		? Choose your default editor: Visual Studio Code
		√ Choose the type of app that you're building · javascript
		Please tell us about your project
		? What javascript framework are you using react
		? Source Directory Path:  src
		? Distribution Directory Path: dist
		? Build Command:  npm.cmd run-script build
		? Start Command: npm.cmd run-script start
		Using default provider  awscloudformation

		Successfully made configuration changes to your project.
	
	amplify publish
	
		√ Successfully pulled backend environment dev from the cloud.

			Current Environment: dev

		┌──────────┬─────────────────────────────┬───────────┬───────────────────┐
		│ Category │ Resource name               │ Operation │ Provider plugin   │
		├──────────┼─────────────────────────────┼───────────┼───────────────────┤
		│ Hosting  │ S3AndCloudFront             │ Create    │ awscloudformation │
		├──────────┼─────────────────────────────┼───────────┼───────────────────┤
		│ Auth     │ esp32assettrackview0e231fc2 │ No Change │ awscloudformation │
		├──────────┼─────────────────────────────┼───────────┼───────────────────┤
		│ Geo      │ esp32assettrackmap          │ No Change │ awscloudformation │
		└──────────┴─────────────────────────────┴───────────┴───────────────────┘
		√ Are you sure you want to continue? (Y/n) · yes

		Deployment completed.
		Deploying root stack esp32assettrackview [ ==============================---------- ] 3/4
				amplify-esp32assettrackview-d… AWS::CloudFormation::Stack     UPDATE_IN_PROGRESS             Sat Aug 19 2023 22:33:59…
				hostingS3AndCloudFront         AWS::CloudFormation::Stack     CREATE_COMPLETE                Sat Aug 19 2023 22:38:39…
				authesp32assettrackview0e231f… AWS::CloudFormation::Stack     UPDATE_COMPLETE                Sat Aug 19 2023 22:34:03…
				geoesp32assettrackmap          AWS::CloudFormation::Stack     UPDATE_COMPLETE                Sat Aug 19 2023 22:34:05…
		Deployed hosting S3AndCloudFront [ ======================================== ] 4/4
				OriginAccessIdentity           AWS::CloudFront::CloudFrontOr… CREATE_COMPLETE                Sat Aug 19 2023 22:34:07…
				S3Bucket                       AWS::S3::Bucket                CREATE_COMPLETE                Sat Aug 19 2023 22:34:28…
				CloudFrontDistribution         AWS::CloudFront::Distribution  CREATE_COMPLETE                Sat Aug 19 2023 22:37:59…
		Deployment state saved successfully.

		Hosting endpoint: https://d26g9ivzxrshe0.cloudfront.net

		> esp32-asset-tracker-viewer@2.0.0 build
		> vite build

		vite v4.4.9 building for production...
		✓ 4306 modules transformed.
		dist/index.html                        0.70 kB │ gzip:   0.41 kB
		dist/assets/index-901af280.css       342.38 kB │ gzip:  35.69 kB
		dist/assets/mapbox-gl-5ab45547.js    767.60 kB │ gzip: 200.40 kB
		dist/assets/index-14849184.js      1,798.11 kB │ gzip: 482.35 kB

		(!) Some chunks are larger than 500 kBs after minification. Consider:
		- Using dynamic import() to code-split the application
		- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
		- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
		✓ built in 27.80s
		frontend build command exited with code 0
		Publish started for S3AndCloudFront
		√ Uploaded files successfully.
		Your app is published successfully.
		https://xxxxxxxxxxx.cloudfront.net
	```
- browse https://xxxxxxxxxxx.cloudfront.net

# 6. Cleanup

- esp32-asset-tracker:
	- delete EventBridge rule (geofenceiotassettrackingrule)
	- delete geofence (des-sources) from geofence collection (geofenceiotassettracking)
	- delete geofence collection (geofenceiotassettracking)
	- delete SNS topic (iotassettrackingsnstopic)
	- delete IoT rule (iot_asset_tracking_rule)
	- detach and delete IoT policy (MyClientDeviceESP-03-policy)
	- detach, deactivate and delete IoT certificate attached to the IoT thing (MyClientDeviceESP-03)
	- delete IoT thing (MyClientDeviceESP-03)

- esp32-asset-tracker-viewer
	- from a command prompt:

		```
		cd esp32-asset-tracker-viewer
		amplify delete
		```
