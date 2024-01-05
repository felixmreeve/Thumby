from thumbyGraphics import display as disp

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


# ********** master debug flag **********
global DEBUG_MODE
DEBUG_MODE = False
# ***************************************


def set_font(w, h):
	disp.setFont(
		f"/lib/font{w}x{h}.bin",
		w, h,
		1)


def dprint(*args, **kwargs):
	global DEBUG_MODE
	if DEBUG_MODE:
		print(*args, **kwargs)