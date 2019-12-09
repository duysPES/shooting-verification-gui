from enum import Enum, auto

class ErrorCodes(Enum):
    CHKSUM = auto()
    NVALIDOBJ = auto()
    SWITCHNOTEXIST = auto()
    PAYLOAD = auto()

class ChkSumError(Exception):
    def __init__(self):
        Exception.__init__(self, "Checksums of supplied and calculated did not match")

class NotValidSwitchObj(ValueError):
    def __init__(self):
        ValueError.__init__(self, "Not a valid switch object passed.")


class SwitchDoesNotExist(KeyError):
    def __init__(self):
        KeyError.__init__(self, "Switch does not exist.")

class IncorrectPayLoad(Exception):
    def __init__(self):
        Exception.__init__(self, "Payload differs from expected result")

class NotValidInfoType(ValueError):
    def __init__(self):
        ValueError.__init__(self, "Not a valid InfoType option")

class NotValidModeType(ValueError):
    def __init__(self):
        ValueError.__init__(self, "Not a valid ConnMode option")

class ConnPackageSwitchValueError(ValueError):
    def __init__(self):
        ValueError.__init__(self, "Message containing switch information not in tuple or list format.")
