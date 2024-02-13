import thumbyButton as butt
from thumbyGraphics import display as disp

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

def splash_setup():
    disp.fill(0)
    disp.setFPS(30)
    

def main_splash():
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
    disp.drawText('A:start',0 , SCREEN_H-(FONT_H+1)*2, 1)
    disp.drawText('B:quit', 0, SCREEN_H-(FONT_H+1), 1)
    while True:
        inpt.update_input()
        if inpt.justPressed(butt.buttonA):
            return True
        if inpt.justPressed(butt.buttonB):
            return False
        disp.update()


def no_faves_splash():
    splash_setup()
    util.set_font(FONT_W, FONT_H)
    disp.drawText("no faves!", 0, 0, 1)
    disp.drawText("B:exit", 0, SCREEN_H-FONT_H, 1)
    util.set_font(MINI_FONT_W, MINI_FONT_H)
    disp.drawText("press up to", FONT_W*2, SCREEN_H//2 - MINI_FONT_H-1, 1)
    disp.drawText("fave traks", FONT_W*2, SCREEN_H//2, 1)
    while not inpt.justPressed(butt.buttonB):
        inpt.update_input()
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
    while not (inpt.justPressed(butt.buttonL) \
               or inpt.justPressed(butt.buttonB)):
        inpt.update_input()
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
        if inpt.justPressed(butt.buttonB):
            return False
        if inpt.justPressed(butt.buttonA):
            return True
        disp.update()