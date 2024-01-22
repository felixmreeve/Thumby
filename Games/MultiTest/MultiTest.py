import thumby
disp = thumby.display
link = thumby.link


def send(b_count, a_count):
	data = bytearray([b_count, a_count])
	thumby.link.send(data)


def receive():
	data = thumby.link.receive()
	if data:
		return data[0], data[1]
	else:
		return data


def main():
	my_counts = [0, 0]
	their_counts = [0, 0]
	disp.setFont(f"/lib/font5x7.bin", 5, 7, 1)
	while True:
		disp.fill(0)
		if thumby.buttonB.justPressed():
			my_counts[0] += 1
		if thumby.buttonA.justPressed():
			my_counts[1] += 1
		send(my_counts[0], my_counts[1])
		data = receive()
		if data:
			their_counts = data[0], data[1]
		disp.drawText(f"  me: {my_counts[0]:<2} {my_counts[1]:<2}", 1, 1, 1)
		disp.drawText(f"them: {their_counts[0]:<2} {their_counts[1]:<2}", 1, 9, 1)
		disp.update()


main()