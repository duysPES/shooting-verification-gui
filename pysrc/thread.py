from enum import Enum
from collections import deque
from multiprocessing import Queue


class ConnMode(Enum):
    """
    Different connection states, used by the gui
    to determine placement of data within internal widgets
    """
    DEBUG = 0,
    """
    For Debug purposes
    """

    MAIN = 1,
    """
    Main information
    """

    STATUS = 2,
    """
    Status from switch
    """

class InfoType(Enum):
    """
    Different info types. To tag which entity
    sent a package up the ConnPackage channel
    """
    SWITCH = 0,
    """
    Entity is `Switch`
    """

    OTHER = 1,
    """
    Entity is `Not Switch`
    """

    KILL = -1,
    """
    Entity sends SIGINT
    """

class ConnPackage:
    """
    a package protocol that zips information and sends through 
    queue channel to main thread.

    ```python
    from multiprocessing import Queue, Process

    def func(q):
        package = ConnPackage()
        package.set_sender(queue)

        itype = InfoType.SWITCH
        mode = ConnType.MAIN
        msg = "Hello, world!"

        # deque([InfoType.SWITCH, ConnType.MAIN, "Hello, world!])
        packet = package.create_package(itype, mode, msg)
        packet.send(packet) 

    queue = Queue()
    process = Process(target=func, args=(q,))
    process.start()

    # deque([InfoType.SWITCH, ConnType.MAIN, "Hello, world!])
    packet = queue.get_nowait()
    process.join()

    ```
    """
    __sender = None

    def __init__(self, sender_obj=None):
        if sender_obj is not None:
            if not isinstance(sender_obj, Queue):
                raise ValueError("Constructor arg is not Queue obj")
            self.__sender = sender_obj

    def set_sender(self, sender):
        """
        ```python
        input: Queue
        return: None
        ```

        sets internal queue
        """
        self.__sender = sender

    def send(self, p):
        """
        ```python
        input: deque
        return: None
        ```

        Sends information down channel
        """
        self.__sender.put(p)

    def put(self, msg):
        """
        this is a redundant method, before removing need to make sure this api is not
        being used
        """
        self.__sender.put(msg)

    def create_package(self, infotype, mode, msg):
        """
        ```python
        input: InfoType, ConnMode, PyObj
        return: Deque
        ```

        constructs a package from supplied args.
        """
        packet = deque((infotype, mode, msg))
        return packet

    def switch(self, switch):
        """
        ```python
        input: Switch
        return: None
        ```

        helper method that constructs a package based on 
        switch instance, sets some defaults. Sends packet down channel

        ```
        type(info_type) == type(InfoType.SWITCH)
        type(mode) == type(ConnMode.MAIN)
        type(msg) == type(tuple) # (switch.position, switch.address)
        
        ```
        """
        packet = self.create_package(infotype=InfoType.SWITCH,
                                     mode=ConnMode.MAIN,
                                     msg=(switch.position, switch.address))
        self.send(packet)

    def switch_status(self, switch):
        """
        ```python
        input: Switch
        return: None
        ```
        helper method that constructs a package based on switch status reponse, sets some
        defaults and sends it down channel

        ```
        type(info_type) == type(InfoType.SWITCH)
        type(mode) == type(ConnMode.STATUS)
        type(msg) == type(tuple) # (switch.position, switch.address, switch.package)
        
        ```
        """
        msg = (switch.position, switch.address, switch.package)
        packet = self.create_package(
            infotype=InfoType.SWITCH,
            mode=ConnMode.STATUS,
            msg=msg,
        )
        self.send(packet)

    def debug(self, msg):
        """
        ```python
        input: str
        return: None
        ```
        helper method that constructs a default debug message, and sends down channel

        """
        packet = self.create_package(infotype=InfoType.OTHER,
                                     mode=ConnMode.DEBUG,
                                     msg=msg)
        self.send(packet)

    def done(self):
        """
        ```python
        input: None
        return: None
        ```

        Sends the KILL command down the channel to alert other end
        that the thread is about to end.
        """
        packet = self.create_package(infotype=InfoType.KILL,
                                     mode=ConnMode.DEBUG,
                                     msg="")
        self.send(packet)