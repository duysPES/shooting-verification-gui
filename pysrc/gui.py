import PySimpleGUI as sg
from pysrc.config import Config
from pysrc.layout import LayOuts
import serial
from pysrc.lisc import LISC
from pysrc.switch_sim import SimClient, Simulator
from pysrc.states_sim import SimStates, SimStateMachine
from multiprocessing import Process, Queue
import time
from pysrc.thread import InfoType, ConnMode
from collections import deque
from pysrc.switch import Switch
from pysrc.commands import Status, Commands

c = Config()

sg.change_look_and_feel('GreenTan')


class SimpleShootingInterface:
    """
    Main Program handler. Controls GUI that users will be using
    to inventory addressable switches, and running switch simulator
    """

    lo = LayOuts()
    """
    variable to helper class that stores all layouts for PySimpleGui
    """

    inventory_queue = Queue()
    """
    thread-safe *half-duplex* channel that is used when moving
    entire inventory process on a seperate thread. This allows for communication
    back to main thread.
    """

    def __init__(self):
        self.layout = self.lo.main_layout()
        self.window = sg.Window("",
                                layout=self.layout,
                                default_element_size=(40, 1),
                                grab_anywhere=False,
                                size=(str(c.ssi("width")),
                                      str(c.ssi("height"))),
                                finalize=True)
        self.set_window_title()

    def send_to_multiline(self, widget, msg, clear=False):
        """
        ```
        input: sg.Element, str, bool
        return: None
        ```
        helper method to update a tk multiline element

        ```python
        my_widget = window['label']
        send_to_multiline(my_widget, msg="hello, world", clear=False)

        print(my_widget.DisplayText) # "hello, world"
        ```
        """

        if clear:
            widget(msg)
        else:
            current = widget.get()
            new_string = current + str(msg)
            widget(new_string)

    def write_element(self, window, key, msg, append=True):
        """
        ```
        input: sg.Window, str, str, bool
        return: None
        ```
        same functionality as send_to_multiline except you can 
        specifiy sg.Window object.

        """

        ele = window.Element(key)
        try:
            ele.update(msg + '\n', append=append)
        except Exception:
            print("label here", msg, ele)
            ele.DisplayText = msg

    def send_to_main(self, msg, clear=False):
        """
        ```
        input: str, bool
        return: None
        ```
        helper method to update main multiline element in 
        GUI, where Switch information is posted.
        """
        widget = self.window['multiline_switch_canvas']
        self.send_to_multiline(widget=widget, msg=msg, clear=clear)

    def send_to_debug(self, msg, clear=False):
        """
        ```
        input: str, bool
        return: None
        ```
        helper method to update multiline that serves as debug output.

        """
        widget = self.window['multiline_default_output']
        self.send_to_multiline(widget=widget, msg=msg, clear=clear)

    def update_anticipated(self, num):
        """        
        ```
        input: str
        return: None
        ```
        helper method to update number of anticipated switches

        """
        w = self.window['label_anticipated_amount']
        w(num)

    def set_window_title(self, msg=""):
        """
        ```
        input: str
        return: None
        ```
        Set window title.

        """
        msg = "SSI v{} {}".format(c.ssi("version"), msg)
        self.window.TKroot.title(msg)

    def loop(self):
        """
        **main program loop, this is where ALL 
        the magic happens.**

        ```python
        gui.loop()
        # things crash
        # things burn
        # things take over the world.
        ```
        """

        inventory = False
        vol_temp_window = None

        while True:
            event, values = self.window.read(timeout=c.ssi('async_timeout'))
            if event != '__TIMEOUT__':
                print(event, values)
            if event in (None, 'Quit'):
                break

            if 'Change Expected Amount' in event:
                cur_val = self.window['label_expected_amount'].DisplayText
                layout = [[
                    sg.Input("{}".format(cur_val), focus=True, key='input_box')
                ], [sg.Button('Exit', bind_return_key=True)]]
                win2 = sg.Window("Edit Expected Amount")

                while True:
                    ev2, vals2 = win2.read()
                    if ev2 is None or ev2 == 'Exit':
                        print(ev2, vals2)

                        self.window['label_expected_amount'](str(
                            vals2['input_box']))
                        win2.close()
                        break

            if 'Run' == values['main_menu']:
                simulator = Simulator(self)
                simulator.run()

            if 'button_inventory' in event:
                inventory = True
                self.set_window_title()
                with LISC(port='/dev/ttyS6', baudrate=9600, timeout=0) as lisc:
                    thread = Process(target=lisc.do_inventory,
                                     args=(self.inventory_queue, ))
                    thread.start()
                    # thread.join()

            if inventory:
                try:
                    # returns a deque object with information
                    msgs = self.inventory_queue.get_nowait()
                    if not isinstance(msgs, deque):
                        raise ValueError(
                            "Message from queue is not ConnPackage obj")

                    if len(msgs) > 0:

                        info_type, mode, msg = msgs
                        if info_type == InfoType.KILL:
                            self.send_mode(mode, "Done with Inventory")
                            inventory = False

                        if info_type == InfoType.SWITCH:

                            if mode == ConnMode.STATUS:
                                pos, addr, status = msg
                                self.send_mode(mode, status)

                            if mode == ConnMode.MAIN:
                                pos, addr = msg
                                self.update_anticipated(num=int(pos))
                                msg = "--> {}: [{}]".format(pos, addr)
                                self.send_mode(mode, msg)

                        if info_type == InfoType.OTHER:
                            self.send_mode(mode, msg)

                except Exception:
                    pass

        self.window.close()

    def send_mode(self, mode, payload):
        """
        ```
        input: ConnMode, PyObj
        return: None
        ```

        a proxy method that takes incoming data from 
        the queue object, and updates applicable elements
        within the main gui based on Connection Mode and InfoTypes
        found in packets.
        """

        if mode == ConnMode.DEBUG:
            self.send_to_debug(msg=payload, clear=False)
        elif mode == ConnMode.MAIN:
            self.send_to_main(msg=payload, clear=False)

        elif mode == ConnMode.STATUS:
            status = Status(status)
            voltage = status.voltage
            temp = status.temp

            msg = "{}V, {}C".format(voltage, temp)
            self.set_window_title(msg=msg)
        else:
            raise TypeError("Not a valid enum state")


