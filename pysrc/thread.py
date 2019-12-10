from enum import Enum
from collections import deque
from multiprocessing import Queue


class ConnMode(Enum):
    DEBUG = 0,
    MAIN = 1,
    STATUS = 2,


class InfoType(Enum):
    SWITCH = 0,
    OTHER = 1,
    KILL = -1,


class ConnPackage:
    __sender = None

    def __init__(self, sender_obj=None):
        if sender_obj is not None:
            if not isinstance(sender_obj, Queue):
                raise ValueError("Constructor arg is not Queue obj")
            self.__sender = sender_obj

    def set_sender(self, sender):
        self.__sender = sender

    def send(self, p):
        self.__sender.put(p)

    def put(self, msg):
        self.__sender.put(msg)

    def create_package(self, infotype, mode, msg):
        packet = deque((infotype, mode, msg))
        return packet

    def switch(self, switch):
        packet = self.create_package(infotype=InfoType.SWITCH,
                                     mode=ConnMode.MAIN,
                                     msg=(switch.position, switch.address))
        self.send(packet)

    def switch_status(self, switch):
        msg = (switch.position, switch.address, switch.package)
        packet = self.create_package(
            infotype=InfoType.SWITCH,
            mode=ConnMode.STATUS,
            msg=msg,
        )
        self.send(packet)

    def debug(self, msg):
        packet = self.create_package(infotype=InfoType.OTHER,
                                     mode=ConnMode.DEBUG,
                                     msg=msg)
        self.send(packet)

    def done(self):
        packet = self.create_package(infotype=InfoType.KILL,
                                     mode=ConnMode.DEBUG,
                                     msg="")
        self.send(packet)