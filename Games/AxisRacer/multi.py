from thumbyLink import link

global GAME_NAME
GAME_NAME = "AxisRacer"


def send_null():
    link.send(bytearray([0]))


def recieve_null():
    link.receieve()


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

def send_trak(trak_name):
    data = bytearray([]) + trak_name.encode()
    link.send(data)

def receieve_trak():
    data = link.receive()
    if data == None:
        return None
    else:
        # return code and trak name
        return data[0], data[1:].decode()