from notes import note_dict
import pyaudio
import numpy as np
import pickle
import time

p = pyaudio.PyAudio()

recording = pickle.load(open("recording.pkl", "rb"))

fs = 44100       # sampling rate, Hz, must be integer
volume = 0.5     # range [0.0, 1.0]

stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)

start_time = time.time()

for note in recording:


	# Calculate frequency and duration from recording
	note_freq = 0
	for freq in note_dict:
		if note_dict[freq] == note[0]:
			note_freq = freq
			break
	duration = note[4]
	print (note[0])


	# generate samples, note conversion to float32 array
	samples = (volume*np.sin(2*np.pi*np.arange(fs*duration)*note_freq/fs)).astype(np.float32).tobytes()

	# Delay until it is the correct time to play the note
	playback_time = time.time() - start_time
	note_start_time = note[3]
	# if playback_time < note_start_time:
		# time.sleep(note_start_time-playback_time)

	# play. May repeat with different volume values (if done interactively) 
	stream.write(samples)


stream.stop_stream()
stream.close()

p.terminate()