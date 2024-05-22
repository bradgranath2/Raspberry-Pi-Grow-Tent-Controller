import RPi.GPIO as GPIO
import datetime
import time
import threading
#import Adafruit_DHT
import smbus
import sqlite3
import cv2
import numpy as np
import logging
import os

#define directories and filenames
WORKING_DIR = '/var/www/html/grow/'
IMG_SUBDIR = 'images/'
LOG_FILE = 'grow.log'
SQLITE_FILE = "grow.db"


# Define pin numbers
LIGHTS_PIN = 5
FAN_PIN = 6
HUMIDIFIER_PIN = 10
HEATER_PIN = 9
DEHUMIDIFIER_PIN = 7
PUMP_PIN = 8

# DHT22 Sensor //not connected in this instance
SENSOR_PIN = 17

# Define I2C bus number
IIC_BUS = 1

# Define the Cameras
CAM_ID_TOP = 0
CAM_ID_BOTTOM = 2
REBOOT_CAM_FAILURE_THRESHOLD=5
global rebootcount = 0

#set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename=WORKING_DIR + LOG_FILE,encoding='utf-8',level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger.debug("GrowController.py was started")

# Set up the database connection and cursor
try:
       con = sqlite3.connect(WORKING_DIR + SQLITE_FILE)
       con.row_factory =  sqlite3.Row
       cur = con.cursor()
       #print("Database connected")
       logger.debug("Database connected")
except Exception as e:
       #print("Err while trying to connect to the database :" + e)
       logger.error("Err while trying to connect to the database :" + str(e))

# Set up the Tables if this is a new instance
tablecreatequery = "CREATE TABLE IF NOT EXISTS environment (time TEXT, temp TEXT, humid TEXT, relaymask TEXT, picfile TEXT);"
cur.execute(tablecreatequery)
tablecreatequery = "CREATE TABLE IF NOT EXISTS settings ("
tablecreatequery += "lightson TEXT DEFAULT \"5:00AM\" , "
tablecreatequery += "lightsoff TEXT DEFAULT \"8:00PM\", "
tablecreatequery += "pumprun INTEGER DEFAULT 90, "
tablecreatequery += "pumpinter INTEGER DEFAULT 600, "
tablecreatequery += "fantemp INTEGER DEFAULT 85, "
tablecreatequery += "heattemp INTEGER DEFAULT 75, "
tablecreatequery += "fanhumid INTEGER DEFAULT 85, "
tablecreatequery += "humidhumid INTEGER DEFAULT 70, "
tablecreatequery += "dehumidhumid INTEGER DEFAULT 80, "
tablecreatequery += "lightsenab INTEGER DEFAULT 1, "
tablecreatequery += "fanenab INTEGER DEFAULT 1, "
tablecreatequery += "humidenab INTEGER DEFAULT 0, "
tablecreatequery += "heatenab INTEGER DEFAULT 1, "
tablecreatequery += "dehumidenab INTEGER DEFAULT 0, "
tablecreatequery += "pumpenab INTEGER DEFAULT 0, "
tablecreatequery += "sensortype TEXT DEFAULT \"SHT30\");"
cur.execute(tablecreatequery)
con.commit()


# populate the settings if it has never been done
cur.execute("SELECT * FROM settings;")
checkset = cur.fetchone()
if checkset is None:
   settingcreatequery = "INSERT INTO settings DEFAULT VALUES;"
   cur.execute(settingcreatequery)
   con.commit()
   #print("The settings table doesn't exist, so it was created!")
   logger.error("The settings table doesn't exist, so it was created!")

cur.execute("SELECT * FROM settings;")
settings = cur.fetchone()

# Define lights on and off times (in 12-hour format with AM/PM)
global lights_on_time
lights_on_time = datetime.datetime.strptime(settings['lightson'],'%I:%M%p').time()  # lights on time
global lights_off_time
lights_off_time = datetime.datetime.strptime(settings['lightsoff'],'%I:%M%p').time() # lights off time

# Define pump runtime and interval (in seconds) //pump not connected here
global pump_runtime
pump_runtime = settings['pumprun']  # pump runtime in seconds (90 seconds = 1.5 minutes)
global pump_interval
pump_interval = settings['pumpinter'] # pump interval in seconds (600 seconds = 10 minutes)

# Define temperature and humidity thresholds
global Temperature_Threshold_Fan
Temperature_Threshold_Fan = settings['fantemp']  # Will turn on Fan if temperature in Fahrenheit (F) is above this value.
global Temperature_Threshold_Heat
Temperature_Threshold_Heat = settings['heattemp']  # Will turn on Heat if temperature in Fahrenheit (F) is below this value.
global Humidity_Threshold_Fan
Humidity_Threshold_Fan = settings['fanhumid']  # Will turn on Fan once humidity is above this percentage (%) to try and move lower humidity air in. Disable this if humidity outside the tent/room is higher.
global Humidity_Threshold_Humidifier
Humidity_Threshold_Humidifier = settings['humidhumid']  # Will turn on Humidifier once humidity is below this percentage (%).
global Humidity_Threshold_Dehumidifier
Humidity_Threshold_Dehumidifier = settings['dehumidhumid'] # Will turn on Dehumidifier once humidity is above this percentage (%).

# Define appliance control flags (True: Enabled, False: Disabled)
global lights_enabled
lights_enabled = bool(settings['lightsenab'])  # Change to True or False
global fan_enabled
fan_enabled = bool(settings['fanenab'])  # Change to True or False
global humidifier_enabled
humidifier_enabled = bool(settings['humidenab'])  # Change to True or False
global heater_enabled
heater_enabled = bool(settings['heatenab'])  # Change to True or False
global dehumidifier_enabled
dehumidifier_enabled = bool(settings['dehumidenab'])  # Change to True or False
global pump_enabled
pump_enabled = bool(settings['pumpenab'])  # Change to True or False
global sensor_type
sensor_type = settings['sensortype'] #DHT22 or SHT30

logquery=''
#Load settings from database file")
for setting in settings:
  logquery += str(setting) + ", "
logger.debug("Settings Loaded from database file")
logger.debug(logquery);

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([LIGHTS_PIN, FAN_PIN, HUMIDIFIER_PIN, HEATER_PIN, DEHUMIDIFIER_PIN, PUMP_PIN], GPIO.OUT)

# Set up I2C bus
bus = smbus.SMBus(IIC_BUS)

# Function to update settings from the database
def update_settings():

    global lights_on_time
    global lights_off_time
    global pump_runtime
    global pump_interval
    global Temperature_Threshold_Fan
    global Temperature_Threshold_Heat
    global Humidity_Threshold_Fan
    global Humidity_Threshold_Humidifier
    global Humidity_Threshold_Dehumidifier
    global lights_enabled
    global fan_enabled
    global humidifier_enabled
    global heater_enabled
    global dehumidifier_enabled
    global pump_enabled
    global sensor_type

    cur.execute("SELECT * FROM settings;")
    upsettings = cur.fetchone()

    logquery=''
    for upsetting in upsettings:
      logquery += str(upsetting) + ", "
    logger.debug("The updated settings were fetched from the database")
    logger.debug(logquery)

    # Define lights on and off times (in 12-hour format with AM/PM)
    lights_on_time = datetime.datetime.strptime(upsettings['lightson'],'%I:%M%p').time()  # lights on time
    lights_off_time = datetime.datetime.strptime(upsettings['lightsoff'],'%I:%M%p').time() # lights off time

    # Define pump runtime and interval (in seconds) //pump not connected here
    pump_runtime = upsettings['pumprun']  # pump runtime in seconds (90 seconds = 1.5 minutes)
    pump_interval = upsettings['pumpinter'] # pump interval in seconds (600 seconds = 10 minutes)

    # Define temperature and humidity thresholds
    Temperature_Threshold_Fan = upsettings['fantemp']  # Will turn on Fan if temperature in Fahrenheit (F) is above this value.
    Temperature_Threshold_Heat = upsettings['heattemp']  # Will turn on Heat if temperature in Fahrenheit (F) is below this value.
    Humidity_Threshold_Fan = upsettings['fanhumid']  # Will turn on Fan once humidity is above this percentage (%) to try and move lower humidity >
    Humidity_Threshold_Humidifier = upsettings['humidhumid']  # Will turn on Humidifier once humidity is below this percentage (%).
    Humidity_Threshold_Dehumidifier = upsettings['dehumidhumid'] # Will turn on Dehumidifier once humidity is above this percentage (%).

    # Define appliance control flags (True: Enabled, False: Disabled)
    lights_enabled = bool(upsettings['lightsenab'])  # Change to True or False
    fan_enabled = bool(upsettings['fanenab'])  # Change to True or False
    humidifier_enabled = bool(upsettings['humidenab'])  # Change to True or False
    heater_enabled = bool(upsettings['heatenab'])  # Change to True or False
    dehumidifier_enabled = bool(upsettings['dehumidenab'])  # Change to True or False
    pump_enabled = bool(upsettings['pumpenab'])  # Change to True or False
    sensor_type = upsettings['sensortype'] #DHT22 or SHT30

    logger.debug("The update_settings function believes that: "+str(lights_on_time) + str(lights_off_time) + str(pump_runtime) + str(pump_interval) + str(Temperature_Threshold_Fan) + str(Temperature_Threshold_Heat) + str(Humidity_Threshold_Fan) + str(Humidity_Threshold_Humidifier) + str(Humidity_Threshold_Dehumidifier) + str(lights_enabled) + str(fan_enabled) + str(humidifier_enabled) + str(heater_enabled) + str(dehumidifier_enabled) + str(pump_enabled) + str(sensor_type))

# Function to print status with device and status information
def print_status(device, status):
    if device == "Lights" and not lights_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Fan" and not fan_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Humidifier" and not humidifier_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Dehumidifier" and not dehumidifier_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Heater" and not heater_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Pump" and not pump_enabled:
        print(f"{device}: \033[91mDisabled\033[0m")
    elif device == "Sensor" and not sensor_type == "DHT22" and not sensor_type == "SHT30":
        print(f"{device}: \033[91mIncompatible\033[0m")
    else:
        print(f"{device}: {status}")

# Function to create a binary mask for the state of the relays
def get_relay_mask():
    return str(GPIO.input(LIGHTS_PIN)) + str(GPIO.input(FAN_PIN)) + str(GPIO.input(HUMIDIFIER_PIN)) + str(GPIO.input(HEATER_PIN)) + str(GPIO.input(DEHUMIDIFIER_PIN)) + str(GPIO.input(PUMP_PIN))

# Function to read temperature from DHT22 sensor
def get_temperature():
    if sensor_type == "DHT22":
        sensor = Adafruit_DHT.DHT22
        humidity, temperature = Adafruit_DHT.read_retry(sensor, SENSOR_PIN)
        if temperature is not None:
            return temperature * 9/5.0 + 32  # Convert Celsius to Fahrenheit
        else:
            return None  # Return None if reading failed
    elif sensor_type == "SHT30":
        # SHT30 address, 0x44(68)
        # Send measurement command, 0x2C(44)
        # 0x06(06) High repeatability measurement
        bus.write_i2c_block_data(0x44, 0x2C, [0x06])

        time.sleep(1)

        # SHT30 address, 0x44(68)
        # Read data back from 0x00(00), 6 bytes
        # cTemp MSB, cTemp LSB, cTemp CRC, Humididty MSB, Humidity LSB, Humidity CRC

        #trying to read the reply
        data = bus.read_i2c_block_data(0x44, 0x00, 6)

        # Convert the data
        cTemp = ((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45
        fTemp = cTemp * 1.8 + 32
        return fTemp
    else:
        return None #Return none if sensor type is not set correctly

# Function to read humidity from DHT22 sensor
def get_humidity():
    if sensor_type == "DHT22":
        sensor = Adafruit_DHT.DHT22
        humidity, temperature = Adafruit_DHT.read_retry(sensor, SENSOR_PIN)
        if humidity is not None:
            return humidity
        else:
            return None  # Return None if reading failed
    elif sensor_type == "SHT30":
        # SHT30 address, 0x44(68)
        # Send measurement command, 0x2C(44)
        #		0x06(06)	High repeatability measurement
        bus.write_i2c_block_data(0x44, 0x2C, [0x06])

        time.sleep(0.5)

        # SHT30 address, 0x44(68)
        # Read data back from 0x00(00), 6 bytes
        # cTemp MSB, cTemp LSB, cTemp CRC, Humididty MSB, Humidity LSB, Humidity CRC
        data = bus.read_i2c_block_data(0x44, 0x00, 6)

        # Convert the data
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
        return humidity
    else:
        return None #Return none if sensor type is not set correctly

# Function to control the pump based on configured runtime and interval
def control_pump():
    while True:
        if pump_enabled:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            #print(f"Current Pump Status:\nPump: \033[92mON\033[0m for {pump_runtime} seconds\nTimestamp: {timestamp}\n")
            GPIO.output(PUMP_PIN, GPIO.HIGH)  # Turn on the pump relay
            time.sleep(pump_runtime)  # Run the pump for the specified duration
            GPIO.output(PUMP_PIN, GPIO.LOW)  # Turn off the pump relay
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            #print(f"Current Pump Status:\nPump: \033[93mOFF\033[0m for {pump_interval} seconds\nTimestamp: {timestamp}\n")
            time.sleep(pump_interval)  # Wait for the remaining interval
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            #print(f"Current Pump Status:\nPump: \033[91mOFF\033[0m\nTimestamp: {timestamp}\n")
            time.sleep(60)  # Wait for a minute if the pump is disabled

#Function to save a picture with the webcam
def snap_shot():
    global rebootcount
    img_name = 'noimage'
    top = snap_single(CAM_ID_TOP)
    bottom = snap_single(CAM_ID_BOTTOM)

    #glue both images together top to bottom
    try:
       both = np.concatenate((top,bottom), axis=0)

       img_name = "growbox_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"

       write_status = cv2.imwrite(WORKING_DIR + IMG_SUBDIR + img_name, both, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
       
       logger.debug(img_name)
       if write_status is True:
              logger.debug("Writing image successful")
       else:
              logger.error("Writing image Failed!")
              img_name = 'noimage'
    except Exception as e:
       logger.error("An error occured while trying to concatonate and write the images " + str(e))
       logger.error("Attempting reboot " + str(datetime.datetime.now().time()))

       #There is a bug in the RPi3B USB controller that cause it to disconnect from all devices. 
       #Currently only fixed by a reboot. So. Here we are. Find a way to remove this ASAP.
       rebootcount++
       if rebootcount = REBOOT_CAM_FAILURE_THRESHOLD
       os.system('sudo systemctl reboot -i')
    return img_name

#function to capture a single frame
def snap_single(index):
    # intialize the webcam
    snapped = False;
    cam = cv2.VideoCapture(index, cv2.CAP_V4L2)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    width = 2592
    height = 1944
    #img_name = "noimagecaptured"

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    #Webcam Initialized
    logger.debug("Webcam Initialized")

    # intializing frame 
    while not snapped:
       ret, frame = cam.read()

       if not ret:
          logger.error("Failed to capture frame")
          break

       # name the image files with a timestamp
       #img_name = "growbox_" + str(datetime.datetime.now().time()).replace(':','').replace('.','') + ".png"

       #flip and rotate the image
       frame = cv2.flip(frame,0)
       frame = cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
       snapped = True


    # release the camera
    cam.release()
    #print("Camera Released")
    logger.debug("Camera Released")
    return frame

# Print current settings
 #print("LIGHTS ON:" + str(lights_on_time))
 #print("LIGHTS OFF:" + str(lights_off_time))
 #print("TIMENOW: " + str(datetime.datetime.now().time()))
 #print("LIGHTS?" + str(bool(lights_enabled and lights_on_time <= datetime.datetime.now().time() < lights_off_time)))

# Start the pump control loop in a separate thread
pump_thread = threading.Thread(target=control_pump)
pump_thread.daemon = True  # Daemonize the thread to allow main program exit
pump_thread.start()

try:
   # Startup sequence to test relay functionality
   # print("\033[92m\nRaspberry Pi Grow Tent/Room Controller - Version 1.0\033[0m")
   # print("\033[94mDedicated to Emma. My dog who loved to smell flowers and eat vegetables right off the plants.\nMay she rest in peace.\n\033[0m")
   # print("OpenCV2 version: " + str(cv2.__version__))
   # time.sleep(5)
   # print("Startup Sequence: \033[93mTesting Relays...\033[0m")
   GPIO.output([LIGHTS_PIN, FAN_PIN, HUMIDIFIER_PIN, HEATER_PIN, DEHUMIDIFIER_PIN, PUMP_PIN], GPIO.HIGH)  # Turn on all relays except the pump
   time.sleep(1)  # Keep all relays on for 1 second
   GPIO.output([LIGHTS_PIN, FAN_PIN, HUMIDIFIER_PIN, HEATER_PIN, DEHUMIDIFIER_PIN, PUMP_PIN], GPIO.LOW)  # Turn off all relays except the pump
   # print("Startup Sequence: \033[92mRelay Test Complete.\033[0m\n")
   # print_status("Sensor: ", sensor_type)
   time.sleep(1)


   # Main loop for controlling relays based on thresholds and snapping timelapse pics from the webcam...
   while True:
        update_settings()
        logger.debug("The Main Loop believes that: "+str(lights_on_time) + str(lights_off_time) + str(pump_runtime) + str(pump_interval) + str(Temperature_Threshold_Fan) + str(Temperature_Threshold_Heat) + str(Humidity_Threshold_Fan) + str(Humidity_Threshold_Humidifier) + str(Humidity_Threshold_Dehumidifier) + str(lights_enabled) + str(fan_enabled) + str(humidifier_enabled) + str(heater_enabled) + str(dehumidifier_enabled) + str(pump_enabled) + str(sensor_type))
        # print("Current Status:")
        check_time = datetime.datetime.now().time()
        filename="nopicture"
        if lights_enabled and lights_on_time <= check_time < lights_off_time:
           GPIO.output(LIGHTS_PIN, GPIO.HIGH)
           # print_status("Lights", "\033[92mON\033[0m")
           # get a webcam snapshot
           #print("Attempting snapshot")
           logger.debug("Attempting snapshot")
           filename = snap_shot()

        else:
           GPIO.output(LIGHTS_PIN, GPIO.LOW)
           # print_status("Lights", "\033[93mOFF\033[0m")
        temperature = get_temperature()
        humidity = get_humidity()

        if fan_enabled and (temperature >= Temperature_Threshold_Fan or humidity >= Humidity_Threshold_Fan):
           GPIO.output(FAN_PIN, GPIO.HIGH)
           #print_status("Fan", "\033[92mON\033[0m")
        else:
            GPIO.output(FAN_PIN, GPIO.LOW)
            #print_status("Fan", "\033[93mOFF\033[0m")

        if humidifier_enabled and humidity < Humidity_Threshold_Humidifier:
           GPIO.output(HUMIDIFIER_PIN, GPIO.HIGH)
           #print_status("Humidifier", "\033[92mON\033[0m")
        else:
            GPIO.output(HUMIDIFIER_PIN, GPIO.LOW)
            #print_status("Humidifier", "\033[93mOFF\033[0m")

        if dehumidifier_enabled and humidity > Humidity_Threshold_Dehumidifier:
           GPIO.output(DEHUMIDIFIER_PIN, GPIO.HIGH)
           #print_status("Dehumidifier", "\033[92mON\033[0m")
        else:
           GPIO.output(DEHUMIDIFIER_PIN, GPIO.LOW)
           #print_status("Dehumidifier", "\033[93mOFF\033[0m")

        if heater_enabled and temperature < Temperature_Threshold_Heat:
           GPIO.output(HEATER_PIN, GPIO.HIGH)
           #print_status("Heater", "\033[92mON\033[0m")
        else:
            GPIO.output(HEATER_PIN, GPIO.LOW)
            #print_status("Heater", "\033[93mOFF\033[0m")

        #if not pump_enabled:
            #print_status("Pump", "\033[91mDisabled\033[0m")
        #else:
            #print_status("Pump", "\033[92mEnabled\033[0m")

        if temperature is not None:
            logger.debug("Temperature: " + str(temperature) + " vs " + str(Temperature_Threshold_Heat))

        if humidity is not None:
            logger.debug("Humidity: " + str(humidity) + " vs " + str(Humidity_Threshold_Fan))

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        #print(f"Timestamp: {timestamp}\n")
        logger.debug("Timestamp: " + timestamp)


        query = "INSERT INTO environment (time,temp,humid,relaymask,picfile) VALUES ('" + str(timestamp) + "', '" + str(get_temperature()) + "', '" + str(get_humidity()) + "', '" + str(get_relay_mask()) + "', '" + filename + "');"
        #print("Trying query: " + query)
        logger.debug("Trying query: " + query)
        cur.execute(query)
        con.commit()
        time.sleep(60)  # Adjust this sleep duration as needed

except KeyboardInterrupt:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    logger.error("The program was interuppted by the user at: " +  timestamp)
    GPIO.cleanup()
    con.close()
except Exception as e:
    #print(f"An error occurred: {str(e)}")
    logger.error("An error occured: " + str(e))
    GPIO.cleanup()
    con.close()
