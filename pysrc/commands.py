from enum import Enum


class Commands(Enum):
    """
    A list of all commands avaiable
    """
    ACK = b"\x06"
    NACK = b"\x15"
    GoInactive = b"\x1e"
    SendStatus = b"\x05"

    @staticmethod
    def is_ack(msg):
        return Commands.ACK.value == msg

    @staticmethod
    def is_nack(msg):
        return Commands.NACK.value == msg


class StatusFields:
    V = ['Voltage', 'V']
    T = ['Temperature', 'T']
    C = ['Continuity', 'C']
    PE = ['Packet Errors', 'PE']
    CE = ['Chksum Errors', 'CE']
    F = ['Fires', 'F']

    def __init__(self):
        self.all_fields = [self.V, self.T, self.C, self.PE, self.CE, self.F]

    def short(self):
        buf = []
        for field in self.all_fields:
            buf.append(field[1])
        return buf

    def long(self):
        buf = []
        for field in self.all_fields:
            buf.append(field[0])
        return buf


class Status:
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
        return self.body[0]

    @property
    def temp(self):
        return self.body[1]

    # dereference the raw bytes to the individual
    # fields that make up a status_response
    def parse(self):
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
        msg = ""
        for i, bit in enumerate("{:08b}".format(int(flag_bit))):
            flag = self.bitwise[i]
            status = "ON" if int(bit) else "OFF"
            msg += "\t{:15s}: {}\n".format(flag, status)
        return msg


#### Unit Tests#####
__packet = b'\x0b\xd0\xb64\x1f\x05\x01\x00\x00(j'


def test_bit_flag_parsing():
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
    body = __packet[3:-1]
    status = Status(body)
    voltage = status.voltage
    assert voltage == body[0]


def test_temperature():
    body = __packet[3:-1]
    status = Status(body)
    temp = status.temp
    assert temp == body[1]