import datetime
from enum import Enum

LOG_PATH = "logs/"
class __ServerLog:
    """
    Class that holds logic of writing to log file by the Simulation Server
    """

    fname = "server.log"
    """
    `fname = 'server.log'`
    """
    @staticmethod
    def log(msg):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+__ServerLog.fname, "w") as f:
            f.write("{}: [{}]".format(now, msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+__ServerLog.fname, "w+") as f:
            pass

class __GuiLog:
    """
    Class that holds logic of writing to log file by the GUI itself.
    """
    fname = "gui.log"
    """
    `fname = 'gui.log'`
    """

    @staticmethod
    def log(msg):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+__GuiLog.fname, "w") as f:
            f.write("{}: [{}]".format(now, msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+__GuiLog.fname, "w+") as f:
            pass

class LogType(Enum):
    """
    Stores different types of Logs.
    """
    
    gui = 0
    """
    LogType from main GUI application
    """

    server = 1
    """
    LogType from Switch Simulator that is run from an external
    Rust TCP server
    """




class Log:
    """
    A parent wrapper Log class that
    allows for easy API to log to different
    LogTypes. It allows for scalability and addition of more
    LogTypes without much code refactoring

    it's as simple as 
    ```python
    # Log from server output
    Log.log("hello from server", LogType.server)
    
    # Log from main gui
    Log.log("hello from gui", LogType.gui)

    # Clear all the log files
    Log.clear()

    # Clear only a certain log file
    Log.clear(LogType.server)
    ```
    """
    @staticmethod
    def log(msg, to):
        """
        ```
        input: str, LogType
        return: Log # for chaining together methods.
        ```

        Logs a message to a file depending on LogType
        """
        if not isinstance(to, LogType):
            raise ValueError("Need to supply a LogType instance")

        
        if to == LogType.gui:
            __GuiLog.log(msg)
        elif to == LogType.server:
            __ServerLog.log(msg)
        else:
            raise AssertionError("LogType: Asserting my dominance")
        
        return Log

    @staticmethod
    def clear(log_type=None):
        """
        ```python
        input: LogType
        return: None
        ```

        clears log files
        """
        all_logs = {
            LogType.gui: __GuiLog,
            LogType.server: __ServerLog
        }


        if log_type is None:
            # clear all logs
            for _, log in all_logs.items():
                log.clear()
            return
        
        if not isinstance(log_type, LogType):
            raise ValueError("Need to supply either None or a LogType")
            
        all_logs[log_type].clear()



