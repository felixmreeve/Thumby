import math
import random

import thumbyButton
from thumbyGraphics import display as disp
from thumbySaves import saveData as save
import thumbySprite as sprite

global GAME_NAME
GAME_NAME = "AxisRacer"

import util
import splash
# trak size will be roughly TRAK_SCALE * screensize
global TRAK_SCALE
TRAK_SCALE = const(10)
global TRAK_SEGMENT_LENGTH
TRAK_SEGMENT_LENGTH = const(8)

global SCREEN_W, SCREEN_H
SCREEN_W = const(72)
SCREEN_H = const(40)

global FONT_W, FONT_H
FONT_W = const(5)
FONT_H = const(7)
global MINI_FONT_W, MINI_FONT_H
MINI_FONT_W = const(3)
MINI_FONT_H = const(5)
global BIG_FONT_W, BIG_FONT_H
BIG_FONT_W = const(8)
BIG_FONT_H = const(8)

global TRAK_PREVIEW_W, TRAK_PREVIEW_H
TRAK_PREVIEW_W = const(SCREEN_W - (FONT_W+1)*2)
TRAK_PREVIEW_H = const(SCREEN_H - (FONT_H+1))

# how many trak segments to draw before/after center
global RACE_SEGMENT_RANGE
RACE_SEGMENT_RANGE = ((max(SCREEN_W, SCREEN_H)//2) // TRAK_SEGMENT_LENGTH) + 1 

global RACER_MAX_SPEED
RACER_MAX_SPEED = 8
global RACER_ACCELERATION, RACER_DECCELERATION
RACER_ACCELERATION = 0.1
RACER_DECCELERATION = 0.2


def get_fave_heart():
	return sprite.Sprite(
		7, 7,
		bytearray([14,17,33,66,33,17,14,14,31,63,126,63,31,14]),
		1, 1,
		0
	)


def add_fave(data, trak_name):
	fave_names = data["fave_names"]
	# put new faves at the front of the list
	fave_names.insert(0, trak_name)
	save.save()


def remove_fave(data, trak_name):
	fave_names = data["fave_names"]
	fave_names.remove(trak_name)
	save.save()


def toggle_fave(data, trak):
	trak_name = trak["name"]
	if trak_name in data["fave_names"]:
		trak["fave"] = False
		remove_fave(data, trak_name)
	else:
		trak["fave"] = True
		add_fave(data, trak_name)


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


def get_dist(x0, y0, x1, y1):
	vx = x1-x0
	vy = y1-y0
	return math.sqrt(vx*vx + vy*vy)


def get_camera():
	camera = {
		"x": 0,
		"y": 0,
		"r": 0, # rotation
		"s": 1, # scale
		"filmwidth": 72,
		"filmheight": 40
	}
	return camera


def get_racer(sprite):
	racer = {
		"seg": 0, # segment on track
		"t": 0, # t interpolation value along segment
		"r": 0, # rotation
		"v": 0, # velocity
		"x": 0,
		"y": 0,
		"sprite": sprite
	}
	return racer


def update_racer_pos(racer, points):
	t = racer["t"]
	i0 = racer["seg"]*2 # double since points are x, y
	i1 = next_idx(i0, points)
	# get start/end of current segment
	x0, y0 = points[i0], points[i0+1]
	x1, y1 = points[i1], points[i1+1]
	# interpolate along the segment
	racer["x"] = (1-t)*x0 + t*x1
	racer["y"] = (1-t)*y0 + t*y1


def update_racer_rot(racer, points):
	i0 = racer["seg"]*2  # double since points are x, y
	i1 = next_idx(i0, points)
	x0, y0 = points[i0], points[i0+1]
	x1, y1 = points[i1], points[i1+1]
	vx = x1-x0
	vy = y1-y0 # negative so that 0 is up
	#vx, vy = normalise(vx, vy)
	# add pi/2 so up = 0 and % to change range 0<a<2pi
	angle = (math.atan2(vy, vx) + (math.pi/2)) % (2*math.pi)
	racer["r"] = angle
	racer["sprite"].setFrame( get_rot_frame(racer["r"]) )


def get_rot_frame(angle):
	return int(angle / (2*math.pi)*8 + 0.5) % 8


def get_rot_frame_offset(angle, size=2):
	frame = get_rot_frame(angle)
	# offsets per frame
	frame_offsets = (
		( 0,  1),
		(-1,  1),
		(-1,  0),
		(-1, -1),
		( 0, -1),
		( 1, -1),
		( 1,  0),
		( 1,  1),
	)
	offset = (frame_offsets[frame][0]*size, frame_offsets[1]*size)
	return frame_offsets[frame]


def next_idx(i, trak):
	return (i+2) % len(trak)


def prev_idx(i, trak):
	return (i-2) % len(trak)


def draw_trak_ui(name, num, fave):
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
	fave_heart = get_fave_heart()
	fave_heart.setFrame(int(fave))
	disp.drawSprite(fave_heart)


def draw_trak(camera, trak, preview = False, segment = None, segment_range = None):
	global FONT_WIDTH, FONT_HEIGHT
	if preview:
		points = trak["preview"]
	else:
		points = trak["trak"]

	if segment is None:
		start = 0
		end = len(points)
	else:
		start = ((segment - segment_range)*2) % len(points)
		end = ((segment + segment_range+1)*2) % len(points)

	if end < start:
		# need two ranges at end/start of trak
		sub_ranges = ((start, len(points)), (0, end),)
	else:
		sub_ranges = ((start, end),)

	for start, end in sub_ranges:
		for i in range(start, end, 2):
			x0, y0 = view_transform(camera, points[i], points[i+1])
			i1 = next_idx(i, points)
			x1, y1 = view_transform(camera, points[i1], points[i1+1])
			if on_screen(x0, y0) or on_screen(x1, y1):
				if i == 0:
					draw_start_line(x0, y0, x1, y1)
				disp.drawLine(x0, y0, x1, y1, 1)


def draw_racer(camera, racer, blocker = None):
	#a = int(racer["r"]*4*math.pi + 2*math.pi/16) / (4*math.pi)
	#print(a)
	#x_offset, y_offset = racer["x"] - 4*math.sin(a), racer["y"] + 4*math.cos(a)
	#print(math.cos(racer["r"]), math.sin(racer["r"]), "\n")
	sprite_x, sprite_y = view_transform(
		camera, racer["x"], racer["y"])#x_offset, y_offset)

	offset = get_rot_frame_offset(racer["r"])
	sprite_x = sprite_x + offset[0] - 3.5
	sprite_y = sprite_y + offset[1] - 3.5

	racer["sprite"].x, racer["sprite"].y = sprite_x, sprite_y
	if blocker:
		blocker.x, blocker.y = sprite_x, sprite_y
		#blocker.x, blocker.y = view_transform(
		#camera, racer["x"], racer["y"])
		#blocker.x -= 3.5
		#blocker.y -= 3.5
		disp.drawSprite(blocker)
		#disp.drawRectangle(int(racer["sprite"].x+3.5-3), int(racer["sprite"].y+3.5-3), 5, 5, 1)
	disp.drawSprite(racer["sprite"])


def offset_points(points, offset):
	points_out = []
	points_out += [n for n in points[offset*2:]]
	points_out += [n for n in points[:offset*2]]
	return points_out


def generate_key_points(width, height, n_key_points):
	trak = []
	# generate key points at regular angles
	# with some variation in distance from centre
	max_dist = 10
	cx, cy = width/2, height/2
	for i in range(n_key_points):
		# point angle in radians
		a = i/n_key_points * 2 * math.pi
		vx = math.sin(a)
		vy = math.cos(a)
		dist = random.uniform(0.1, 1.0)
		x = cx + vx * dist * width/2
		y = cy + vy * dist * height/2
		trak.append(x)
		trak.append(y)
	# offset indices by random amount
	# to randomise start
	offset = random.randrange(0, len(trak)//2)
	trak = offset_points(trak, offset)
	return trak


def generate_mid_points(key_trak, n_segment_points):
	# after the key points are generated
	# add mid points between them
	trak = []
	for i in range(0, len(key_trak), 2):
		x, y = key_trak[i], key_trak[i+1]
		i1 = next_idx(i, key_trak)
		x1, y1 = key_trak[i1], key_trak[i1+1]
		# seqment points are mid points plus key point
		for i in range(n_segment_points):
			x_i = (x*(n_segment_points-i) + x1*i) / n_segment_points
			y_i = (y*(n_segment_points-i) + y1*i) / n_segment_points
			trak.append(x_i)
			trak.append(y_i)
	return tuple(trak)


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


def generate_quadratic_bezier_points(segment_trak, key_step, n_curve_segments):
	trak = []
	for i1 in range(0, len(segment_trak), 2*key_step):
		i0 = prev_idx(i1, segment_trak)
		i2 = next_idx(i1, segment_trak)
		x0, y0 = segment_trak[i0], segment_trak[i0+1]
		x1, y1 = segment_trak[i1], segment_trak[i1+1]
		x2, y2 = segment_trak[i2], segment_trak[i2+1]
		trak.append(x0)
		trak.append(y0)
		step = 1/n_curve_segments
		for t in frange(step, 1, step):
			x = x1 + (1-t)*(1-t)*(x0-x1) + t*t*(x2-x1)
			y = y1 + (1-t)*(1-t)*(y0-y1) + t*t*(y2-y1)
			trak.append(x)
			trak.append(y)
		trak.append(x2)
		trak.append(y2)
	return trak


# TODO: rewrite to be:
# - more memory efficient > pre allocate trak list as [0.0] * length*2
# make sure there's no duplicate point at the start/end
# write to be based on number of segments, not segment length? for consistency
def resample_trak(in_trak, segment_dist, cleanup = False):
	# first calculate all current segment distances
	total_distance = 0
	distances = []
	for i0 in range(0, len(in_trak), 2):
		i1 = next_idx(i0, in_trak)
		x0, y0 = in_trak[i0], in_trak[i0+1]
		x1, y1 = in_trak[i1], in_trak[i1+1]
		total_distance += get_dist(x0, y0, x1, y1)
	n_segments = round(total_distance/segment_dist)
	fdist = total_distance/n_segments
	trak = []
	new_i = 0
	current_dist = 0
	x0, y0 = in_trak[0], in_trak[1]
	for i0 in range(0, len(in_trak), 2):
		i1 = next_idx(i0, in_trak)
		x1, y1 = in_trak[i1], in_trak[i1+1]
		seg_dist = get_dist(x0, y0, x1, y1)
		while current_dist < seg_dist:
			t = current_dist/seg_dist
			x = (1-t)*x0 + t*x1
			y = (1-t)*y0 + t*y1
			trak.append(x)
			trak.append(y)
			current_dist += fdist
		if cleanup:
			# clean up in_trak to reduce memory
			in_trak[i1] = None
			in_trak[i1+1] = None
		current_dist -= seg_dist
		x0, y0 = x1, y1
	util.dprint("first point:", trak[0], trak[1])
	util.dprint("last point:", trak[-2], trak[-1])
	return trak, fdist


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


def generate_trak_name():
	global GAME_NAME
	adjectives_file = f"/Games/{GAME_NAME}/words/adjectives.txt"
	nouns_file = f"/Games/{GAME_NAME}/words/nouns.txt"
	adjective = pick_line(adjectives_file)
	noun = pick_line(nouns_file)
	name = f"{adjective} {noun}"
	return name
	

def _generate_trak(trak_num, name_seed, fave, width, height, n_key_points, n_segment_points, resample_segment_length, preview_segment_length):
	"""
	can be quite expensive as only needs to run infrequently
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	# show name while trak generates
	# so that user doesn't get bored
	disp.fill(0)
	draw_trak_ui(name_seed, trak_num, fave)
	disp.update()

	# if we use the name as the seed
	# we can share traks via the name
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
	util.dprint("random size: {}x{}".format(width, height))
	util.dprint("generating key points")
	key_points = generate_key_points(
		width, height,
		n_key_points)

	util.dprint("generating mid points")
	trak = generate_mid_points(key_points, n_segment_points)
	
	util.dprint("generating bezier curves")
	# TODO: think about cubic bezier for smoother corners
	# but maybe more boring?
	# would require generating mid points between tangent
	# points, not all points
	trak = generate_quadratic_bezier_points(
		trak, n_segment_points, 12)

	util.dprint("resampling")
	trak, seg_dist = resample_trak(trak, resample_segment_length, cleanup = True)

	util.dprint("generating preview")
	preview_points, preview_seg_dist = resample_trak(trak, preview_segment_length)

	util.dprint("checking dimensions")
	bx, by, bw, bh = get_bounding_box(key_points)

	# find centre
	cx = bx + bw/2
	cy = by + bh/2

	trak_dict = {
		"num": trak_num,
		"name": name_seed,
		"fave": fave,
		"trak": trak,
		"keys": key_points,
		"preview": preview_points,
		"seg_dist" : seg_dist,
		"cx": cx, "cy": cy,
		"bx": bx, "by": by,
		"bw": bw, "bh": bh
	}
	util.dprint(f"generated trak!\n{bx}, {by}\n{bw}x{bh}")
	return trak_dict


def generate_trak(data, old_trak, trak_num, from_faves):
	# wrapper around _generate_trak
	# so that consistent inputs can be set here
	global TRAK_SCALE, TRAK_SEGMENT_LENGTH
	# clean up old trak for memory reasons first!
	if old_trak:
		old_trak.clear()
	# preview_segment_length will be roughly X pixels onscreen
	# if set to X * TRAK_SCALE
	preview_segment_length = 2 * TRAK_SCALE
	max_width = SCREEN_W * TRAK_SCALE
	max_height = SCREEN_H * TRAK_SCALE

	util.dprint("generating_trak")
	if from_faves:
		name = from_faves[trak_num]
	else:
		trak_seed = data["seed"] + trak_num
		util.dprint(f"with seed {trak_seed}")
		random.seed(trak_seed)
		
		util.dprint("naming trak")
		name = generate_trak_name()

	# need to check fave status against saved faves
	if name in data["fave_names"]:
		fave = True
	else:
		fave = False

	util.dprint(f"name {name}")

	return _generate_trak(
		trak_num, name, fave,
		(int(max_width * 0.8), max_width),
		(int(max_height * 0.8), max_height),
		12, 2,
		TRAK_SEGMENT_LENGTH, preview_segment_length)


def update_camera_preview(camera, trak):
	global TRAK_PREVIEW_W, TRAK_PREVIEW_H
	translate(camera, trak["cx"], trak["cy"])
	width_scale = trak["bw"] / TRAK_PREVIEW_W
	height_scale = trak["bh"] / TRAK_PREVIEW_H
	cam_scale = max(width_scale, height_scale)
	# translate up above text
	translate(
		camera,
		0, cam_scale*(camera["filmheight"]-TRAK_PREVIEW_H)/2,
		rel=True)
	scale(camera, cam_scale)


def draw_start_line(x0, y0, x1, y1):
	nx, ny = get_normal_in(x0, y0, x1, y1)
	nx = int(2.5 * nx)
	ny = int(2.5 * ny)
	#disp.drawLine(x0-nx, y0-ny, x0+nx, y0+ny, 1)
	disp.setPixel(x0-nx, y0-ny, 1)
	disp.setPixel(x0+nx, y0+ny, 1)


def draw_trak_select(camera, trak):
	disp.fill(0) # Fill canvas to black
	draw_trak(camera, trak, preview = True)
	draw_trak_ui(trak["name"], trak["num"], trak["fave"])
	disp.update()


def trak_select(data, selection = 0, use_faves=False):
	global FONT_WIDTH, FONT_HEIGHT
	util.set_font(5, 7)
	camera = get_camera()
	if use_faves:
		# copy of faves
		from_faves = data["fave_names"][:]
		max_traks = len(from_faves)
	else:
		from_faves = None
		max_traks = 0

	util.dprint(f"max_traks is {max_traks}")
	trak_num = selection
	trak = generate_trak(data, None, trak_num, from_faves)
	util.dprint("entering trak select loop")
	while True:
		if (not max_traks or trak_num < max_traks) \
		and thumbyButton.buttonR.pressed():
			if trak_num == max_traks-1:
				# if we reach the end of max_traks
				splash.end_faves_splash()
			else:
				trak_num += 1
			#trak = []
			trak = generate_trak(data, trak, trak_num, from_faves)
		if trak_num > 0 and thumbyButton.buttonL.pressed():
			trak_num -= 1
			#trak = []
			trak = generate_trak(data, trak, trak_num, from_faves)
		#hold in loop until a is pressed
		if thumbyButton.buttonA.justPressed():
			# trak is chosen
			break
		if thumbyButton.buttonB.justPressed():
			# cancel
			trak = []
			break
		if thumbyButton.buttonU.justPressed():
			toggle_fave(data, trak)
		update_camera_preview(camera, trak)
		draw_trak_select(camera, trak)
	return trak, selection


def update_racer(racer, trak):
	points = trak["trak"]

	if racer["v"] < RACER_MAX_SPEED \
	and thumbyButton.buttonA.pressed():
		racer["v"] += RACER_ACCELERATION
	else:
		racer["v"] -= RACER_DECCELERATION
		racer["v"] = max(0, racer["v"])
	# move along segment by velocity
	racer["t"] += racer["v"] / TRAK_SEGMENT_LENGTH
	# move to next segment if t > 1
	while racer["t"] >= 1:
		racer["seg"] = (racer["seg"] + 1) % (len(points)//2)
		racer["t"] -=1

	update_racer_pos(racer, points)
	update_racer_rot(racer, points)


def update_camera(camera, racer):
	translate(camera, racer["x"], racer["y"])


def update_race(camera, racer, trak):
	update_racer(racer, trak)
	update_camera(camera, racer)


def draw_race(camera, trak, racer, blocker, framerate):
	global RACE_SEGMENT_RANGE
	disp.fill(0)
	draw_trak(camera, trak, segment=racer["seg"], segment_range=RACE_SEGMENT_RANGE)

	draw_racer(camera, racer, blocker)
	# framerate in corner
	#disp.drawText(str(next(framerate)), 1, 1, 1)
	disp.update()


def race(trak, multiplayer = False):
	disp.setFPS(60)
	racer_sprite = sprite.Sprite(
		7, 7,
		# BITMAP: width: 56, height: 7
		bytearray([0,54,74,65,74,54,0,24,36,68,67,49,10,13,28,34,34,20,34,54,8,12,18,17,97,70,40,88,0,54,41,65,41,54,0,88,40,70,97,17,18,12,8,54,34,20,34,34,28,13,10,49,67,68,36,24]),
		0, 0,
		0
	)
	racer = get_racer(racer_sprite)
	start_point = trak["trak"][:2]
	#racers = [get_racer() for i in range(2)]
	camera = get_camera()
	blocker = sprite.Sprite(
		7, 7,
		bytearray([99,65,0,0,0,65,99]),
		0, 0,
		1
	)
	# start in trak preview position
	#update_camera_preview(camera, trak))
	framerate = util.framerate()
	while True:
		#input()
		if thumbyButton.buttonB.justPressed():
			break
		update_race(camera, racer, trak)
		draw_race(camera, trak, racer, blocker, framerate)
		fps = next(framerate)
	