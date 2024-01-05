import sys
import thumbyButton as butt
from thumbyGraphics import display as disp

import util
# get button state
# including query all just pressed
# TODO: don't duplicate consts
global FONT_W, FONT_H
FONT_W = const(5)
FONT_H = const(7)
global MINI_FONT_W, MINI_FONT_H
MINI_FONT_W = const(3)
MINI_FONT_H = const(5)
global BIG_FONT_W, BIG_FONT_H
BIG_FONT_W = const(8)
BIG_FONT_H = const(8)

global KEYS
KEYS = [
	butt.buttonA,
	butt.buttonB,
	butt.buttonU,
	butt.buttonD,
	butt.buttonL,
	butt.buttonR
]

global INPUTS
INPUTS = {}

def updateInput():
	global KEYS, INPUTS
	for key in KEYS:
		if key.justPressed():
			INPUTS[key] = 2
		elif key.pressed():
			INPUTS[key] = 1
		else:
			INPUTS[key] = 0

def justPressed(key):
	return INPUTS[key] == 2

def pressed(key):
	return INPUTS[KEY] > 0

def tapDir():
	x, y = 0, 0
	if justPressed(butt.buttonU):
		y -= 1
	elif justPressed(butt.buttonD):
		y += 1
	if justPressed(butt.buttonL):
		x -= 1
	elif justPressed(butt.buttonR):
		x += 1
	return x, y

# keyboard input
def keyboard():
	global FONT_W, FONT_H
	disp.setFPS(30)
	util.set_font(FONT_W, FONT_H)
	msg = ""
	letters = [
		"QWERTYUIOP",
		"ASDFGHJKL ",
		"ZXCVBNM   "
	]
	enter_x = len(letters[-1]) - 1
	enter_y = len(letters)-1
	
	enter = thumbySprite.Sprite(
		5, 7,
		# BITMAP: width: 10, height: 7
		bytearray([16,56,124,16,31,111,71,3,111,96]),
		enter_x, enter_y, -1
	)
	
	sel_x = 0
	sel_y = 0
	while True:
		# input
		updateInput()
		if justPressed(butt.buttonA):
			if enter_pos:
				# done - return msg
				break
			msg += letters[y][x].lower()
		if justPressed(butt.buttonB):
			msg = ""
			break
		vx, vy = tapDir()
		sel_x += vx
		sel_y += vy
		sel_x %= len(letters[0])
		sel_y %= len(letters)
		# draw
		disp.fill(0)
		for x in range(len(letters[0])):
			for y in range(len(letters)):
				col = 1
				if sel_x == x and sel_y == y:
					col = 0
					disp.drawFilledRectangle(1 + x*(FONT_W+2)-1, 1 + y*(FONT_H+2)-1, FONT_W+2, FONT_H+2, 1)
				if sel_x == enter_x and sel_y == y:
					enter.setFrame(col)
					# draw enter
					disp.drawSprite(enter)
				else:
					disp.drawText(letters[y][x], 1 + x*(FONT_W+2), 1 + y*(FONT_H+2), col)
		disp.update()
	print(f"msg is {msg}")
	return msg