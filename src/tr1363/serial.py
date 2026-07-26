"""Handles serial communications only."""

import serial


class Serial:
    def __init__(self, port, baud):
        self.ser = serial.Serial(
            port,
            baud,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
        )

        print(self.ser.get_settings())

    def read_status(self):
        request = b"~22014A42E00201FD28\r"

        print(f"Sending request {request}...")
        self.ser.reset_input_buffer()
        self.ser.write(request)

        frame = self.ser.read_until(b"\r")
        print("\nASCII response:")
        print(frame)

        return frame

    def close(self):
        self.ser.close()
