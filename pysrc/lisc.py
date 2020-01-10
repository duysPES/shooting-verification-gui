import sys, os
sys.path.append(os.path.join(sys.path[0], '..'))

import serial
import time
import multiprocessing as mp
from pysrc.switch import SwitchManager, Switch
from pysrc.commands import Commands
from pysrc.thread import ConnMode, InfoType, ConnPackage
import pysrc.log as log
import socket
import select


class Lisc:
    """
    Abstract representation of the embedded device
    that handles the actual communication between computer
    and addressable switch. This class is actually a wrapper 
    around a TCP client, the actual communication with switches
    is done via a seperate Rust server
    """

    package = ConnPackage()
    """
    package object that zips all incoming reponses from switches in a compatible format 
    that is consumed by GUI at the end of the half-duplex sender
    """

    server_ip = "127.0.0.1"
    server_port = 8001
    buffer_size = 1024

    def __init__(self, lisc_port, lisc_ip):
        self.lisc_port = lisc_port
        self.lisc_ip = lisc_ip

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_ip, self.server_port))
        s.settimeout(1)

        self.conn = s

    def log(self, msg, status):
        """
        ```python
        input: str, LogType
        return: None
        ```

        Wrapper around log for quick logging api calls
        """

        log.log(status)(msg=msg, to=log.LogType.gui)

    def do_inventory(self, sender, start_msg):
        """
        ```
        input: queue.Queue, bytes
        return: None
        ```
        The main inventory protocol of the LISC.
        Sends a customed defined `start` message to lisc server
        and relay information back from server until a designated 
        `stop` signal is recieved

        """
        self.package.set_sender(sender)
        resp = self.send_recv(start_msg, timeout=1)
        self.log(resp, 'info')
        while 1:
            resp = self.listen(timeout=1)
            if resp == b"DONE":
                self.package.done()
                break

            elif resp != b"":
                self.process(resp)

    def process(self, data: bytes):
        resp: list = data.decode().upper().split(",")
        info, mode, msg = resp[0], resp[1], resp[2:]
        msg = "".join(msg)
        self.package.from_lisc_server(info, mode, msg)

    def send_recv(self, msg, timeout=1):
        self.send(msg)
        return self.listen(timeout=timeout)

    def send(self, msg):
        """
        ```
        input: bytes, int
        return: None
        ```
        Sends information to lisc server
        """
        self.conn.send(msg)

    def listen(self, timeout=1):
        """
        ```
        input: int
        return: bytes
        ``` 
        waits and listens for information from lisc server every `poll` seconds
        """
        self.conn.settimeout(timeout)
        while 1:
            try:
                data = self.conn.recv(self.buffer_size)
                if len(data) > 0:
                    return data

            except socket.timeout:
                print(f"Timeout occured")
                return b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


if __name__ == "__main__":
    with Lisc() as lisc:
        lisc.do_inventory()