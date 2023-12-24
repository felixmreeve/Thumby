distance = 2
distances = [4.0, 1.0, 4.0, 0.5, 0.5, 1.0, 3.0]
total_distance = sum(distances)
print(f"total_distance {total_distance}")
n_segments = round(total_distance/distance)
fdist = total_distance/n_segments
dist_i = 0
running_total = 0 
current_dist = 0
print(distances)
seg_dist_total = 0
for i, seg_dist in enumerate(distances):
	print(f"\nsegment {i}: {seg_dist} starts at {seg_dist_total}")
	while current_dist < seg_dist:
		t = current_dist/seg_dist
		print(f"P: {running_total}, {t}")
		
		current_dist += fdist
		running_total += fdist
	current_dist -= seg_dist
	seg_dist_total += seg_dist

#raise Exception("stop")

import math
import random
import time

#import thumby
import thumbyGraphics
import thumbyButton

# display is 72x40
# 0,0 is top left
DEBUG_MODE = False


def dprint(*args, **kwargs):
	if DEBUG_MODE:
		print(*args, **kwargs)


def next_point(i, track):
	return (i+2) % len(track)


def prev_point(i, track):
	return (i-2) % len(track)


def generate_key_points(width, height,
						n_key_points):
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
		i1 = next_point(i, key_track)
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
	

def generate_quadratic_bezier_points(segment_track,
									 key_step,
									 n_curve_segments):
	track = []
	for i1 in range(0, len(segment_track), 2*key_step):
		i0 = prev_point(i1, segment_track)
		i2 = next_point(i1, segment_track)
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


def resample_track(og_track, segment_dist):
	track = []
	distances = []
	for i0 in range(0, len(og_track), 2):
		i1 = next_point(i0, og_track)
		x0, y0 = og_track[i0], og_track[i0+1]
		x1, y1 = og_track[i1], og_track[i1+1]
		vx = x1-x0
		vy = y1-y0
		distance = math.sqrt(vx*vx + vy*vy)
		distances.append(distance)
	total_distance = sum(distances)
	print(f"total track distance {total_distance}")
	n_segments = round(total_distance/segment_dist)
	fdist = total_distance/n_segments
	print(f"using {n_segments} segments to resample by {fdist} distance")
	
	for i, seg_dist in enumerate(distances):
		print(f"\nsegment {i}: {seg_dist} starts at {seg_dist_total}")
		while current_dist < seg_dist:
			t = current_dist/seg_dist
			print(f"P: {running_total}, {t}")
			
			current_dist += fdist
			running_total += fdist
		current_dist -= seg_dist
		seg_dist_total += seg_dist
	
		
	return og_track


def generate_track(width, height,
				   n_key_points, n_segment_points,
				   resample_segment_length):
	"""
	can be quite expensive as only needs to run once
	n_segment_points: needs to be >= 2, larger
					  numbers bias curve tighter
					  to corner, lower numbers lead
					  to wavier, smoother curves
					  and less straights
	"""
	print("generating_track")
	print("generating key points")
	key_points = generate_key_points(width, height,
								n_key_points)
	print("generating mid points")
	track = generate_mid_points(key_points, n_segment_points)
	print("generating bezier curves")
	track = generate_quadratic_bezier_points(
			track, n_segment_points, 6)
	print("resampling")
	track = resample_track(track, resample_segment_length)
	print("generated track!")
	return track, key_points


def debugDrawScene(key_points):
	for i in range(0, len(key_points), 2):
		x, y = key_points[i], key_points[i+1]
		thumbyGraphics.display.setPixel(x, y, 1)


def drawScene(track, key_points):
	thumbyGraphics.display.fill(0) # Fill canvas to black
	for i in range(0, len(track), 2):
		x0, y0 = track[i], track[i+1]
		i1 = next_point(i, track)
		x1, y1 = track[i1], track[i1+1]
		thumbyGraphics.display.drawLine(x0, y0, x1, y1, 1)
	if DEBUG_MODE:
		debugDrawScene(key_points)
	thumbyGraphics.display.update()


def main():
	# Set the FPS (without this call, the default fps is 30)
	thumbyGraphics.display.setFPS(60)
	print("entering main loop")
	seed = 0
	random.seed(seed)
	while(1):
		track, key_points = generate_track(
						   thumbyGraphics.display.width,
						   thumbyGraphics.display.height,
						   12, 2, 2)
		track = [int(p) for p in track]
		drawScene(track, key_points)
		while not thumbyButton.buttonA.justPressed():
			#hold here until a is pressed
			pass

main()