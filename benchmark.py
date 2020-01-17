# This script will benchmark switches and loop over them n times. To record errors and package errors.

from multiprocessing import Process, Queue
from pysrc.config import Config
from pysrc.lisc import LISC
from pysrc.log import LOG_PATH
import pysrc.log as log


def logit(msg, status='info'):
    """
        ```python
        input: str
        return: None
        ```
        Wrapper around log object to verify that output from GUI is going to gui.log
        """
    log.log(status)(msg, log.LogType.gui)


if __name__ == "__main__":
    c = Config()
    port = str(c.lisc('port'))
    baudrate = int(c.lisc('baudrate'))
    expected_switches = int(c.switches('expected'))
    queue = Queue()
    log.Log.clear()

    for round in range(100):
        logit(f"Starting round {round}\n\n", "info")

        with LISC(port=port, baudrate=baudrate, timeout=3) as lisc:
            thread = Process(target=lisc.do_inventory,
                             args=(queue, expected_switches))
            thread.start()
        thread.join()
