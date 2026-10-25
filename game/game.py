import json
import sys
from pathlib import Path

import pygame

from clock import Clock
from input_handler import get_lane_from_event

from input_handler import (
    get_lane_from_event,
    init_hardware,
    poll_hardware_input,
    close_hardware,
)


WIDTH, HEIGHT = 400, 600
LANE_WIDTH = WIDTH // 4
HIT_Y = 520
NOTE_SPEED = 0.4       # pixels per millisecond
HIT_WINDOW = 400       # milliseconds
PERFECT_WINDOW = 120
SONG_LENGTH_MS = 60000  # cut every song after 1 minute


def run_game():
    # Load the chart stored beside this module.
    #chart_path = Path(__file__).resolve().with_name("chart.json")

    #with open(chart_path, "r") as chart_file:
        #chart = json.load(chart_file)
    # python3 game.py charts/acdc.json (defaults to chart.json)
    chart = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "chart.json"))
    notes = [note for note in chart["notes"] if note["t"] < SONG_LENGTH_MS]
    for note in notes:
        note["status"] = "waiting"

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(chart.get("title", "Beat Forge"))
    frame_clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    score = 0

    last_result = ""

    # audio_path is relative to the project folder, look for it from here or from this file's folder
    for folder in (Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent):
        audio_path = folder / chart.get("audio_path", "")
        if audio_path.is_file():
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            break
    else:
        print("Audio not found:", chart.get("audio_path"))

    song_clock = Clock()
    song_clock.start()

    hits = 0
    misses = 0
    running = True
    state = "playing"
    ended_at = None

    while running:
        now_ms = song_clock.elapsed() * 1000

        # Always handle events so the window can be closed on any screen.
        poll_hardware_input()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # Only accept game input while playing.
            if state == "playing":
                lane = get_lane_from_event(event)

                if lane is not None:
                    possible_notes = [
                        note for note in notes
                        if note["status"] == "waiting"
                        and note["lane"] == lane
                        and abs(now_ms - note["t"]) <= HIT_WINDOW
                    ]

                    if possible_notes:
                        closest_note = min(
                            possible_notes,
                            key=lambda note: abs(now_ms - note["t"])
                        )
                        error_ms = abs(now_ms - closest_note["t"])
                        closest_note["status"] = "hit"
                        hits += 1

                        if error_ms <= PERFECT_WINDOW:
                            score += 100
                            last_result = "Perfect!"
                        else:
                            score += 50
                            last_result = "Okay"

        # Update missed notes only during gameplay.
        if state == "playing":
            for note in notes:
                if (
                    note["status"] == "waiting"
                    and now_ms > note["t"] + HIT_WINDOW
                ):
                    note["status"] = "missed"
                    misses += 1
                    last_result = "Miss"

            # Switch to the short ending pause when every note is done.
            if notes and all(note["status"] != "waiting" for note in notes):
                state = "ending"
                ended_at = now_ms
                pygame.mixer.music.fadeout(1000)

        # Show the results screen after the two-second pause.
        elif state == "ending" and now_ms - ended_at >= 1000:
            state = "ended"

        screen.fill((15, 15, 25))

        if state in ("playing", "ending"):
            # Gameplay screen: lanes and hit line.
            pygame.draw.line(
                screen, (220, 220, 220), (0, HIT_Y), (WIDTH, HIT_Y), 3
            )

            for lane_number in range(4):
                x = lane_number * LANE_WIDTH
                pygame.draw.line(
                    screen, (65, 65, 85), (x, 0), (x, HEIGHT), 2
                )

            score_text = font.render(
                f"Score: {score}", True, (255, 255, 255)
            )
            screen.blit(score_text, (10, 10))

            if last_result:
                result_text = font.render(
                    last_result, True, (255, 220, 80)
                )
                screen.blit(result_text, (10, 42))

            # Draw notes that are still waiting to be hit.
            for note in notes:
                if note["status"] != "waiting":
                    continue

                y = HIT_Y - (note["t"] - now_ms) * NOTE_SPEED

                if -20 <= y <= HEIGHT + 20:
                    x = note["lane"] * LANE_WIDTH + 10
                    pygame.draw.rect(
                        screen,
                        (90, 200, 255),
                        (x, y - 10, LANE_WIDTH - 20, 50),
                    )

        else:  # state == "ended"
            total_notes = hits + misses
            possible_score = total_notes * 100
            accuracy = (
                score / possible_score * 100 if possible_score > 0 else 0
            )

            if accuracy >= 90:
                stars = 5
            elif accuracy >= 80:
                stars = 4
            elif accuracy >= 70:
                stars = 3
            elif accuracy >= 60:
                stars = 2
            else:
                stars = 1

            title_text = font.render("Game Over", True, (255, 255, 255))
            score_text = font.render(
                f"Final score: {score}", True, (255, 255, 255)
            )
            accuracy_text = font.render(
                f"Accuracy: {accuracy:.1f}%", True, (255, 255, 255)
            )
            hits_text = font.render(
                f"Hits: {hits}   Misses: {misses}",
                True,
                (255, 255, 255),
            )


            star_y = 420
            star_size = 18
            star_gap = 14
            total_width = 5 * star_size + 4 * star_gap
            start_x = (WIDTH - total_width) // 2

            for i in range(5):
                color = (255, 220, 80) if i < stars else (90, 90, 100)
                x = start_x + i * (star_size + star_gap)
                pygame.draw.polygon(
                    screen,
                    color,
                    [
                        (x + 9, star_y),
                        (x + 12, star_y + 6),
                        (x + 18, star_y + 7),
                        (x + 13, star_y + 11),
                        (x + 15, star_y + 18),
                        (x + 9, star_y + 14),
                        (x + 3, star_y + 18),
                        (x + 5, star_y + 11),
                        (x, star_y + 7),
                        (x + 7, star_y + 6),
                    ],
                )

            screen.blit(
                title_text,
                (WIDTH // 2 - title_text.get_width() // 2, 200),
            )
            screen.blit(
                score_text,
                (WIDTH // 2 - score_text.get_width() // 2, 260),
            )
            screen.blit(
                accuracy_text,
                (WIDTH // 2 - accuracy_text.get_width() // 2, 310),
            )
            screen.blit(
                hits_text,
                (WIDTH // 2 - hits_text.get_width() // 2, 360),
            )

        pygame.display.flip()
        frame_clock.tick(120)

    print(f"Hits: {hits}, misses: {misses}")
    close_hardware()
    pygame.quit()


if __name__ == "__main__":
    run_game()
