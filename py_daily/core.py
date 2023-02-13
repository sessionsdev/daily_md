import configparser
import os
import pickle
import re
import shutil
import sys
import time
import logging
from datetime import datetime
from typing import Callable, List, Pattern, Tuple, Dict, Union
from py_daily import file_processor, constants

today_full_date: str = datetime.now().strftime("%Y-%m-%d %A")
today: str = datetime.now().strftime("%Y-%m-%d")
fp = file_processor.FileProcessor()


def insert_header_today(lines: List[str]) -> List[str]:
    header: str = f"# {today_full_date}"
    if not lines or lines[-1].strip():
        lines.append("\n")
    lines.append(header + " \n")
    lines.append("\n")
    return lines


def get_or_create_today_header_index(lines: List[str]) -> int:
    header = f"# {today_full_date}\n"
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


def print_date_section(lines: List[str], indices: Tuple[int, int]) -> None:
    separator = "\n-----------------------------------------\n"
    print(separator, end="")
    for line in lines[indices[0]: indices[1]]:
        print(line, end="")
    print(separator)


def append_text_today(lines: List[str], text: str) -> list[str] or None:
    index_today_end = fp._indexes.get(constants.DATE_INDEXES_KEY).get(today)[1]
    if index_today_end:
        lines.insert(index_today_end + 1, text)
        return lines
    else:
        return None


def handle_todo_args(todo_args):
    todo = f"- [ ] {todo_args}\n"
    fp.process_file(append_text_today, text=todo)


def handle_log_args(log_args):
    log = f"- {log_args}\n"
    fp.process_file(append_text_today, text=log)


def handle_print_args(print_args):
    date_indexes = fp._indexes["date_indexes"]
    today_sliced = today[:10]

    if print_args == "default":
        if not date_indexes.get(today_sliced):
            print("Today's header not yet create.  Creating now...")
            fp.process_file(insert_header_today)
            print("Done creating today's header.")
            return

        print_date_section(fp._lines, date_indexes.get(today))
    else:
        date_pattern = expand_date_pattern(print_args) or None
        if date_pattern is None:
            return

        for date in date_indexes.keys():
            if re.match(date_pattern, date) is not None:
                print_date_section(fp._lines, date_indexes.get(date))


def expand_date_pattern(pattern):
    year_pattern = r"(?P<year>\d{4})"
    month_pattern = r"(?P<month>\d{2})"
    day_pattern = r"(?P<day>\d{2})"

    year_wildcard = "*"
    month_wildcard = "*"
    day_wildcard = "*"

    # split pattern into parts
    parts = pattern.split("-")

    # replace year wildcard with regex pattern
    if len(parts) >= 1 and parts[0] != year_wildcard:
        parts[0] = year_pattern
    if len(parts) >= 2 and parts[1] == month_wildcard:
        parts[1] = month_pattern
    if len(parts) >= 3 and parts[2] == day_wildcard:
        parts[2] = day_pattern

    # join parts back into a single string
    pattern = "-".join(parts)

    # return complete regex pattern
    return f"^{pattern}$"
