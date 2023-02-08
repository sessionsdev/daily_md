#!/usr/bin/env python3

import argparse
import configparser
import os
import pickle
import re
import shutil
import time
from datetime import datetime
from typing import Callable, List, Pattern, Tuple

today: str = datetime.now().strftime("%Y-%m-%d %A")


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
        self.date_index_filename = config["DEFAULT"]["date_index_filename"]
        self.lines = self.load_and_index_file()

    def load_and_index_file(self):
        try:
            # shutil.copy2(self.file_path, f"{self.file_path}.bak")
            with open(self.file_path, "r") as f:
                lines = f.readlines()
        except Exception as e:
            raise e

        if self.is_updated():
            self.index_file(lines)
        return lines

    def is_updated(self):
        if not os.path.exists(self.date_index_filename):
            return True
        return os.path.getmtime(self.file_path) > os.path.getmtime(
            self.date_index_filename
        )

    def index_file(self, lines: List[str]):
        section_indices = {}

        # Loop through the lines to find the section headers and store the indices
        start_index = None
        for i, line in enumerate(lines):
            if line.startswith("#"):
                if start_index is not None:
                    section_indices[previous_date] = (start_index, i - 1)
                start_index = i
                previous_date = line[2:12]

        section_indices[previous_date] = (start_index, i)

        with open(self.date_index_filename, "wb") as f:
            pickle.dump(section_indices, f)

    def backup_file(self):
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

        for backup in backups[self.num_backups :]:
            os.remove(os.path.join(self.backups_dir, backup))

    def process_file(self, line_processor: Callable, *args, **kwargs):
        print(self.lines)
        processed_lines = line_processor(self.lines, *args, **kwargs)
        if processed_lines is not None:
            self.backup_file()
            try:
                with open(self.file_path, "w") as f:
                    f.seek(0)
                    f.write("".join(processed_lines))
                    self.index_file(processed_lines)
            except Exception as e:
                most_recent_backup = max(
                    os.listdir(self.backups_dir), key=lambda x: os.path.getctime(x)
                )
                shutil.copy2(
                    most_recent_backup, self.file_path
                )  # Restore the most recent backup
                raise e  # Raise the original exception


def insert_header_today(lines: List[str]) -> List[str]:
    header: str = f"# {today}\n"
    if not any(line.startswith(header) for line in lines):
        lines.append("\n" + header + "\n")
    return lines


def get_or_create_today_header_index(lines: List[str]) -> int:
    header = f"# {today}\n"
    for index, line in enumerate(lines):
        if line.startswith(header):
            return index
    lines = insert_header_today(lines)
    return len(lines) - 1


def get_section_indices(lines: List[str], header_index: int) -> Tuple[int, int]:
    next_header_index: int = None

    for i, line in enumerate(lines[header_index + 1 :], start=header_index + 1):
        if line.startswith("#"):
            next_header_index = i
            break

    return header_index, next_header_index - 1 if next_header_index else len(lines) - 1


def print_header(header_text):
    header_length = len(header_text) + 8
    print("+" + "-" * header_length + "+")
    print("|    " + header_text + "    |")
    print("+" + "-" * header_length + "+")


def print_all_tasks(lines: List[str]) -> None:

    incomplete_str = "- [ ]"
    incomplete_tasks = []

    for line in lines:
        if line.startswith(incomplete_str):
            incomplete_tasks.append(line)

    print_header("TASKS ({} total)".format(len(incomplete_tasks)))
    for i, task in enumerate(incomplete_tasks, start=1):
        print("{}) {}".format(i, task.replace("- [ ]", "")), end="")


def gather_incomplete_task_indices(lines: List[str]) -> List[int]:
    return [index for index, line in enumerate(lines) if line.startswith("- [ ]")]


def print_task_list(lines: List[str], indices: List[int]):
    print_header("TASK LIST")
    for task_num, task_index in enumerate(indices, start=1):
        task = lines[task_index].replace("- [ ]", "")
        print(f" {task_num}) {task}")


def complete_tasks(lines: List[str]) -> List[str]:
    incomplete_indices = gather_incomplete_task_indices(lines)
    task_num = 1
    while incomplete_indices:
        print_task_list(lines, incomplete_indices)
        user_input = input(
            "Enter the number of the task item you want to complete (or 'q' to quit): "
        )

        if user_input.lower() == "q":
            break

        try:
            selected_task_num = int(user_input)
        except ValueError:
            print(
                "Invalid input. Please enter a number between 1 and {} or 'q' to quit.".format(
                    len(incomplete_indices)
                )
            )
            continue

        if selected_task_num not in range(1, len(incomplete_indices) + 1):
            print(
                "Invalid input. Please enter a number between 1 and {} or 'q' to quit.".format(
                    len(incomplete_indices)
                )
            )
            continue

        task_index = incomplete_indices[selected_task_num - 1]
        task = lines[task_index].replace("- [ ]", "- [x]")
        lines[task_index] = task
        incomplete_indices = gather_incomplete_task_indices(lines)
        task_num += 1

    return lines


def migrate_tasks(lines: List[str]) -> List[str]:
    """
    This function takes a list of strings (lines) and returns a list of strings where
    the tasks marked with "- [ ]" are moved to the section with today's header.
    The tasks are marked as migrated by replacing "- [ ]" with "- [>]".

    :param lines: list of strings representing tasks.
    :return: list of strings with the migrated tasks.
    """
    today_header_index = get_or_create_today_header_index(lines)
    section_today = get_section_indices(lines, today_header_index)
    items_to_move = []

    for i in range(section_today[0]):
        line = lines[i]

        if line.startswith("- [ ]"):
            items_to_move.append(line)
            lines[i] = line.replace("- [ ]", "- [>]")

    lines[section_today[1] + 1 : section_today[1] + 1] = items_to_move

    return lines


def find_matching_date_indices(
    date_pattern: str, lines: List[str]
) -> List[Tuple[int, int]]:
    pattern: Pattern[str] = re.compile(f'# {date_pattern.replace("*", "[0-9]+")}')
    print(f"PATTERN: {pattern}")
    return tuple(i for i, line in enumerate(lines) if pattern.match(line))


def print_date_sections(lines: List[str], date_pattern: str = today) -> None:
    indices = find_matching_date_indices(date_pattern, lines)
    section_indices = [get_section_indices(lines, index) for index in indices]

    separator = "\n-----------------------------------------\n"
    print(separator, end="")
    for start, end in section_indices:
        section = lines[start : end + 1]
        print("".join(section), end=separator)


def append_text_today(lines: List[str], text: str) -> list[str]:
    indexes: Tuple[int, int] = get_section_indices(
        lines, get_or_create_today_header_index(lines)
    )
    lines.insert(indexes[1] + 1, text)
    return lines


# def process_file(
#     line_processor: Callable, file_path=FILEPATH, mode="r+", *args, **kwargs
# ):
#     """
#     Process a file line by line using a `line_processor` function.
#
#     Arguments:
#         line_processor: A function that takes a line as input and returns a modified line.
#         file_path: The path to the file (default is `FILEPATH`).
#         mode: The mode in which the file should be opened (default is 'r+').
#         *args: Additional positional arguments to pass to `line_processor`.
#         **kwargs: Additional keyword arguments to pass to `line_processor`.
#
#     Returns:
#         The processed lines as a list of strings.
#     """
#     backup_file_path = file_path + ".bak"
#     try:
#         # Create a backup of the file
#         shutil.copy2(file_path, backup_file_path)
#         with open(file_path, mode) as f:
#             lines = f.readlines()
#             lines = line_processor(lines, *args, **kwargs)
#             if lines is not None:
#                 f.seek(0)
#                 f.write("".join(lines))
#                 bai.index_file(lines)
#                 bai.backup_file()
#     except Exception as e:
#         shutil.copy2(backup_file_path, file_path)  # Restore the backup
#         os.remove(backup_file_path)  # Delete the backup file
#         raise e  # Raise the original exception
#     else:
#         # Delete the backup file if no exception was raised
#         os.remove(backup_file_path)


def py_daily_parser(file_processor):
    command_task = "task"
    command_log = "log"

    parser = argparse.ArgumentParser(description="py-daily CLI utility")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-p",
        "--print",
        choices=[command_task, command_log],
        nargs="?",
        help="print task tasks or logs",
    )
    group.add_argument("command", nargs="?", help="add a task task or a log")
    parser.add_argument("value", nargs="?", help="description of the task task or log")

    args = parser.parse_args()
    print(args)

    if args.print:
        print(args.print)
        # user provided -p or --print
        if args.print == 'task':
            print("PRINTING TASKS")
            file_processor.process_file(print_all_tasks)
        elif args.print == command_log:
            pass

    elif args.command:
        text_value = args.value

        # user provided command
        if args.command == command_task:
            task_item: str = f"- [ ] {text_value}\n"
            print("Adding to-do item:", task_item)
            file_processor.process_file(append_text_today, text=task_item)
        elif args.command == "log":
            log_item = f"- {text_value}\n"
            print("Logging entry:", log_item)
            file_processor.process_file(append_text_today, text=log_item)
        elif args.command == "migrate":
            # process_file(migrate_tasks)
            file_processor.process_file(complete_tasks)
        else:
            print(
                file_processor.process_file(
                    print_date_sections, date_pattern=args.command
                )
            )
    else:
        file_processor.process_file(print_date_sections, date_pattern=today)


if __name__ == "__main__":
    py_daily_parser(file_processor=FileProcessor())
