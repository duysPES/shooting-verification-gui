import configparser
# from dotted_dict import DottedDict
import os, sys


class Config(configparser.ConfigParser):
    """
    Class the stores config.ini file in top-level
    directory.
    """

    config_file_path = os.path.join(sys.path[0], 'config.ini')
    """
    relative path to config file based on 
    where main.py is called.
    """
    def __init__(self):
        super(Config, self).__init__(self)
        self.read(self.config_file_path)

        # self.d = DottedDict({s: dict(self.items(s)) for s in self.sections()})

    def ssi(self, section):
        """
        Returns section values of SSI header in config.ini

        Input: str
        return: str
        """

        return self['SSI'][section]

    def lisc(self, section):
        """
        Returns section values of lisc header in config.ini
        
        Input: str
        return: str
        """
        return self['LISC'][section]

    def sim_server(self, section):
        """
        Returns section values of sim_server header in config.ini
        
        Input: str
        return: str
        """
        return self['SIM_SERVER'][section]

    # def dotted_dict(self):
    #     return self.d
