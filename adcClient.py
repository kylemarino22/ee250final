import numpy as np
import time
import board
import busio
import socket
import json
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Setup I2C bus for ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)

# Set ADC settings:
# Continuous measurement
# PGA set to 16
# Data Rate at 3300 hz
ads.mode = ADS.Mode.CONTINUOUS
ads.gain = 16
ads.data_rate = 3300

# Constants used in the code
SAMPLE_COUNT = 3000
SAMPLE_THRESHOLD = 100
SAMPLE_DURATION = 0.1

# UDP Settings. Server is on port 20001 with IP 192.168.1.12
serverAddressPort   = ("192.168.1.12", 20001)
bufferSize          = 2048

# Main loop of script
while True:

    # Each loop of the while loop results in a packet of samples being sent
    # Initialize arrays for the current packet
    start_time = time.time()
    udp_json = {}
    sample_data = []
    sample_count = 0

    # Record until 1 ms has passed, sends 10 udp packets/sec
    # Even though the sensor is set at 3300hz, the true data rate in python is
    # around 2400hz, which is still good enough for this projct. 
    while (time.time() - start_time < SAMPLE_DURATION):
        # Read ADC and append it to the sample_data list
        sample_data.append (ads.read(0,is_differential=True))
        sample_count += 1

        # Take the absolute average of the first 20 samples to determine
        # if any notes are being played. We don't want to send packets 
        # when nothing is being played.
        if (sample_count == 20):
            sum = 0
            for sample in sample_data:
                sum += abs(sample)
            avg = sum/20

            # If the absolute average is too low, discard the recorded data
            # and start again. This throws away samples that are taken when
            # nothing is being played
            if (avg < SAMPLE_THRESHOLD):
                sample_data = []
                sample_count = 0
                start_time = time.time()

    # Put data into a json object to be sent over UDP
    udp_json["sample_data"] = sample_data
    udp_json["duration"] = SAMPLE_DURATION
    udp_json["sample_count"] = sample_count
    udp_json["timeStamp"] = time.time()
    bytesToSend = json.dumps(udp_json).encode('utf-8')

    # Send the json object over UDP
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
