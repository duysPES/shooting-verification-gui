from enum import Enum


class Commands(Enum):
    ACK = 0x06
    NACK = 0x15
    GoInactive = 0x1E
    SendStatus = 0x05

    # Fire = 0x5A
    @staticmethod
    def is_ack(msg):
        return Commands.ACK.value == msg

    @staticmethod
    def is_nack(msg):
        return Commands.NACK.value == msg
