import socket
import time
import sys
import time
from pysrc.config import Config
import PySimpleGUI as sg
from pysrc.switch import Switch, SwitchManager
from pysrc.states_sim import SimStateMachine, SimStates
import subprocess
import time
import os
import datetime
import pysrc.log as log

c = Config()


class SimClient:
    """
    A TCP client that connects to the spawned instance of the switch simulator.
    This class handles all the send/recv protocol between the server
    """

    switch_counter = 0
    """
    This should actually be the reponsibility of the switch manager, need to refactor this.
    """

    switch_manager = SwitchManager()
    """
    keeps track of the emulated switches coming from the simulator
    """
    def __init__(self, server, port, max_timeout=60):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.port = port
        self.max_timeout = max_timeout

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()
        self.stop_server()

    def log(self, msg, status):
        """
        ```python
        input: str, LogType
        return: None
        ```
        Wrapper around log function for easy redirecting of server stdout to file.
        """
        log.log(status)(msg=msg, to=log.LogType.server)

    def connect(self):
        """
        Attempts a connection to the server on designated port.
        """
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

    def read(self, output, timeout=0.01, delay=0.0):
        """
        ```python
        input: sg.Element, float, float
        return: str or Switch
        ```
        Reads from socket.

        Returns a switch object if successfuly,
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
                if len(d) > 0:
                    data.append(d)
            except Exception:
                end = time.time()
        try:
            return "".join([d.decode() for d in data])
        except UnicodeDecodeError:
            # most likely information is a long byte string simulating a switch
            switch = Switch(position=self.switch_counter, raw=data[0])
            if not self.switch_manager.switch_exists(address=switch.address):

                output("Found Switch: {}".format(switch.address))
                self.switch_manager.add(switch)
                self.switch_counter += 1

            return switch
        # return data if parse is not True else "".join(
        #     [d.decode() for d in data])

    def write(self, msg):
        """
        ```python
        input: bytes
        return: None
        ```
        Send a message to the server
        """
        self.socket.sendall(msg)

    def start_server(self):
        """
        Attempts to run external binary that contains the server and switch simulator
        """
        exe = os.getcwd() + "/sf_sim/target/release/sim"
        self.server = subprocess.Popen(["{}".format(exe)])
        self.log(self.server.stdout, 'info')

    def stop_server(self):
        """
        Attempts to close server by sending a terminate signal
        """
        self.server.terminate()

    def shutdown(self):
        """
        Shuts down internal states that relate to connecting to the server
        """
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()


class Simulator:
    """
    Handles the GUI layout and interacts with the SimClient
    to redirect output from the server to the appropriate widgets
    """
    server = None
    """
    SimClient instance
    """

    host = None
    """
    host where server will connect
    """

    port = None
    """
    port where server will connect
    """

    window = None
    """
    main sg.Window object for simulation gui
    """

    gui_timeout = 0.1
    """
    async timeout for gui read/eval loop
    """

    state_handler = None
    """
    a handle to the state machine that directs
    the different states each incoming switch is in.
    """
    def __init__(self, gui):
        self.gui = gui
        self.host = 'localhost'
        self.port = 8000

        layout = self.gui.lo.simulation_layout()
        self.window = sg.Window(
            'Switch Simulator Server {}'.format(c.sim_server("version")),
            layout)

    def log(self, msg, status):
        """
        ```python
        input: str, LogType
        return: None
        ```
        Wrapper around log function for easy redirecting of server stdout to file.
        """
        log.log(status)(msg=msg, to=log.LogType.gui)

    def run(self):
        """
        The main event loop that is spawned from main gui.
        """
        time.sleep(0.1)
        with SimClient(server=self.host, port=self.port) as client:
            connected = False
            while True:
                if not connected:
                    connected = self.attempt_connection(client)

                event, _ = self.window.read(timeout=self.gui_timeout)

                if event == 'button_inventory':
                    client.switch_manager.switches.clear()
                    self.clear()
                    self.server_mode('None Detected')
                    self.output("Scanning for switches...")
                    client.write(b'begin_inventory')
                    self.state_handler = SimStateMachine(SimStates.awaiting)

                data = client.read(output=self.output)

                if event is None or event == 'Exit' or data == 'closed connection':
                    self.log("Remote host closed connection", 'info')
                    self.window.close()
                    break

                if isinstance(data, Switch):
                    # parses data and acts accordingly as well as changes to next
                    # state depending on incoming data
                    self.state_handler.execute(client, data, self)
                elif len(data) > 0:
                    # here we can assume any other data send via socket relates to the status
                    # of which the sim switches are in.. the different modes [status, goidle]
                    switches = client.switch_manager
                    latest_switch = switches.latest_switch
                    msg = "[{}] {}".format(latest_switch, data)
                    self.server_mode(msg)

    def output(self, msg, append=True):
        """
        ```python
        input: str, bool
        return: None
        ```

        update the main sim multiline widget.
        """
        self.gui.write_element(self.window, 'ml_main', msg, append)

    def status_output(self, msg):
        """
        ```python
        intput: str
        return: None
        ```
        update information to the status multiline widget
        """
        self.window.Element('ml_status')(msg)

    def clear(self):
        """
        clear multiline widgets
        """
        self.window.Element('ml_status')('')
        self.window.Element('ml_main')('')

    def server_mode(self, msg):
        """
        ```python
        input: str
        return: None
        ```
        update the current emulated mode of the switches from the simulation server
        """
        self.window.Element('label_server_mode')(msg)

    def update_conn_status(self, msg):
        """
        ```python
        input: str
        return: None
        ```
        update the connection status of the server
        """
        self.window.Element('label_connection_status')(msg)

    def attempt_connection(self, client):
        """
        ```python
        input: SimClient
        return: bool
        ```

        Attempts connection to the server and immediately reads from socket which contains
        server connection status
        """
        status, msg = client.connect()
        if status:
            connection_status = client.read(delay=0.2, output=self.output)
            _, _ = self.window.read(timeout=self.gui_timeout)
            self.update_conn_status(connection_status)
            return True
