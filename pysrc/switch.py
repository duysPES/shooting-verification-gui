import sys
import os
sys.path.append(os.getcwd() + "/../")

from pysrc.errors import NotValidSwitchObj, SwitchDoesNotExist
import struct

# volts: u8,
# temp: u8,
# detd: u8,
# perror: u8,
# cerror: u8,
# nfire: u8,
# flags: u8,
SWITCH_STATUS = [
    "VOLT: {}V\n", "TEMP: {}C\n", "DETD: {}\n", "PERROR: {}\n", "CERROR: {}\n",
    "NFIRE: {}\n", "FLAGS: 0x{:02x}\n"
]


class SwitchManager:
    switches = dict()
    __addr_list = list()

    def add(self, sw):
        if not self.is_switch_obj(sw):
            raise NotValidSwitchObj

        if self.switch_exists(sw.address):
            print("Switch already exists.")
            return

        self.switches[sw.address] = sw
        self.__addr_list.append(sw.address)

    def remove(self, sw):
        try:
            self.switches.pop(sw.address)
            self.__addr_list.remove(sw.address)
        except SwitchDoesNotExist:
            print("Unable to remove a switch that doesn't exist.")

    @property
    def latest_switch(self):
        return self.__addr_list[-1]

    def is_switch_obj(self, obj):
        return isinstance(obj, Switch)

    def switch_exists(self, address):
        found = True
        for addr in self.switches.keys():
            if address == addr:
                return found
        return not found

    def get(self, switch):
        for switch_obj in self.switches.values():
            if switch.address == switch_obj.address:
                return switch

    def update(self, switch, msg):
        switch = self.get(switch)
        switch.update(msg)

    @property
    def num(self):
        return len(self.switches)


class Switch:
    def __init__(self, position, raw):
        self.position = position
        # self.raw = list(struct.unpack("B" * len(raw), raw))
        self.raw = raw

        self.address = self.hex(self.raw[:3])
        self.package = self.raw[3:-1]

    @property
    def raw_address(self):
        return self.raw[:3]

    def update(self, raw):
        if not isinstance(raw, bytes):
            raise ValueError(
                "updating internal switch body, must be bytes instance")

        # self.raw = list(struct.unpack("B" * len(raw), raw))
        self.raw = raw
        self.address = self.hex(self.raw[:3])
        self.package = bytes(self.raw[3:-1])

    def hex(self, collection):
        return "0x" + "".join(["{:x}".format(i).zfill(2) for i in collection])

    @staticmethod
    def to_int(msg):
        if not isinstance(msg, bytes):
            return msg

        return list(struct.unpack("B" * len(msg), msg))

    def gen_package(self, msg):
        raw = bytes(self.raw[:3])
        if not isinstance(msg, bytes):
            msg = bytes([msg])

        chksum = 0
        for i in raw + msg:
            chksum ^= i

        return raw + msg + bytes([chksum])


######## TEST MODULES ###########
__addr = b'\xff\x1a#\x15\xd3'
__status = b'\x0b\xd0\xb65\x1c\x05\x01\x00\x00(h'


def test_to_int_from_bytes():
    actual = [11, 208, 182, 53, 28, 5, 1, 0, 0, 40, 104]
    assert Switch.to_int(__status) == actual


def test_switch_update():
    switch = Switch(position=1, raw=__addr)
    switch.update(raw=__status)

    assert switch.package == b'5\x1c\x05\x01\x00\x00('


def test_addr_is_bytes():
    assert isinstance(__addr, bytes) == True


def test_switch_address():
    switch = Switch(position=1, raw=__addr)
    assert switch.address == "0xff1a23"


def test_switch_package():
    switch = Switch(position=1, raw=__addr)
    assert bytes(switch.package) == b"\x15"


def test_switch_chksum():
    switch = Switch(position=1, raw=__addr)
    chksum = 0
    for byte in switch.raw[:-1]:
        chksum ^= byte

    assert chksum == switch.raw[-1]


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


def test_switch_package_gen():
    switch = Switch(position=1, raw=__addr)
    cmd = b"\x1e"
    chksum = 0
    for i in __addr[:3] + cmd:
        chksum ^= i

    chksum = bytes([chksum])
    packet = __addr[:3] + cmd + chksum

    assert packet == switch.gen_package(msg=cmd)