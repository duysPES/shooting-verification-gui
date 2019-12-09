import PySimpleGUI as sg
from pysrc.config import Config
from pysrc.layout import LayOuts
import serial
from pysrc.lisc import LISC
from pysrc.switch_sim import SimClient, Simulator
from pysrc.states_sim import SimStates, SimStateMachine
from multiprocessing import Process, Queue
import time
from pysrc.thread import InfoType

c = Config().dotted_dict()

sg.change_look_and_feel('GreenTan')


class SimpleShootingInterface:
    lo = LayOuts()
    inventory_queue = Queue()

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
        inventory = False

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
                inventory = True
                from pysrc.commands import Commands
                with LISC(port='/dev/ttyS6', baudrate=9600, timeout=0) as lisc:
                    thread = Process(target=lisc.do_inventory,
                                     args=(self.inventory_queue, ))
                    thread.start()
                    # thread.join()

            if inventory:
                try:
                    from_queue = self.inventory_queue.get_nowait()
                    if len(from_queue) > 0:
                        info_type = from_queue[0]

                        if info_type == InfoType.KILL:
                            inventory = False

                        for item in from_queue:
                            print(item)
                except Exception:
                    pass

        self.window.close()

    # def parse_type(self, msg):
    #     #print('msg: ', msg)
    #     latest = msg[-1]
    #     infotype, mode, payload = latest
    #     #print("payload: ", payload)

    #     if infotype == InfoType.OTHER:
    #         self.send_mode(mode, payload)

    #     elif infotype == InfoType.SWITCH:
    #         if not isinstance(payload, bytes):
    #             print("value: {}, type: {}".format(payload, type(payload)))
    #             raise ConnPackageSwitchValueError()
    #         # add length of list where InfoType is SWITCH to msg
    #         # at this point if InfoType is for switch, msg WILL be tuple

    #         num_switch_msgs = 0
    #         for m in msg:
    #             print("Message: ", m)
    #             if m[0] == InfoType.SWITCH:
    #                 num_switch_msgs += 1
    #         pos, addr = payload
    #         # display switches to canvas
    #         main_canvas_msg = "[{}] {}".format(pos, addr)

    #         # update anticipated amount based on number of switch messages recieved
    #         self.update_anticipated(num=num_switch_msgs)

    #         self.send_mode(mode, main_canvas_msg)

    #     else:
    #         raise NotValidInfoType

    # def send_mode(self, mode, payload):
    #     if mode == ConnMode.DEBUG:
    #         self.send_to_debug(msg=payload, clear=False)
    #     elif mode == ConnMode.MAIN:
    #         self.send_to_main(msg=payload, clear=False)
    #     else:
    #         raise NotValidModeType


if __name__ == "__main__":

    gui = SimpleShootingInterface()
    gui.loop()
