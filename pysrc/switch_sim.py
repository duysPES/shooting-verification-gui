import socket
import time
import sys
import time

import PySimpleGUI as sg
from pysrc.switch import Switch, SwitchManager
from pysrc.states_sim import SimStateMachine, SimStates


class SimClient:
    switch_counter = 0
    switch_manager = SwitchManager()
    max_timeout = 5

    def __init__(self, server, port, max_timeout=60):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.port = port
        self.max_timeout = max_timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print('cleaning up resources')
        self.shutdown()

    def connect(self):
        # attempt to connect to supplied sim server
        start = time.time()
        elapsed_time = 0

        while 1:
            if elapsed_time >= self.max_timeout:
                return (False, "Unable to connect to socket..")

            try:
                self.socket.connect((self.server, self.port))
                return (True, "Successfully connected to: {}".format(
                    self.socket.getpeername()))
            except Exception:
                elapsed_time = time.time() - start

    def read(self, timeout=0.01, delay=0.0):
        """
        Will return a switch object if successfuly,
        otherwise will return "closed connection" object
        """

        start = time.time()
        end = start
        data = []

        time.sleep(delay)
        while 1:
            if (end - start) >= timeout:
                break
            try:

                d = self.socket.recv(16, socket.MSG_DONTWAIT)
                if len(d) == 0:
                    data = []
                    data.append(b'closed connection')
                    break

                data.append(d)
            except Exception:
                end = time.time()

        try:
            return "".join([d.decode() for d in data])
        except UnicodeDecodeError:
            # most likely information is a long byte string simulating a switch
            switch = Switch(position=self.switch_counter, raw=data[0])
            if not self.switch_manager.switch_exists(address=switch.address):
                self.switch_manager.add(switch)
                self.switch_counter += 1

            return switch
        # return data if parse is not True else "".join(
        #     [d.decode() for d in data])

    def write(self, msg):
        self.socket.sendall(msg)

    def shutdown(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()


class Simulator:
    server = None
    port = None
    window = None
    gui_timeout = 0.1
    state_handler = None

    def __init__(self, gui):
        self.gui = gui
        self.server = 'localhost'
        self.port = 8000

        layout = self.gui.lo.simulation_layout()
        self.window = sg.Window('Switch Simulator Server', layout)

    def run(self):
        with SimClient(server=self.server, port=self.port) as client:
            connected = False
            while True:
                if not connected:
                    connected = self.attempt_connection(client)

                event, _ = self.window.read(timeout=self.gui_timeout)

                if event == 'button_inventory':
                    self.output("Scanning for switches...")
                    client.write(b'begin_inventory')
                    self.state_handler = SimStateMachine(SimStates.awaiting)

                data = client.read()

                if event is None or event == 'Exit' or data == 'closed connection':
                    print("Remote host closed connection")
                    self.window.close()
                    break

                if isinstance(data, Switch):
                    # parses data and acts accordingly as well as changes to next
                    # state depending on incoming data
                    self.state_handler.execute(client, data)

    def output(self, msg, append=True):
        self.gui.write_element(self.window, 'ml_main', msg, append)

    def update_conn_status(self, msg):
        self.window.Element('label_connection_status')(msg)

    def attempt_connection(self, client):
        status, msg = client.connect()
        if status:
            print(msg)
            connection_status = client.read(delay=0.2)
            print(connection_status)
            _, _ = self.window.read(timeout=self.gui_timeout)
            self.update_conn_status(connection_status)
            return True
