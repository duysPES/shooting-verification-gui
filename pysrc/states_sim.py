## possible states
from pysrc.switch import Switch
from pysrc.commands import Commands


class SimStates:
    def __init__(self, action):
        self.action = action

    def __str__(self):
        return self.action

    def __cmp__(self, other):
        return cmp(self.action, other.action)

    def __hash__(self):
        return hash(self.action)


class State:
    def run(self):
        assert 0, "run not implemented"

    def next(self, input):
        assert 0, "next not implemented"


class SimStateMachine:
    def __init__(self, init_state):
        self.current_state = init_state

    def run_test(self, inputs):
        state_cntr = 0
        for i in inputs:
            # print(str(state_cntr) + ": ", end='')
            self.current_state = self.current_state.next(i)
            assert i == self.current_state
            self.current_state.run()
            state_cntr += 1

    def execute(self, client, recv_data):
        self.current_state.run(client, recv_data)


SimStates.awaiting = SimStates("awaiting")
SimStates.send_status = SimStates("send_status")
SimStates.send_idle = SimStates("send_idle")


class Awaiting(State):
    def run(self, client, recv_data):
        print("Waiting for incoming data")
        print(client, recv_data)

        assert isinstance(recv_data,
                          Switch), "execuational data is not Switch object"
        # read from client
        print(recv_data.package, Commands.NACK,
              Commands.is_nack(recv_data.package[0]))

    def next(self, input):
        # depending on input of server, decide how to proceed
        if input == SimStates.send_status:
            return SimStates.send_status

        if input == SimStates.send_idle:
            return SimStates.send_idle

        return SimStates.awaiting


class SendStatus(State):
    def run(self):
        print("Sending status command")

    def next(self, input):
        # here input is ignored, it will go straight back to awaiting state
        assert input == SimStates.awaiting
        return SimStates.awaiting


class SendIdle(State):
    def run(self):
        print("Sending Idle Command")

    def next(self, input):
        # input is ignored, it will go straight back to awaiting state
        assert input == SimStates.awaiting

        return SimStates.awaiting


SimStates.awaiting = Awaiting()
SimStates.send_status = SendStatus()
SimStates.send_idle = SendIdle()


def test_state_transitions():
    transitions = [
        SimStates.send_status, SimStates.awaiting, SimStates.send_idle,
        SimStates.awaiting
    ]

    SimStateMachine(SimStates.awaiting).run_test(transitions)