import os

import pygame


# Two layouts so either hand position works.
LANE_KEYS = {
    pygame.K_d: 0, pygame.K_f: 1, pygame.K_j: 2, pygame.K_k: 3,
    pygame.K_LEFT: 0, pygame.K_DOWN: 1, pygame.K_UP: 2, pygame.K_RIGHT: 3,
}

# Event we post when an external controller sends a hit.
HARDWARE_HIT = pygame.event.custom_type()

_serial = None
_serial_buffer = b""
_joysticks = []


def init_hardware(port=None, baud=9600):
    """Optional controllers. Safe to skip: the game works with keyboard only.

    - Gamepads: buttons 0-3 map to lanes 0-3.
    - Serial (e.g. Arduino): set port or the BEATFORGE_SERIAL env var. The
      board should print one lane number (0-3) per line when a pad is hit.
      Needs `pip install pyserial`.
    """
    global _serial

    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        _joysticks.append(pygame.joystick.Joystick(i))

    port = port or os.environ.get("BEATFORGE_SERIAL")
    if port:
        try:
            import serial
            _serial = serial.Serial(port, baud, timeout=0)
            print(f"Hardware connected on {port}")
        except Exception as error:
            print(f"No hardware on {port} ({error}), using keyboard only")
            _serial = None


def poll_hardware_input():
    """Turn serial lines into HARDWARE_HIT events. Does nothing without hardware."""
    global _serial_buffer

    if _serial is None:
        return

    try:
        _serial_buffer += _serial.read(_serial.in_waiting or 1)
    except Exception:
        return

    while b"\n" in _serial_buffer:
        line, _serial_buffer = _serial_buffer.split(b"\n", 1)
        text = line.strip().decode(errors="ignore")
        if text.isdigit() and 0 <= int(text) <= 3:
            pygame.event.post(pygame.event.Event(HARDWARE_HIT, lane=int(text)))


def get_lane_from_event(event):
    """Return lane 0-3 for a hit, or None if the event isn't a hit."""
    if event.type == pygame.KEYDOWN:
        return LANE_KEYS.get(event.key)

    if event.type == pygame.JOYBUTTONDOWN and event.button < 4:
        return event.button

    if event.type == HARDWARE_HIT:
        return event.lane

    return None


def close_hardware():
    global _serial

    if _serial is not None:
        _serial.close()
        _serial = None
    _joysticks.clear()
