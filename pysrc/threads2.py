import multiprocessing as mp
import time
from enum import Enum, auto


class ConnMode(Enum):
    DEBUG = auto(),
    MAIN = auto(),


class InfoType(Enum):
    SWITCH = auto(),
    OTHER = auto(),


class ConnPackage:
    messages = []

    def __ini__(self, sender_obj):
        self.sender = sender_obj

    def add(self, package):
        if not isinstance(package, (tuple, list)):
            raise ValueError("Package is not tuple or list")

        self.messages.append(package)

    def send(self):
        self.sender.send(self.messages)

    def create_package(self, infotype, mode, msg):
        return (infotype, mode, msg)

    def create_switch_package(self, switch):
        package = self.create_package(infotype=InfoType.SWITCH,
                                      mode=ConnMode.MAIN,
                                      msg=(switch.position, switch.address))

        return package


class ThreadProcesses:
    @staticmethod
    def do_inventory(child, LISC, expected, use_worker):
        """
        Scans for switches while not blocking main thread. Connection 
        back to main thread is established via child object. Message
        structure must be the following
        msg: [(mode, msg)]
        
        Message will be a list of tuples, each tuple represents either switch information
        or general messages to be parsed by main thread
        """
        package = ConnPackage(child)

        with LISC(port='/dev/ttyUSB0', baudrate=9600, timeout=0) as lisc:
            ### RESET LISC ###
            package.create_package(infotype=InfoType.OTHER,
                                   mode=ConnMode.DEBUG,
                                   msg="Resetting LISC")

            lisc.reset()

            ### LISTEN FOR FIRST SWITCH ###
            response = lisc.recieve(timeout=1, use_worker=use_worker)  # async
            switch = lisc.parse_response(
                response)  # should be first switch response
            package = create_package(switch)

            ### LISTEN FOR N SWITCHES ###

    @staticmethod
    def recieve_bytes(child, ser, timeout):
        buffer = []
        start = time.time()

        while time.time() - start <= timeout:
            if ser.inWaiting() > 0:
                buffer.append(ser.read(1))
                start = time.time()

        if child is None:
            return buffer
        else:
            child.send(buffer)
            return None

    @staticmethod
    def loop_and_read(child, ser, timeout=5):
        """
        Reads from serial obj and prints to stdout
        times out after supplied seconds.
        """
        ser.flushInput()
        ser.flushOutput()
        start = time.time()
        while True:
            now = time.time()
            if now - start >= timeout:
                print("\nTimeout reached, ending loop")
                break

            bytes_to_read = ser.inWaiting()
            data = ser.read(bytes_to_read)

            if data:
                start = time.time()
                try:
                    data = data.decode()
                    #print(data, end='')
                    child.send(data)
                except UnicodeDecodeError:
                    child.send("[{}] not recognized".format(data))


class Thread:
    func = None
    args = None
    name = None
    process = None
    parent = None

    def __init__(self, name, func, args):
        self.func = func
        self.args = args
        self.name = name

        parent, child = mp.Pipe(duplex=False)

        args = (child, ) if args is None else ((child, ) + args)
        self.parent = parent
        self.process = mp.Process(target=func, args=args)

    def daemon(self):
        self.process.daemon = True
        return self

    def start(self):
        self.process.start()
        print("Starting task: {}".format(self.name))
        return self

    def join(self):
        self.process.join()
        return self

    def close(self):
        self.process.close()
        return self

    def kill(self):
        self.process.kill()
        return self

    def is_alive(self):
        return self.process.is_alive


class MultiWorkers:
    def __init__(self, max_workers=5):
        self.threads = dict()
        self.parent = dict()
        self.max_workers = max_workers

    def thread(self, name, func, args=None):
        if len(self.threads.keys()) == self.max_workers:
            # max amount of workers has been reached
            # try to find a process that has finished and
            # replace that process with this thread
            pass
            # make_space()

        thread = Thread(name=name, func=func, args=args)

        self.threads[name] = thread

        # worker.thread(name, func, args).start()
        return thread

    def get_thread(self, name):
        try:
            return self.threads[name]
        except KeyError:
            return None

    def get_parents(self):
        lst = []
        for thread in self.threads.values():
            lst.append(thread.parent)
        return lst

    def find_thread_by_parent(self, parent):
        for thread in self.threads.values():
            if parent is thread.parent:
                return thread

    def remove(self, thread):

        if thread is None:
            raise NotImplementedError("Thread doesn't exist in collection")

        if not thread.is_alive():
            thread.close()
        else:
            thread.kill()

    def wait_for_workers(self):
        for thread in self.threads.values():
            thread.join()
        self.clean_up()

    def clean_up(self):
        for thread_name in self.threads.keys():
            self.remove(name=thread_name)
        self.threads = dict()

    def start(self, key=None):
        if key is None:
            for name, thread in self.threads.items():
                print("Worker {} beginning", name)
                thread.start()

        else:
            self.threads[key].start()
        return self
