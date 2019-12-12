import serial
import time
import multiprocessing as mp
from pysrc.switch import SwitchManager, Switch
from pysrc.commands import Commands
from pysrc.thread import ConnMode, InfoType, ConnPackage
import pysrc.logging as log

class LISC(serial.Serial):
    """
    Abstract representation of the embedded device
    that handles the actual communication between computer
    and addressable switch. Inherits from `serial.Serial`
    from *pyserial*, with extended functionalities

    ```python
    lisc = Lisc()
    lisc.reset()
    lisc.talk_to_switches()
    lisc.ask_switches_for_cake()
    lisc.blowup()
    lisc.take_over_the_world()
    # possibilities are endless
    ```
    """

    switch_manager = SwitchManager()
    """
    manager for keeping track of switches
    """

    package = ConnPackage()
    """
    package object that zips all incoming reponses from switches in a compatible format 
    that is consumed by GUI at the end of the half-duplex sender
    """
    def log(self, msg, status):
        """
        ```python
        input: str, LogType
        return: None
        ```

        Wrapper around log for quick logging api calls
        """

        log.log(status)(msg=msg, to=log.LogType.gui)

    def do_inventory(self, sender):
        """
        ```
        input: queue.Queue
        return: None
        ```
        The main inventory protocol of the LISC.

        For each `expected` switch it will do the following:

        1. Listen for broadcasting message
        2. Send StatusRequest
        3. Send GoInactive

        """
        # package = ConnPackage(queue)
        self.package.set_sender(sender)
        self.package.debug("Resetting LISC")
        self.reset()
        self.flushInput()
        self.flushOutput()
        # response = self.read_serial(lisc)
        for i in range(3):
            # listen for broadcast address
            broadcast_response = self.listen()
            self.log(f"Broadcast Address: 0x{broadcast_response}", 'warning')

            # internally create a switch obj
            switch = Switch(position=i + 1, raw=broadcast_response)
            self.package.switch(switch)  # sending switch contents via sender
            self.switch_manager.add(switch)

            status_cmd = switch.gen_package(Commands.SendStatus.value)
            self.package.debug("Sending command: {}".format(status_cmd.hex()))
            response = self.send(status_cmd)
            self.package.debug("Response: {}".format(response.hex()))
            self.switch_manager.update(switch, response)
            self.package.switch_status(switch)

            go_inactive = switch.gen_package(Commands.GoInactive.value)
            self.package.debug("Sending command: {}".format(go_inactive.hex()))
            response = self.send(go_inactive)
            self.package.debug("Response: {}".format(response.hex()))

            self.switch_manager.update(switch, response)
            # self.package.switch(switch)
            time.sleep(2)

        self.package.done()

    def send(self, msg, tries=5):
        """
        ```
        input: bytes, int
        return: None
        ```
        Send byte string on connected port, and listen for response
        returns entire byte response
        """
        attempt = 0
        response = b""
        body = None
        while 1:
            if attempt == tries:
                err = \
                """
                Incorrect response recieved from switch.
                Last response is: 0x{}
                """.format(response.hex())
                raise serial.SerialException(err)

            # attempt to write to stream
            self.write(msg)
            response = self.listen()

            body = response[3:-1]

            # checking checksum
            if not self.chksum_ok(msg):
                attempt += 1
                self.package.debug("Chksum incorrect")
                continue

            # most likely a successful attempt, if it passes
            if len(body) > 1:
                self.package.debug("Receiving status message")
                break
            elif len(body) == 1:
                if body == Commands.ACK.value:
                    self.package.debug("ACK Recieved")
                    break
                else:
                    self.package.debug("NACK recieved trying again..")
                    attempt += 1
                    continue
            else:
                attempt += 1

        return response

    def listen(self, timeout=3, tries=5):
        '''
        ```
        input: int, int
        return: bytes
        ``` 
        a timer based serial listen protocol.


        Since packets don't all have fixed lengths, 
        we could complicate the code by hard-coding expected lengths by reponse,
        but this is error prone and could lead to bugs if things change.
        Therefore this method just *listens* on the serial port for 
        a maximum of *timeout*. It returns any information recieved.
        If buffer is at least 5 bytes long it will pre-maturely break the loop and return results

        *5 bytes is minimum length of a standard NACK/ACK packet*
        
     
        '''
        now = time.time()
        buf = b""

        while time.time() - now <= timeout:
            in_waiting = self.inWaiting()
            if in_waiting > 0:
                buf += self.read(in_waiting)
                now = time.time()
            
            # if len(buf) >= 5:
            #     break

        return buf

    def chksum_ok(self, data):
        """
        ```
        input: bytes
        return: bool
        ```
        calculates internal checksum on data and matches with supplied checksum
        """
        if not isinstance(data, bytes):
            raise ValueError("Incoming data must be a bytes")

        good_data = True

        supplied_chksum = data[-1]
        calculated_chksum = 0

        for idx in range(len(data) - 1):
            calculated_chksum ^= data[idx]

        if calculated_chksum != supplied_chksum:
            self.log(f"Checksums do not match: calc: {calculated_chksum} != provided: {supplied_chksum}", 'warning')
            return not good_data

        return good_data

    def chksum(self, data):
        """
        ```
        input: bytes
        return: bytes
        ```
        return a bytes of data with included checksum
        """
        chksum = 0
        if not isinstance(data, bytes):
            data = bytes([data])

        for element in data:
            chksum ^= element

        data += bytes([chksum])

        return data

    def delay(self, seconds):
        '''
        ```
        input: int
        return: None
        ```
        mechanical `delay` that uses the time module instead of
        relying on `time.sleep()` which can can issues in multithreading
        '''
        start = time.time()

        while time.time() - start <= seconds:
            continue

    def reset(self):
        """
        ```
        input: None
        return: None
        ```

        macro method that soft resets LISC
        """
        self.write(b'zl')
        self.delay(1)
        self.write(b'zL')
