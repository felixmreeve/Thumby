# display is 72x40
# 0,0 is top left
import math
import random
import time

#import thumby
import thumbyGraphics
import thumbyButton


global DEBUG_MODE, DEBUG_DOTS
DEBUG_MODE = False
DEBUG_DOTS = False


def dprint(*args, **kwargs):
	global DEBUG_MODE
	if DEBUG_MODE:
		print(*args, **kwargs)


def next_idx(i, track):
	return (i+2) % len(track)


def prev_idx(i, track):
	return (i-2) % len(track)


def on_screen(x, y):
	if 0 <= x < thumbyGraphics.display.width \
	   and 0 <= y <thumbyGraphics.display.height:
		   return True
	else:
		return False


def translate(entity, x, y, r=False):
	if r:
		entity["x"] += x
		entity["y"] += y
	else:
		entity["x"] = x
		entity["y"] = y


def view_transform(camera, x, y):
	x1 = int(x - camera["x"] + camera["filmwidth"]/2)
	y1 = int(y - camera["y"] + camera["filmheight"]/2)
	return x1, y1


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
	return min_x, min_y, w, h


def generate_track(width, height, n_key_points, n_segment_points, resample_segment_length):
	"""
	can be quite expensive as only needs to run once
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	dprint("generating_track")
	if not type(width) == int:
		print("randomising width")
		width = random.randint(width[0], width[1])
	if not type(height) == int:
		print("randomising height")
		height = random.randint(height[0], height[1])
	
	dprint("generating key points")
	key_points = generate_key_points(width, height,
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
	cy = by + bw/2
	
	track_dict = {
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


def debugDrawScene(camera, key_points):
	camx, camy = get_view_transform(camera)
	thumbyGraphics.display.drawRectangle(int(key_points[0]-1 + camx), int(key_points[1]-1 + camy), 3, 3, 1)
	for i in range(2, len(key_points), 2):
		x, y = key_points[i], key_points[i+1]
		x, y = int(x + camx), int(y + camy)
		thumbyGraphics.display.setPixel(x, y, 1)


def drawScene(camera, track):
	thumbyGraphics.display.fill(0) # Fill canvas to black
	points = track["track"]
	key_points = track["keys"]
	#####
	
	
	translate(camera, points[0], points[1])
	
	#model = identity_matrix()
	
	#view = camera["transform"]
	
	#project = camera["project"]
	
	
	#####
	firstx, firsty = points[0:2]
	camx, camy = get_view_transform(camera)
	print(f"first point:{firstx}, {firsty}")
	tx, ty = firstx+camx, firsty+camy
	print(f"transformed: {tx}, {ty}")
	for i in range(0, len(points), 2):
		x0, y0 = view_transform(camera, points[i], points[i+1])
		i1 = next_idx(i, points)
		x1, y1 = view_transform(camera, points[i1], points[i1+1])
		
		if on_screen(x0, y0) or on_screen(x1, y1):
			if DEBUG_MODE and DEBUG_DOTS:
				thumbyGraphics.display.setPixel(x0, y0, 1)
			else:
				thumbyGraphics.display.drawLine(x0, y0, x1, y1, 1)
	if DEBUG_MODE and not DEBUG_DOTS:
		debugDrawScene(camera, key_points)
		pass
	thumbyGraphics.display.update()


def main():
	global DEBUG_DOTS
	# Set the FPS (without this call, the default fps is 30)
	thumbyGraphics.display.setFPS(60)
	dprint("entering main loop")
	camera = getCamera()
	seed = time.ticks_cpu()
	if DEBUG_MODE: seed = 0
	random.seed(seed)
	max_width = thumbyGraphics.display.width * 2
	max_height = thumbyGraphics.display.height * 2
	while(1):
		track = generate_track(
		   (max_width//2, max_width),
		   (max_height//2, max_height),
		   12, 2, 4)
		drawScene(camera, track)
		while not thumbyButton.buttonA.justPressed():
			#hold in loop until a is pressed
			if thumbyButton.buttonB.justPressed():
				#flip DEBUG DOTS
				DEBUG_DOTS = not DEBUG_DOTS
				drawScene(camera, track)


main()