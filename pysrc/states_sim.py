## possible states
from pysrc.switch import Switch, SWITCH_STATUS
from pysrc.commands import Commands


class SimStates:
    """
    A universal class that allows for different states
    """
    def __init__(self, action):
        self.action = action

    def __str__(self):
        return self.action

    def __hash__(self):
        return hash(self.action)


class State:
    """
    The global abstract methods that each state will implement
    """
    def run(self, client, recv_data, sim):
        """
        Runs a current states run method
        """
        assert 0, "run not implemented"

    def next(self, input):
        """
        Moves to next state in the statemachine
        """
        assert 0, "next not implemented"


class SimStateMachine:
    """
    The actual machine that is responsible for driving each
    state to next
    """
    def __init__(self, init_state):
        self.current_state = init_state

    def execute(self, client, recv_data, sim):
        """
        ```python
        input: SimClient, Switch, Simulator
        return: None
        ```
        Drives current states method of run()

        *each state will have different
        logic.*
        """
        print(client, recv_data)
        self.current_state = self.current_state.run(client, recv_data, sim)


SimStates.awaiting = SimStates("awaiting")
SimStates.send_status = SimStates("send_status")
SimStates.send_idle = SimStates("send_idle")


class Awaiting(State):
    """
    The awaiting state. This state waits for incoming data from
    the server.
    """
    def run(self, client, recv_data, sim):
        """
        Checks contents of initial broadcast msg from switch,
        checks to see if payload is either NACK/ACK and constructs the 
        GetStatus command.
        """
        print("Waiting for incoming data")

        assert isinstance(recv_data,
                          Switch), "execuational data is not Switch object"
        # # read from client
        # print(recv_data.package, Commands.NACK,
        #       Commands.is_nack(recv_data.package[0]))

        # three possibilities:
        # 1) NACK => broadcasting
        # 2) ACK => Return status of GoIdle
        # 3) LONG LIST OF BYTES => GetStatus
        package = recv_data.package
        print("Package: ", package.hex(), len(package))

        if len(package) > 1:
            # return msg for switch responding with get_status
            pass

        elif len(package) == 1:
            # could be ACK or NACK
            if Commands.is_ack(package):
                # Return msg for switch going idle
                print("Switch going idle")

            elif Commands.is_nack(package):
                # switch is broadcasting
                # either send switch straight to GetStatus
                # or GoIdle
                # FOR NOW - we will just ask for status, and move one
                response_msg = recv_data.gen_package(
                    msg=Commands.SendStatus.value)

                client.write(response_msg)
                return self.next(SimStates.send_status)

            else:
                raise Exception("Package does not contain ACK or NACK, HUH??")
        else:
            raise Exception(
                "Package size is 0, this code should have never been reached")

    def next(self, input):
        """
        Returns next state which is GetStatus
        """
        # depending on input of server, decide how to proceed
        if input == SimStates.send_status:
            return SimStates.send_status

        return SimStates.awaiting


class SendStatus(State):
    """
    The SendStatus state, switch on server should be sending
    mock data in the payload structure as defined by PES SureFire
    Protocol.
    """
    def run(self, client, recv_data, sim):
        """
        Update incoming status information to status display widget
        Generate package command for switch to GoIdle
        """
        print("Switch in Status Mode")
        print(recv_data.package)
        output = sim.window.Element('ml_status')

        msg = "[{}]\n".format(recv_data.address)
        for idx, ele in enumerate(recv_data.package):
            msg += SWITCH_STATUS[idx].format(ele)
        print(msg)
        output('')
        output(msg)
        response_msg = recv_data.gen_package(msg=Commands.GoInactive.value)
        client.write(response_msg)
        return self.next(SimStates.send_idle)

    def next(self, input):
        """
        Redundant and unecessary, but used so it flows with rest of states
        .. Hey this isn't the prettiest, but it works.
        """
        # here input is ignored, it will go straight back to awaiting state
        return input


class SendIdle(State):
    """
    SendIdle state that simply restarts the loop and puts internal
    state machine back to `Awaiting` for new switch.
    """
    def run(self, client, recv_data, sim):
        # update gui and send command to server to go to next switch.
        print("In Idle State")
        return self.next(SimStates.awaiting)

    def next(self, input):
        # input is ignored, it will go straight back to awaiting state

        return input


SimStates.awaiting = Awaiting()
SimStates.send_status = SendStatus()
SimStates.send_idle = SendIdle()

# def test_state_transitions():
#     transitions = [
#         SimStates.send_status, SimStates.awaiting, SimStates.send_idle,
#         SimStates.awaiting
#     ]

#     SimStateMachine(SimStates.awaiting).run_test(transitions)