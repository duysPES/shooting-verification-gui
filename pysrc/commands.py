from enum import Enum


class DangerZone(Enum):
    """
    Enum that holds all commands that are dangerous and revolve around
    ballistics
    """

    PreArm = (b"\x3c", 5)
    """
    Pre arm switch, expect ACK
    """

    Arm = (b"\x4b", 5)
    """
    Arm switch, expect ACK
    """

    Fire = (b"\x5a", -1)
    """
    Opens FET to fire switch. Most dangerous command
    """


class Commands(Enum):
    """
    Enum that holds all supported commands of
    Pioneer's Addressable Switches, along with byte values and
    response length for each.
    """

    ACK = (b"\x06", -1)
    """
    Acknowledgement.
    """

    NACK = (b"\x15", -1)
    """
    Not Acknowledged, mainly used when something
    went wrong
    """

    GoInactive = (b"\x1e", 5)
    """
    Command to put addressed switch into low power
    mode and allow pass-thru to next switch in chain
    """
    SendStatus = (b"\x05", 11)
    """
    Command that is used for switch to report
    debug information.
    """

    NULL = (b"", -1)
    """
    Command that represents a NULL
    """
    @staticmethod
    def is_ack(msg):
        """
        Helper method to determine if msg is ACK
        """
        return Commands.ACK.value[0] == msg

    @staticmethod
    def is_nack(msg):
        """
        Helper method to determine if msg is NACK
        """
        return Commands.NACK.value[0] == msg

    @staticmethod
    def parse_packet(msg):
        """
        parses cmd byte to string for easier debugging
        """
        cmd = msg[3:-1]

        cmdset = [
            Commands.ACK, Commands.NACK, Commands.GoInactive,
            Commands.SendStatus
        ]

        danger_zone = [DangerZone.PreArm, DangerZone.Arm, DangerZone.Fire]
        for c in cmdset + danger_zone:
            if cmd == c.value[0]:
                return c

        return Commands.NULL

    @staticmethod
    def prettify(msg):
        """
        takes a list of bytes, converts to hex, and returns a pretty string
        """
        try:
            hs = msg.hex()
            s = [hs[i:i + 2] for i in range(0, len(hs), 2)]
            addr = s[:3]
            contents = s[3:-1]
            chksum = s[-1]

            return "{} {} {}".format("".join(addr), "".join(contents), chksum)
        except Exception:
            return ""


class StatusFields:
    """
    Class that returns human-readable fields from a switches
    GetStatus command.

    """

    V = ['Voltage', 'V']
    """
    Voltage
    """

    T = ['Temperature', 'T']
    """
    Temperature
    """

    C = ['Continuity', 'C']
    """
    Detonator detection
    """

    PE = ['Packet Errors', 'PE']
    """
    Number of reported packet errors
    """

    CE = ['Chksum Errors', 'CE']
    """
    Number of reported checksum errors
    """

    F = ['Fires', 'F']
    """
    Reported number of fires 

    *(when switch goes into `Fire` mode this value will increase by 1)*
    """
    def __init__(self):
        self.all_fields = [self.V, self.T, self.C, self.PE, self.CE, self.F]

    def short(self):
        """
        returns a list of all human-readable
        field names in their short name versions

        *etc: C,PE,F,...*
        """

        buf = []
        for field in self.all_fields:
            buf.append(field[1])
        return buf

    def long(self):
        """
        returns a list of all human-readable
        field names in their long name versions

        *etc: Fires, Chksum Errors, ....*
        """

        buf = []
        for field in self.all_fields:
            buf.append(field[0])
        return buf


class Status:
    """
    Handles and parses the raw bytes of the reponse of GetStatus
    from an addressable switch.

    ```python
    # To obtain Voltage, Temperature, and pretty formatting.

    # raw_packet of get_status is 11 bytes long
    raw_packet = b"\\xff\\x0a\\x12\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\xba"
    #              [---addr----][V   T   C   PE  CE  F  BF][Chksum]
    # human-hex:      0xff0a12  01  02  03   04  05 06  07   ba


    # only interested in bytes after `address` 
    # and not including `chksum`
    status_body = [3:-1] 
    status = Status(status_body)

    # obtain voltage
    voltage = status.voltage

    # obtain temperature
    temperature = status.temperature

    pretty_str = status.parse()
    # above prints...
    '''
    Voltage        : 1
    Temperature    : 2
    Continuity     : 3
    Packet Errors  : 4
    Chksum Errors  : 5
    Fires          : 6
            NU             : OFF
            FctrMode       : OFF
            BrdcstDisabled : OFF
            Inactive       : OFF
            Statused       : OFF
            PreArmed       : ON
            Armed          : ON
            Fired          : ON
    '''
    ```
    """
    def __init__(self, body):
        self.body = body

        if not isinstance(body, bytes):
            try:
                self.body = bytes(body)
            except:
                raise ValueError("incorrect input type.")

        self.bitwise = [
            'NU', 'FctrMode', 'BrdcstDisabled', 'Inactive', 'Statused',
            'PreArmed', 'Armed', 'Fired'
        ]

    @property
    def voltage(self):
        """
        returns voltage value from status byte string
        """

        return self.body[0]

    @property
    def temp(self):
        """
        returns temperature value from status byte string
        """

        return self.body[1]

    # dereference the raw bytes to the individual
    # fields that make up a status_response
    def parse(self):
        """
        takes entire status byte string and returns
        a pretty string that can be used for reporting.
        
        *see above for example usage*

        ```
        input: None
        return: str
        ```
        """
        fields = StatusFields()
        if len(self.body) != len(fields.all_fields) + 1:
            raise IndexError(
                "Provided status report not same length as fields in memory.")

        status_report = ""
        bit_flag = self.body[-1]
        bit_report = self.bitflag_parse(bit_flag)

        for i, field in enumerate(fields.long()):
            status_report += "{:15s}: {}\n".format(field, self.body[i])

        # add bit report
        status_report += "{}".format(bit_report)
        return status_report

    def bitflag_parse(self, flag_bit):
        """
        The last bit in status byte message is a bit
        flag byte, used to report certains flags that
        have been set. 

        ```
        input: bytes
        return: str
        ```
        """
        msg = ""
        for i, bit in enumerate("{:08b}".format(int(flag_bit))):
            flag = self.bitwise[i]
            status = "ON" if int(bit) else "OFF"
            msg += "\t{:15s}: {}\n".format(flag, status)
        return msg


#### Unit Tests#####
__packet = b'\x0b\xd0\xb64\x1f\x05\x01\x00\x00(j'


def test_bit_flag_parsing():
    """
    unit test for correct parsing of the
    bit flag byte in status report
    """

    flag_bit = __packet[-2]
    status = Status(__packet[3:-1])

    bit_report = status.bitflag_parse(flag_bit)
    actual = ["OFF", "OFF", "ON", "OFF", "ON", "OFF", "OFF", "OFF"]

    so_far_so_good = True
    lines = bit_report.split("\n")[:-1]
    for i, line in enumerate(lines):
        if actual[i] not in line:
            so_far_so_good = False

    assert so_far_so_good


def test_voltage():
    """
    unit test for testing voltage placement and value
    """

    body = __packet[3:-1]
    status = Status(body)
    voltage = status.voltage
    assert voltage == body[0]


def test_temperature():
    """
    unit test for testing temperature placement and value
    """
    body = __packet[3:-1]
    status = Status(body)
    temp = status.temp
    assert temp == body[1]