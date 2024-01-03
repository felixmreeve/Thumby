# display is 72x40
# 0,0 is top left
import math
import random
import time
from sys import print_exception

#import thumby
import thumbyButton
from thumbyGraphics import display as disp
import thumbySprite

# GLOBALS
global FONT_WIDTH, FONT_HEIGHT
FONT_WIDTH = 5
FONT_HEIGHT = 7

global SEED
SEED = 0

global TRACK_PREVIEW_SIZE
TRACK_PREVIEW_SIZE = (disp.width - (FONT_WIDTH+1)*2,
					  disp.height - (FONT_HEIGHT+1))

global DEBUG_MODE, DEBUG_DOTS
DEBUG_MODE = False
DEBUG_DOTS = False


def splash():
	disp.fill(0)
	disp.drawSprite(thumbySprite.Sprite(37,20,
		bytearray([128,192,224,112,48,48,112,224,128,0,0,0,0,0,0,0,192,160,80,168,212,234,245,250,253,254,127,191,95,175,87,43,21,10,5,2,1,159,255,240,224,240,56,28,15,3,0,0,0,0,128,252,245,234,213,171,215,47,95,55,43,21,10,5,2,1,0,0,0,0,0,0,0,0,3,1,0,1,3,3,6,6,6,6,6,3,3,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
		0,0,0))
	disp.setFont("/lib/font8x8.bin",8,8,1)
	disp.drawText("Ace",38,0,1)
	disp.drawText("Racer",30,10,1)
	disp.setFont("/lib/font5x7.bin",5,10,1)
	disp.drawText("Text editor",3,22,1)
	disp.drawText('A/B: Start',6,33,1)
	while not thumbyButton.actionJustPressed():
		disp.update()


def dprint(*args, **kwargs):
	global DEBUG_MODE
	if DEBUG_MODE:
		print(*args, **kwargs)


def next_idx(i, track):
	return (i+2) % len(track)


def prev_idx(i, track):
	return (i-2) % len(track)


def on_screen(x, y):
	if 0 <= x < disp.width \
	and 0 <= y < disp.height:
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
	

def init_random():
	global DEBUG_MODE
	SEED = time.ticks_cpu()
	if DEBUG_MODE: SEED = 0
	random.seed(SEED)


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
	adjectives_file = "/Games/Racer/words/adjectives.txt"
	nouns_file = "/Games/Racer/words/nouns.txt"
	adjective = pick_line(adjectives_file)
	noun = pick_line(nouns_file)
	name = f"{adjective} {noun}"
	return name
	

def generate_track(track_num, width, height, n_key_points, n_segment_points, resample_segment_length):
	"""
	can be quite expensive as only needs to run once
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	dprint("generating_track")
	random.seed(SEED + track_num)
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
	
	dprint("checking dimensions")
	bx, by, bw, bh = get_bounding_box(key_points)
	
	# find centre
	cx = bx + bw/2
	cy = by + bh/2
	
	dprint("naming track")
	name = generate_track_name()
	
	track_dict = {
		"name": name,
		"track": track,
		"keys": key_points,
		"seg_dist" : seg_dist,
		"cx": cx, "cy": cy,
		"bx": bx, "by": by,
		"bw": bw, "bh": bh
	}
	dprint(f"generated track!\n{bx}, {by}\n{bw}x{bh}")
	return track_dict


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
	global TRACK_PREVIEW_SIZE
	
	translate(camera, track["cx"], track["cy"])
	width_scale = track["bw"] / TRACK_PREVIEW_SIZE[0]
	height_scale = track["bh"] / TRACK_PREVIEW_SIZE[1]
	cam_scale = max(width_scale, height_scale)
	dprint("scale", cam_scale)
	# translate up above text
	translate(
		camera,
		0, cam_scale*(camera["filmheight"]-TRACK_PREVIEW_SIZE[1])/2,
		rel=True)
	scale(camera, cam_scale)


def debugDrawScene(camera, track):
	cx, cy = view_transform(camera, track["cx"], track["cy"])
	disp.drawRectangle(cx-1, cy-1, 3, 3, 1)
	key_points = track["keys"]
	x0, y0 = view_transform(camera, key_points[0], key_points[1])
	disp.drawRectangle(x0-1, y0-1, 3, 3, 1)
	for i in range(2, len(key_points), 2):
		x, y = view_transform(camera, key_points[i], key_points[i+1])
		disp.setPixel(x, y, 1)


def draw(camera, track):
	global DEBUG_MODE, DEBUG_DOTS
	global FONT_WIDTH, FONT_HEIGHT
	disp.fill(0) # Fill canvas to black
	points = track["track"]
	key_points = track["keys"]
	
	firstx, firsty = points[0:2]
	dprint(f"first point:{firstx}, {firsty}")
	tx, ty = view_transform(camera, firstx, firsty)
	dprint(f"transformed: {tx}, {ty}")
	for i in range(0, len(points), 2):
		x0, y0 = view_transform(camera, points[i], points[i+1])
		i1 = next_idx(i, points)
		x1, y1 = view_transform(camera, points[i1], points[i1+1])
		
		if on_screen(x0, y0) or on_screen(x1, y1):
			if DEBUG_MODE and DEBUG_DOTS:
				disp.setPixel(x0, y0, 1)
			else:
				disp.drawLine(x0, y0, x1, y1, 1)
	if DEBUG_MODE and not DEBUG_DOTS:
		debugDrawScene(camera, track)
		pass
	
	disp.drawText(track["name"], 
		0, disp.height - FONT_HEIGHT,
		1)
	disp.drawText("<",
		0, (disp.height-FONT_HEIGHT)//2,
		1)
	disp.drawText(">",
		disp.width-FONT_WIDTH,
		(disp.height-FONT_HEIGHT)//2,
		1)
	disp.update()


def main():
	global DEBUG_DOTS
	global FONT_WIDTH, FONT_HEIGHT
	
	init_random()

	disp.setFont(
		f"/lib/font{FONT_WIDTH}x{FONT_HEIGHT}.bin",
		FONT_WIDTH, FONT_HEIGHT,
		1)
	# Set the FPS (without this call, the default fps is 30)
	disp.setFPS(60)
	camera = getCamera()
	
	max_width = disp.width * 10
	max_height = disp.height * 10
	dprint("entering main loop")
	track_num = 0
	while True:
		track = generate_track(
			track_num,
			(int(max_width * 0.8), max_width),
			(int(max_height * 0.8), max_height),
			12, 2, 10)
		update(camera, track)
		draw(camera, track)
		while True:
			if thumbyButton.buttonR.justPressed():
				track_num += 1
				break
			if thumbyButton.buttonL.justPressed():
				track_num -= 1
				break
			#hold in loop until a is pressed
			if DEBUG_MODE and thumbyButton.buttonB.justPressed():
				#flip DEBUG DOTS
				DEBUG_DOTS = not DEBUG_DOTS
				draw(camera, track)


try:
	splash()
	main()
except Exception as x:
	try:
		import emulator
		print_exception(x)
	except ImportError:
		with open('/Games/Racer/crashdump.log','w',encoding="utf-8") as f:
			print_exception(x,f)
	disp.fill(0)
	disp.drawText("Editor died",3,8,1)
	disp.drawText("Problem was:",0,22,1)
	#sideScroll(str(x),0,30,d.width,-1,{'A':lambda:hardware.reset(),'B':lambda:hardware.reset()})
