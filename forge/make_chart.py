import argparse  # Read optional settings supplied when starting this script.
import json  # Convert between Python dictionaries and JSON files.
from pathlib import Path  # Build paths that work on different operating systems.

ROOT = Path(__file__).resolve().parent.parent  # The project folder containing forge/.
BOOST = {"low": 1.3, "mid": 1.15, "high": 1.0}  # Favor kicks and snares when choosing hits.


def make_chart(analysis, title, audio_path, min_strength=0.0, half_beats=True):  # Reusable chart builder.
    beats = sorted(set(analysis["beats_ms"]))  # Put beats in order and remove duplicate times.
    onsets = analysis["onsets"]  # Keep the original hit list unchanged.
    grid = list(beats)  # Start with one possible note position per beat.
    if half_beats:  # Allow the denser rhythm used in your current script.
        for a, b in zip(beats, beats[1:]):  # Visit consecutive pairs of beats.
            grid.append((a + b) // 2)  # Add the integer midpoint between each pair.
    grid = sorted(set(grid))  # Sort the full grid and remove duplicate positions.
    notes = []  # Store only notes that pass the spacing rule.
    used_onsets = set()  # Track selected hit indices so one hit cannot create two notes.
    lane_switch = True  # Make the first accepted kick use lane 0.
    prev_lane = None  # There is no previous lane before the first note.
    same_lane_count = 0  # Start with no consecutive lane repetitions.

    for beat in grid:  # Process possible note positions in time order.
        if notes and beat - notes[-1]["t"] < 150:  # Step 6: compare against the last accepted note.
            continue  # Drop positions less than 150 ms later, including duplicate times.
        hits_near_beat = []  # Collect candidates for this position only.
        for index, onset in enumerate(onsets):  # Give each original hit a stable identifier.
            if index in used_onsets:  # Check whether this hit already supplied a note.
                continue  # Do not reuse the same detected hit.
            if onset["strength"] < min_strength:  # Step 7: filter faint hits using raw strength.
                continue  # Raising min_strength reduces chart density.
            if abs(beat - onset["t"]) <= 100:  # Accept hits at most 100 ms from this position.
                hits_near_beat.append((index, onset))  # Retain the hit and its identifier.
        if not hits_near_beat:  # No usable hit supports this grid position.
            continue  # Skip this position instead of making an unsupported note.
        index, strongest = max(  # Select one candidate without modifying the original hit.
            hits_near_beat,  # Search only the hits collected for this position.
            key=lambda pair: pair[1]["strength"] * BOOST[pair[1]["band"]],  # Compare boosted strength.
        )  # Finish selecting the strongest candidate.
        if strongest["band"] == "low":  # Kicks alternate between the two left lanes.
            lane = 0 if lane_switch else 1  # Choose the next kick lane.
            lane_switch = not lane_switch  # Remember the opposite lane for the next accepted kick.
        elif strongest["band"] == "mid":  # Snares normally use lane 2.
            lane = 2  # Assign the snare lane.
        else:  # The remaining supported band is high.
            lane = 3  # Hi-hats normally use lane 3.
        same_lane_count = same_lane_count + 1 if lane == prev_lane else 1  # Count this lane's run.
        if same_lane_count >= 4:  # Step 5: break a run before its fourth identical note.
            lane = lane - 1 if lane == 3 else lane + 1  # Move to an adjacent valid lane.
            same_lane_count = 1  # The moved note starts a new run.
        prev_lane = lane  # Remember the lane actually assigned.
        notes.append({"t": beat, "lane": lane})  # Store only the two fields required by the game.
        used_onsets.add(index)  # Mark this hit as consumed only after accepting its note.

    validate_notes(notes)  # Step 6: independently check the finished chart before returning it.
    return {  # Wrap the notes in the metadata expected by the game.
        "title": title,  # The title shown to players.
        "audio_path": audio_path,  # The matching audio file; paths are relative to the project root.
        "bpm": analysis["bpm"],  # Preserve the Listener's tempo estimate.
        "notes": notes,  # Supply the sorted, filtered playable notes.
    }  # Finish the chart dictionary.


def validate_notes(notes):  # Step 6: reject an invalid chart rather than silently saving it.
    previous_time = None  # Allow the first note at any nonnegative time.
    for note in notes:  # Examine every output note.
        if type(note["t"]) is not int or note["t"] < 0:  # Require whole milliseconds from song start.
            raise ValueError("Each note time must be a nonnegative integer.")  # Explain the bad time.
        if type(note["lane"]) is not int or note["lane"] not in range(4):  # Require lanes 0–3.
            raise ValueError("Each lane must be an integer from 0 to 3.")  # Explain the bad lane.
        if previous_time is not None and note["t"] - previous_time < 150:  # Also catches unsorted/duplicate times.
            raise ValueError("Notes must be sorted, unique, and at least 150 ms apart.")  # Explain the violation.
        previous_time = note["t"]  # Compare the next note with this accepted timestamp.


def save_chart(chart, output_path):  # Step 6: save a complete chart in the agreed JSON format.
    validate_notes(chart["notes"])  # Check again in case a caller changed the notes.
    output_path = Path(output_path)  # Accept either a path object or a string.
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Create output folders when needed.
    with output_path.open("w", encoding="utf-8") as file:  # Open the destination and close it automatically.
        json.dump(chart, file, indent=2, allow_nan=False)  # Write readable JSON with standard double quotes.
        file.write("\n")  # End the file with a newline.
    print(f"Saved {len(chart['notes'])} notes to {output_path}")  # Confirm the result and its location.
    if not chart["notes"]:  # A beats-only Listener file is valid but cannot supply drum notes yet.
        print("No notes: check whether onsets is empty or the strength threshold is too high.")  # Explain emptiness.


def main():  # Run this entry point when generating a chart from an existing analysis file.
    parser = argparse.ArgumentParser(description=__doc__)  # Describe this script in --help.
    parser.add_argument("input", nargs="?", default=str(ROOT / "onsets.json"))  # Optional analysis filename.
    parser.add_argument("--output", default=str(ROOT / "chart.json"))  # Match your current game's filename.
    parser.add_argument("--title", default="Under the River")  # Allow another song title.
    parser.add_argument("--audio", default="drmseq-under-the-river-179464.mp3")  # Match the audio in your repo.
    parser.add_argument("--min-strength", type=float, default=0.0)  # Step 7: try 0.3 to remove faint hits.
    parser.add_argument("--beats-only", action="store_true")  # Step 7: omit half-beats for an easier chart.
    args = parser.parse_args()  # Read the chosen settings.
    if not 0 <= args.min_strength <= 1:  # Raw onset strengths use the range zero through one.
        parser.error("--min-strength must be between 0 and 1")  # Stop and explain an invalid setting.
    with Path(args.input).open(encoding="utf-8") as file:  # Open the Listener's analysis file.
        analysis = json.load(file)  # Load its BPM, beat times, and detected hits.
    print(f"{len(analysis['beats_ms'])} beats, {len(analysis['onsets'])} hits")  # Keep your step-one check.
    chart = make_chart(analysis, args.title, args.audio, args.min_strength, not args.beats_only)  # Generate notes.
    save_chart(chart, args.output)  # Validate and write the finished game chart.


if __name__ == "__main__":  # Run the command only when executed directly, not when imported by run.py.
    main()  # Start the existing-analysis workflow.
