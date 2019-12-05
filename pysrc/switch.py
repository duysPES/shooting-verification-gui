import sys
import os
sys.path.append(os.getcwd() + "/../")

from pysrc.errors import NotValidSwitchObj, SwitchDoesNotExist
import struct


class SwitchManager:
    switches = dict()

    def add(self, sw):
        if not self.is_switch_obj(sw):
            raise NotValidSwitchObj

        self.switches[sw.address] = sw

    def remove(self, sw):
        try:
            self.switches.pop(sw.address)
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
    def __init__(self, position, raw):
        self.position = position

        self.raw_address = list(struct.unpack("B" * len(raw), raw))
        # self.raw_address = [
        #     int.from_bytes(i, byteorder='big', signed=False) for i in raw
        # ]

        self.address = self.hex(self.raw_address[:2])
        self.package = self.raw_address[2:-1]
        self.chksum = self.raw_address[-1]

    def hex(self, collection):
        return "0x" + "".join(["{:x}".format(i).zfill(2) for i in collection])


######## TEST MODULES ###########
__addr = b"\xff\x0a\x15\xe0"


def test_addr_is_bytes():
    assert isinstance(__addr, bytes) == True


def test_switch_address():
    switch = Switch(position=1, raw=__addr)
    assert switch.address == "0xff0a"


def test_switch_package():
    switch = Switch(position=1, raw=__addr)
    assert bytes(switch.package) == b"\x15"


def test_switch_chksum():
    switch = Switch(position=1, raw=__addr)
    chksum = 0
    for byte in switch.raw_address[:-1]:
        chksum ^= byte

    assert chksum == switch.chksum


def test_manager_exists():
    manager = SwitchManager()
    switch = Switch(position=1, raw=__addr)
    manager.add(switch)
    assert manager.switch_exists(address=switch.address) == True


def test_manager_not_exists():
    manager = SwitchManager()
    switch = Switch(position=1, raw=__addr)
    manager.add(switch)
    manager.remove(switch)
    assert not manager.switch_exists(address=switch.address) == True