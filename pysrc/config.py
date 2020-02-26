import configparser
# from dotted_dict import DottedDict
import os, sys


class Config(configparser.ConfigParser):
    """
    Class the stores config.ini file in top-level
    directory.
    """
    """
    relative path to config file based on 
    where main.py is called.
    """
    def __init__(self):
        super(Config, self).__init__(self)
        # config_file_path = os.path.join(sys.path[0], 'config.ini')
        try:
            config_file_path = os.path.join(os.getenv("HOME"),
                                            "svg/config.ini")
        except TypeError:
            config_file_path = os.path.join(
                os.getenv("USERPROFILE", "svg\\config.ini"))

        self.config_file_path = config_file_path
        self.read(self.config_file_path)

        # self.d = DottedDict({s: dict(self.items(s)) for s in self.sections()})

    def dump(self):
        with open(self.config_file_path, "w") as conf:
            self.write(conf)

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

    def switches(self, section):
        """
        returns section values of switches header in config.ini
        """
        return self['SWITCHES'][section]

    def update_switches(self, section, value, dump=True):
        """
        updates a field in switches section
        """

        self['SWITCHES'][section] = value
        if dump:
            self.dump()

    # def dotted_dict(self):
    #     return self.d
