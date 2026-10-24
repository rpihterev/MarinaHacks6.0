import librosa
import matplotlib.pyplot as plt
import numpy as np
import json





#load audio
waveform, sample_rate = librosa.load("drmseq-under-the-river-179464.mp3", sr=22050, mono=True)

tempo, beat_times = librosa.beat.beat_track(y=waveform, sr=sample_rate, units="time")
beat_times = np.round(beat_times * 1000).astype(int)
tempo = tempo.tolist()

onsets = {
  "bpm": tempo[0],
  "beats_ms": beat_times.tolist(),
  "onsets": []
}

with open("onsets.json", "w") as f:
    json.dump(onsets, f, indent=4)