import sys
import json

import librosa
import numpy as np

HOP = 256
MIN_STRENGTH = 0.2   # skip hits weaker than 20% of the band's loudest
SNAP_MS = 50         # snap to the grid if within this many ms


def listen(song_path):
    #load audio
    waveform, sample_rate = librosa.load(song_path, sr=22050, mono=True)
    duration_ms = len(waveform) / sample_rate * 1000

    #finding tempo and beats, marking beats with miliseconds
    tempo, beat_times = librosa.beat.beat_track(y=waveform, sr=sample_rate, units="time")
    beat_times = np.round(beat_times * 1000).astype(int)
    if len(beat_times) < 2:
        raise ValueError("not enough beats found in " + str(song_path))

    onsets = {
      "bpm": round(float(np.atleast_1d(tempo)[0]), 1),
      "beats_ms": beat_times.tolist(),
      "onsets": []
    }

    #separating drums from vocals/other
    _, waveform_drums = librosa.effects.hpss(waveform)

    S = librosa.power_to_db(librosa.feature.melspectrogram(y=waveform_drums, sr=sample_rate, n_mels=128, hop_length=HOP))
    freqs = librosa.mel_frequencies(n_mels=128, fmax=sample_rate/2)

    low_freqs = (freqs>1) & (freqs<150)
    mid_freqs = (freqs>200) & (freqs<2500)
    high_freqs = (freqs>5000)

    bands = {"low": S[low_freqs], "mid": S[mid_freqs], "high": S[high_freqs]}

    #onset envelope per band: how much louder each band got since the last frame.
    #a kick makes "low" spike, a snare makes "mid" spike, a hi-hat makes "high" spike
    envelopes = {}
    for name, S_band in bands.items():
        env = librosa.onset.onset_strength(S=S_band, sr=sample_rate, hop_length=HOP)
        envelopes[name] = env / (env.max() + 1e-9)   #scale to 0..1 so bands are comparable (+tiny so a silent band can't divide by 0)

    #peak picking per band: a frame counts as a hit if it is the biggest value
    #in a small window AND clearly above the local average (delta).
    #wait=8 frames (~93 ms) stops one drum hit from being counted twice
    for name, env in envelopes.items():
        peaks = librosa.util.peak_pick(env, pre_max=3, post_max=3, pre_avg=20, post_avg=20, delta=0.08, wait=8)
        times_ms = librosa.frames_to_time(peaks, sr=sample_rate, hop_length=HOP) * 1000
        for t, p in zip(times_ms, peaks):
            if env[p] < MIN_STRENGTH:   #skip faint bumps (bass rumble, bleed from other drums)
                continue
            onsets["onsets"].append({"t": int(round(t)), "band": name, "strength": round(float(env[p]), 3)})

    #snap to the beat grid: split every beat into 4 steps, and move each hit to the
    #nearest step if it is within SNAP_MS. this fixes detection being a few ms off
    #(the low band tends to fire ~25 ms early) so notes feel exactly on the beat
    grid = [b + (nxt - b) * k / 4 for b, nxt in zip(beat_times[:-1], beat_times[1:]) for k in range(4)]
    grid = np.array(grid + [beat_times[-1]])
    for o in onsets["onsets"]:
        nearest = grid[np.abs(grid - o["t"]).argmin()]
        if abs(nearest - o["t"]) <= SNAP_MS:
            o["t"] = int(round(nearest))

    #snapping can land two hits of the same band on the same time, keep only the first
    seen = set()
    unique = []
    for o in onsets["onsets"]:
        if (o["t"], o["band"]) not in seen:
            seen.add((o["t"], o["band"]))
            unique.append(o)
    onsets["onsets"] = unique

    #all bands mixed together in time order
    onsets["onsets"].sort(key=lambda o: o["t"])

    onsets["duration_ms"] = int(duration_ms)
    return onsets, envelopes


def plot(onsets, envelopes, out_path="onsets.png"):
    #sanity check picture: each band's envelope with its detected hits as dots
    #(first 10 seconds so you can actually see them)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    beat_times = np.array(onsets["beats_ms"])
    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    for ax, (name, env) in zip(axes, envelopes.items()):
        t = librosa.times_like(env, sr=22050, hop_length=HOP)
        ax.plot(t, env, linewidth=0.8)
        hits = [o for o in onsets["onsets"] if o["band"] == name]
        ax.plot([o["t"]/1000 for o in hits], [o["strength"] for o in hits], "ro", markersize=4)
        ax.vlines(beat_times/1000, 0, 1, colors="gray", alpha=0.3)
        ax.set_ylabel(name)
    axes[0].set_xlim(0, 10)
    axes[-1].set_xlabel("seconds (gray lines = beats)")
    plt.tight_layout()
    plt.savefig(out_path)


if __name__ == "__main__":
    #usage: python listen.py song.mp3 [--plot]
    song = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "songs/under_the_river.mp3"
    try:
        onsets, envelopes = listen(song)
    except ValueError as error:
        sys.exit(str(error))

    #writing json file
    with open("onsets.json", "w") as f:
        json.dump(onsets, f, indent=4)

    for name in envelopes:
        count = sum(o["band"] == name for o in onsets["onsets"])
        print(f"{name}: {count} onsets")
    print(f"total: {len(onsets['onsets'])} onsets in {onsets['duration_ms']/1000:.1f} s, bpm {onsets['bpm']}")

    if "--plot" in sys.argv:
        plot(onsets, envelopes)
        print("wrote onsets.png")

