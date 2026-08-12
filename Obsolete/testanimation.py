import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig, ax =plt.subplots()
line, = ax.plot([],[])

def update(frame):
	print("Update  called")
	return [line]
def main():

	ani = animation.FuncAnimation(fig, update, blit=False, interval = 100, cache_frame_data= False)
	plt.show()
	return ani
ani = main()
