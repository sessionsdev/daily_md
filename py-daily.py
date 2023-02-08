#!/usr/bin/env python3

import argparse
import configparser
import os
import pickle
import re
import shutil
import sys
import time
import logging
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
        self.lines = []
        self.date_indices = {}

        self.load_and_index_file()

    def load_and_index_file(self):
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

        if self.is_updated():
            self.index_file(lines)
        else:
            self.load_date_index()
        self.lines = lines

    def load_date_index(self):
        try:
            with open(self.date_index_filename, "rb") as f:
                self.date_indices = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Index file '{self.date_index_filename}' not found")

    def is_updated(self):
        if not os.path.exists(self.date_index_filename):
            return True
        return os.path.getmtime(self.file_path) > os.path.getmtime(
            self.date_index_filename
        )

    def index_file(self, lines: List[str]):
        """
        Given a list of strings `lines`, this function indexes the file with date headers and
        returns a dictionary of the indices of each section. The first line must start with "#".
        Raises a `ValueError` if the input is not a list of strings or if the first line does not start with "#".
        """
        if not lines or not lines[0].startswith("#"):
            raise ValueError("The first line must start with '#'")

        section_indices = {}

        # Loop through the lines to find the section headers and store the indices
        section_start_index = 0
        previous_date = lines[0][2:12]
        for i, line in enumerate(lines[1:], 1):
            if line.startswith("#"):
                section_indices[previous_date] = (section_start_index, i - 1)
                section_start_index = i
                previous_date = line[2:12]

        section_indices[previous_date] = (section_start_index, i)

        with open(self.date_index_filename, "wb") as f:
            pickle.dump(section_indices, f, protocol=pickle.HIGHEST_PROTOCOL)

        self.date_indices = section_indices

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

        for backup in backups[self.num_backups:]:
            os.remove(os.path.join(self.backups_dir, backup))

    def process_file(self, line_processor: Callable, *args, **kwargs):
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

    for i, line in enumerate(lines[header_index + 1:], start=header_index + 1):
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

    lines[section_today[1] + 1: section_today[1] + 1] = items_to_move

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
        section = lines[start: end + 1]
        print("".join(section), end=separator)


def append_text_today(lines: List[str], text: str) -> list[str]:
    indexes: Tuple[int, int] = get_section_indices(
        lines, get_or_create_today_header_index(lines)
    )
    lines.insert(indexes[1] + 1, text)
    return lines


def py_daily_parser(file_processor=None):
    parser = argparse.ArgumentParser(description='Process some options.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--log', dest='log', help='Log an entry')
    group.add_argument('-t', '--todo', dest='todo', help='Add a to-do item')
    group.add_argument('-m', '--migrate', dest='migrate', action='store_true', help='Migrate past uncompleted todo items to today\'s section')
    group.add_argument('-c', '--complete', dest='complete', help='Mark an item as complete')
    group.add_argument('-p', '--print', dest='print', help='Print an argument', nargs=1)

    args = parser.parse_args()
    print(args)

    if args.log:
        # Handle the -l or --log option with argument "some text"
        print(f"Log entry: {args.log}")
    elif args.todo:
        # Handle the -t or --todo option with argument "some text"
        print(f"To-do item: {args.todo}")
    elif args.migrate:
        # Handle the -m or --migrate option
        print("Migrating past uncompleted to-do items to today's section.")
    elif args.complete:
        # Handle the -c or --complete option with argument "some text"
        print(f"Marking item as complete: {args.complete}")
    elif args.print is not None:
        # Handle the -p or --print option with argument "some text"
        print(f"Print argument: {args.print}")
    else:
        # Handle the -h or --help option
        print("Displaying help message.")

    # task = "task"
    # log = "log"
    # migrate = "migrate"
    #
    # parser = argparse.ArgumentParser(description="py-daily CLI utility")
    #
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument(
    #     "-p",
    #     "--print",
    #     choices=[task, log],
    #     nargs="?",
    #     help="print task tasks or logs",
    # )
    # group.add_argument("command", nargs="?", help="add a task task or a log")
    # parser.add_argument("value", nargs="?", help="description of the task task or log")
    #
    # args = parser.parse_args()
    # print(args)
    #
    # if args.print:
    #     print(args.print)
    #     # user provided -p or --print
    #     if args.print == task:
    #         print("PRINTING TASKS")
    #         file_processor.process_file(print_all_tasks)
    #     elif args.print == log:
    #         pass
    #
    # elif args.command:
    #     text_value = args.value
    #
    #     # user provided command
    #     if args.command == task:
    #         task_item: str = f"- [ ] {text_value}\n"
    #         print("Adding to-do item:", task_item)
    #         file_processor.process_file(append_text_today, text=task_item)
    #     elif args.command == log:
    #         log_item = f"- {text_value}\n"
    #         print("Logging entry:", log_item)
    #         file_processor.process_file(append_text_today, text=log_item)
    #     elif args.command == migrate:
    #         file_processor.process_file(migrate_tasks)
    #     else:
    #         print(
    #             file_processor.process_file(
    #                 print_date_sections, date_pattern=args.command
    #             )
    #         )
    # else:
    #     file_processor.process_file(print_date_sections, date_pattern=today)


if __name__ == "__main__":
    py_daily_parser()
