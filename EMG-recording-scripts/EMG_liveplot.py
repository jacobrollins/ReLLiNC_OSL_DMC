import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
sys.excepthook = lambda *args: sys.__excepthook__(*args)

# Serial connection settings
PORT = '/dev/serial0'
BAUDRATE = 2764800

# Initialize serial
ser = serial.Serial(PORT, BAUDRATE, timeout=1)

# Plotting setup
fig, ax = plt.subplots()
lines = [ax.plot([], [], label=f'Ch {i+1}')[0] for i in range(8)]
for line in lines: 
	line.set_data([],[]) #initialize with empty data

ax.set_xlim(0, 200)
ax.set_ylim(-1000000, 1000000)
ax.legend()
data_buffer = [[] for _ in range(8)]
x_vals = []

# EMG data extraction
def i24_to_int(b_list):
    val = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    if val & 0x800000:
        val -= 1 << 24
    return val

def parse_emg_packet(packet):
    emg_row = []
    for i in range(8):
        idx = 7 + i * 3  # Correct: bytes 7–30 inclusive
        b = packet[idx:idx+3]
        val = i24_to_int([b[0], b[1], b[2]])
        emg_row.append(val)
    return emg_row

# Animation update function
def update(frame):
	global x_vals
	print ("Update Called") #debug

	while ser.in_waiting >= 33:
		print(f"Bytes Available: {ser.in_waiting}") #debug no. bytes available

		raw = ser.read(33)
		if raw[0] == 0xFC and raw[1] == 0x1A:
			print ("valid packet start found")
			emg_row = parse_emg_packet(raw)
			print(f"parsed emg row: {emg_row}")
			for i in range(8):
				data_buffer[i].append(emg_row[i])
				if len(data_buffer[i]) > 200:
					data_buffer[i].pop(0)
			x_vals.append(len(x_vals))
			if len(x_vals) > 200:
				x_vals.pop(0)
			for i, line in enumerate(lines):
				line.set_data(x_vals, data_buffer[i])
		else:
			print ("invalid packet start, skipping")
	return lines

ani = animation.FuncAnimation(fig, update, blit=True, interval=10, cache_frame_data=False, save_count=0 )
plt.show()
