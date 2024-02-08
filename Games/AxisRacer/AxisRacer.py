# display is 72x40
# 0,0 is top left
# GLOBALS
global GAME_NAME
GAME_NAME = "AxisRacer"

import math
import time
import sys

import thumby
import thumbyButton
from thumbyGraphics import display as disp
import thumbyHardware as hard
# import game libs
if not f"/Games/{GAME_NAME}" in sys.path:
    sys.path.append(f"/Games/{GAME_NAME}")

import util
import inpt
import save
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


def trak_menu(multilink = False):
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
            trak = traklib.trak_select(selection=0, use_faves=False, multilink=multilink)
        elif choice == 1:
            if save.num_faves() == 0:
                splash.no_faves_splash()
            else:
                trak = traklib.trak_select(selection=0, use_faves=True, multilink=multilink)
        elif choice == 2:
            trak_name = inpt.keyboard()
            # add generated trak to faves
            if trak_name:
                # if it's already in faves, unfave then refave
                if save.in_faves(trak_name):
                    save.remove_fave(trak_name)
                save.add_fave(trak_name)
                choice = 1
                trak = traklib.trak_select(selection=0, use_faves=True, multilink=multilink)
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
            # send an additional handshake for half-duplex
            multi.send_handshake(player_num)
            multi.receive_handshake()
            break
        disp.update()
        if thumbyButton.buttonB.justPressed():
            break
    return player_num


def one_player():
    while True:
        trak = None
        trak = trak_menu()
        if trak:
            choice = trak["num"]
            traklib.race(trak, multilink = False)
        else:
            break


def two_player():
    global GAME_NAME
    player_num = handshake()
    if not player_num:
        return

    while True:
        if player_num == 1:
            trak = None
            trak = trak_menu(multilink = True)
            if trak:
                traklib.race(trak, multilink = True)
            else:
                break
        elif player_num == 2:
            trak = traklib.waiting_for_trak_select()
            if trak:
                traklib.race(trak, multilink = True)
            else:
                break
        else:
            raise RuntimeError(f"player_num is {player_num}")


def hot_seat():
    # choose players
    player_names = named_players_menu(title="hotseat:")
    if player_names:
        while True:
            trak = None
            trak = trak_menu()
            if trak:
                time_trial_race(trak, player_names)
            else:
                break


def time_trial():
    while True:
        trak = None
        trak = trak_menu()
        if trak:
            time_trial_race(trak)
        else:
            break


def tournament():
    player_names = named_players_menu()
    raise Exception("tournament not implemented")


def achievements():
    raise Exception("achievements not implemented")


def share_times():
    raise Exception("share times not implemented")


def demo_mode():
    raise Exception("demo mode not implemented")


def reroll_traks():
    # get user confirmation
    if splash.reroll_splash():
        util.dprint("rerolling seed")
        save.reset_seed()


def main_menu():
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
            break # back out to splash
        elif choice == 0: # 1 player
            one_player()
        elif choice == 1: # 2 player
            two_player()
        elif choice == 2: # hot seat
            hot_seat()
        elif choice == 3: # time trial
            time_trial()
        elif choice == 4: # tournament
            tournament()
        elif choice == 5: # achievements
            achievements()
        elif choice == 6: # share times
            share_times()
        elif choice == 7: # demo mode
            demo_mode()
        elif choice == 8: # reroll traks
            reroll_traks()
            choice = 0 # reset choice to 1 player so they can see new traks


def main():
    while True:
        start = splash.main_splash()
        if start:
            save.init()
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
