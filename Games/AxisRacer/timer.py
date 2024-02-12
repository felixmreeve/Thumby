import time


def get_timer():
    timer = {
        "s_ticks": time.ticks_ms(),
        "s_time": 0.0,
        "time": 0.0,
    }
    return timer


def get_race_timer():
    timer = get_timer()
    timer["s_time"] = -3.0
    timer["time"] = -3.0
    return timer


def update_timer(timer):
    ticks = time.ticks_ms()
    timer["time"] = timer["s_time"] + (ticks - timer["s_ticks"])/1000