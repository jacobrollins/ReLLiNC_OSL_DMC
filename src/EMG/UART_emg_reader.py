"""UART packet reader for the eight-channel EPM EMG data stream.

Developed using EMG_save_3.py as a reference, but refactored to be more modular and testable.

The reader deliberately has no import-time hardware side effects.  Create an
instance from the application that consumes EMG data, then call ``poll()``
once per control-loop iteration and use ``latest_samples`` (or
``read_latest()``) as the most recent complete EPM packet.

The application can call "read_latest()" at whatever speed is required
but be aware that the EPM reads packets at a baud rate of 2764800 (corresonding to 4000hz),
and so calling read_latest() at a slower rate will result in skipped packets.
The reader will record skipped bytes and packets, which can be queried for debugging purposes.

Written by: Jacob Rollins
Last edits: 8/3/26
"""

from typing import Optional, Sequence
import serial


PACKET_HEADER = b"\xFC\x1A" #UART start header
PACKET_SIZE = 33
CHANNEL_COUNT = 8
BAUDRATE = 2764800
PORT = '/dev/serial0'  # default UART port for Raspberry Pi

#converts 3 byte hex value from EPM data stream to signed integer
def i24_to_int(b_list):
    if len(b_list) != 3:
        raise ValueError("A 24-bit EPM sample must contain exactly three bytes.")

    value = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    return value - (1 << 24) if value & 0x800000 else value


def parse_emg_packet(packet):
   #Decode 8 EMG samples from one 33-byte EPM packet
    if len(packet) != PACKET_SIZE:
        raise ValueError(f"Expected a {PACKET_SIZE}-byte EPM packet, got {len(packet)} bytes.")
    if bytes(packet[:2]) != PACKET_HEADER:
        raise ValueError("Packet does not start with the EPM header 0xFC 0x1A.")

    return [i24_to_int(packet[7 + channel * 3 : 10 + channel * 3]) for channel in range(CHANNEL_COUNT)]


class UARTEMGReader:
    """Read, frame, and decode EPM EMG packets received over UART.

    Channel numbers are zero-based: channel 0 is EPM CH1 and channel 1 is
    EPM CH2. The newest valid packet is retained so multiple devices can
    read different channels without waiting for another UART packet.
    """

    packet_header = PACKET_HEADER
    packet_size = PACKET_SIZE
    channel_count = CHANNEL_COUNT

    def __init__(
        self,
        port: str = PORT,
        baudrate: int = BAUDRATE,
        timeout: float = 0.0,
        max_buffer_size: int = 1024 * 1024,
        serial_connection=None,
    ):
        if max_buffer_size < self.packet_size:
            raise ValueError("max_buffer_size must be at least one packet long.")

        if serial_connection is None:
            if serial is None:
                raise RuntimeError("pyserial is required to open a UART connection.")
            serial_connection = serial.Serial(port, baudrate, timeout=timeout)

        self.serial = serial_connection
        self.max_buffer_size = max_buffer_size
        self._buffer = bytearray()
        self.latest_samples: Optional[list[int]] = None
        self.packet_count = 0
        self.skipped_bytes = 0


    def feed(self, data):
        """Add UART bytes, decode all complete packets, and return their count.

        This public method also makes the packet framing behavior testable with
        recorded data, without connecting to the EPM hardware.
        """
        self._buffer.extend(data)
        self._limit_buffer()
        return self._process_buffer()

    def poll(self):
        """Read all currently available UART bytes and decode complete packets.

        The call is non-blocking when the underlying serial connection uses a
        zero timeout.  It returns the number of valid packets decoded.
        """
        waiting = self.serial.in_waiting
        if waiting:
            return self.feed(self.serial.read(waiting))
        return 0

    def read_latest(self) -> Optional[list[int]]:
       #Poll once and return a copy of the latest complete packet, if any
        self.poll()
        return None if self.latest_samples is None else self.latest_samples.copy()

    def read_channel(self, channel):   #Return the newest hex value for a zero-based EPM channel.

        if not 0 <= channel < self.channel_count:
            raise ValueError(f"Channel must be between 0 and {self.channel_count - 1}.")

        samples = self.read_latest()
        if samples is None:
            raise RuntimeError("No complete EPM packet has been received yet.")
        return samples[channel]

    def close(self):
        #Close the UART connection if it is open
        if getattr(self.serial, "is_open", False):
            self.serial.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _limit_buffer(self):
        if len(self._buffer) > self.max_buffer_size:
            discarded = len(self._buffer) - self.max_buffer_size
            del self._buffer[:discarded]
            self.skipped_bytes += discarded

    def _process_buffer(self): #process packet buffer from 3 byte hex values to integers. returns number of decoded packets
        
        decoded_packets = 0
        while len(self._buffer) >= self.packet_size:
            if self._buffer[:2] != self.packet_header:
                del self._buffer[0]
                self.skipped_bytes += 1
                continue

            packet = self._buffer[: self.packet_size]
            del self._buffer[: self.packet_size]
            self.latest_samples = parse_emg_packet(packet)
            self.packet_count += 1
            decoded_packets += 1

        return decoded_packets