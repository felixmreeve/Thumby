from thumbyLink import link

global GAME_NAME
GAME_NAME = "AxisRacer"

CODE_NULL      = const(0)
CODE_PLAYER_1  = const(1)
CODE_PLAYER_2  = const(2)
CODE_T_CANCEL  = const(3)
CODE_T_WAIT    = const(4)
CODE_T_START   = const(5)
CODE_RACER     = const(6)


def send_null():
    link.send(bytearray([CODE_NULL]))


def receive_null():
    link.receive()


def send_player_num(player_num):
    data = bytearray([player_num])
    return link.send(data)


def receive_player_num():
    return link.receive()


def send_handshake(player_num = 0):
    #msg = GAME_NAME + str(player_num)
    #data = msg.encode()
    data = bytearray([player_num])
    return link.send(data)


def receive_handshake():
    data = link.receive()
    if data == None:
        return 0
    else:
        #msg = data[:-1]
        #their_player_num = int(data[-1])
        their_player_num = data[0]
        #if msg.decode() == GAME_NAME:
        # set player_num to one more than theirs
        # so if they don't have a player_num yet (0)
        #     then we reserve player 1
        # and if they are already player 1
        #     then we become player 2
        return their_player_num + 1


def send_trak(trak_name, confirm=False):
    # send code and trak name
    code = CODE_T_START if confirm else CODE_T_WAIT
    data = bytearray([code]) + trak_name.encode()
    link.send(data)


def receive_trak():
    data = link.receive()
    if data == None:
        return None
    elif data[0] in (CODE_T_WAIT, CODE_T_START):
        # return code and trak name
        return data[0], data[1:].decode()
    else:
        # either other player has cancelled or is sending invalid info
        return CODE_T_CANCEL, ""


def send_racer(seg, t):
    data = bytearray([
        CODE_RACER,
        seg,
        0
    ])
    link.send(data)


def receive_racer():
    data = link.receive()
    if data == None:
        return None
    elif data[0] == CODE_RACER:
        return data
    else:
        # TODO: figure out logic for if we don't receive a racer
        return None