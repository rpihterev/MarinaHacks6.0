#your script loads the file with json.load and prints the number of beats and hits

#
import json
import time
from operator import attrgetter

#load in json to chart 
chart = json.load(open("onsets2.json"))
#extracts bpm attribute from chart and assigns to bpm
bpm = chart["bpm"]
# 60000ms = 1 s => 60000 ms / bpm == ms/beats
#beats_ms = 60000 / bpm

beats_ms_array = chart["beats_ms"]

beats_ms_count = len(beats_ms_array)

onsets_array = chart["onsets"]

onsets_count = len(onsets_array)

print(beats_ms_count, onsets_count)

next_index = 0

#for each beat, if hit - beat <= 100; add to hitsNearBeat
#a hit near beat is hit - beat <= 100ms

#check if onset is empty, expection handling if empty

#if not empty, itereate through onsets_array["t"]

notesToDisplay = []
same_lane_count = 0
prev_lane = 0
lane_switch = True
for beat in beats_ms_array:
    hitsNearBeat = []
    for onset in onsets_array:
        if abs(beat - onset["t"]) <= 100:
            #add to list for that specific beat 
            hitsNearBeat.append(onset)
            #print(hitsNearBeat)
    #have at most one note per beat
    if hitsNearBeat:
        #copy of the max
        copy_of_max = max(hitsNearBeat, key=lambda x: x["strength"]).copy()
        copy_of_max["t"] = beat
        #low (kick) goes to lane 0 or 1. Switch between them each time, so the same key is not pressed over and over.
        #mid (snare) goes to lane 2.
        #high (hi-hat) goes to lane 3.
        
        if copy_of_max["band"] == "low":
            if lane_switch:
                copy_of_max["lane"] = 0
                lane_switch = not lane_switch
            else:
                copy_of_max["lane"] = 1
                lane_switch = not lane_switch
        elif copy_of_max["band"] == "mid":
            copy_of_max["lane"] = 2
        else:
            copy_of_max["lane"] = 3
    prev_lane = copy_of_max["lane"]        
    #want to check same_lane_count,         
    if(prev_lane != 0):
            prev_lane = copy_of_max["lane"]
        else:
            if(prev_lane == copy_of_max["lane"]):
                same_lane_count += 1
        if(same_lane_count >= 4){
            
        }
        #REMOVE----------
        copy_of_max.pop("band")
        copy_of_max.pop("strength")
        notesToDisplay.append(copy_of_max)
        
print(notesToDisplay)
with open("data2.json", "w") as f:
    json.dump(notesToDisplay, f)

        
            
            






