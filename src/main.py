from machine import Pin, PWM, time_pulse_us
from umqtt.simple import MQTTClient
from utime import localtime
import time
import network
import ssl 
import urequests
import ujson
import math
import gc

# Reading the Credentials File
file = open("sensitiveInfo.json", 'r')
fileData = ujson.load(file)
file.close()

# Declaration of Pins for the Motor Driver and Motor Frequency Setup
in3 = Pin(0, Pin.OUT)
in4 = Pin(1, Pin.OUT)
enb = PWM(Pin(5))
enb.freq(2000)

# Tank characteristics declaration
tank_radius = 2.4 
tank_height = 7.9

# Declaration of sound speed and pulse duration in microseconds
SOUND_SPEED = 340
TRIG_PULSE_DURATION_US = 10

# Trigger/Echo Pins for Tank A's HC sensor
trig_pin_A = Pin(14, Pin.OUT) 
echo_pin_A = Pin(15, Pin.IN)

# Trigger/Echo Pins for Tank B's HC sensor
trig_pin_B = Pin(18, Pin.OUT) 
echo_pin_B = Pin(19, Pin.IN)

# Pump LED declaration
pump_led = Pin(16, Pin.OUT)

# LEDs for Tank A
red_led_A = Pin(13, Pin.OUT)
yellow_led_A = Pin(12, Pin.OUT)
green_led_A = Pin(11, Pin.OUT)

# LEDs for Tank B
red_led_B = Pin(17, Pin.OUT)
yellow_led_B = Pin(20, Pin.OUT)
green_led_B = Pin(21, Pin.OUT)

# Function to connect to the specified network
def connect():
    # Attempting to access the network
    wlan = network.WLAN(network.STA_IF)  
    wlan.active(True)  
    wlan.connect(fileData["SSID"], fileData["Password"])
    # Loop that waits until the connection is established
    while wlan.isconnected() == False:
        print('Waiting for connection')   
        time.sleep(1)
    # Notify that the connection was successfully established
    return True

# Function to connect to the HiveMQ Broker
def setupHive():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_NONE
    mqttClient = MQTTClient(client_id=fileData["ClientID"],
                            server=fileData["MQTT"],
                            port=fileData["Port"],
                            user=fileData["User"],
                            password=fileData["Pass"],
                            ssl=context)
    mqttClient.connect()
    return mqttClient

# Function to measure distance sensed by the HC-SR04 sensor
def measureDistances(trig_pin, echo_pin):
    # Signal preparation
    trig_pin.value(0)
    time.sleep_us(5)
    # Activate Trigger pin
    trig_pin.value(1)
    time.sleep_us(TRIG_PULSE_DURATION_US)
    trig_pin.value(0)
    # Measure and convert reflection time to distance
    ultrason_duration = time_pulse_us(echo_pin, 1, 30000) 
    distance_cm = SOUND_SPEED * ultrason_duration / 20000
    # Calculate the real tank height
    height = tank_height - (distance_cm - 0.7)
    # Return the real height
    return height

# Function to calculate the volume of a tank
def calculateVolume(height):
    # Tank volume calculation (cm^3)
    volume = height * math.pi * pow(tank_radius, 2)
    # Return the volume
    return volume

# Function to calculate volumes of both tanks
def calculateVolumes():
    # Get liquid heights of the tanks
    height_A = measureDistances(trig_pin_A, echo_pin_A)
    height_B = measureDistances(trig_pin_B, echo_pin_B)
    # Calculate current volumes
    volume_A = calculateVolume(height_A)
    volume_B = calculateVolume(height_B)
    # Array of volumes
    volumes = [volume_A, volume_B]
    print("Volume A: " + str(volumes[0]) + " Volume B: " + str(volumes[1]))
    # Return the volumes
    return volumes
    
# Function to manage LED states according to calculated volumes
def manageLEDs(red_led, yellow_led, green_led, volume):
    # Red Light (Full Tank)
    if volume >= 133.9:
        red_led.value(1)
        yellow_led.value(0)
        green_led.value(0)
        # Return tank state
        return "Red"
    # Yellow Light (Tank above Half)
    elif volume >= 80.5 and volume < 133.9:
        red_led.value(0)
        yellow_led.value(1)
        green_led.value(0)
        # Return tank state
        return "Yellow"
    # Green Light (Tank below Half)
    elif volume < 80.5:
        red_led.value(0)
        yellow_led.value(0)
        green_led.value(1)
        # Return tank state
        return "Green"

# Function to control the pump according to volumes
def controlPump(client, volumes):
    # Liquid balancing variable
    balanced = False
    # Check if Tank A volume is greater than Tank B by 10 or more ml
    if volumes[0] >= volumes[1] + 10:
        # Publish pump activation info
        postPumpData(client, "ON")
        # Use 100% of pump capacity
        enb.duty_u16(65535)
        # Loop to balance liquids
        while balanced == False:
            # Blink pump LED
            pump_led.value(1)
            time.sleep(0.5)
            pump_led.value(0)
            # Pump direction
            in3.low()
            in4.high()
            # Get volumes during balancing
            current_volumes = calculateVolumes()
            # Stop pump when volume difference is 5 ml or less
            if abs(current_volumes[0] - current_volumes[1]) <= 5:
                balanced = True
        # Publish pump deactivation info
        postPumpData(client, "OFF")
        # Turn off the pump
        enb.duty_u16(0)
        in3.low()
    # Check if Tank B volume is greater than Tank A by 10 or more ml
    if volumes[1] >= volumes[0] + 10:
        # Publish pump activation info
        postPumpData(client, "ON")
        # Use 100% of pump capacity
        enb.duty_u16(65535)
        # Loop to balance liquids
        while balanced == False:
            # Blink pump LED
            pump_led.value(1)
            time.sleep(0.5)
            pump_led.value(0)
            # Pump direction
            in3.high()
            in4.low()
            # Get volumes during balancing
            current_volumes = calculateVolumes()
            # Stop pump when volume difference is 5 ml or less
            if abs(current_volumes[0] - current_volumes[1]) <= 5: 
                balanced = True
        # Publish pump deactivation info
        postPumpData(client, "OFF")
        # Turn off the pump
        enb.duty_u16(0)
        in4.low()

# Function to publish information about a tank
def postTankData(client, tank, volume, state, timeStamp):
    # Prepare the message
    msg = ujson.dumps({
        "Tank": tank,
        "Volume": volume,
        "State": state,
        "Time": timeStamp})
    # Publish message to the topic 
    client.publish("topic/tank", msg)
    # Prepare and execute the HTTP request
    headers = {
        "Authorization": fileData["Bearer"],
        "Content-Type": "application/json"
    }
    req = urequests.post(
        'http://theorify.mooo.com/api/tanquesPosts',
        headers=headers,
        data=ujson.dumps({"Tank": str(tank), "Volume": float(volume), "State": str(state), "Time": str(timeStamp)})
    )

# Function to publish information about the pump
def postPumpData(client, state):
    # Prepare the message
    msg = ujson.dumps({
        "State": state,
        "Time": getTime()
    })
    # Publish message to the topic 
    client.publish("topic/pump", msg)
    # Prepare and execute the HTTP request
    headers = {
        "Authorization": fileData["Bearer"],
        "Content-Type": "application/json"
    }
    req = urequests.post(
        'http://theorify.mooo.com/api/bombaPosts',
        headers=headers,
        data=ujson.dumps({"State": state, "Time": getTime()})
    )
    
# Function to get and return the current date/time
def getTime():
    # Prepare timestamp
    dateTimeObj = localtime()
    Dyear, Dmonth, Dday, Dhour, Dmin, Dsec, Dweekday, Dyearday = (dateTimeObj)
    timestamp = "{}/{}/{} {}:{}:{}"
    # Return current date/time
    return timestamp.format(Dyear, Dmonth, Dday, Dhour, Dmin, Dsec)

# Main function
def main():
    # Attempt to connect to the Internet
    netStatus = connect()
    if netStatus == True:
        client = setupHive()
        while True:
            # Get current tank volumes
            volumes = calculateVolumes()
            # Manage tank LEDs and get their states
            state_A = manageLEDs(red_led_A, yellow_led_A, green_led_A, volumes[0])
            state_B = manageLEDs(red_led_B, yellow_led_B, green_led_B, volumes[1])
            # Publish tank information
            postTankData(client, "A", volumes[0], state_A, getTime())
            postTankData(client, "B", volumes[1], state_B, getTime())
            # Manage the pump according to volumes
            controlPump(client, volumes)
            # Clean up using garbage collector
            gc.collect()
            # Sleep for 5 seconds
            time.sleep(5)
    
# Call the main function
main()
