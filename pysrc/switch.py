

from pysrc.errors import NotValidSwitchObj, SwitchDoesNotExist

class SwitchManager:
    switches = dict()

    def add(self, sw):
        if not self.is_switch_obj(sw):
            raise NotValidSwitchObj

        self.switches[sw.address] = sw

    def remove(self, position):
        try:
            self.switches.pop(position)
        except SwitchDoesNotExist:
            print("Unable to remove a switch that doesn't exist.")

    def is_switch_obj(self, obj):
        return isinstance(obj, Switch)

    def switch_exists(self, address):
        found = True
        for addr in self.switches.keys():
            if address == addr:
                return found 
        return not found
    
    def get(self, position):
        for switch in self.switches.values():
            if switch.position == position:
                return switch

    @property
    def num(self):
        return len(self.switches)


class Switch:
    def __init__(self, position, address, raw):
        self.address = address
        self.position = position
        self.raw_address = [int.from_bytes(i, byteorder='big', signed=False) for i in raw]
