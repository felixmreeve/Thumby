import thumbyLink as link

global GAME_NAME
GAME_NAME = "AxisRacer"


def send_handshake():
	msg = GAME_NAME
	data = msg.encode()
	link.send_data(data)


def receive_handshake():
	data = link.receive_data()
	if data != None \
	and data.decode() == GAME_NAME:
		return True
	else:
		return False
