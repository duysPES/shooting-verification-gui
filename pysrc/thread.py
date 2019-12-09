from enum import Enum
from collections import deque


class ConnMode(Enum):
    DEBUG = 0,
    MAIN = 1,


class InfoType(Enum):
    SWITCH = 0,
    OTHER = 1,
    KILL = -1,


class ConnPackage:
    messages = deque([])
    max_messages = 5

    def __init__(self, sender_obj):
        self.sender = sender_obj

    def add(self, package):

        if not isinstance(package, (tuple, list)):
            raise ValueError(
                "Package is not tuple or list, value: {}, type: {}", package,
                type(package))

        if len(self.messages) == self.max_messages:
            # rotate and repalce
            self.messages.rotate(-1)
            self.messages[-1] = package
            return

        self.messages.append(package)

    def send(self):
        self.sender.put(self.messages)

    def put(self, msg):
        self.sender.put(msg)

    def create_package(self, infotype, mode, msg):
        packet = (infotype, mode, msg)
        self.add(packet)

    def switch(self, switch):
        self.create_package(infotype=InfoType.SWITCH,
                            mode=ConnMode.MAIN,
                            msg=(switch.position, switch.address))
        self.send()

    def debug(self, msg):
        self.create_package(infotype=InfoType.OTHER,
                            mode=ConnMode.DEBUG,
                            msg=msg)
        self.send()

    def done(self):
        self.create_package(infotype=InfoType.KILL,
                            mode=ConnMode.DEBUG,
                            msg="")
        self.send()