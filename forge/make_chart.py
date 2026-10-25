#your script loads the file with json.load and prints the number of beats and hits

#
import json
import sys

#kicks and snares get a small boost so hi-hats don't win every strength tie
BOOST = {"low": 1.3, "mid": 1.15, "high": 1.0}

#load in json to chart 
with open(sys.argv[1] if len(sys.argv) > 1 else "onsets.json") as f:
    chart = json.load(f)
#extracts bpm attribute from chart and assigns to bpm
bpm = chart["bpm"]
# 60000ms = 1 s => 60000 ms / bpm == ms/beats
#beats_ms = 60000 / bpm

beats_ms_array = chart["beats_ms"]

beats_ms_count = len(beats_ms_array)

onsets_array = chart["onsets"]

onsets_count = len(onsets_array)

print(beats_ms_count, onsets_count)

#for each beat, if hit - beat <= 100; add to hitsNearBeat
#a hit near beat is hit - beat <= 100ms

#check if onset is empty, expection handling if empty

#if not empty, itereate through onsets_array["t"]

#also try the half-beats, so there are more notes per second
grid = []
for a, b in zip(beats_ms_array, beats_ms_array[1:]):
    grid += [a, (a + b) // 2]
grid.append(beats_ms_array[-1])

notesToDisplay = []
same_lane_count = 0
prev_lane = 0
lane_switch = True
for beat in grid:
    hitsNearBeat = []
    for onset in onsets_array:
        if abs(beat - onset["t"]) <= 100:
            #add to list for that specific beat 
            hitsNearBeat.append(onset)
            #print(hitsNearBeat)
    #have at most one note per beat
    if hitsNearBeat:
        #copy of the max
        copy_of_max = max(hitsNearBeat, key=lambda x: x["strength"] * BOOST[x["band"]]).copy()
        copy_of_max["t"] = beat
        #low (kick) goes to lane 0 or 1. Switch between them each time, so the same key is not pressed over and over.
        #mid (snare) goes to lane 2.
        #high (hi-hat) goes to lane 3.
        
        if copy_of_max["band"] == "low":
            if lane_switch:
                copy_of_max["lane"] = 0
                same_lane_count = 1
                lane_switch = not lane_switch
            else:
                copy_of_max["lane"] = 1
                same_lane_count = 1
                lane_switch = not lane_switch
        elif copy_of_max["band"] == "mid":
            copy_of_max["lane"] = 2
        else:
            copy_of_max["lane"] = 3
    
        copy_of_max.pop("band")
        copy_of_max.pop("strength")
        
        if copy_of_max["lane"] == 2 or copy_of_max["lane"] == 3:
            if prev_lane == copy_of_max["lane"]:
                same_lane_count += 1
                if same_lane_count >= 4 and copy_of_max["lane"] == 2:
                    copy_of_max["lane"] = 3
                    same_lane_count = 1
                elif same_lane_count >= 4 and copy_of_max["lane"] == 3:
                    copy_of_max["lane"] = 2
                    same_lane_count = 1
            else:
                same_lane_count = 1
        prev_lane = copy_of_max["lane"]
        notesToDisplay.append(copy_of_max)
        
print(notesToDisplay)
#the game reads chart["notes"], so wrap the notes with the song info
out = {"title": "Under the River", "audio_path": "songs/under_the_river.mp3", "bpm": bpm, "notes": notesToDisplay}
with open("charts/under_the_river.json", "w") as f:
    json.dump(out, f, indent=2)
