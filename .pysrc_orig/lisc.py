import serial
import time
import multiprocessing as mp
from pysrc.threads import MultiWorkers, ThreadProcesses
from pysrc.errors import ChkSumError, IncorrectPayLoad, ErrorCodes
from pysrc.switch import SwitchManager, Switch


class LISC(serial.Serial):
    incoming_buffer = []
    workers = MultiWorkers()
    switch_manager = SwitchManager()

    def echo(self):
        """
        Opens up port and prints any output to stdout
        """
        func = ThreadProcesses.loop_and_read
        args = (
            self,
            5,
        )  # loop_and_read args (ser, timeout)
        self.workers.thread(name='echo', func=func, args=args).start()

        parent = self.workers.threads['echo'].parent
        while 1:
            try:
                print(parent.recv(), end="")
            except EOFError:
                break

    def send(self, byte_string):
        """
        Send byte string on connected port
        """
        self.write(byte_string)

    def get_response_from_parent(self, parent):

        while parent.poll(timeout=5):
            try:
                return parent.recv()
            except EOFError:
                return None

    def get_response_from_thread(self, thread_name):
        thread = self.workers.threads[thread_name]
        response = self.get_response_from_parent(thread.parent)
        return response

    def recieve(self, timeout=5, use_worker=True):
        """
        Listens on port channel for incoming information
        returns information.

        Has ability to spawn a async task by using avaiable worker.
        """
        if not use_worker:  #turn this method into sync one
            response = ThreadProcesses.recieve_bytes(None, self, timeout)
            return response

        func = ThreadProcesses.recieve_bytes
        args = (self, 1)  # recieve_bytes func args: (ser, timeout)
        thread_name = 'recieve_bytes'
        self.workers.thread(name=thread_name, func=func, args=args).start()

        response = self.get_response_from_thread(thread_name)
        return response

    def parse_response(self, response, expected=None):
        """
        method parses responses from switches ONLY, not LISC itself.
        Therefore ALL switches will begin with it's address. Reject response 
        if payload is less than 4 bytes long addr+chksum
        """

        if len(response) < 4:
            # either corrupt package or LISC response
            return None
        else:
            #perform chksum on data to make sure it matches
            if not self.chksum_ok(response):
                raise ChkSumError()

            raw_address = response[:3]
            address = raw_address.hex()
            payload = response[3:-1]

            if expected != payload and expected is not None:
                raise IncorrectPayLoad

            if not self.switch_manager.switch_exists(address=address):
                num = self.switch_manager.num
                switch = Switch(position=num + 1, raw=raw_address)
                self.switch_manager.add(sw=switch)
            else:
                print("Switch Exists")

            return switch

    def bytearray_to_hex(self, arr):
        return "".join([i.hex() for i in arr])

    def chksum_ok(self, data):
        if not isinstance(data, bytes):
            raise ValueError("Incoming data must be a collection")

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
        return a list of data with included checksum
        """
        if not isinstance(data, list):
            data = list(data)
        chksum = 0
        for element in data:
            chksum ^= element

        data.append(chksum)

        return data

    def delay(self, seconds):
        start = time.time()

        while time.time() - start <= seconds:
            continue

    def create_command_packet_for(self, switch, cmd, to_bytearray=True):
        # command structure {3byte id}{payload}{chksum}
        packet = switch.raw_address + [cmd.value]
        packet = self.chksum(packet)
        print("Packet: ", packet)
        return bytearray(packet) if to_bytearray is True else packet

    def reset(self):
        self.send(b'zl')
        self.delay(3)
        self.send(b'zL')


if __name__ == "__main__":
    # ser = LISC(port='/dev/ttyUSB0', baudrate=9600, timeout=0)
    # ser.listen()
    # ser.close()
    with LISC(port='/dev/ttyUSB0', baudrate=9600, timeout=1) as lisc:
        print("Connected to :", lisc.portstr)
        # lisc.echo()
        lisc.reset()
        print("LISTENING")
        response = lisc.recieve(timeout=1)
        print("MADE IT HERE")
        print(response, lisc.parse_response(response))
        lisc.workers.wait_for_workers()
        print("DONE WITH MAIN THREAD")
