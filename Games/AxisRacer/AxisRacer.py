# display is 72x40
# 0,0 is top left
# GLOBALS
global GAME_NAME
GAME_NAME = "AxisRacer"

import math
import random
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
import inpt
import util
	
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

# track size will be roughly TRACK_SCALE * screensize
global TRACK_SCALE
TRACK_SCALE = const(10)

global TRACK_PREVIEW_W, TRACK_PREVIEW_H
TRACK_PREVIEW_W = const(SCREEN_W - (FONT_W+1)*2)
TRACK_PREVIEW_H = const(SCREEN_H - (FONT_H+1))

global EMULATOR
try:
	import emulator
except ImportError:
	EMULATOR = False
else:
	EMULATOR = True

# ********** master debug flag **********
global DEBUG_MODE
DEBUG_MODE = True
# ***************************************
# extra debug flags
global DEBUG_ON_DEVICE, DEBUG_DOTS, DEBUG_FIXED_SEED, DEBUG_KEYS
DEBUG_ON_DEVICE = False
DEBUG_DOTS = False
DEBUG_FIXED_SEED = False
DEBUG_KEYS = False
if not EMULATOR :
	DEBUG_MODE = DEBUG_ON_DEVICE


def splash_setup():
	disp.fill(0)
	disp.setFPS(30)
	

def splash():
	splash_setup()
	"""
	# BITMAP: width: 32, height: 32
	disp.drawSprite(
		thumbySprite.Sprite(32, 32,
		bytearray([0,128,224,240,240,248,248,61,29,31,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
			0,1,3,7,7,15,15,15,14,14,14,12,12,12,28,28,28,60,60,124,252,248,248,248,240,240,224,224,192,192,128,0,
			0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,195,255,255,255,255,255,255,255,255,255,254,
			0,0,0,0,0,192,192,224,224,240,240,240,248,248,248,252,252,252,254,254,255,127,127,63,63,31,31,15,15,3,1,0]),
		0, 0, 0))
	"""
	util.set_font(BIG_FONT_W, BIG_FONT_H)
	disp.drawText("aXis",38,0,1)
	disp.drawText("raCer",30,10,1)
	util.set_font(FONT_W, FONT_H)
	disp.drawText('A:start',6,33,1)
	while not thumbyButton.actionJustPressed():
		disp.update()


def no_faves_splash():
	splash_setup()
	util.set_font(FONT_W, FONT_H)
	disp.drawText("no faves!", 0, 0, 1)
	disp.drawText("B:exit", 0, SCREEN_H-FONT_H, 1)
	util.set_font(MINI_FONT_W, MINI_FONT_H)
	disp.drawText("press up to", FONT_W*2, SCREEN_H//2 - MINI_FONT_H-1, 1)
	disp.drawText("fave traks", FONT_W*2, SCREEN_H//2, 1)
	while not thumbyButton.buttonB.justPressed():
		if thumbyButton.buttonU.justPressed() \
		or thumbyButton.buttonA.justPressed():
			# hacky fix to avoid up having any effect
			# TODO: write a better justPressed function
			# to avoid this by checking all buttons
			pass
		disp.update()


def end_faves_splash():
	splash_setup()
	util.set_font(FONT_W, FONT_H)
	disp.drawText("no more!", 0, 0, 1)
	disp.drawText("<", 0, (SCREEN_H - FONT_H) // 2, 1)
	disp.drawText("B:exit", 0, SCREEN_H-FONT_H, 1)
	util.set_font(MINI_FONT_W, MINI_FONT_H)
	disp.drawText("press up to", FONT_W*2, SCREEN_H//2 - MINI_FONT_H-1, 1)
	disp.drawText("fave traks", FONT_W*2, SCREEN_H//2, 1)
	while not (thumbyButton.buttonL.justPressed() \
			   or thumbyButton.buttonB.justPressed()):
		if thumbyButton.buttonU.justPressed() \
		or thumbyButton.buttonA.justPressed():
			# hacky fix to avoid presses having any effect
			# TODO: write a better justPressed function
			# to avoid this by checking all buttons
			pass
		disp.update()


def reroll_splash():
	splash_setup()
	util.set_font(FONT_W, FONT_H)
	disp.drawText("reroll all", 0, 0, 1)
	disp.drawText("traks?", 0, FONT_H+1, 1)
	disp.drawText("B:no A:yes", 0, SCREEN_H-FONT_H, 1)
	util.set_font(MINI_FONT_W, MINI_FONT_H)
	disp.drawText("fave traks", 0, (FONT_H+1)*2 + 2, 1)
	disp.drawText("will be safe", 0, (FONT_H+1)*2 + 2 + MINI_FONT_H+1, 1)
	while True:
		if thumbyButton.buttonB.justPressed():
			return False
		if thumbyButton.buttonA.justPressed():
			return True
		disp.update()


def reroll_tracks(data):
	# get user confirmation
	if reroll_splash():
		seed = new_seed()
		save.setItem("seed", seed)
		data["seed"] = seed
		save.save()


def new_seed():
	return time.ticks_cpu()


def load_data():
	global GAME_NAME
	global DEBUG_MODE, DEBUG_FIXED_SEED
	dprint("loading data")
	save.setName(GAME_NAME)
	updated = False
	
	if save.hasItem("seed"):
		dprint("loading seed")
		seed = save.getItem("seed")
	
	else:
		seed = new_seed()
		dprint(f"generating seed save {seed}")
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


def menu(*choices, selection=0):
	disp.setFPS(30)
	util.set_font(FONT_W, FONT_H)
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
		for i, choice in enumerate(choices):
			col = 1
			y = (SCREEN_H)//2 - FONT_H-1 + (i-selection) * (FONT_H+1)
			if i == selection:
				col = 0
				disp.drawFilledRectangle(0, y-1, SCREEN_W, FONT_H+2, 1)
			disp.drawText(choice, 1, y, col)
		disp.update()
	return


def add_fave(data, track_name):
	fave_names = data["fave_names"]
	# put new faves at the front of the list
	fave_names.insert(0, track_name)
	save.save()


def remove_fave(data, track_name):
	fave_names = data["fave_names"]
	fave_names.remove(track_name)
	save.save()


def toggle_fave(data, track):
	track_name = track["name"]
	if track_name in data["fave_names"]:
		track["fave"] = False
		remove_fave(data, track_name)
	else:
		track["fave"] = True
		add_fave(data, track_name)
		


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


def dprint(*args, **kwargs):
	global DEBUG_MODE
	if DEBUG_MODE:
		print(*args, **kwargs)


def next_idx(i, track):
	return (i+2) % len(track)


def prev_idx(i, track):
	return (i-2) % len(track)


def on_screen(x, y):
	global SCREEN_W, SCREEN_H
	if 0 <= x < SCREEN_W \
	and 0 <= y < SCREEN_H:
		   return True
	else:
		return False


def translate(entity, x, y, rel=False):
	if rel:
		entity["x"] += x
		entity["y"] += y
	else:
		entity["x"] = x
		entity["y"] = y


def scale(entity, s, rel=False):
	if rel:
		entity["s"] *= s
	else:
		entity["s"] = s


def view_transform(camera, x, y):
	x1 = int((x - camera["x"])/camera["s"] + camera["filmwidth"]/2)
	y1 = int((y - camera["y"])/camera["s"] + camera["filmheight"]/2)
	return x1, y1


def normalise(x, y):
	v_len = math.sqrt(x*x + y*y)
	return x/v_len, y/v_len


def get_tangent(x0, y0, x1, y1):
	dx = x1 - x0
	dy = y1 - y0
	return normalise(dx, dy)


def get_normal_out(x0, y0, x1, y1):
	dx = x1 - x0
	dy = y1 - y0
	return normalise(-dy, dx)
	
	
def get_normal_in(x0, y0, x1, y1):
	dx = x1 - x0
	dy = y1 - y0
	return normalise(dy, -dx)


def offset_points(points, offset):
	points_out = []
	points_out += [n for n in points[offset*2:]]
	points_out += [n for n in points[:offset*2]]
	return points_out


def generate_key_points(width, height, n_key_points):
	track = []
	# generate key points at regular angles
	# with some variation in distance from centre
	max_dist = 10
	cx, cy = width/2, height/2
	for i in range(n_key_points):
		# point angle in radians
		a = i/n_key_points * 2 * math.pi
		vx = math.sin(a)
		vy = math.cos(a)
		
		dist = random.uniform(0.1, 0.9)

		x = cx + vx * dist * width/2
		y = cy + vy * dist * height/2
		track.append(x)
		track.append(y)
	# offset indices by random amount
	# to randomise start
	offset = random.randrange(0, len(track)//2)
	track = offset_points(track, offset)
	return track


def generate_mid_points(key_track, n_segment_points):
	# after the key points are generated
	# add mid points between them
	track = []
	for i in range(0, len(key_track), 2):
		x, y = key_track[i], key_track[i+1]
		i1 = next_idx(i, key_track)
		x1, y1 = key_track[i1], key_track[i1+1]
		# seqment points are mid points plus key point
		for i in range(n_segment_points):
			x_i = (x*(n_segment_points-i) + x1*i) / n_segment_points
			y_i = (y*(n_segment_points-i) + y1*i) / n_segment_points
			track.append(x_i)
			track.append(y_i)
	return tuple(track)


def frange(start, stop, step):
	# from https://pynative.com/python-range-for-float-numbers/#h-range-of-floats-using-generator-and-yield
	count = 0
	while True:
		temp = float(start + count * step)
		if step > 0 and temp >= stop:
			break
		elif step < 0 and temp <= stop:
			break
		yield temp
		count += 1


def generate_quadratic_bezier_points(segment_track, key_step, n_curve_segments):
	track = []
	for i1 in range(0, len(segment_track), 2*key_step):
		i0 = prev_idx(i1, segment_track)
		i2 = next_idx(i1, segment_track)
		x0, y0 = segment_track[i0], segment_track[i0+1]
		x1, y1 = segment_track[i1], segment_track[i1+1]
		x2, y2 = segment_track[i2], segment_track[i2+1]
		track.append(x0)
		track.append(y0)
		step = 1/n_curve_segments
		for t in frange(step, 1, step):
			x = x1 + (1-t)*(1-t)*(x0-x1) + t*t*(x2-x1)
			y = y1 + (1-t)*(1-t)*(y0-y1) + t*t*(y2-y1)
			track.append(x)
			track.append(y)
		track.append(x2)
		track.append(y2)
	return track


def resample_track(in_track, segment_dist):
	# first calculate all current segment distances
	distances = []
	for i0 in range(0, len(in_track), 2):
		i1 = next_idx(i0, in_track)
		x0, y0 = in_track[i0], in_track[i0+1]
		x1, y1 = in_track[i1], in_track[i1+1]
		vx = x1-x0
		vy = y1-y0
		distance = math.sqrt(vx*vx + vy*vy)
		distances.append(distance)
	total_distance = sum(distances)
	n_segments = round(total_distance/segment_dist)
	fdist = total_distance/n_segments
	track = []
	current_dist = 0
	x0, y0 = in_track[0], in_track[1]
	for i, seg_dist in enumerate(distances):
		i1 = next_idx(i*2, in_track) # i*2 to get in_track x value idx
		x1, y1 = in_track[i1], in_track[i1+1]
		while current_dist < seg_dist:
			t = current_dist/seg_dist
			x = (1-t)*x0 + t*x1
			y = (1-t)*y0 + t*y1
			track.append(x)
			track.append(y)
			current_dist += fdist
		current_dist -= seg_dist
		x0, y0 = x1, y1
	return track, fdist


def get_bounding_box(point_list):
	min_x, min_y = point_list[0], point_list[1]
	max_x, max_y = point_list[0], point_list[1]
	# compare starting from second point
	for i in range(2, len(point_list), 2):
		x, y = point_list[i], point_list[i+1]
		if x < min_x:
			min_x = x
		if y < min_y:
			min_y = y
		if x > max_x:
			max_x = x
		if y > max_y:
			max_y = y
	#round the min down and the max up to ints
	min_x, min_y = int(min_x), int(min_y)
	max_x, max_y = int(max_x+0.5), int(max_y+0.5)
	w = max_x - min_x
	h = max_y - min_y
	
	x_coords = sorted(point_list[::2])
	y_coords = sorted(point_list[1::2])
	
	return min_x, min_y, w, h


def pick_line(file_name):
	with open(file_name, encoding="utf-8") as f:
		lines = f.read().splitlines()
	return random.choice(lines)


def generate_track_name():
	global GAME_NAME
	adjectives_file = f"/Games/{GAME_NAME}/words/adjectives.txt"
	nouns_file = f"/Games/{GAME_NAME}/words/nouns.txt"
	adjective = pick_line(adjectives_file)
	noun = pick_line(nouns_file)
	name = f"{adjective} {noun}"
	return name
	

def _generate_track(track_num, name_seed, fave, width, height, n_key_points, n_segment_points, resample_segment_length, preview_segment_length):
	"""
	can be quite expensive as only needs to run infrequently
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	# show name while track generates
	# so that user doesn't get bored
	disp.fill(0)
	draw_track_ui(name_seed, track_num, fave)
	disp.update()
	
	# if we use the name as the seed
	# we can share tracks via the name
	# add seed together from first/second part
	# to avoid one word overriding seed
	name_parts = name_seed.split()
	name_seed_part1 = int.from_bytes(name_parts[0].encode(), 'big')
	name_seed_part2 = int.from_bytes(name_parts[-1].encode(), 'big')
	name_seed_int = name_seed_part1 + name_seed_part2
	random.seed(name_seed_int)
	
	if not type(width) == int:
		width = random.randint(width[0], width[1])
	if not type(height) == int:
		height = random.randint(height[0], height[1])
	dprint("random size: {}x{}".format(width, height))
	dprint("generating key points")
	key_points = generate_key_points(
		width, height,
		n_key_points)
	
	dprint("generating mid points")
	track = generate_mid_points(key_points, n_segment_points)
	
	dprint("generating bezier curves")
	# TODO: think about cubic bezier for smoother corners
	# but maybe more boring?
	# would require generating mid points between tangent
	# points, not all points
	track = generate_quadratic_bezier_points(
		track, n_segment_points, 12)
		
	dprint("resampling")
	track, seg_dist = resample_track(track, resample_segment_length)
	
	dprint("generating preview")
	preview_points, preview_seg_dist = resample_track(track, preview_segment_length)
	
	dprint("checking dimensions")
	bx, by, bw, bh = get_bounding_box(key_points)
	
	# find centre
	cx = bx + bw/2
	cy = by + bh/2
	
	track_dict = {
		"num": track_num,
		"name": name_seed,
		"fave": fave,
		"track": track,
		"keys": key_points,
		"preview": preview_points,
		"seg_dist" : seg_dist,
		"cx": cx, "cy": cy,
		"bx": bx, "by": by,
		"bw": bw, "bh": bh
	}
	dprint(f"generated track!\n{bx}, {by}\n{bw}x{bh}")
	return track_dict


def generate_track(data, track_num, from_faves=None):
	# wrapper around _generate_track
	# so that consistent inputs can be set here
	global TRACK_SCALE
	# preview_segment_length will be roughly X pixels onscreen
	# if set to X * TRACK_SCALE
	preview_segment_length = 2 * TRACK_SCALE
	max_width = SCREEN_W * TRACK_SCALE
	max_height = SCREEN_H * TRACK_SCALE
	
	dprint("generating_track")
	if from_faves:
		name = from_faves[track_num]
	else:
		track_seed = data["seed"] + track_num
		dprint(f"with seed {track_seed}")
		random.seed(track_seed)
		
		dprint("naming track")
		name = generate_track_name()
	
	# need to check fave status against saved faves
	if name in data["fave_names"]:
		fave = True
	else:
		fave = False
	
	dprint(f"name {name}")
	
	return _generate_track(
		track_num, name, fave,
		(int(max_width * 0.8), max_width),
		(int(max_height * 0.8), max_height),
		12, 2,
		10, preview_segment_length)


def get_camera():
	camera = {}
	camera["x"] = 0
	camera["y"] = 0
	camera["r"] = 0 # rotation
	camera["s"] = 1 # scale
	camera["filmwidth"] = 72
	camera["filmheight"] = 40
	return camera


def update(camera, track):
	global TRACK_PREVIEW_W, TRACK_PREVIEW_H
	
	translate(camera, track["cx"], track["cy"])
	width_scale = track["bw"] / TRACK_PREVIEW_W
	height_scale = track["bh"] / TRACK_PREVIEW_H
	cam_scale = max(width_scale, height_scale)
	# translate up above text
	translate(
		camera,
		0, cam_scale*(camera["filmheight"]-TRACK_PREVIEW_H)/2,
		rel=True)
	scale(camera, cam_scale)


def draw_track_ui(name, num, fave):
	global FONT_W, FONT_H
	util.set_font(FONT_W, FONT_H)
	disp.drawText(
		name,
		0, SCREEN_H - FONT_H,
		1)
	if num > 0:
		disp.drawText("<", 0, (SCREEN_H - FONT_H) // 2, 1)
	disp.drawText(
		">",
		SCREEN_W - FONT_W,
		(SCREEN_H - FONT_H) // 2,
		1)
	if fave:
		disp.drawText("F", 0, 0, 1)
	


def debug_draw_scene(camera, track):
	global DEBUG_KEYS
	# draw box in centre
	cx, cy = view_transform(camera, track["cx"], track["cy"])
	disp.drawRectangle(cx-1, cy-1, 3, 3, 1)
	if DEBUG_KEYS:
		# draw key points
		key_points = track["keys"]
		x0, y0 = view_transform(camera, key_points[0], key_points[1])
		disp.drawRectangle(x0-1, y0-1, 3, 3, 1)
		for i in range(2, len(key_points), 2):
			x, y = view_transform(camera, key_points[i], key_points[i+1])
			disp.setPixel(x, y, 1)


def draw_start_line(x0, y0, x1, y1):
	nx, ny = get_normal_in(x0, y0, x1, y1)
	nx = int(2.5 * nx)
	ny = int(2.5 * ny)
	#disp.drawLine(x0-nx, y0-ny, x0+nx, y0+ny, 1)
	disp.setPixel(x0-nx, y0-ny, 1)
	disp.setPixel(x0+nx, y0+ny, 1)


def draw(camera, track):
	global DEBUG_MODE, DEBUG_DOTS
	global FONT_WIDTH, FONT_HEIGHT
	disp.fill(0) # Fill canvas to black
	points = track["preview"]
	key_points = track["keys"]
	
	for i in range(0, len(points), 2):
		x0, y0 = view_transform(camera, points[i], points[i+1])
		i1 = next_idx(i, points)
		x1, y1 = view_transform(camera, points[i1], points[i1+1])
		
		if on_screen(x0, y0) or on_screen(x1, y1):
			if i == 0:
				draw_start_line(x0, y0, x1, y1)
			if DEBUG_MODE and DEBUG_DOTS:
				disp.setPixel(x0, y0, 1)
			else:
				disp.drawLine(x0, y0, x1, y1, 1)
	if DEBUG_MODE and not DEBUG_DOTS:
		debug_draw_scene(camera, track)
	draw_track_ui(track["name"], track["num"], track["fave"])
	disp.update()


def track_select(data, use_faves=False):
	global DEBUG_DOTS
	global FONT_WIDTH, FONT_HEIGHT
	util.set_font(5, 7)
	# Set the FPS (without this call, the default fps is 30)
	# track selection is targeting low fps:
	disp.setFPS(15)
	camera = get_camera()
	if use_faves:
		# copy of faves
		from_faves = data["fave_names"][:]
		max_tracks = len(from_faves)
	else:
		from_faves = None
		max_tracks = 0

	dprint(f"max_tracks is {max_tracks}")
	track_num = 0
	track = generate_track(data, track_num, from_faves)
	dprint("entering track select loop")
	while True:
		if (not max_tracks or track_num < max_tracks) \
		and thumbyButton.buttonR.pressed():
			print(f"track_num is {track_num}")
			if track_num == max_tracks-1:
				# if we reach the end of max_tracks
				end_faves_splash()
			else:
				track_num += 1
			track = generate_track(data, track_num, from_faves)
		if track_num > 0 and thumbyButton.buttonL.pressed():
			track_num -= 1
			track = generate_track(data, track_num, from_faves)
		#hold in loop until a is pressed
		if thumbyButton.buttonA.justPressed():
			# track is chosen
			break
		if thumbyButton.buttonB.justPressed():
			# cancel
			track = []
			break
		if thumbyButton.buttonU.justPressed():
			toggle_fave(data, track)
		update(camera, track)
		draw(camera, track)
	return track


def track_menu(data):
	while True:
		track = []
		choice = menu(
			"traks",
			"faves",
			"get trak"
		)
		if choice == -1:
			break
		elif choice == 0:
			track = track_select(data, use_faves=False)
		elif choice == 1:
			dprint("no of faves: ", len(data["fave_names"]))
			if len(data["fave_names"]) == 0:
				no_faves_splash()
			else:
				track = track_select(data, use_faves=True)
		elif choice == 2:
			track_name = inpt.keyboard()
			if track_name:
				# if it's already in faves, unfave then refave
				if track_name in data["fave_names"]:
					remove_fave(data,track_name)
				add_fave(data, track_name)
				track_select(data, use_faves=True)
		if track:
			pass
			# race!


def main():
	while True:
		splash()
		data = load_data()
		while True:
			choice = menu(
				"1 player",
				"2 player",
				"tournament",
				"achievements",
				"reroll traks"
			)
			if choice == -1:
				# back out to splash and reload data
				break
			elif choice == 0: # 1 player
				track_menu(data)
			elif choice == 1: # 2 player
				raise Exception("not implemented")
			elif choice == 2: # tournament
				raise Exception("not implemented")
			elif choice == 3: # achievements
				raise Exception("not implemented")
			elif choice == 4: # reroll tracks
				reroll_tracks(data)

if __name__ == "__main__":
	try:
		main()
	except Exception as x:
		if EMULATOR:
			sys.print_exception(x)
		else:
			with open(f'/Games/{GAME_NAME}/logs/crashdump.log','w',encoding="utf-8") as f:
				sys.print_exception(x,f)
		display_error(x)
