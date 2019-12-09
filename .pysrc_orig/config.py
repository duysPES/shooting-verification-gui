import configparser
from dotted_dict import DottedDict


class Config(configparser.ConfigParser):
    config_file_path = "./config.ini"

    def __init__(self):
        super(Config, self).__init__(self)
        self.read(self.config_file_path)

        self.d = DottedDict({s: dict(self.items(s)) for s in self.sections()})

    def dotted_dict(self):
        return self.d
