import json
import time
import pygame

LANE_KEYS = {pygame.K_d: 0, pygame.K_f: 1, pygame.K_j: 2, pygame.K_k: 3}
WIDTH, HEIGHT, LANE_W = 400, 600, 100
HIT_Y = 520            # where notes should be hit
SPEED = 0.4            # pixels per ms
HIT_WINDOW = 120       # ms either side that still counts
OFFSET_MS = 0          # calibration, tune later

chart = json.load(open("chart.json"))
notes = chart["notes"]
next_i = 0             # one note at a time, so one pointer is enough
hits = misses = 0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.mixer.music.load(chart["audio_path"])
pygame.mixer.music.play()
start = time.perf_counter()

running = True
while running:
    now = (time.perf_counter() - start) * 1000 - OFFSET_MS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key in LANE_KEYS and next_i < len(notes):
            note = notes[next_i]
            if LANE_KEYS[event.key] == note["lane"] and abs(now - note["t"]) <= HIT_WINDOW:
                hits += 1
                next_i += 1

    while next_i < len(notes) and now > notes[next_i]["t"] + HIT_WINDOW:
        misses += 1
        next_i += 1

    if next_i >= len(notes) and now > notes[-1]["t"] + 2000:
        running = False

    screen.fill((15, 15, 25))
    pygame.draw.line(screen, (200, 200, 200), (0, HIT_Y), (WIDTH, HIT_Y), 3)
    for note in notes[next_i:]:
        if note["t"] - now > HEIGHT / SPEED:
            break
        y = HIT_Y - (note["t"] - now) * SPEED
        pygame.draw.rect(screen, (90, 200, 255), (note["lane"] * LANE_W + 10, y - 10, LANE_W - 20, 20))
    pygame.display.flip()
    clock.tick(120)

print(f"hits {hits}, misses {misses}")
pygame.quit()