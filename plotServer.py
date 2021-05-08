import socket
import json
import time
import numpy as np
import matplotlib.pyplot as plt
import sys
import keyboard
import pickle
from notes import note_dict

# Parameters for UDP Server
localIP = "192.168.1.12"
localPort = 20001
bufferSize = 8912

# Since the ADC outputs at around 2400hz, the maximum we can resolve
# is a frequency of 1200 hz
MAX_FRQ = 1200

# Function that averages an array of numbers
def average (arr):
    sum = 0
    for val in arr:
        sum += val

    return sum/len(arr)

# Start UDP server
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))
UDPServerSocket.settimeout(0.1)

# Flags set on keypresses
start_recording_flag = False
pause_recording_flag = False
delete_recording_flag = False

# Loop variables
recording_start_time = 0
recording_duration = 0
recording_flag = False
recording = []


# Control Menu
print ("Controls:")
print ("Start recording: r")
print ("Pause recording: p")
print ("Delete recording: d")
print ("Save recording: s")
print ("Quit program: q")

while(True):

    if keyboard.is_pressed('r') and start_recording_flag is False:
        start_recording_flag = True
        print("\nRecording Started")

    if keyboard.is_pressed('p') and pause_recording_flag is False:
        pause_recording_flag = True
        print("\nRecording Paused")

    if keyboard.is_pressed('d') and delete_recording_flag is False:
        delete_recording_flag = True
        print("\nRecording Deleted")

    if keyboard.is_pressed('s'):
        # Save recording to a file
        pickle.dump(recording, open("recording.pkl", "wb"))
        print(recording)
        print("Recording Saved")
        time.sleep(0.25)

    if keyboard.is_pressed('q'):
        print("\nExiting Program")
        exit(0)



    # Recieve UDP packet from client. Has a timeout of 0.1 if nothing is sent.
    bytesAddressPair = [None,None]
    try:
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    except socket.timeout:
        continue

    # Read UDP packet
    message = bytesAddressPair[0]
    res_dict = json.loads(message.decode('utf-8'))
    time_recv = res_dict["timeStamp"]

    # Handle flags set by keypresses    
    if start_recording_flag:
        start_recording_flag = False
        pause_recording_flag = False
        recording_flag = True
        recording_start_time = time_recv - recording_duration

    if pause_recording_flag:
        recording_flag = False

    if delete_recording_flag:
        recording_duration = 0
        recording = []
        delete_recording_flag = False

    # Prepare UDP JSON packet for plotting
    sample_data = res_dict["sample_data"]
    duration = res_dict["duration"]
    sample_count = res_dict["sample_count"]
    period = duration/sample_count
    time_data = np.arange(0, duration, period)   #generate a array of time values fr$
    time_data = time_data[-sample_count:]

    # Clear plots
    plt.clf()

    # Plot samples in the time domain
    plt.subplot(211)
    plt.plot(time_data, sample_data)
    plt.title("Overview")
    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.ylim(-2000,2000)

    # Calculate FFT of samples
    sample_fft = np.fft.fft(sample_data)/sample_count
    k = np.arange(sample_count)
    frq = k/duration
    max_frq_idx = int(MAX_FRQ*duration)
    frq = frq[range(max_frq_idx)]
    sample_fft = sample_fft[range(max_frq_idx)]

    # Plot samples in frequency domain
    plt.subplot(212)
    plt.plot(frq, abs(sample_fft))
    plt.title("Sample FFT")
    plt.xlabel("Frequency")
    plt.ylabel("Amplitude")

    # Draws a frame of the plot. Used so the plots can be redrawn on every packet
    plt.draw()
    plt.pause(0.0001)

    # Threshold amplitude of FFT spike to be considered a note
    NOTE_THRESHOLD = 30
    currPeakFreqArr = []
    currPeakAmpArr = []
    currNotes = []

    # Iterate through samples to find the peaks. These peaks are the frequencies
    # that are being played.
    for i in range (0, len(sample_fft)):

        # If the peak is above the threshold, record the frequency and amplitude
        if (abs(sample_fft[i]) > NOTE_THRESHOLD):
            currPeakFreqArr.append(frq[i])
            currPeakAmpArr.append(abs(sample_fft[i]))

        # If we have finished recording a peak, average the frequency of the points
        # that were above the threshold and find the maximum amplitude.
        else:
            if (len(currPeakFreqArr) > 0):
                avgPeakFreq = average(currPeakFreqArr)
                maxPeakAmp = max(currPeakAmpArr)
                currNotes.append([None,avgPeakFreq,maxPeakAmp])
                currPeakFreqArr = []
                currPeakAmpArr = []


    # Find the closest note that coresponds with the measured frequency
    for note in currNotes:
        currNote_freq = note[1]

        min_delta = 1000
        closest_freq = 0
        # Iterate through dictionary of notes and frequencies, and
        # find the note with the closest frequency to the measured frequency
        for note_freq in note_dict.keys():
            curr_delta = abs(currNote_freq - note_freq)
            if (min_delta > curr_delta):
                min_delta = curr_delta
                closest_freq = note_freq

        note[0] = note_dict[closest_freq]
        note[1] = closest_freq

    # Find the note with the largest amplitude. Because each note has harmonic
    # resonant frequencies, it is difficult to determine if multiple notes are 
    # being played. For now, I will just choose the note with teh largest amplitude.
    currNote = [None, 0, 0]
    for note in currNotes:
        if currNote[2] < note[2]:
            currNote = note

    # Add the time since the recording started and the duration of the note to 
    # the list that holds note information
    currNote.append(time_recv - recording_start_time)
    currNote.append(duration)

    if recording_flag:
        # Recalculate recording duration every time a new note is added
        recording_duration = time_recv - recording_start_time
        if len(recording) == 0:
            # Start the recording with the first note
            recording.append(currNote)
        else:
            if (currNote[0] is not None) and (recording[-1][0] != currNote[0]):
                # Add new note if it is different and valid (not None)
                recording.append(currNote)
            else:
                # Increase note duration if note is repeated
                recording[-1][4] = recording_duration - recording[-1][3] + duration

    print (currNote)


