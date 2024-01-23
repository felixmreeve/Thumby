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
import thumbyHardware as hard
# import game libs
if not f"/Games/{GAME_NAME}" in sys.path:
    sys.path.append(f"/Games/{GAME_NAME}")
import util
import inpt
import splash
import traklib
import multi

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
DEBUG_MODE = True
# ***************************************
# extra debug flags
global DEBUG_ON_DEVICE, DEBUG_FIXED_SEED
DEBUG_ON_DEVICE = False
DEBUG_FIXED_SEED = True
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
            hard.reset()

# currently not used
def player_count_menu(min_players = 2, max_players = 8, title = "players:"):
    options = []
    for i in range(min_players, max_players+1):
        option = str(i) + " player"
        options.append(option)
    choice = menu(
        *options,
        selection = 0,
        title = title
    )
    if choice == -1:
        return None
    else:
        return min_players+choice

# default option of [] means it will remember the list for later
def named_players_menu(player_names = [], min_players = 2, title = "players:"):
    choice = 0
    if len(player_names) >= min_players:
        choice = len(player_names)+1 # race!
    while True:
        if len(player_names) < min_players:
            options = ["+"]
        else:
            options = ["+", "race!"]
        choice = menu(
            *player_names,
            *options,
            selection = choice,
            title = title
        )
        if choice == -1:
            return None
        elif choice < len(player_names): # edit/remove a name
            player_name = inpt.keyboard(player_names[choice])
            if not player_name:
                player_names.pop(choice)
            else:
                player_names[choice] = player_name
        elif choice == len(player_names): # plus
            player_name = inpt.keyboard()
            if player_name:
                player_names.append(player_name)
            choice = len(player_names)
        elif choice == len(player_names)+1: # race!
            return player_names


def trak_menu(data):
    choice = 0
    while True:
        # reset previously selected trak to clear memory
        trak = None
        choice = menu(
            "trak list",
            "faves",
            "get trak",
            selection = choice,
            title = "trak:"
        )
        if choice == -1:
            break
        elif choice == 0:
            trak = traklib.trak_select(data, selection=0, use_faves=False)
        elif choice == 1:
            util.dprint("no of faves: ", len(data["fave_names"]))
            if len(data["fave_names"]) == 0:
                splash.no_faves_splash()
            else:
                trak = traklib.trak_select(data, selection=0, use_faves=True)
        elif choice == 2:
            trak_name = inpt.keyboard()
            if trak_name:
                # if it's already in faves, unfave then refave
                if trak_name in data["fave_names"]:
                    traklib.remove_fave(data,trak_name)
                traklib.add_fave(data, trak_name)
                choice = 1
                trak = traklib.trak_select(data, selection=0, use_faves=True)
        if trak:
            break
    return trak


def handshake():
    player_num = 0
    disp.setFPS(30)
    util.set_font(FONT_W, FONT_H)
    while True:
        disp.fill(0)
        disp.drawText("waiting for", 1, 1, 1)
        disp.drawText("connection", 1, 8, 1)
        multi.send_handshake()
        result = multi.receive_handshake()
        if result:
            player_num = result
        if player_num:
            disp.drawText("success!", 1, 16, 1)
            # send an additional handshake for half-duplex
            multi.send_handshake(player_num)
            multi.receive_handshake()
            break
        disp.update()
        if thumbyButton.buttonB.justPressed():
            break
        
    return player_num


def one_player(data):
    while True:
        trak = None
        trak = trak_menu(data)
        if trak:
            choice = trak["num"]
            traklib.race(trak, multiplayer = False)
        else:
            break


def two_player(data):
    player_num = handshake()
    if not player_num:
        return
    while True:
            trak = None
            trak = trak_menu(data)
            if trak:
                traklib.race(trak, multiplayer = True)
            else:
                break


def hot_seat(data):
    # choose players
    player_names = named_players_menu(title="hotseat:")
    if player_names:
        while True:
            trak = None
            trak = trak_menu(data)
            if trak:
                time_trial_race(trak, player_names)
            else:
                break


def time_trial(data):
    while True:
        trak = None
        trak = trak_menu(data)
        if trak:
            time_trial_race(trak)
        else:
            break


def tournament(data):
    player_names = named_players_menu()
    raise Exception("tournament not implemented")

            
def achievements(data):
    raise Exception("achievements not implemented")


def share_times(data):
    raise Exception("share times not implemented")


def demo_mode(data):
    raise Exception("demo mode not")


def main_menu():
    data = load_data()
    choice = 0
    while True:
        choice = menu(
            "1 player",
            "2 player",
            "hot seat",
            "time trial",
            "tournament",
            "achievements",
            "share times",
            "demo mode",
            "reroll traks",
            selection = choice,
            title = "menu:"
        )
        if choice == -1:
            break # back out to splash and reload data
        elif choice == 0: # 1 player
            one_player(data)
        elif choice == 1: # 2 player
            two_player(data)
        elif choice == 2: # hot seat
            hot_seat(data)
        elif choice == 3: # time trial
            time_trial(data)
        elif choice == 4: # tournament
            tournament(data)
        elif choice == 5: # achievements
            achievements(data)
        elif choice == 6: # share times
            share_times(data)
        elif choice == 7: # demo mode
            demo_mode(data)
        elif choice == 8: # reroll traks
            reroll_traks(data)
            choice = 0 # reset choice to 1 player so they can see new traks


def main():
    while True:
        start = splash.main_splash()
        if start:
            main_menu()
        else:
            # quit
            disp.fill(0)
            disp.update()
            hard.reset()


try:
    main()
except Exception as x:
    if EMULATOR:
        sys.print_exception(x)
    else:
        with open(f'/Games/{GAME_NAME}/logs/crashdump.log','w',encoding="utf-8") as f:
            sys.print_exception(x,f)
    display_error(x)
