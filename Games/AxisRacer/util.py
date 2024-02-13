from thumbyGraphics import display as disp
import time

global GAME_NAME
GAME_NAME = "AxisRacer"

global FONT_W, FONT_H
FONT_W = const(5)
FONT_H = const(7)
global MINI_FONT_W, MINI_FONT_H
MINI_FONT_W = const(3)
MINI_FONT_H = const(5)
global BIG_FONT_W, BIG_FONT_H
BIG_FONT_W = const(8)
BIG_FONT_H = const(8)

global SCREEN_W, SCREEN_H
SCREEN_W = const(72)
SCREEN_H = const(40)

global EMULATOR
try:
    import emulator
except ImportError:
    EMULATOR = False
else:
    EMULATOR = True

# ********** master debug flag **********
global DEBUG_MODE
DEBUG_MODE = False
# ***************************************
# extra debug flags
global DEBUG_ON_DEVICE, DEBUG_FIXED_SEED
DEBUG_ON_DEVICE = True
DEBUG_FIXED_SEED = False
if not EMULATOR:
    DEBUG_MODE = DEBUG_MODE and DEBUG_ON_DEVICE


def set_font(w, h):
    disp.setFont(
        f"/lib/font{w}x{h}.bin",
        w, h,
        1)


def dprint(*args, **kwargs):
    global DEBUG_MODE
    if DEBUG_MODE:
        print(*args, **kwargs)


def framerate():
    # creates a framerate generator object
    # where if called once per frame it will return fps
    old_time = time.ticks_us()
    yield 0
    while True:
        new_time = time.ticks_us()
        diff = time.ticks_diff(new_time, old_time)
        fps = round(1000000/diff)
        old_time = new_time
        yield fps


def new_seed():
    return time.ticks_cpu()