from enum import Enum
from pysrc.lisc import LISC
from pysrc.switch import Switch, SwitchManager
from pysrc.commands import Commands, DangerZone
import time


class DangerousLISC(LISC):
    switch_manager = SwitchManager()

    def do_dangerous_inventory(self, sender, num_switches):
        """
        The very dangerous piece of code that provides access to commands that could result
        in blowing things up. It is essentially the normaly inventory process, with the exception
        of the `dangerous` commands, it will put switch into firing mode.
        """
        self.log("Starting Dangerous Inventory process", "warning")

        def send_recieve(switch, cmd, clear_buffer=True, update=True):
            is_status = True if cmd == Commands.SendStatus else False

            cmd = cmd.value
            cmd = (switch.gen_package(cmd[0]), cmd[1])
            resp = self.send(cmd, clear_buffer=clear_buffer)
            if update:
                self.switch_manager.update(switch, resp)

            if is_status:
                self.package.switch_status(switch)

        def fire(switch):
            cmd = DangerZone.Fire.value
            cmd = (switch.gen_package(cmd[0]), cmd[1])
            _resp = self.send(cmd, ignore_return=True)
            self.switch_manager.remove(switch)
            time.sleep(10)

        def listen_broadcast(tries=5, length=5):
            if tries == 0:
                errmsg = f"Max attempts reached. Can't detect broadcasting of switch. Aborting inventory protocol."
                self.log(errmsg, 'error')
                self.package.debug(errmsg)
                self.package.done()
                self.off()
                raise Exception(errmsg)

            self.log(f"Listening for broadcast [{tries}]", 'info')
            resp = self.listen(length)
            if len(resp) == 5 and resp is not None:
                return resp
            else:
                tries -= 1
                resp = listen_broadcast(tries=tries)
            return resp

        def do_firing(num_switches):
            for i in range(num_switches):
                broadcast_reponse = listen_broadcast()
                self.log(f"Broadcast Address: 0x{broadcast_reponse.hex()}",
                         'info')
                switch = Switch(position=i + 1, raw=broadcast_reponse)
                self.package.switch(switch)
                self.switch_manager.add(switch)
                self.package.debug(f"Found switch: {switch.address}")

                send_recieve(switch, Commands.SendStatus, update=True)
                print(i, num_switches)
                if i == num_switches - 1:
                    # do the actual firing here
                    # send pre-arm

                    self.log("**PRE ARMING**", 'warning')
                    self.package.debug(f"Pre arming switch: {i+1}")
                    send_recieve(switch, DangerZone.PreArm, update=True)

                    self.log("*** ARMING ***", "warning")
                    self.package.debug(f"Arming switch: {i+1}")
                    send_recieve(switch, DangerZone.Arm, update=True)

                    self.log("**** FIRE *****", "warning")
                    self.package.debug(f"*** FIRE ****")
                    fire(switch)
                    return
                else:

                    send_recieve(switch,
                                 Commands.GoInactive,
                                 update=True,
                                 clear_buffer=True)
                    time.sleep(2)

        self.package.set_sender(sender)
        self.package.debug("Resetting LISC")

        for firing_switch in [x + 1 for x in range(num_switches)][::-1]:
            print('resetting')
            self.reset()
            do_firing(firing_switch)
            print("done with switch, ", firing_switch)
        self.off()
        self.package.done()
