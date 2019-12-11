from enum import Enum, auto

class NotValidSwitchObj(ValueError):
    """
    Supplied object is not of type Switch from switch.py
    """
    def __init__(self):
        ValueError.__init__(self, "Not a valid switch object passed.")


class SwitchDoesNotExist(KeyError):
    """
    Switch does not exist in collection
    """

    def __init__(self):
        KeyError.__init__(self, "Switch does not exist.")

