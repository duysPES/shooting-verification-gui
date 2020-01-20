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
import pysrc.log as log
from pysrc.log import LogType
from pysrc.credentials import check_credentials

from pysrc.log import LOG_PATH

c = Config()

sg.change_look_and_feel('GreenTan')

log.Log.clear()


class SSI:
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
                                size=(c.ssi("width"), c.ssi("height")),
                                finalize=True)
        self.set_window_title()

    @staticmethod
    def log(msg, status='info'):
        """
        ```python
        input: str
        return: None
        ```
        Wrapper around log object to verify that output from GUI is going to gui.log
        """
        log.log(status)(msg, log.LogType.gui)

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

    def reset_elements(self):
        """
        resets all elements to their default values
        """

        self.send_to_main("", clear=True)
        self.send_to_debug("", clear=True)
        self.update_anticipated(0)

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

    def set_window_title_dangerous(self, msg=""):
        """
        Sets window title with prepended DANGER
        """
        msg = f"SSI v{c.ssi('version')} DANGER: {msg}"
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
        dangerzone = False
        # set both multiline elements to autoscroll
        self.window.FindElement(
            key='multiline_default_output').Autoscroll = True

        self.window.FindElement(
            key='multiline_switch_canvas').Autoscroll = True

        while True:
            event, values = self.window.read(timeout=c.ssi('async_timeout'))
            if event != '__TIMEOUT__':
                pass
            if event in (None, 'Quit'):
                break

            if dangerzone:
                from pysrc.danger import DangerousLISC
                log.Log.clear(LogType.gui)
                self.send_to_debug("", clear=True)
                self.send_to_main("", clear=True)
                self.log("Beginning Dangerous inventory run", 'warning')
                inventory = True
                self.set_window_title_dangerous()

                expected_switches = self.read_expected()
                self.send_to_debug(f"Expecting {expected_switches} switches..")

                port = str(c.lisc('port'))
                baudrate = int(c.lisc('baudrate'))
                with DangerousLISC(port=port, baudrate=baudrate,
                                   timeout=3) as lisc:
                    self.log("Spawning thread for dangerous inventory run",
                             'warning')
                    thread = Process(target=lisc.do_dangerous_inventory,
                                     args=(self.inventory_queue,
                                           expected_switches))
                    thread.start()
                dangerzone = False

            if 'Danger Zone' in event:
                layout = [[sg.Text("Please enter valid credentials")],
                          [
                              sg.Text("Username: "),
                              sg.Input(key="username_input", password_char="*")
                          ],
                          [
                              sg.Text("Password: "),
                              sg.Input(key="password_input", password_char="*")
                          ], [sg.Submit(size=(10, 1))],
                          [sg.Text("", key="status_label", size=(20, 1))]]

                win2 = sg.Window("Firing Override",
                                 layout=layout,
                                 size=(300, 150),
                                 finalize=True)
                while True:
                    ev2, vals2 = win2.read()
                    if ev2 is None or ev2 == "Exit":
                        break

                    if ev2 == "Submit":
                        dangerzone = True
                        win2.close()
                        break
                        user = vals2['username_input']
                        pwd = vals2['password_input']
                        if check_credentials(user, pwd):
                            dangerzone = True
                            win2.close()
                            break
                        else:
                            print("incorrect")
                            win2['status_label']("Incorrect Credentials")

            if 'Change Expected Amount' in event:
                amnts = [x + 1 for x in range(30)]
                layout = [
                    [
                        # sg.Input("{}".format(cur_val), focus=True, key='input_box')
                        sg.Spin(amnts,
                                initial_value=c.switches('expected'),
                                key='input_box',
                                size=(50, 100),
                                font=('any 24'))
                    ],
                    [sg.Button('Exit', bind_return_key=True)]
                ]
                win2 = sg.Window("Edit Expected Amount",
                                 layout=layout,
                                 size=(300, 300))

                while True:
                    ev2, vals2 = win2.read()
                    if ev2 is None or ev2 == 'Exit':
                        # set config

                        c.update_switches('expected',
                                          str(vals2['input_box']),
                                          dump=True)
                        self.window['label_expected_amount'](str(
                            vals2['input_box']))
                        win2.close()
                        break

            if 'Run' == values['main_menu']:
                self.send_to_debug(
                    "Would normally start simulation server, but that has been disabled for now."
                )
                # self.log('Beginning simulation', 'info')
                # simulator = Simulator(self)
                # simulator.run()

            if 'View Logs' == values['main_menu']:
                layout = [[
                    sg.Multiline("",
                                 size=(c.ssi('width'), c.ssi('height')),
                                 key="log_view")
                ]]
                log_view = sg.Window("Logs",
                                     layout=layout,
                                     grab_anywhere=False,
                                     size=(c.ssi("width"), c.ssi("height")),
                                     finalize=True)

                while True:
                    ev2, vals2 = log_view.read(timeout=3)

                    with open(LOG_PATH + "gui.log", "r") as l:
                        buffer = l.read()
                        log_view['log_view'](buffer)

                    if ev2 is None or ev2 == 'Exit':
                        log_view.close()
                        break

            if 'button_inventory' in event:
                # clear elements
                log.Log.clear(LogType.gui)
                self.send_to_debug("", clear=True)
                self.send_to_main("", clear=True)
                self.log("Beginning inventory run", 'info')
                inventory = True
                self.set_window_title()

                expected_switches = self.read_expected()
                self.send_to_debug(f"Expecting {expected_switches} switches..")

                port = str(c.lisc('port'))
                baudrate = int(c.lisc('baudrate'))
                with LISC(port=port, baudrate=baudrate, timeout=3) as lisc:
                    self.log("Spawning thread for inventory run", 'info')
                    thread = Process(target=lisc.do_inventory,
                                     args=(self.inventory_queue,
                                           expected_switches))
                    thread.start()

            if inventory:
                try:
                    # returns a deque object with information
                    msgs = self.inventory_queue.get_nowait()
                    if not isinstance(msgs, deque):
                        """
                        This piece of code should never run, if it does it is a programmer induced bug
                        and not the users fault. msgs is in incorrect format, the entire program will
                        not work as intended. Instead of exiting the programming, simply stop the inventory
                        process and default back to normal GUI.
                        """
                        inventory = False  # turn off inventory
                        errmsg = \
                        """
                        Message from queue is not a ConnPackage, fatal error. Program will
                        not work as expected
                        """
                        self.log(errmsg, 'error')

                    elif len(msgs) > 0:

                        info_type, mode, msg = msgs
                        if info_type == InfoType.KILL:
                            msg = "Done with inventory process"
                            self.send_mode(mode, msg)
                            inventory = False
                            self.log(msg, "info")

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

                    else:
                        # here for brevity
                        pass

                except Exception:
                    pass

        self.window.close()
        self.log("Main Gui loop closing", "info")

    def read_expected(self):
        """
        ```python
        input: None
        return: int
        ```
        Helper method that returns the number for anticipated switches
        from label. Attempts to convert to int, with some error checking.
        If it fails the conversion it will by default return `1`
        """
        num = self.window['label_expected_amount'].DisplayText
        try:
            num = int(num)
        except ValueError:
            num = 1

        return num

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
            status = Status(payload)
            voltage = status.voltage
            temp = status.temp
            msg = "{}V, {}C".format(voltage, temp)
            self.set_window_title(msg=msg)
        else:
            errmsg = \
                """
                This block should never run. Input ConnMode from 
                thread supplies an invalid enum type, mode: {}
                """.format(mode)
            self.log(errmsg, 'error')
