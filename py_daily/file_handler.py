import configparser
import os
import pickle
import shutil
import sys
import time
from typing import List, Callable
from py_daily import constants


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class FileHandler(metaclass=Singleton):
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        self._file_path = config["DEFAULT"]["file_path"]
        self._backups_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            config["DEFAULT"]["backup_file_path"],
        )
        self._num_backups = int(config["DEFAULT"].get("num_backups_to_keep", "10"))
        self._indexes_filename = config["DEFAULT"]["date_index_filename"]
        self.is_save_index = config["DEFAULT"]["save_index"]

        self._lines, self._indexes = self._load_and_index_file()

    @property
    def lines(self):
        return self._lines

    @property
    def date_indexes(self):
        return self._indexes.get(constants.DATE_INDEXES_KEY) or {}

    @property
    def todo_indexes(self):
        return self._indexes.get(constants.TASK_INDEXES_KEY) or []

    def _load_and_index_file(self):
        try:
            with open(self._file_path, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"File not found: {self._file_path}")
            sys.exit(1)
        except PermissionError:
            print(f"Permission denied: {self._file_path}")
            sys.exit(1)
        except IsADirectoryError:
            print(f"{self._file_path} is a directory, not a file.")
            sys.exit(1)
        except IOError as e:
            print(f"An error occurred while reading the file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            sys.exit(1)

        if self._is_updated():
            indexes = self._index_file(lines)
        else:
            indexes = self._load_indexes()

        return lines, indexes

    def _load_indexes(self):
        try:
            with open(self._indexes_filename, "rb") as f:
                indexes = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Index file '{self._indexes_filename}' not found")

        return indexes

    def _is_updated(self):
        if not os.path.exists(self._indexes_filename):
            return True
        return os.path.getmtime(self._file_path) > os.path.getmtime(
            self._indexes_filename
        )

    def _index_file(self, lines: List[str]):
        """
        Indexes a file with date headers and returns a dictionary of the indices of each section. The first line must
        start with "#". The indexed data is stored in a pickle file with the name `self.date_index_filename`.

        Args:
        lines (List[str]): A list of strings representing the lines of the file.

        Returns:
        None

        Raises:
        ValueError: If the input is not a list of strings or if the first line does not start with "#".
        """
        if not lines or not lines[0].startswith("#"):
            raise ValueError("The first line must start with '#'")

        indexes = {constants.DATE_INDEXES_KEY: {}, constants.TASK_INDEXES_KEY: []}

        # Loop through the lines to find the section headers and store the indices
        section_start_index = 0
        previous_date = lines[0][2:12]
        for i, line in enumerate(lines):
            if not line or not line.strip():
                continue
            if line.startswith("#"):
                indexes[constants.DATE_INDEXES_KEY][previous_date] = (
                    section_start_index,
                    i,
                )
                section_start_index = i
                previous_date = line[2:12]
            if line.startswith(constants.TODO):
                indexes[constants.TASK_INDEXES_KEY].append(i)

        # Add code to handle the last section
        indexes[constants.DATE_INDEXES_KEY][previous_date] = (
            section_start_index,
            i + 1,
        )

        if self.is_save_index:
            with open(self._indexes_filename, "wb") as file_object:
                pickle.dump(indexes, file_object, protocol=pickle.HIGHEST_PROTOCOL)

        return indexes

    def _backup_file(self):
        """
        This function handles backups of the file specified by the 'filepath' attribute of the class instance.
        The backups are stored in a directory specified by the 'backups_dir' attribute of the class instance.
        The number of backups to keep is specified by the 'num_backups' attribute of the class instance.

        Returns:
            None
        """
        timestamp = str(int(time.time()))

        if not os.path.exists(self._backups_dir):
            os.makedirs(self._backups_dir)

        shutil.copy(
            self._file_path,
            os.path.join(
                self._backups_dir, os.path.basename(self._file_path) + "." + timestamp
            ),
        )

        backups = [
            f
            for f in os.listdir(self._backups_dir)
            if f.startswith(os.path.basename(self._file_path) + ".")
        ]

        backups.sort(key=lambda x: int(x.split(".")[-1]), reverse=True)

        for backup in backups[self._num_backups :]:
            os.remove(os.path.join(self._backups_dir, backup))

    def clear_index_cache(self):
        try:
            os.remove(self._indexes_filename)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"An unexpected error occurred while deleting the cache: {e}")

    def write_to_file(self, lines_to_write: list[str]):
        # processed_lines = line_processor(self._lines, *args, **kwargs)
        if lines_to_write is not None:
            self._backup_file()
            try:
                with open(self._file_path, "w") as f:
                    f.seek(0)
                    f.write("".join(lines_to_write))
                self._index_file(lines_to_write)
            except Exception as e:
                most_recent_backup = max(
                    os.listdir(self._backups_dir), key=lambda x: os.path.getctime(x)
                )
                shutil.copy2(most_recent_backup, self._file_path)
                raise e
