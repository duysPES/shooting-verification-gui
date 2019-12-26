import datetime
from enum import Enum

LOG_PATH = "logs/"
class ServerLog:
    """
    Class that holds logic of writing to log file by the Simulation Server
    """

    fname = "server.log"
    """
    `fname = 'server.log'`
    """
    @staticmethod
    def log(msg, status):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+ServerLog.fname, "a") as f:
            f.write("{}: {} [{}]\n".format(now, status.value.upper(), msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+ServerLog.fname, "w+") as f:
            pass

class GuiLog:
    """
    Class that holds logic of writing to log file by the GUI itself.
    """
    fname = "gui.log"
    """
    `fname = 'gui.log'`
    """

    @staticmethod
    def log(msg, status):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+GuiLog.fname, "a") as f:
            f.write("{}: {} [{}]\n".format(now, status.value.upper(), msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+GuiLog.fname, "w+") as f:
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



class LogStatus(Enum):
    """
    Holds the severity of the log nature
    """
    info = 'info'
    warning = 'warning'
    error = 'error'



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
    def log(msg, to, status):
        """
        ```
        input: str, LogType, LogStatus
        return: Log for chaining together methods.
        ```

        Logs a message to a file depending on LogType and LogStatus
        """
        if not isinstance(to, LogType):
            raise ValueError("Need to supply a LogType instance")
        
        if not isinstance(status, LogStatus):
            raise ValueError("Need to supply a LogStatus instance")
        
        if to == LogType.gui:
            GuiLog.log(msg, status)
        elif to == LogType.server:
            ServerLog.log(msg, status)
        else:
            raise AssertionError("LogType: Asserting my dominance")
        
        return Log

    @staticmethod
    def logerr(msg, to):
        """
        ```pyton
        input: str, LogType
        return: None
        ```
        wrapper to main log func, defaults to error type
        """
        Log.log(msg, to, status=LogStatus.error)

    @staticmethod
    def logwarn(msg, to):
        """
        ```pyton
        input: str, LogType
        return: None
        ```
        wrapper to main log func, defaults to warn type
        """
        Log.log(msg, to, status=LogStatus.warning)

    @staticmethod
    def loginfo(msg, to):
        """
        ```pyton
        input: str, LogType
        return: None
        ```
        wrapper to main log func, defaults to info type
        """
        Log.log(msg, to, status=LogStatus.info)

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
            LogType.gui: GuiLog,
            LogType.server:ServerLog
        }


        if log_type is None:
            # clear all logs
            for _, log in all_logs.items():
                log.clear()
            return
        
        if not isinstance(log_type, LogType):
            raise ValueError("Need to supply either None or a LogType")
            
        all_logs[log_type].clear()

VALID_STATUS = {
    'info' : Log.loginfo,
    'warning' : Log.logwarn,
    'error' : Log.logerr,
}

def log(status):
    status = status.lower()

    if status not in VALID_STATUS.keys():
        if status[0] not in [i[0] for i in VALID_STATUS.keys()]:
            Log.logwarn("Incorrect LogStatus supplied, msg={}".format(msg), LogType.gui)
            return

    log = VALID_STATUS[status]
    return log
