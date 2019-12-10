import PySimpleGUI as sg


class LayOuts:
    def main_menu(self):
        layout = sg.Menu(
            [['Edit', ['Change Expected Amount']], ['Simulation', ['Run']]],
            tearoff=False,
            key='main_menu')

        return layout

    def anticipated_layout(self):
        layout = [[sg.Text('Anticipated', key='label_anticipated')],
                  [
                      sg.Frame('',
                               border_width=1,
                               layout=[
                                   [
                                       sg.Text('0',
                                               size=(2, 1),
                                               font='any 16',
                                               key='label_anticipated_amount')
                                   ],
                               ])
                  ]]
        return layout

    def expected_layout(self):
        layout = [[sg.Text('Expected', key='label_expected')],
                  [
                      sg.Frame('',
                               border_width=1,
                               layout=[
                                   [
                                       sg.Text('3',
                                               size=(2, 1),
                                               font='any 16',
                                               key='label_expected_amount')
                                   ],
                               ])
                  ]]
        return layout

    def column1_layout(self):
        layout = sg.Column(layout=[
            [
                sg.Button("Inventory",
                          bind_return_key=True,
                          size=(20, 3),
                          key='button_inventory'),
                sg.Frame('', border_width=0, layout=self.anticipated_layout()),
                sg.Frame('', border_width=0, layout=self.expected_layout())
            ],
            [
                sg.Multiline(default_text='',
                             size=(51, 15),
                             key='multiline_default_output')
            ],
        ])

        return layout

    def column2_layout(self):
        layout = sg.Column(layout=[
            [
                sg.ProgressBar(1000,
                               orientation='h',
                               size=(33, 20),
                               key='progressbar',
                               visible=False)
            ],
            [
                sg.Multiline(default_text='',
                             size=(25, 30),
                             key='multiline_switch_canvas')
            ],
        ],
                           justification='center')

        return layout

    def main_layout(self):
        layout = [
            [self.main_menu(),
             self.column1_layout(),
             self.column2_layout()],
        ]
        return layout

    def simulation_layout(self):
        layout = [[
            sg.Column(layout=[[
                sg.Text("Awaiting Connection...",
                        key='label_connection_status',
                        size=(20, 1)),
            ], [
                sg.Multiline(key='ml_main', size=(30, 10)),
            ], [
            ], [sg.Button("Start Inventory", key='button_inventory'),
                sg.Exit()]]),
            sg.Column(layout=[[
                sg.Text('Server Mode: ', size=(20,1))],[
                sg.Text('None Detected', size=(20,1), key='label_server_mode')],[sg.Text("Switch Status")],
                [sg.Multiline(key='ml_status', size=(15,10)),]]
            )
            ]]
        return layout

    def vol_temp_layout(self):
        layout = [
            [sg.Text("Voltage", size=(10,1)), sg.Text('Temperature', size=(10,1))],
            [sg.Text("N/A", key="label_voltage", size=(10,1)), sg.Text('N/A', size=(10,1),key='label_temperature')]
        ]
        return layout


