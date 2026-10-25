
import argparse  # Read the song filename and optional tuning settings.
import json  # Save the Listener's analysis in the shared JSON format.
from pathlib import Path  # Resolve filenames independently of the launch directory.

from make_chart import ROOT, make_chart, save_chart  # Reuse chart generation instead of duplicating it.


def main():  # Coordinate the Listener and Chart maker.
    parser = argparse.ArgumentParser(description=__doc__)  # Provide usage instructions through --help.
    parser.add_argument("song")  # e.g. songs/acdc.mp3, relative to the project folder.
    parser.add_argument("--output")  # Default: charts/<song>.json, where the song select screen looks.
    parser.add_argument("--title")  # Default: the title listen.py makes from the filename.
    parser.add_argument("--min-strength", type=float, default=0.0)  # Forward the faint-hit filter to the chart maker.
    parser.add_argument("--beats-only", action="store_true")  # Allow a simpler chart without half-beats.
    args = parser.parse_args()  # Collect the supplied settings.
    if not 0 <= args.min_strength <= 1:  # Validate the tuning setting before expensive audio analysis.
        parser.error("--min-strength must be between 0 and 1")  # Explain how to fix the invalid setting.
    song_path = Path(args.song)  # Convert the filename into a path object.
    if not song_path.is_absolute():  # Interpret relative song paths from the project root.
        song_path = ROOT / song_path  # Locate the song beside forge/, or in a specified subfolder.
    song_path = song_path.resolve()  # Make the actual audio location unambiguous.
    if not song_path.is_file():  # Catch a missing audio file before loading the Listener's dependencies.
        parser.error(f"Song not found: {song_path}")  # Display the exact missing location.
    from listen import listen  # Use your teammate's existing listen(song_path) function in forge/listen.py.
    print(f"Analyzing {song_path.name}...")  # Audio analysis can take time; show that work has started.
    analysis, _ = listen(str(song_path))  # Receive the analysis dictionary and ignore plotting envelopes.
    onsets_path = Path(__file__).resolve().parent / "onsets.json"  # Preserve the agreed intermediate file for inspection or reuse.
    with onsets_path.open("w", encoding="utf-8") as file:  # Open the intermediate file and close it afterward.
        json.dump(analysis, file, indent=2, allow_nan=False)  # Save the Listener's complete results.
        file.write("\n")  # End the JSON file cleanly.
    audio_path = song_path.as_posix()  # Absolute paths also work when audio is outside the project.
    if song_path.is_relative_to(ROOT):  # Prefer a portable relative path for songs inside the project.
        audio_path = song_path.relative_to(ROOT).as_posix()  # Store forward slashes for game compatibility.
    title = args.title or analysis["title"]  # Fall back to the filename-based title.
    chart = make_chart(analysis, title, audio_path, args.min_strength, not args.beats_only)  # Build the chart.
    save_chart(chart, args.output)  # Validate and save; errors stop the run instead of reporting success.


if __name__ == "__main__":  # Avoid starting analysis if another script imports this module.
    main()  # Run the complete song-to-chart pipeline.

