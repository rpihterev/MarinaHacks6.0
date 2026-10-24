import json
import numpy as np
import soundfile as sf

SR, BPM, BEATS, LEAD_IN_MS = 44100, 120, 128, 1000
beat_ms = 60000 / BPM
beats = [round(LEAD_IN_MS + i * beat_ms) for i in range(BEATS)]

audio = np.zeros(int(SR * (beats[-1] + 2000) / 1000), dtype=np.float32)
t = np.arange(int(0.03 * SR)) / SR
for b in beats:
    click = 0.5 * np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 80)
    start = int(b * SR / 1000)
    audio[start:start + len(click)] += click
sf.write("song.wav", audio, SR)

chart = {
    "title": "Metronome 120",
    "audio_path": "song.wav",
    "bpm": BPM,
    "notes": [{"t": b, "lane": i % 4} for i, b in enumerate(beats)],
}
with open("chart.json", "w") as f:
    json.dump(chart, f, indent=2)