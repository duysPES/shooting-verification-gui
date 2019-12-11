import datetime
from enum import Enum

LOG_PATH = "logs/"
class ServerLog:
    fname = "server.log"
    @staticmethod
    def log(msg):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+ServerLog.fname, "w") as f:
            f.write("{}: [{}]".format(now, msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+ServerLog.fname, "w+") as f:
            pass

class GuiLog:
    fname = "gui.log"
    @staticmethod
    def log(msg):
        now = datetime.datetime.now().ctime()
        with open(LOG_PATH+GuiLog.fname, "w") as f:
            f.write("{}: [{}]".format(now, msg))

    @staticmethod
    def clear():
         with open(LOG_PATH+GuiLog.fname, "w+") as f:
            pass

class LogType(Enum):
    gui = 0
    server = 1




class Log:
    @staticmethod
    def log(msg, to):
        if not isinstance(to, LogType):
            raise ValueError("Need to supply a LogType instance")

        
        if to == LogType.gui:
            GuiLog.log(msg)
        elif to == LogType.server:
            ServerLog.log(msg)
        else:
            raise AssertionError("LogType: Asserting my dominance")
        
        return Log

    @staticmethod
    def clear(log_type=None):
        all_logs = {
            LogType.gui: GuiLog,
            LogType.server: ServerLog
        }


        if log_type is None:
            # clear all logs
            for _, log in all_logs.items():
                log.clear()
            return
        
        if not isinstance(log_type, LogType):
            raise ValueError("Need to supply either None or a LogType")
            
        all_logs[log_type].clear()



