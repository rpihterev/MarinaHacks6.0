

from pathlib import Path
import json
import sys

#the project folder that holds forge/, songs/ and charts/
ROOT = Path(__file__).resolve().parent.parent

#kicks and snares get a small boost so hi-hats don't win every strength tie
BOOST = {"low": 1.3, "mid": 1.15, "high": 1.0}


def make_chart(chart, title, audio_path, min_strength=0.0, half_beats=True):
    #extracts bpm attribute from chart and assigns to bpm
    bpm = chart["bpm"]
    # 60000ms = 1 s => 60000 ms / bpm == ms/beats
    #beats_ms = 60000 / bpm

    beats_ms_array = chart["beats_ms"]

    #skip faint hits, raising min_strength makes the chart easier
    onsets_array = [onset for onset in chart["onsets"] if onset["strength"] >= min_strength]

    #for each beat, if hit - beat <= 100; add to hitsNearBeat
    #a hit near beat is hit - beat <= 100ms

    #also try the half-beats, so there are more notes per second
    grid = beats_ms_array
    if half_beats:
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

    #the game reads chart["notes"], so wrap the notes with the song info
    return {"title": title, "audio_path": audio_path, "bpm": bpm, "notes": notesToDisplay}


def save_chart(out, output_path=None):
    #default: charts/<song>.json in the project folder, where the song select screen looks
    if output_path is None:
        output_path = ROOT / "charts" / (Path(out["audio_path"]).stem + ".json")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {len(out['notes'])} notes to {output_path}")


if __name__ == "__main__":
    #load in json to chart
    with open(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / "onsets.json") as f:
        chart = json.load(f)
    print(len(chart["beats_ms"]), len(chart["onsets"]))
    save_chart(make_chart(chart, chart["title"], chart["audio_path"]))
