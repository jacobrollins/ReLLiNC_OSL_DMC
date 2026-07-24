import serial
import plotly.graph_objs as go
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import threading

# Serial connection settings
PORT = '/dev/serial0'
BAUDRATE = 2500000
ser = serial.Serial(PORT, BAUDRATE, timeout=1)

# Constants
NUM_CHANNELS = 8
PACKET_SIZE = 33
EMG_START = 7
BUFFER_SIZE = 200

# Initialize buffers
emg_buffers = [[0] * BUFFER_SIZE for _ in range(NUM_CHANNELS)]

# Convert 3-byte i24 to signed integer
def i24_to_int(b_list):
    val = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    if val & 0x800000:
        val -= 1 << 24
    return val

# Parse 8 channels of EMG from a packet
def parse_emg_packet(packet):
    emg_row = []
    for i in range(NUM_CHANNELS):
        idx = EMG_START + i * 3
        b = packet[idx:idx + 3]
        val = i24_to_int(b)
        emg_row.append(val)
    return emg_row

# Serial reading in background thread
def serial_reader():
    print("Serial Reader thread started.")
    while True:
        if ser.in_waiting >= PACKET_SIZE:
            raw = ser.read(PACKET_SIZE)
            if raw[0] == 0xFC and raw[1] == 0x1A:
                emg_row = parse_emg_packet(raw)
                print("EMG data received:", emg_row)
                for i in range(NUM_CHANNELS):
                    emg_buffers[i].append(emg_row[i])
                    if len(emg_buffers[i]) > BUFFER_SIZE:
                        emg_buffers[i].pop(0)

# Start serial reading thread
threading.Thread(target=serial_reader, daemon=True).start()

# Dash app
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H2("Live EMG Stream"),
    dcc.Interval(id='interval', interval=100, n_intervals=0),
    dcc.Graph(id='emg-plot')
])

@app.callback(Output('emg-plot', 'figure'), [Input('interval', 'n_intervals')])
def update_graph(n):
    print("Updating graph...")
    # Only update if we have at least 10 samples
    if len(emg_buffers[0]) < 10:
        print("Not enough data to update plot.")
        return dash.no_update

    length = len(emg_buffers[0])
    # X-axis in seconds, assuming 4000 Hz sampling
    x_vals = [i / 4000 for i in range(length)]

    traces = [
        go.Scatter(
            x=x_vals,
            y=emg_buffers[i][-length:],
            mode='lines',
            name=f'Ch {i + 1}'
        ) for i in range(NUM_CHANNELS)
    ]

    layout = go.Layout(
        title="EMG Channels",
        xaxis=dict(title='Time (s)'),
        yaxis=dict(range=[-1000000, 1000000], title='Amplitude (ADC counts)'),
        height=600
    )

    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
