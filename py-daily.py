#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime
import re
from typing import List, Tuple, Callable
import shutil
import os
import pickle
import time

config = configparser.ConfigParser()
config.read('config.ini')

FILEPATH = config['DEFAULT']['file_path']
today: datetime = datetime.now().strftime("%Y-%m-%d %A")


class BackupAndIndexFile:
    def __init__(self, filepath: str, num_backups: int = 10):
        self.filepath = filepath
        self.num_backups = num_backups

        self.backups_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'backups')

    def handle_backups(self):
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

        shutil.copy(self.filepath, os.path.join(self.backups_dir,
                    os.path.basename(self.filepath) + '.' + timestamp))

        backups = [f for f in os.listdir(self.backups_dir) if f.startswith(
            os.path.basename(self.filepath) + '.')]

        backups.sort(key=lambda x: int(x.split('.')[-1]), reverse=True)

        for backup in backups[self.num_backups:]:
            os.remove(os.path.join(self.backups_dir, backup))

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

        with open("section_indices.pickle", "wb") as f:
            pickle.dump(section_indices, f)

    def load_index(self):
        section_indices = {}
        with open("section_indices.pickle", "rb") as f:
            section_indices = pickle.load(f)
        return section_indices


bai = BackupAndIndexFile(FILEPATH)


def insert_todays_header(lines: List[str]) -> List[str]:
    header: str = f'# {today}\n'
    if not any(line.startswith(header) for line in lines):
        lines.append("\n" + header + "\n")
    return lines


def get_or_create_today_header_index(lines: List[str]) -> int:
    header = f'# {today}\n'
    for index, line in enumerate(lines):
        if line.startswith(header):
            return index
    lines = insert_todays_header(lines)
    return len(lines) - 1


def get_section_indices(lines: List[str], header_index: int) -> Tuple[int, int]:
    next_header_index: int = None

    for i, line in enumerate(lines[header_index+1:], start=header_index+1):
        if line.startswith("#"):
            next_header_index = i
            break

    return (header_index, next_header_index-1 if next_header_index else len(lines)-1)


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
            "Enter the number of the task item you want to complete (or 'q' to quit): ")

        if user_input.lower() == 'q':
            break

        try:
            selected_task_num = int(user_input)
        except ValueError:
            print("Invalid input. Please enter a number between 1 and {} or 'q' to quit.".format(
                len(incomplete_indices)))
            continue

        if selected_task_num not in range(1, len(incomplete_indices) + 1):
            print("Invalid input. Please enter a number between 1 and {} or 'q' to quit.".format(
                len(incomplete_indices)))
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
    section_indices = get_section_indices(lines, today_header_index)
    items_to_move = []

    for i in range(section_indices[0]):
        line = lines[i]

        if line.startswith("- [ ]"):
            items_to_move.append(line)
            lines[i] = line.replace("- [ ]", "- [>]")

    lines[section_indices[1]+1:section_indices[1]+1] = items_to_move

    return lines


def find_matching_date_indices(date_pattern: str, lines: List[str]) -> List[Tuple[int, int]]:
    pattern: str = re.compile(f'# {date_pattern.replace("*", "[0-9]+")}')
    print(f'PATTERN: {pattern}')
    return tuple(i for i, line in enumerate(lines) if pattern.match(line))


def print_date_sections(lines: List[str], date_pattern: str = today) -> None:
    indices = find_matching_date_indices(date_pattern, lines)
    section_indices = [get_section_indices(lines, index) for index in indices]

    separator = "\n-----------------------------------------\n"
    print(separator, end="")
    for start, end in section_indices:
        section = lines[start:end+1]
        print("".join(section), end=separator)


def append_text_today(lines: List[str], text: str) -> None:
    indexs: Tuple(int, int) = get_section_indices(
        lines, get_or_create_today_header_index(lines))
    lines.insert(indexs[1]+1, text)
    return lines


def process_file(line_processor: Callable, file_path=FILEPATH, mode='r+', *args, **kwargs):
    """
    Process a file line by line using a `line_processor` function.

    Arguments:
        line_processor: A function that takes a line as input and returns a modified line.
        file_path: The path to the file (default is `FILEPATH`).
        mode: The mode in which the file should be opened (default is 'r+').
        *args: Additional positional arguments to pass to `line_processor`.
        **kwargs: Additional keyword arguments to pass to `line_processor`.

    Returns:
        The processed lines as a list of strings.
    """
    backup_file_path = file_path + '.bak'
    try:
        # Create a backup of the file
        shutil.copy2(file_path, backup_file_path)
        with open(file_path, mode) as f:
            lines = f.readlines()
            lines = line_processor(lines, *args, **kwargs)
            if lines is not None:
                f.seek(0)
                f.write(''.join(lines))
                bai.index_file(lines)
                bai.handle_backups()
    except Exception as e:
        shutil.copy2(backup_file_path, file_path)  # Restore the backup
        os.remove(backup_file_path)  # Delete the backup file
        raise e  # Raise the original exception
    else:
        # Delete the backup file if no exception was raised
        os.remove(backup_file_path)


def py_daily_parser():
    parser = argparse.ArgumentParser(description='py-daily CLI utility')

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-p', '--print', choices=['task', 'log'], nargs=1, help='print task tasks or logs')
    group.add_argument('command', nargs='?', help='add a task task or a log')
    parser.add_argument('value', nargs='?',
                        help='description of the task task or log')

    args = parser.parse_args()

    if args.print:
        # user provided -p or --print
        if args.print == 'task':
            process_file(print_all_tasks)
        elif args.print == 'log':
            pass

    elif args.command:
        text_value = args.value

        # user provided command
        if args.command == 'task':
            task_item: str = f'- [ ] {text_value}\n'
            print("Adding to-do item:", task_item)
            process_file(append_text_today, text=task_item)
        elif args.command == 'log':
            log_item = f'- {text_value}\n'
            print("Logging entry:", log_item)
            process_file(append_text_today, text=log_item)
        elif args.command == 'migrate':
            # process_file(migrate_tasks)
            process_file(complete_tasks)
        else:
            print(process_file(print_date_sections, date_pattern=args.command))
    else:
        process_file(print_date_sections, date_pattern=today)


if __name__ == "__main__":
    py_daily_parser()

    section_indices = bai.load_index()

    # Print the section indices
    print(section_indices)
