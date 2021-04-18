from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime
import logging
import time
import RPi.GPIO as GPIO
import json

led_pin = 12
button_pin = 10
host = "" # Replace with your IoT Core endpoint 
rootCAPath = "certs/root-CA.crt" # Replace with AWS root CA cert path
certificatePath = "certs/<filename>.cert.pem" # Replace with the certification file path
privateKeyPath = "certs/<filename>.private.key" # Replace with the private key file path
port = 8883 #MQTT
clientId = "<CLIENT_ID>" # Replace with the client id
buttonTopic = "" # Replace with the mqtt topic for pub
ledTopic = "" # Rplace with the mqtt topic for sub

# Setup RPI GPIO
GPIO.setwarnings(False) # Ignore warning
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(led_pin, GPIO.OUT)

# General message notification callback
def customOnMessage(message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    try:
        payload = json.loads(message.payload)
        print(payload)
        blink_times = payload['blink']
        if isinstance(blink_times, int):
            blink(blink_times)
    except e:
        print(e)

# Suback callback
def customSubackCallback(mid, data):
    print("Received SUBACK packet id: ")
    print(mid)
    print("Granted QoS: ")
    print(data)
    print("++++++++++++++\n\n")


# Puback callback
def customPubackCallback(mid):
    print("Received PUBACK packet id: ")
    print(mid)
    print("++++++++++++++\n\n")

# Button callback
def button_callback(channel):
    payload = {
        "ts": time.time(),
        "button": True
    }
    pub_message = json.dumps(payload)
    print(pub_message)
    myAWSIoTMQTTClient.publishAsync(buttonTopic, pub_message, 1, ackCallback=customPubackCallback)

# Blink
def blink(times):
    for i in range(times):
        print("Blink")
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(led_pin, GPIO.LOW)
        time.sleep(0.5)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myAWSIoTMQTTClient.onMessage = customOnMessage

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
# Note that we are not putting a message callback here. We are using the general message notification callback.
myAWSIoTMQTTClient.subscribeAsync(ledTopic, 1, ackCallback=customSubackCallback)
time.sleep(2)

GPIO.add_event_detect(10,GPIO.RISING,callback=button_callback)

message = input("Press return key to quit\n")

GPIO.cleanup()
