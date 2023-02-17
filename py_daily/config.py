import configparser
import os


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.config.read(self.config_file)

    def get_value(self, section, key, default=None):
        return self.config.get(section, key, fallback=default)


config = Config()
