from .serial import Serial
from .parser import Parser


class TR1363:
    def __init__(self, port):
        self.port = port
        self.baud = 19200

    def read_status(self):
        serial = Serial(self.port, self.baud)
        status_frame = serial.read_status()
        serial.close()

        parser = Parser()
        status = parser.parse_frame(status_frame)

        return status
