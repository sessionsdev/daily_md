import configparser
import os
import pickle
import shutil
import sys
import time
from typing import List, Callable, Tuple, Dict, Union


class FileProcessor:
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.file_path = config["DEFAULT"]["file_path"]
        self.backups_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            config["DEFAULT"]["backup_file_path"],
        )
        self.num_backups = int(config["DEFAULT"].get("num_backups_to_keep", 10))
        self.indexes_filename = config["DEFAULT"]["date_index_filename"]
        self.lines = []
        self.indexes = {}

        self._load_and_index_file()

    def _load_and_index_file(self):
        print("LOADING AND INDEXING FILE")
        try:
            with open(self.file_path, "r") as f:
                lines = f.readlines()
        except FileNotFoundError as e:
            print(f"File not found: {self.file_path}")
            sys.exit(1)
        except PermissionError as e:
            print(f"Permission denied: {self.file_path}")
            sys.exit(1)
        except IsADirectoryError as e:
            print(f"{self.file_path} is a directory, not a file.")
            sys.exit(1)
        except IOError as e:
            print(f"An error occurred while reading the file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            sys.exit(1)

        if self._is_updated():
            self._index_file(lines)
        else:
            self._load_indexes()
        self.lines = lines

    def _load_indexes(self):
        try:
            with open(self.indexes_filename, "rb") as f:
                self.indexes = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Index file '{self.indexes_filename}' not found"
            )

    def _is_updated(self):
        if not os.path.exists(self.indexes_filename):
            return True
        return os.path.getmtime(self.file_path) > os.path.getmtime(
            self.indexes_filename
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
        print("INDEXING FILE........")

        if not lines or not lines[0].startswith("#"):
            raise ValueError("The first line must start with '#'")

        indexes = {
            "date_indexes": {},
            "incomplete_task_indexes": []
        }

        # Loop through the lines to find the section headers and store the indices
        section_start_index = 0
        previous_date = lines[0][2:12]
        for i, line in enumerate(lines):
            if not line or not line.strip():
                continue
            if line.startswith("#"):
                indexes["date_indexes"][previous_date] = (section_start_index, i - 1)
                section_start_index = i
                previous_date = line[2:12]
            if line.startswith("- [ ]"):
                indexes["incomplete_task_indexes"].append(i)

        indexes["date_indexes"][previous_date] = (section_start_index, i)

        with open(self.indexes_filename, "wb") as file_object:
            pickle.dump(indexes, file_object, protocol=pickle.HIGHEST_PROTOCOL)

        self.indexes = indexes

    def _backup_file(self):
        """
        This function handles backups of the file specified by the 'filepath' attribute of the class instance.
        The backups are stored in a directory specified by the 'backups_dir' attribute of the class instance.
        The number of backups to keep is specified by the 'num_backups' attribute of the class instance.

        Returns:
            None
        """
        timestamp = str(int(time.time()))

        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)

        shutil.copy(
            self.file_path,
            os.path.join(
                self.backups_dir, os.path.basename(self.file_path) + "." + timestamp
            ),
        )

        backups = [
            f
            for f in os.listdir(self.backups_dir)
            if f.startswith(os.path.basename(self.file_path) + ".")
        ]

        backups.sort(key=lambda x: int(x.split(".")[-1]), reverse=True)

        for backup in backups[self.num_backups:]:
            os.remove(os.path.join(self.backups_dir, backup))

    def process_file(
            self,
            line_processor: Callable[[List[str], Tuple, Dict], Union[List[str], None]],
            *args,
            **kwargs,
    ):
        processed_lines = line_processor(self.lines, *args, **kwargs)
        if processed_lines is not None:
            self._backup_file()
            try:
                with open(self.file_path, "w") as f:
                    f.seek(0)
                    f.write("".join(processed_lines))
                self._index_file(processed_lines)
            except Exception as e:
                most_recent_backup = max(
                    os.listdir(self.backups_dir), key=lambda x: os.path.getctime(x)
                )
                shutil.copy2(
                    most_recent_backup, self.file_path
                )  # Restore the most recent backup
                raise e  # Raise the original exception
