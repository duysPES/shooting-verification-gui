import PySimpleGUI as sg
from pysrc.config import Config
from pysrc.layout import LayOuts
import serial
from multiprocessing import Process
from multiprocess.connection import wait
from pysrc.threads import Thread, ThreadProcesses, MultiWorkers, ConnMode, InfoType
from pysrc.lisc import LISC
from pysrc.errors import NotValidInfoType, NotValidModeType, ConnPackageSwitchValueError
from pysrc.switch_sim import SimClient, Simulator
from pysrc.states_sim import SimStates, SimStateMachine

c = Config().dotted_dict()

sg.change_look_and_feel('GreenTan')


class SimpleShootingInterface:
    lo = LayOuts()
    workers = MultiWorkers(max_workers=2)

    def __init__(self):
        self.layout = self.lo.main_layout()
        self.window = sg.Window("SSI v{}".format(c.SSI.version),
                                layout=self.layout,
                                default_element_size=(40, 1),
                                grab_anywhere=False,
                                size=(str(c.SSI.width), str(c.SSI.height)))

    def send_to_multiline(self, widget, msg, clear=False):
        if clear:
            widget(msg)
        else:
            current = widget.get()
            new_string = current + str(msg)
            widget(new_string)

    def write_element(self, window, key, msg, append=True):

        ele = window.Element(key)
        try:
            ele.update(msg + '\n', append=append)
        except Exception:
            print("label here", msg, ele)
            ele.DisplayText = msg

    def send_to_main(self, msg, clear=False):
        widget = self.window['multiline_switch_canvas']
        self.send_to_multiline(widget=widget, msg=msg, clear=clear)

    def send_to_debug(self, msg, clear=False):
        widget = self.window['multiline_default_output']
        self.send_to_multiline(widget=widget, msg=msg, clear=clear)

    def update_anticipated(self, num):
        widget = self.window['label_anticipated_amount']
        widget(str(num))

    def loop(self):
        while True:
            event, values = self.window.read(timeout=c.SSI.async_timeout)
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
                expected = self.window['label_expected_amount'].DisplayText
                self.send_to_debug("Expecting {} switches...".format(expected))
                func = ThreadProcesses.do_inventory
                args = (LISC, int(expected), True
                        )  # args: (LISC, use_worker[async])
                thread_name = "do_inventory"
                self.workers.thread(name=thread_name, func=func,
                                    args=args).start()

            for parent in self.workers.get_parents():
                if parent.poll():
                    try:
                        msg = parent.recv()

                        self.parse_type(msg)
                        # self.send_to_debug(msg="Incoming switch..", clear=False)

                        # for switch in msg:
                        #     switch_msg = "[{}] {}".format(switch[0], switch[1])
                        #     self.send_to_main(msg=switch_msg, clear=False)
                        #     self.update_anticipated(num=len(msg))

                    except EOFError:
                        # no more data to read and other end was clsoed
                        thread = self.workers.find_thread_by_parent(parent)
                        self.workers.remove(thread)
                    else:
                        pass

        self.window.close()

    def parse_type(self, msg):
        latest = msg[-1]
        infotype, mode, payload = latest

        if infotype == InfoType.OTHER:
            self.send_mode(mode, payload)

        elif infotype == InfoType.SWITCH:
            if not isinstance(payload, (tuple, list)):
                raise ConnPackageSwitchValueError
            # add length of list where InfoType is SWITCH to msg
            # at this point if InfoType is for switch, msg WILL be tuple

            num_switch_msgs = 0
            for m in msg:
                print(m)
                if m[0] == InfoType.SWITCH:
                    num_switch_msgs += 1
            pos, addr = payload
            # display switches to canvas
            main_canvas_msg = "[{}] {}".format(pos, addr)

            # update anticipated amount based on number of switch messages recieved
            self.update_anticipated(num=num_switch_msgs)

            self.send_mode(mode, main_canvas_msg)

        else:
            raise NotValidInfoType

    def send_mode(self, mode, payload):
        if mode == ConnMode.DEBUG:
            self.send_to_debug(msg=payload, clear=False)
        elif mode == ConnMode.MAIN:
            self.send_to_main(msg=payload, clear=False)
        else:
            raise NotValidModeType


if __name__ == "__main__":

    gui = SimpleShootingInterface()
    gui.loop()
