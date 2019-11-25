import serial
import time
from multiprocessing import Process


class LISC(serial.Serial):
    incoming_buffer = None

    def __init(self, *args, **kwargs):
        super(LISC, self).__init__(self, args, kwargs)

    def inventory(self, package, n=1):
        i = 0
        elem, bar, anti = package
        bar(visible=True)
        output = []

        while i <= n:
            line = self.readline()
            if b'' != line:
                output.append("0x" + line.decode())
                elem("".join(output))
                anti(i)
                bar.UpdateBar((i + 1) * (1000 / n))
                i += 1

        bar(visible=False)


if __name__ == "__main__":
    ser = LISC(port='COM5', baudrate=115200, timeout=0)
    ser.listen()
    ser.close()

    print("Connected to :", ser.portstr)
