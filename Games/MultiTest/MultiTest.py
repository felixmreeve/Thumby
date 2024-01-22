import thumby
disp = thumby.display


def send(a_count, b_count):
	data = bytearray([a_count, b_count])
	thumby.link.send(data)


def receive():
	data = thumby.link.receive
	return data[0], data[1]


def menu(*choices, selection=0, title=""):
	disp.setFPS(30)
	while True:
		# input
		if thumby.buttonD.justPressed():
			selection += 1
		if thumby.buttonU.justPressed():
			selection -= 1
		if thumby.buttonA.justPressed():
			return selection # int
		if thumby.buttonB.justPressed():
			return -1 # back out
		selection %= len(choices)
		# draw
		disp.fill(0)
		disp.setFont(f"/lib/font8x8.bin", 8, 8, 1)
		title_y = (40)//2 - 7-1  - selection * (8+1) - 8-1
		disp.drawText(title, 1, title_y, 1)
		disp.setFont(f"/lib/font5x7.bin", 5, 7, 1)
		for i, choice in enumerate(choices):
			col = 1
			y = (40)//2 - 7-1 + (i-selection) * (7+1)
			if i == selection:
				col = 0
				disp.drawFilledRectangle(0, y-1, 72, 7+2, 1)
			disp.drawText(choice, 1, y, col)
		disp.update()


def play():
	my_counts = [0, 0]
	their_counts = [0, 0]
	disp.setFont(f"/lib/font8x8.bin", 8, 8, 1)
	while True:
		disp.fill(0)
		if thumby.buttonA.justPressed():
			my_counts[0] += 1
		if thumby.buttonB.justPressed():
			my_counts[1] += 1
		disp.drawText(f"  me: {my_counts[0]} {my_counts[1]}")
		disp.drawText(f"them: {my_counts[0]} {my_counts[1]}")
		disp.update()

def main():
	while True:
		choice = menu(
			"player1",
			"player2",
			selection=0,
			title="choose:"
		)
		if choice == -1:
			break
		elif choice == 0:
			player_num = 1
			play()
		elif choice == 1:
			player_num = 2
		


main()