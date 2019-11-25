import PySimpleGUI as sg
from pysrc.config import Config
from pysrc.layout import LayOuts
from pysrc.lisc import LISC
import serial
from multiprocessing import Process

c = Config().dotted_dict()

sg.change_look_and_feel('GreenTan')


class SimpleShootingInterface:
    lo = LayOuts()

    def __init__(self):
        self.layout = self.lo.main_layout()
        self.window = sg.Window("SSI v{}".format(c.SSI.version),
                                layout=self.layout,
                                default_element_size=(40, 1),
                                grab_anywhere=False,
                                size=(str(c.SSI.width), str(c.SSI.height)))

    def loop(self):
        while True:
            event, values = self.window.read()  #timeout=c.SSI.async_timeout)
            print(event, values)
            if event in (None, 'Quit'):
                break

            if 'Change Expected Amount' in event:
                cur_val = self.window['label_expected_amount'].DisplayText
                layout = [[
                    sg.Input("{}".format(cur_val), focus=True, key='input_box')
                ], [sg.Button('Exit', bind_return_key=True)]]

                win2 = sg.Window('Window 2', layout)

                while True:
                    ev2, vals2 = win2.read()
                    if ev2 is None or ev2 == 'Exit':
                        print(ev2, vals2)

                        self.window['label_expected_amount'](str(
                            vals2['input_box']))
                        win2.close()
                        break

            if 'button_inventory' in event:
                with LISC(port='COM5', baudrate=115200, timeout=0) as lisc:
                    elem = self.window['multiline_switch_canvas']
                    bar = self.window['progressbar']
                    anticipated = self.window['label_anticipated_amount']
                    expected = self.window['label_expected_amount'].DisplayText

                    lisc.inventory((elem, bar, anticipated), n=int(expected))

        self.window.close()


if __name__ == "__main__":

    gui = SimpleShootingInterface()
    gui.loop()
