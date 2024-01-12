import sys
import os

from thumbyGraphics import display as disp
import thumbyButton as butt
import thumbyHardware as hard

EMULATOR = not hasattr(disp.display,"cs")

dir_type = 0x4000
file_type = 0x8000


def display_error(msg):
	msg = str(msg)
	x0 = 0
	y0 = 32
	w = 72
	msg_len=len(msg)*6+w
	pos=0
	disp.fill(0)
	disp.drawText("Thumby crash", 0, 0, 1)
	disp.drawText(" * Error: * ", 0, 16, 1)
	while True:
		msg_x = x0 + w - pos
		disp.drawFilledRectangle(x0, y0, w, 8, 0)
		disp.drawText(msg, msg_x, y0, 1)
		disp.update()
		pos += 1
		pos %= msg_len
		if butt.buttonA.justPressed() \
		or butt.buttonB.justPressed():
			hard.reset()


def list_entries(path):
	entries = os.ilistdir(path)
	entries_sorted = []
	if path != "/":
		entries_sorted.append(("..", dir_type))
	dir_idx = len(entries_sorted)
	for e_name, e_type, _, _ in entries:
		if e_type == dir_type:
			entries_sorted.insert(dir_idx, (e_name, e_type))
			dir_idx += 1
		else:
			entries_sorted.append((e_name, e_type))
	return entries_sorted


def menu(*choices, selection=0, title=""):
	#TODO: add side scrolling
	while True:
		# input
		if butt.buttonD.justPressed():
			selection += 1
		if butt.buttonU.justPressed():
			selection -= 1
		if butt.buttonA.justPressed():
			return "A", selection # int
		if butt.buttonB.justPressed():
			return "B", selection # back out
		selection %= len(choices)
		# draw
		disp.fill(0)
		disp.setFont("/lib/font8x8.bin", 8, 8, 1)
		title_y = 40//2 - 7-1  - selection * (7+1) - 8-1
		disp.drawText(title, 1, title_y, 1)
		disp.setFont("/lib/font5x7.bin", 5, 7, 1)
		for i, choice in enumerate(choices):
			col = 1
			y = (40)//2 - 7-1 + (i-selection) * (7+1)
			if i == selection:
				col = 0
				disp.drawFilledRectangle(0, y-1, 72, 7+2, 1)
			disp.drawText(choice, 1, y, col)
		disp.update()


def clean_path(root, dir_name):
	if dir_name == "..":
		path = root[:root.rindex("/")]
	else:
		path = root+"/"+dir_name
	path = path.replace("//", "/")
	if not path:
		path = "/"
	return path


def enter_dir(path, entry):
	new_path = clean_path(path, entry[0])
	entries = list_entries(new_path)
	if len(new_path) < len(path): # we've gone up a dir
		# find the index of the last folder
		selection = entries.index((path.split("/")[-1], dir_type))
	else:
		# select first dir in list that isn't ..
		selection = 1
	return new_path, selection


def read_file(path, entry):
	file_path = path+"/"+entry[0]
	with open(file_path, encoding="utf-8") as f:
		lines = f.read().splitlines()
	return lines


def action_menu(path, entry):
	btn, choice = menu(
		"transfer",
		"receive",
		"copy",
		"paste",
		"rename",
		"delete",
	)
	if btn == "B":
		return
	# button must have been A:
	


def display_lines(lines):
	disp.setFont("/lib/font5x7.bin", 5, 7, 1)
	sel_x, sel_y = 0, 0
	while True:
		y = 0
		disp.fill(0)
		for l in lines[sel_y:sel_y+4]:
			disp.drawText(l[sel_x:sel_x+12], 0, y, 1)
			y += 8
		if butt.buttonU.justPressed():
			sel_y -= 1
		if butt.buttonD.justPressed():
			sel_y += 1
		if butt.buttonL.justPressed():
			sel_x -= 1
		if butt.buttonR.justPressed():
			sel_x += 1
		if butt.buttonA.justPressed() \
		or butt.buttonB.justPressed():
			break

		if sel_y < 0: sel_y += 1
		if sel_x < 0: sel_x += 1
		
		disp.update()

def main():
	disp.setFPS(30)
	disp.setFont("/lib/font5x7.bin", 5, 7, 1)
	path = "/"
	choice = 0
	while True:
		# menu choices include a > for dir entries
		entries = list_entries(path)
		menu_choices = [">"+e[0] if e[1] == dir_type else e[0] for e in entries]
		btn, choice = menu(*menu_choices, selection = choice, title = path)
		choice_entry = entries[choice]
		if btn == "A":
			if choice_entry[1] == dir_type:
				path, choice = enter_dir(path, choice_entry)
			else:
				lines = read_file(path, choice_entry)
				display_lines(lines)
		elif btn == "B":
			action_menu(path, choice_entry)


try:
	main()
except Exception as x:
	if EMULATOR:
		sys.print_exception(x)
	else:
		with open(f"/Games/{GAME_NAME}/logs/crashdump.log","w",encoding="utf-8") as f:
			sys.print_exception(x,f)
	display_error(x)
