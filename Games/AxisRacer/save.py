from thumbySaves import saveData

import util


def load_seed():
    util.dprint("loading data")
    saveData.setName(util.GAME_NAME)
    
    util.dprint("loading seed")
    seed = saveData.getItem("seed")
    util.dprint(f"seed: {seed}")
    
    if util.DEBUG_MODE and util.DEBUG_FIXED_SEED: seed = 0
    return seed


def reset_seed():
    seed = util.new_seed()
    util.dprint(f"generating seed save {seed}")
    saveData.setItem("seed", seed)
    saveData.save()


def reset_faves():
    fave_names = []
    saveData.setItem("fave_names", fave_names)
    saveData.save()


def load_faves():
    return saveData.getItem("fave_names") or []


def load_fave(trak_num):
    saveData.setName(util.GAME_NAME)
    fave_names = load_faves()
    return fave_names[trak_num]


def add_fave(trak_name):
    fave_names = load_faves()
    fave_names.insert(0, trak_name)
    saveData.setItem("fave_names", fave_names)
    saveData.save()


def remove_fave(trak_name):
    fave_names = load_faves()
    fave_names.remove(trak_name)
    saveData.setItem("fave_names", fave_names)
    saveData.save()


def in_faves(trak_name):
    faves = load_faves()
    if faves:
        return trak_name in faves
    else:
        return False


def num_faves():
    return len(load_faves())


def new_save():
    reset_seed()
    reset_faves()

def init():
    if load_seed() == None:
        new_save()