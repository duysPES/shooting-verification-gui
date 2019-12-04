import socket
import sys
import time
import struct
MAX_TIMEOUT = 5


class Switch:
    def __init__(self, raw_bytes):
        decoded = list(struct.unpack("B" * len(raw_bytes), raw_bytes))

        self.id = decoded[:2]
        self.chksum = decoded[-1]
        self.package = decoded[2:-1]

    @property
    def hex_id(self):
        return "0x" + "".join(["{:x}".format(i) for i in self.id])


class SimClient:
    def __init__(self, server, port, max_timeout=60):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.port = port
        self.max_timeout = max_timeout

    def connect(self):
        # attempt to connect to supplied sim server
        start = time.time()
        elapsed_time = 0

        while 1:
            if elapsed_time >= MAX_TIMEOUT:
                print("Unable to connect to socket..")
                sys.exit(-1)

            try:
                self.socket.connect((self.server, self.port))
                break
            except Exception:
                elapsed_time = time.time() - start

        print("Successfully connected to: {}".format(
            self.socket.getpeername()))

    def read(self, timeout=0.01):
        start = time.time()
        end = start
        data = []

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
            switch = Switch(data[0])

            return switch.hex_id
        # return data if parse is not True else "".join(
        #     [d.decode() for d in data])

    def write(self, msg):
        self.socket.sendall(msg)


if __name__ == "__main__":

    import PySimpleGUI as sg
    server_response = "Server response: \"{}\""
    addr = "addr: {}"
    state = 'state: {}'
    layout = [[
        sg.Text("", key='label_connection_status', size=(30, 1)),
    ], [
        sg.Button("Test", key='button_test'),
    ],
              [
                  sg.Text(addr.format(""), key='text_addr', size=(10, 1)),
                  sg.Text(state.format(""), key='text_state', size=(30, 1))
              ], [
                  sg.Multiline(key='ml_main', size=(30, 10)),
              ], [
                  sg.Input(),
              ],
              [
                  sg.Button("Begin Inventory", key='button_inventory'),
                  sg.Exit()
              ]]

    window = sg.Window("Sim Server", layout)

    def write_main(msg):
        window.Element('ml_main').update(msg + '\n', append=True)

    def write_element(key, msg):

        ele = window.Element(key)
        try:
            ele.update(msg + '\n')
        except Exception:
            ele.DisplayText = msg

    client = SimClient(server='localhost', port=8000)
    client.connect()
    startup_msg = client.read()
    # print("Startup", startup_msg)
    event, values = window.read(timeout=0.01)
    write_element('label_connection_status', startup_msg)

    while True:
        event, values = window.read(timeout=0.01)
        if event is None or event == "Exit":
            break

        if event == "button_inventory":
            write_main("Scanning for switches...")
            client.write(b"begin_inventory")

        if event == 'button_test':
            client.write(b"test")

        # if event == 'button_state':
        #     client.write(b'next_state')
        #     # expecting results: (addr, state)
        #     data = client.read()
        #     data = data.split(',')

        #     if data[0] == "closed connection":
        #         print("Host terminated connection: socket closed")
        #         sys.exit(-1)

        #     window['text_addr'](addr.format(hex(int(data[0]))))
        #     window['text_state'](state.format(data[1]))

        data = client.read()

        if data == 'closed connection':
            print("Remote Host closed connection")
            break

        if len(data) > 0:
            print("Data: ", data)
            write_main(data)

    window.close()

    # data = client.read()
    # client.write(b"Hello from client")
