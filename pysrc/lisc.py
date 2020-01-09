import serial
import time
import multiprocessing as mp
from pysrc.switch import SwitchManager, Switch
from pysrc.commands import Commands
from pysrc.thread import ConnMode, InfoType, ConnPackage
import pysrc.log as log


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

    def do_inventory(self, sender, num_switches):
        """
        ```
        input: queue.Queue, int
        return: None
        ```
        The main inventory protocol of the LISC.

        For each `expected` switch it will do the following:

        1. Listen for broadcasting message
        2. Send StatusRequest
        3. Send GoInactive

        """
        def send_recieve(switch, cmd, clear_buffer=True, update=True):
            is_status = True if cmd == Commands.SendStatus else False

            cmd = cmd.value
            cmd = (switch.gen_package(cmd[0]), cmd[1])
            resp = self.send(cmd, clear_buffer=clear_buffer)
            if update:
                self.switch_manager.update(switch, resp)

            if is_status:
                self.package.switch_status(switch)

        def listen_broadcast(tries=5, length=5):
            if tries == 0:
                self.log("Can't find switch. Aborting inventory", 'error')
                self.package.done()
                raise Exception(
                    "Couldn't continue inventory, switches not found.")

            self.log(f"Listening for broadcast [{tries}]", 'info')
            resp = self.listen(length)
            print(resp.hex(), len(resp))
            if len(resp) == 5:
                return resp
            else:
                tries -= 1
                listen_broadcast(tries=tries)

        self.package.set_sender(sender)
        self.package.debug("Resetting LISC")
        self.reset()

        for i in range(num_switches):
            # listen for broadcast address
            broadcast_response = listen_broadcast()

            self.log(f"Broadcast Address: 0x{broadcast_response.hex()}",
                     'info')
            switch = Switch(position=i + 1, raw=broadcast_response)
            self.package.switch(switch)  # sending switch contents via sender
            self.switch_manager.add(switch)
            self.package.debug(f"Found switch: {switch.address}")

            # Get Status and process
            send_recieve(switch, Commands.SendStatus, update=True)

            # Send GoInactive and process
            send_recieve(switch,
                         Commands.GoInactive,
                         update=True,
                         clear_buffer=False)

            time.sleep(2)

        self.package.done()

    def send(self, msg, tries=5, clear_buffer=True):
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
            to_send, resp_len = msg

            self.write(to_send)
            response = self.listen(resp_len, clear_buffer=clear_buffer)
            self.log(f"Raw response: {response.hex()}", 'info')
            body = response[3:-1]

            # checking checksum
            if not self.chksum_ok(to_send):
                attempt += 1
                self.package.debug("Chksum incorrect")
                continue

            # most likely a successful attempt, if it passes
            if len(body) > 1:
                self.package.debug(
                    f"Receiving status message, {response.hex()}")
                break
            elif len(body) == 1:
                if body == Commands.ACK.value[0]:
                    self.package.debug("ACK Recieved")
                    break

                if body == Commands.NACK.value[0]:
                    self.package.debug("NACK recieved trying again..")
                    attempt += 1
                    continue
                else:
                    self.package.debug(
                        f"Found something else: {response.hex()}, body {body.hex()}"
                    )
                    attempt += 1
                    continue
            else:
                print(f"else {response.hex()}")
                attempt += 1

        return response

    def listen(self, n, clear_buffer=True):
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
        if clear_buffer:
            self.read(self.inWaiting())

        return self.read(n)
        # now = time.time()
        # buf = b""
        # n = self.inWaiting()

        # tracker = ""

        # while time.time() - now <= timeout:
        #     in_waiting = self.inWaiting()
        #     if in_waiting > 0:
        #         tracker += " . " * in_waiting
        #         buf += self.read(in_waiting)
        #         now = time.time()

        # print(tracker)
        # return buf

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
            self.log(
                f"Checksums do not match: calc: {calculated_chksum} != provided: {supplied_chksum}",
                'warning')
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
