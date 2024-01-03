# display is 72x40
# 0,0 is top left
import math
import random
import time
from sys import print_exception

#import thumby
import thumbyButton
from thumbyGraphics import display as disp
from thumbySaves import saveData as save
import thumbySprite
import thumbyHardware
# GLOBALS
global GAME_NAME
GAME_NAME = "AxisRacer"

global FONT_WIDTH, FONT_HEIGHT
FONT_WIDTH = const(5)
FONT_HEIGHT = const(7)

global SCREEN_W, SCREEN_H
SCREEN_W = const(72)
SCREEN_H = const(40)

# track size will be roughly TRACK_SCALE * screensize
global TRACK_SCALE
TRACK_SCALE = const(10)

global TRACK_PREVIEW_W, TRACK_PREVIEW_H
TRACK_PREVIEW_W = const(SCREEN_W - (FONT_WIDTH+1)*2)
TRACK_PREVIEW_H = const(SCREEN_H - (FONT_HEIGHT+1))

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
DEBUG_DOTS = False
DEBUG_FIXED_SEED = False
DEBUG_KEYS = False
if not EMULATOR :
	DEBUG_MODE = DEBUG_ON_DEVICE


def splash():
	disp.fill(0)
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
	disp.setFont("/lib/font8x8.bin",8,8,1)
	disp.drawText("aXis",38,0,1)
	disp.drawText("raCer",30,10,1)
	disp.setFont("/lib/font5x7.bin",5,10,1)
	disp.drawText('A: start',6,33,1)
	while not thumbyButton.actionJustPressed():
		disp.update()


def load_data():
	global GAME_NAME
	dprint("loading data")
	save.setName(GAME_NAME)
	# get seed
	if save.hasItem("seed"):
		dprint("loading seed")
		seed = save.getItem("seed")
	# or set it up for first time
	else:
		seed = time.ticks_cpu()
		dprint(f"generating seed save {seed}")
		save.setItem("seed", seed)
		save.save()
	if DEBUG_MODE and DEBUG_FIXED_SEED: seed = 0
	data = {
		"seed": seed
	}
	return data


def init_random(seed):
	dprint(f"initial seed is {seed}")
	random.seed(seed)


def displayError(msg):
	disp.setFPS(60)
	default_font()
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


def default_font():
	disp.setFont(
		f"/lib/font{FONT_WIDTH}x{FONT_HEIGHT}.bin",
		FONT_WIDTH, FONT_HEIGHT,
		1)


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
	

def _generate_track(track_num, seed, width, height, n_key_points, n_segment_points, resample_segment_length, preview_segment_length):
	"""
	can be quite expensive as only needs to run infrequently
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	dprint("generating_track")
	track_seed = seed + track_num
	dprint(f"with seed {track_seed}")
	random.seed(track_seed)
	
	
	dprint("naming track")
	name = generate_track_name()
	dprint(f"name {name}")
	# show name while track generates
	# so that user doesn't get bored
	disp.fill(0)
	drawTrackUI(name, track_num)
	disp.update()
	
	# if we use the name as the seed
	# we can share tracks via the name
	# add seed together from first/second part
	# to avoid one word overriding seed
	name_seed0 = int.from_bytes(name.split()[0].encode(), 'big')
	name_seed1 = int.from_bytes(name.split()[1].encode(), 'big')
	name_seed = name_seed0 + name_seed1
	random.seed(name_seed)
	
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
		"name": name,
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


def generate_track(track_num, seed):
	# wrapper around _generate_track
	# so that consistent inputs can be set here
	global TRACK_SCALE
	# preview_segment_length will be roughly X pixels onscreen
	# if set to X * TRACK_SCALE
	preview_segment_length = 2 * TRACK_SCALE
	max_width = SCREEN_W * TRACK_SCALE
	max_height = SCREEN_H * TRACK_SCALE
	return _generate_track(
		track_num, seed,
		(int(max_width * 0.8), max_width),
		(int(max_height * 0.8), max_height),
		12, 2,
		10, preview_segment_length)


def getCamera():
	camera = {}
	camera["x"] = 0
	camera["y"] = 0
	camera["r"] = 0 # rotation
	camera["s"] = 1 # scale
	camera["filmwidth"] = 72
	camera["filmheight"] = 40
	return camera


def update(camera, track):
	global FONT_HEIGHT
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


def drawTrackUI(name, track_num):
	global FONT_WIDTH, FONT_HEIGHT
	disp.drawText(name,
		0, SCREEN_H - FONT_HEIGHT,
		1)
	if track_num > 0:
		disp.drawText("<",
			0, (SCREEN_H - FONT_HEIGHT) // 2,
			1)
	disp.drawText(">",
		SCREEN_W - FONT_WIDTH,
		(SCREEN_H - FONT_HEIGHT) // 2,
		1)


def debugDrawScene(camera, track):
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


def drawStartLine(x0, y0, x1, y1):
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
				drawStartLine(x0, y0, x1, y1)
			if DEBUG_MODE and DEBUG_DOTS:
				disp.setPixel(x0, y0, 1)
			else:
				disp.drawLine(x0, y0, x1, y1, 1)
	if DEBUG_MODE and not DEBUG_DOTS:
		debugDrawScene(camera, track)
	drawTrackUI(track["name"], track["num"])
	disp.update()


def track_select(seed):
	global DEBUG_DOTS
	global FONT_WIDTH, FONT_HEIGHT
	
	#init_random()
	default_font()
	# Set the FPS (without this call, the default fps is 30)
	# track selection is targeting low fps:
	disp.setFPS(15)
	camera = getCamera()
	
	dprint("entering track select loop")
	track_num = 0
	track = generate_track(track_num, seed)
	while True:
		if thumbyButton.buttonR.justPressed():
			track_num += 1
			track = generate_track(track_num, seed)
		if track_num > 0 and thumbyButton.buttonL.justPressed():
			track_num -= 1
			track = generate_track(track_num, seed)
		#hold in loop until a is pressed
		if thumbyButton.buttonA.justPressed():
			return track
		if DEBUG_MODE and thumbyButton.buttonB.justPressed():
			#flip DEBUG DOTS
			DEBUG_DOTS = not DEBUG_DOTS
		update(camera, track)
		draw(camera, track)


def main():
	splash()
	data = load_data()
	track = track_select(data["seed"])


try:
	main()
except Exception as x:
	if EMULATOR:
		print_exception(x)
	else:
		with open('/Games/Racer/crashdump.log','w',encoding="utf-8") as f:
			print_exception(x,f)
	displayError(x)
