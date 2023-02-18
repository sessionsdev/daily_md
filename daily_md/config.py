import configparser
import os

from daily_md.constants import CONFIG_FILE_PATH


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = CONFIG_FILE_PATH
        self.config.read(self.config_file)

    def get_value(self, section, key, default=None):
        return self.config.get(section, key, fallback=default)

    def get_all_values(self):
        all_values = {}
        for section in self.config.sections():
            for key, value in self.config.items(section):
                all_values[f"{section}.{key}"] = value
        return all_values


config = Config()
