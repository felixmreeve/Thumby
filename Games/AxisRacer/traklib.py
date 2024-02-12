import math
import random

import thumbyButton
from thumbyGraphics import display as disp
import thumbySprite as sprite

global GAME_NAME
GAME_NAME = "AxisRacer"

import util
import save
import splash
import multi
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

global LOADING_BAR_SIZE, LOADING_BAR_LENGTH
LOADING_BAR_SIZE = 5
LOADING_BAR_LENGTH = 20

global TRAK_PREVIEW_W, TRAK_PREVIEW_H
TRAK_PREVIEW_W = const(SCREEN_W - (FONT_W+1)*2)
TRAK_PREVIEW_H = const(SCREEN_H - (FONT_H+1))

# how many trak segments to draw before/after camera center
global RACE_SEGMENT_RANGE
# there and back again
RACE_SEGMENT_RANGE = (max(SCREEN_W, SCREEN_H) // TRAK_SEGMENT_LENGTH) + 1 

global RACER_MAX_SPEED, RACER_MAX_MPH, RACER_MAX_FORCE, RACER_MAX_DMG, RACER_FORCE_POWER
RACER_MAX_SPEED = 4
RACER_FORCE_POWER = 1.5
RACER_MAX_MPH = 200 # mph value is display equivalent to max speed
RACER_MAX_FORCE = RACER_MAX_SPEED ** RACER_FORCE_POWER * 0.02
RACER_MAX_DMG = 6

global RACER_ACCELERATION, RACER_DECCELERATION
RACER_ACCELERATION = 0.05
RACER_DECCELERATION = 0.08

global RACER_RERAIL_FRAMES
RACER_RERAIL_FRAMES = 20


def get_fave_heart():
    return sprite.Sprite(
        7, 7,
        bytearray([14,17,33,66,33,17,14,14,31,63,126,63,31,14]),
        1, 1,
        0
    )


def toggle_fave(trak):
    trak_name = trak["name"]
    if save.in_faves(trak_name):
        trak["fave"] = False
        save.remove_fave(trak_name)
    else:
        trak["fave"] = True
        save.add_fave(trak_name)


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


def get_racer(sprite, points):
    racer = {
        "seg": 0, # segment on track
        "t": 0, # t interpolation value along segment
        "r": 0, # rotation - "true" rotation to show
        "_r": 0, # skidding rotation for derailing (visual only)
        "rv": 0, # rotational velocity, used as normal force for derailing (via doing dmg)
        "dmg": 0, # if this gets too high - derail
        "v": 0, # velocity
        "x": 0, # x pos
        "y": 0, # y pos
        "on": True, # on=ontrak / off=derailed
        "spr": sprite, # sprite obj
    }
    update_racer_rot(racer, points)

    return racer


def update_racer_seg_t(racer, points):
    # move along segment by velocity
    racer["t"] += racer["v"] / TRAK_SEGMENT_LENGTH
    # move to next segment if t > 1
    while racer["t"] >= 1:
        racer["seg"] = (racer["seg"] + 1) % (len(points)//2)
        racer["t"] -=1


def interpolate_seg(seg, t, points):
    i0 = seg*2 # double since points are x, y
    i1 = next_idx(i0, points)
    # get start/end of current segment
    x0, y0 = points[i0], points[i0+1]
    x1, y1 = points[i1], points[i1+1]
    # interpolate along the segment
    x = (1-t)*x0 + t*x1
    y = (1-t)*y0 + t*y1
    return x, y


def update_racer_pos(racer, points):
    if racer["on"]:
        t = racer["t"]
        racer["x"], racer["y"] = interpolate_seg(racer["seg"], racer["t"], points)
    else: # derail
        racer["x"] += racer["v"] * math.sin(racer["r"])
        racer["y"] -= racer["v"] * math.cos(racer["r"])


def get_seg_angle(i0, points):
    i1 = next_idx(i0, points) 
    x0, y0 = points[i0], points[i0+1]
    x1, y1 = points[i1], points[i1+1]
    vx = x1-x0
    vy = y1-y0 # negative so that 0 is up
    #vx, vy = normalise(vx, vy)
    # add pi/2 so up = 0 and % to change range 0<a<2pi
    angle = (math.atan2(vy, vx) + (math.pi/2)) % (2*math.pi)
    return angle


def update_racer_rot(racer, points, calculate_rv=True):
    if racer["on"]:
        i = racer["seg"]*2  # double since points are x, y
        # we actually check 2 segments ahead to look like drifting
        # and encourage slowing down before corners
        # and speeding up coming out of corners
        i = next_idx(i, points)
        i = next_idx(i, points)
        angle = get_seg_angle(i, points)
        # if rotation has changed
        if angle != racer["r"]:
            if racer["v"] == 0:
                racer["rv"] = 0
            elif calculate_rv:
                # calculate rotate change
                rv = (angle - racer["r"])
                if rv > math.pi:
                    rv = -2*math.pi + rv
                elif rv < -math.pi:
                    rv = 2*math.pi + rv
                # use sqrt to remap a bit to change the weight
                #rv = math.copysign(math.sqrt(abs(rv)), rv)
                racer["rv"] = rv # racer["rv"][0], racer["rv"][1]
            racer["r"] = angle
            racer["_r"] = angle
    else: # derailed
        # check direction of rotational velocity
        if racer["rv"] < 0:
            # rotate by 1 sprite every 2 frames
            racer["_r"] -= math.pi / 8
        else:
            racer["_r"] += math.pi / 8


def update_racer_derail(racer, points):
    global RACER_MAX_FORCE, RACER_RERAIL_FRAMES
    if racer["on"]:
        force = get_racer_force(racer)
        if force > RACER_MAX_FORCE:
            # maximum dmg change per frame is small
            racer["dmg"] += min(force - RACER_MAX_FORCE, RACER_MAX_DMG*0.19)
        else:
            racer["dmg"] -= RACER_MAX_SPEED - racer["v"]
        racer["dmg"] = max(0, racer["dmg"])
        if racer["dmg"] > RACER_MAX_DMG:
            derail(racer, points)
    else:
        racer["t"] += 1/RACER_RERAIL_FRAMES
        if racer["t"] >= 1:
            rerail(racer, points)


def derail(racer, points):
    racer["on"] = False
    racer["t"] = 0 # we'll use t to track how long before it's back on
    i = racer["seg"]*2  # double since points are x, y
    racer["r"] = get_seg_angle(i, points)

def rerail(racer, points):
    racer["on"] = True
    racer["seg"] = (racer["seg"] + 1) % (len(points)//2)
    racer["t"] = 0
    racer["v"] = 0
    racer["_r"] = racer["r"] # reset visual rotation
    racer["rv"] = 0
    racer["dmg"] = 0
    update_racer_rot(racer, points)


def get_racer_force(racer):
    # use power of rv to increase effect
    return abs(racer["rv"] * racer["v"]) ** RACER_FORCE_POWER * racer["v"]/RACER_MAX_SPEED


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


def next_idx(i, points, n=1):
    return (i+n*2) % len(points)


def prev_idx(i, points, n=1):
    return (i-n*2) % len(points)


def draw_trak_ui(name, num, fave, view_only=False):
    global FONT_W, FONT_H
    util.set_font(FONT_W, FONT_H)
    disp.drawText(
        name,
        0, SCREEN_H - FONT_H,
        1)
    if not view_only:
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
    sprite_x, sprite_y = view_transform(
        camera, racer["x"], racer["y"])
    # using r or _r?
    offset = get_rot_frame_offset(racer["r"])
    sprite_x = sprite_x + offset[0] - 3.5
    sprite_y = sprite_y + offset[1] - 3.5

    racer["spr"].x, racer["spr"].y = sprite_x, sprite_y
    racer["spr"].setFrame( get_rot_frame(racer["_r"]) )

    if blocker:
        blocker.x, blocker.y = sprite_x, sprite_y
        disp.drawSprite(blocker)

    disp.drawSprite(racer["spr"])


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
        vy = -math.cos(a)
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
    adjectives_file = f"/Games/{GAME_NAME}/assets/adjectives.txt"
    nouns_file = f"/Games/{GAME_NAME}/assets/nouns.txt"
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


def generate_trak_from_name(trak_num, name, fave):
    # wrapper around _generate_trak
    # so that consistent inputs can be set here
    global TRAK_SCALE, TRAK_SEGMENT_LENGTH
    # preview_segment_length will be roughly X pixels onscreen
    # in preview, if set to X * TRAK_SCALE
    preview_segment_length = 2 * TRAK_SCALE
    max_width = SCREEN_W * TRAK_SCALE
    max_height = SCREEN_H * TRAK_SCALE
    return _generate_trak(
        trak_num, name, fave,
        (int(max_width * 0.8), max_width),
        (int(max_height * 0.8), max_height),
        12, 2,
        TRAK_SEGMENT_LENGTH, preview_segment_length)


def generate_trak(seed, old_trak, trak_num, from_faves):
    # clean up old trak for memory reasons first!
    if old_trak:
        old_trak.clear()

    util.dprint("generating_trak")
    if from_faves:
        name = from_faves[trak_num]
    else:
        trak_seed = seed + trak_num
        util.dprint(f"with seed {trak_seed}")
        random.seed(trak_seed)
        
        util.dprint("naming trak")
        name = generate_trak_name()

    # need to check fave status against saved faves
    # even if we're not in faves currently
    if save.in_faves(name):
        fave = True
    else:
        fave = False

    util.dprint(f"name {name}")

    return generate_trak_from_name(trak_num, name, fave)


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


def draw_trak_select(camera, trak, view_only=False):
    disp.fill(0) # Fill canvas to black
    draw_trak(camera, trak, preview = True)
    draw_trak_ui(trak["name"], trak["num"], trak["fave"], view_only=view_only)
    disp.update()


def waiting_for_trak_select():
    global FONT_W, FONT_H
    disp.setFPS(30)
    util.set_font(FONT_W, FONT_H)
    disp.fill(0)
    disp.drawText("waiting for", 0, 0, 1)
    disp.drawText("trak select", 0, FONT_H, 1)
    disp.update()
    camera = get_camera()
    trak = {}
    while True:
        received = None
        while received == None:
            # no need to send anything
            #multi.send_null()
            received = multi.receive_trak()
        code, trak_name = received
        if code == multi.CODE_T_WAIT \
        and trak_name != trak.get("name"):
            # clear for memory reasons
            trak.clear()
            trak = generate_trak_from_name(-1, trak_name, False)
        if code == multi.CODE_T_START:
            break
        if trak:
            update_camera_preview(camera, trak)
            draw_trak_select(camera, trak, view_only=True)
    return trak


def trak_select(selection = 0, use_faves=False, multilink=False):
    global FONT_WIDTH, FONT_HEIGHT
    seed = save.load_seed()
    
    util.set_font(5, 7)
    camera = get_camera()
    if use_faves:
        # copy of faves
        faves = save.load_faves()[:]
        max_traks = save.num_faves()
    else:
        faves = None
        max_traks = 0

    util.dprint(f"max_traks is {max_traks}")
    trak_num = selection
    trak = generate_trak(seed, None, trak_num, faves)
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
            trak = generate_trak(seed, trak, trak_num, faves)
        if trak_num > 0 and thumbyButton.buttonL.pressed():
            trak_num -= 1
            #trak = []
            trak = generate_trak(seed, trak, trak_num, faves)
        #hold in loop until a is pressed
        if thumbyButton.buttonA.justPressed():
            # trak is chosen
            break
        if thumbyButton.buttonB.justPressed():
            # cancel
            trak = {}
            break
        if thumbyButton.buttonU.justPressed():
            toggle_fave(trak)

        if multilink:
            # no need to recieve from player 2
            #multi.receive_null()
            multi.send_trak(trak["name"], confirm=False)

        update_camera_preview(camera, trak)
        draw_trak_select(camera, trak)
    # no need to receive from player 2
    #multi.receive_null()
    if multilink:
        success = False
        if trak:
            while not success:
                success = multi.send_trak(trak["name"], confirm=True)
        else:
            while not success:
                success = multi.send_trak_cancel()
    return trak


def accelerate(racer):
    acc = RACER_ACCELERATION * (RACER_MAX_SPEED - racer["v"])/RACER_MAX_SPEED
    racer["v"] += acc


def deccelerate(racer):
    dec = (RACER_DECCELERATION * racer["v"]/RACER_MAX_SPEED * 0.5) + (RACER_DECCELERATION * 0.5)
    racer["v"] -= dec


def player_input(racer, points):
    global RACER_MAX_FORCE
    if racer["on"]:
        if thumbyButton.buttonA.pressed():
            accelerate(racer)
        else:
            deccelerate(racer)
    
    if thumbyButton.buttonU.justPressed():
        derail(racer)
    if thumbyButton.buttonD.justPressed():
        rerail(racer, points)
    
    """
    if thumbyButton.buttonL.justPressed():
        RACER_MAX_FORCE -= 0.02
    if thumbyButton.buttonR.justPressed():
        RACER_MAX_FORCE += 0.02
    """
    racer["v"] = min(max(0, racer["v"]), RACER_MAX_SPEED)


def update_racer(racer, points, use_v=True, check_derail=False):
    if use_v and racer["on"]:
        update_racer_seg_t(racer, points)
    update_racer_pos(racer, points)
    update_racer_rot(racer, points)

    if check_derail:
        update_racer_derail(racer, points)


def get_camera_segment(racer, points):
    # look ahead of racer segment
    return (racer["seg"] + 1) % (len(points)//2)


def update_camera(camera, racer, points):
    if racer["on"]:
        seg = get_camera_segment(racer, points)
        x, y = interpolate_seg(seg, racer["t"], points)
        translate(camera, x, y)
    else:
        camera["x"] += racer["v"] * math.sin(racer["r"])
        camera["y"] -= racer["v"] * math.cos(racer["r"])


def update_multi(player, opponent):
    received = multi.receive_racer()
    if received != None:
        code, opponent["seg"], opponent["t"], opponent["v"] = received
    multi.send_racer(player["seg"], player["t"], player["v"])
    return received


def update_race(camera, trak, player, opponent=None, multilink=False):
    points = trak["trak"]
    # process input
    player_input(player, points)

    update_racer(player, points, check_derail=True)
    update_camera(camera, player, points)
    if multilink and opponent:
        received = update_multi(player, opponent)
        # if we've received data, no need to update seg/t from v
        # but if we didn't receieve any data, use v to estimate next seg/t
        update_racer(opponent, points, use_v = not received)
    elif opponent: # cpu
        update_racer(opponent, points)


# screen length vertical loading bar
def draw_loading_bar_v(value, x, y, h):
    global LOADING_BAR_SIZE
    # clamp value
    value = min(1, value)
    disp.drawFilledRectangle(x, y, LOADING_BAR_SIZE, h, 0)
    disp.drawRectangle(x, y, LOADING_BAR_SIZE, h, 1)
    disp.drawFilledRectangle(
        x, y+h - int(value * h),
        LOADING_BAR_SIZE, int(value * h), 
        1
    )


def draw_loading_bar_h(value, x, y, w):
    global LOADING_BAR_SIZE
    # clamp value
    value = min(1, value)
    disp.drawFilledRectangle(x, y, w, LOADING_BAR_SIZE, 0)
    disp.drawRectangle(x, y, w, LOADING_BAR_SIZE, 1)
    disp.drawFilledRectangle(
        x, y,
        int(value * w), LOADING_BAR_SIZE,
        1
    )


def draw_text(msg, x, y):
    disp.drawFilledRectangle(x, y, (MINI_FONT_W+1)*len(msg), MINI_FONT_H+1, 0)
    disp.drawText(msg, x, y, 1)


def draw_hud(player, race_time):
    global RACER_MAX_FORCE
    util.set_font(MINI_FONT_W, MINI_FONT_H)
    # draw speed
    mph = int(player["v"]/RACER_MAX_SPEED * RACER_MAX_MPH)
    draw_text(f"{mph:>3}mph", SCREEN_W-LOADING_BAR_SIZE*2-(MINI_FONT_W+1)*6, SCREEN_H-MINI_FONT_H)
    #disp.drawText(f"{player["rv"]}", 0, MINI_FONT_H+1, 1)
    #draw_text(f"{RACER_MAX_FORCE:.2f}", 0, 5*(MINI_FONT_H+1))
    draw_loading_bar_v(
        get_racer_force(player)/RACER_MAX_FORCE,
        SCREEN_W-5, SCREEN_H-LOADING_BAR_LENGTH,
        LOADING_BAR_LENGTH
    )
    draw_loading_bar_v(
        player["dmg"]/RACER_MAX_DMG,
        SCREEN_W-10, SCREEN_H-LOADING_BAR_LENGTH,
        LOADING_BAR_LENGTH
    )


def draw_debug(camera, trak, player):
    points = trak["trak"]
    px, py = view_transform(camera, player["x"], player["y"])
    i0 = player["seg"] * 2
    i1 = next_idx(i0, points)
    x0, y0 = points[i0], points[i0+1]
    x1, y1 = points[i1], points[i1+1]
    nx, ny = get_normal_in(x0, y0, x1, y1)
    # end point is based on player force
    nx = int(nx * (player["rv"]/RACER_MAX_FORCE) * 20)
    ny = int(ny * (player["rv"]/RACER_MAX_FORCE) * 20)
    disp.drawLine(px, py, px+nx, py+ny, 1)


def draw_race(camera, trak, blocker, player, opponent=None):
    global RACE_SEGMENT_RANGE
    disp.fill(0)
    draw_trak(
        camera,
        trak,
        segment = get_camera_segment(player, trak["trak"]),
        segment_range = RACE_SEGMENT_RANGE
    )
    if opponent:
        draw_racer(camera, opponent, blocker)
    if util.DEBUG_MODE:
        draw_debug(camera, trak, player)
    draw_racer(camera, player, blocker)
    draw_hud(player, None)
    disp.update()


def race(trak, multilink = False):
    # 40fps is a medium between speedy 60 and slow 30
    disp.setFPS(40)
    racer_sprite = sprite.Sprite(
        7, 7,
        # BITMAP: width: 56, height: 7
        bytearray([0,54,74,65,74,54,0,24,36,68,67,49,10,13,28,34,34,20,34,54,8,12,18,17,97,70,40,88,0,54,41,65,41,54,0,88,40,70,97,17,18,12,8,54,34,20,34,34,28,13,10,49,67,68,36,24]),
        0, 0,
        0
    )
    points = trak["trak"]
    player = get_racer(racer_sprite, points)
    opponent = get_racer(racer_sprite, points)

    start_point = points[:2]
    camera = get_camera()
    blocker = sprite.Sprite(
        7, 7,
        bytearray([99,65,0,0,0,65,99]),
        0, 0,
        1
    )
    
    # start in trak preview position
    #update_camera_preview(camera, trak))
    while True:
        #input()
        if thumbyButton.buttonB.justPressed():
            break
        update_race(camera, trak, player, opponent, multilink)
        draw_race(camera, trak, blocker, player, opponent)
