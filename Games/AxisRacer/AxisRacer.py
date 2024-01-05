# display is 72x40
# 0,0 is top left
# GLOBALS
global GAME_NAME
GAME_NAME = "AxisRacer"

import math
import time
import sys

#import thumby
import thumbyButton
from thumbyGraphics import display as disp
from thumbySaves import saveData as save
import thumbySprite
import thumbyHardware
# import game libs
if not f"/Games/{GAME_NAME}" in sys.path:
	sys.path.append(f"/Games/{GAME_NAME}")
import util
import inpt
import splash
import traklib

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

global TRAK_PREVIEW_W, TRAK_PREVIEW_H
TRAK_PREVIEW_W = const(SCREEN_W - (FONT_W+1)*2)
TRAK_PREVIEW_H = const(SCREEN_H - (FONT_H+1))

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
global DEBUG_ON_DEVICE, DEBUG_DOTS, DEBUG_FIXED_SEED, DEBUG_KEYS
DEBUG_ON_DEVICE = False
DEBUG_FIXED_SEED = False
if not EMULATOR:
	DEBUG_MODE = DEBUG_ON_DEVICE


def reroll_traks(data):
	# get user confirmation
	if splash.reroll_splash():
		seed = new_seed()
		save.setItem("seed", seed)
		data["seed"] = seed
		save.save()


def new_seed():
	return time.ticks_cpu()


def load_data():
	global GAME_NAME
	global DEBUG_MODE, DEBUG_FIXED_SEED
	util.dprint("loading data")
	save.setName(GAME_NAME)
	updated = False
	
	if save.hasItem("seed"):
		util.dprint("loading seed")
		seed = save.getItem("seed")
	
	else:
		seed = new_seed()
		util.dprint(f"generating seed save {seed}")
		save.setItem("seed", seed)
		updated = True
		
	if save.hasItem("fave_names"):
		fave_names = save.getItem("fave_names")
	else:
		fave_names = []
		save.setItem("fave_names", fave_names)
		updated = True
	
	if updated:
		save.save()
	
	if DEBUG_MODE and DEBUG_FIXED_SEED: seed = 0
	data = {
		"seed": seed,
		"fave_names": fave_names
	}
	return data


def menu(*choices, selection=0, title=""):
	disp.setFPS(30)
	while True:
		# input
		if thumbyButton.buttonD.justPressed():
			selection += 1
		if thumbyButton.buttonU.justPressed():
			selection -= 1
		if thumbyButton.buttonA.justPressed():
			return selection # int
		if thumbyButton.buttonB.justPressed():
			return -1 # back out
		selection %= len(choices)
		# draw
		disp.fill(0)
		util.set_font(BIG_FONT_W, BIG_FONT_H)
		title_y = (SCREEN_H)//2 - FONT_H-1  - selection * (FONT_H+1) - BIG_FONT_H-1
		disp.drawText(title, 1, title_y, 1)
		util.set_font(FONT_W, FONT_H)
		for i, choice in enumerate(choices):
			col = 1
			y = (SCREEN_H)//2 - FONT_H-1 + (i-selection) * (FONT_H+1)
			if i == selection:
				col = 0
				disp.drawFilledRectangle(0, y-1, SCREEN_W, FONT_H+2, 1)
			disp.drawText(choice, 1, y, col)
		disp.update()
	return



def display_error(msg):
	disp.setFPS(60)
	util.set_font(FONT_W, FONT_H)
	msg = str(msg)
	x0 = 0
	y0 = 32
	w = SCREEN_W
	msg_len=len(msg)*6+w
	pos=0
	disp.fill(0)
	disp.drawText("Thumby crash", 0, 0, 1)
	disp.drawText(" * Error: * ", 0, 16, 1)
	while True:
		msg_x = x0 + SCREEN_W - pos
		disp.drawFilledRectangle(x0, y0, SCREEN_W, 8, 0)
		disp.drawText(msg, msg_x, y0, 1)
		disp.update()
		pos += 1
		pos %= msg_len
		if thumbyButton.buttonA.justPressed() \
		or thumbyButton.buttonB.justPressed():
			thumbyHardware.reset()


def trak_menu(data):
	choice = 0
	while True:
		trak = None
		choice = menu(
			"all traks",
			"faves",
			"get trak",
			selection = choice,
			title = "trak:"
		)
		if choice == -1:
			break
		elif choice == 0:
			trak = traklib.trak_select(data, use_faves=False)
		elif choice == 1:
			util.dprint("no of faves: ", len(data["fave_names"]))
			if len(data["fave_names"]) == 0:
				splash.no_faves_splash()
			else:
				trak = traklib.trak_select(data, use_faves=True)
		elif choice == 2:
			trak_name = inpt.keyboard()
			if trak_name:
				# if it's already in faves, unfave then refave
				if trak_name in data["fave_names"]:
					traklib.remove_fave(data,trak_name)
				traklib.add_fave(data, trak_name)
				choice = 1
				traklib.trak_select(data, use_faves=True)
		if trak:
			pass
			# race!


def main():
	while True:
		if splash.main_splash():
			data = load_data()
			choice = 0
			while True:
				choice = menu(
					"1 player",
					"2 player",
					"tournament",
					"achievements",
					"reroll traks",
					selection = choice,
					title = "menu:"
				)
				if choice == -1:
					# back out to splash and reload data
					break
				elif choice == 0: # 1 player
					trak_menu(data)
				elif choice == 1: # 2 player
					raise Exception("not implemented")
				elif choice == 2: # tournament
					raise Exception("not implemented")
				elif choice == 3: # achievements
					raise Exception("not implemented")
				elif choice == 4: # reroll traks
					reroll_traks(data)
					choice = 0
		else:
			# quit
			disp.fill(0)
			break

try:
	main()
except Exception as x:
	if EMULATOR:
		sys.print_exception(x)
	else:
		with open(f'/Games/{GAME_NAME}/logs/crashdump.log','w',encoding="utf-8") as f:
			sys.print_exception(x,f)
	display_error(x)
