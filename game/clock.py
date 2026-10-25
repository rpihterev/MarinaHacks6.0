import time

import pygame


class Clock:
    """Song clock in seconds.

    Runs on time.perf_counter, and while pygame.mixer.music is playing it
    nudges itself back onto the music position so notes stay in sync even
    if the audio starts late or the game stutters.
    """

    RESYNC_THRESHOLD = 0.05   # seconds of drift before we snap to the music

    def __init__(self, offset_ms=0):
        # offset_ms > 0 makes notes arrive later (use it to tune audio lag).
        self.offset = offset_ms / 1000
        self._start = None

    def start(self):
        self._start = time.perf_counter()

    def elapsed(self):
        if self._start is None:
            return 0.0

        now = time.perf_counter() - self._start

        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            # get_pos is ms since music.play(), but only updates once per
            # audio buffer, so we only correct on bigger drift.
            music_pos = pygame.mixer.music.get_pos() / 1000
            if music_pos >= 0 and abs(music_pos - now) > self.RESYNC_THRESHOLD:
                self._start -= music_pos - now
                now = music_pos

        return now - self.offset