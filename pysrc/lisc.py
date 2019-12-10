import serial
import time
import multiprocessing as mp
from pysrc.errors import ChkSumError, IncorrectPayLoad, ErrorCodes
from pysrc.switch import SwitchManager, Switch
from pysrc.commands import Commands
from pysrc.thread import ConnMode, InfoType, ConnPackage


class LISC(serial.Serial):
    incoming_buffer = []
    switch_manager = SwitchManager()
    package = ConnPackage()

    def do_inventory(self, sender):
        # package = ConnPackage(queue)
        self.package.set_sender(sender)
        self.package.debug("Resetting LISC")
        self.reset()
        # response = self.read_serial(lisc)
        for i in range(3):
            # listen for broadcast address
            broadcast_response = self.listen()
            print("broadcast ", broadcast_response.hex())

            # internally create a switch obj
            switch = Switch(position=i + 1, raw=broadcast_response)
            self.package.switch(switch)  # sending switch contents via sender
            self.switch_manager.add(switch)

            status_cmd = switch.gen_package(Commands.SendStatus.value)
            self.package.debug("Sending command: {}".format(status_cmd.hex()))
            response = self.send(status_cmd)
            self.package.debug("Response: {}".format(response.hex()))
            self.switch_manager.update(switch, response)
            self.package.switch_status(switch)

            go_inactive = switch.gen_package(Commands.GoInactive.value)
            self.package.debug("Sending command: {}".format(go_inactive.hex()))
            response = self.send(go_inactive)
            self.package.debug("Response: {}".format(response.hex()))

            self.switch_manager.update(switch, response)
            # self.package.switch(switch)
            time.sleep(2)

        self.package.done()

    def send(self, msg, tries=5):
        """
        Send byte string on connected port, and listen for response
        returns only the body of packet
        """
        attempt = 0
        response = b""
        body = None
        while 1:
            if attempt == tries:
                err = \
                """
                Incorrect response recieved from switch.
                Last response is: 0x{}
                """.format(response.hex())
                raise serial.SerialException(err)

            # attempt to write to stream
            self.write(msg)
            response = self.listen()

            body = response[3:-1]

            # checking checksum
            if not self.chksum_ok(msg):
                attempt += 1
                self.package.debug("Chksum incorrect")
                continue

            # most likely a successful attempt, if it passes
            if len(body) > 1:
                self.package.debug("Receiving status message")
                break
            elif len(body) == 1:
                if body == Commands.ACK.value:
                    self.package.debug("ACK Recieved")
                    break
                else:
                    self.package.debug("NACK recieved trying again..")
                    attempt += 1
                    continue
            else:
                attempt += 1

        return response

    def listen(self, timeout=3, tries=5):
        now = time.time()
        buf = b""

        while time.time() - now <= timeout:
            in_waiting = self.inWaiting()
            if in_waiting > 0:
                buf += self.read(in_waiting)
                now = time.time()
        return buf

    def bytearray_to_hex(self, arr):
        return "".join([i.hex() for i in arr])

    def chksum_ok(self, data):
        if not isinstance(data, bytes):
            raise ValueError("Incoming data must be a bytes")

        good_data = True

        supplied_chksum = data[-1]
        calculated_chksum = 0

        for idx in range(len(data) - 1):
            calculated_chksum ^= data[idx]

        if calculated_chksum != supplied_chksum:

            print("Checksums do not match: {}/{}".format(
                calculated_chksum, supplied_chksum))
            return not good_data

        return good_data

    def chksum(self, data):
        """
        return a bytes of data with included checksum
        """
        chksum = 0
        if not isinstance(data, bytes):
            data = bytes([data])

        for element in data:
            chksum ^= element

        data += bytes([chksum])

        return data

    def delay(self, seconds):
        start = time.time()

        while time.time() - start <= seconds:
            continue

    def reset(self):
        self.write(b'zl')
        self.delay(2)
        self.write(b'zL')
