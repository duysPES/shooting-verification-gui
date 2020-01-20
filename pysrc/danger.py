from pysrc.commands import Commands


class DangerZone(Commands):
    """
    Enum that holds all commands that are dangerous and revolve around
    ballistics
    """

    PreArm = (b"3c", 5)
    """
    Pre arm switch, expect ACK
    """

    Arm = (b"4b", 5)
    """
    Arm switch, expect ACK
    """

    Fire = (b"5a", -1)
    """
    Opens FET to fire switch. Most dangerous command
    """