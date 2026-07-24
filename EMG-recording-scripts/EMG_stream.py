import asyncio
import websockets
import serial
import threading
import json
import time

# Serial connection settings
PORT = '/dev/serial0'
BAUDRATE = 2500000
PACKET_SIZE = 33
EMG_START = 7
NUM_CHANNELS = 8

# Open serial port
ser = serial.Serial(PORT, BAUDRATE, timeout=1)

# Buffer to hold latest EMG data
latest_emg_data = [0] * NUM_CHANNELS

# Lock to safely share data between threads
data_lock = threading.Lock()

def i24_to_int(b_list):
    val = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    if val & 0x800000:
        val -= 1 << 24
    return val

def parse_emg_packet(packet):
    emg_row = []
    for i in range(NUM_CHANNELS):
        idx = EMG_START + i * 3
        b = packet[idx:idx + 3]
        val = i24_to_int(b)
        emg_row.append(val)
    return emg_row

def serial_reader():
    """Thread that reads EMG data from serial port continuously."""
    global latest_emg_data
    buffer = bytearray()

    print("Serial reader thread started.")
    while True:
        try:
            if ser.in_waiting > 0:
                buffer += ser.read(ser.in_waiting)

            # Look for valid packets in buffer
            while len(buffer) >= PACKET_SIZE:
                # Check packet start bytes
                if buffer[0] == 0xFC and buffer[1] == 0x1A:
                    packet = buffer[:PACKET_SIZE]
                    emg_row = parse_emg_packet(packet)
                    with data_lock:
                        latest_emg_data = emg_row
                    buffer = buffer[PACKET_SIZE:]
                else:
                    # If start bytes not found, discard first byte and retry
                    buffer = buffer[1:]
            time.sleep(0.001)  # small delay to prevent busy wait
        except Exception as e:
            print(f"Serial read error: {e}")

async def handler(websocket, path):
    """Send latest EMG data to websocket clients."""
    print(f"Client connected: {websocket.remote_address}")
    try:
        while True:
            await asyncio.sleep(0.01)  # 100 Hz update rate
            with data_lock:
                data_to_send = list(latest_emg_data)
            # Send JSON string of EMG data array
            await websocket.send(json.dumps(data_to_send))
    except websockets.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main_async():
    loop = asyncio.get_running_loop()
    # Start serial reader thread
    threading.Thread(target=serial_reader, daemon=True).start()

    # Start WebSocket server
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server started on ws://0.0.0.0:8765")

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main_async())

