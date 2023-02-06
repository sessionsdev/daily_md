#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime
import re
from typing import List, Tuple, Callable

config = configparser.ConfigParser()
config.read('config.ini')

FILEPATH = config['DEFAULT']['file_path']
today: datetime = datetime.now().strftime("%Y-%m-%d %A")


def create_today_header(lines: List[str] = None) -> List[str]:
    lines: List[str] = lines or []
    header: str = f'# {today}\n'
    if not any(line.startswith(header) for line in lines):
        lines.append(header + "\n")
    return lines


def get_or_create_today_header_index(lines: List[str] = None) -> int:
    lines = lines or []
    header = f'# {today}\n'
    for index, line in enumerate(lines):
        if line.startswith(header):
            return index
    lines = create_today_header(lines)
    return len(lines) - 1


def get_section_indices(lines: List[str], header_index: int) -> Tuple[int, int]:
    next_header_index: int = 0

    for i, line in enumerate(lines[header_index+1:], start=header_index+1):
        if line.startswith("#"):
            next_header_index = i
            break

    return (header_index, next_header_index-1 if next_header_index else len(lines)-1)


def print_all_tasks(lines: List[str]) -> None:
    incomplete_str = "- [ ]"
    incomplete_todos = []

    for line in lines:
        if line.startswith(incomplete_str):
            incomplete_todos.append(line)
    
    print("----------------------")
    print("TASKS ({} total)".format(len(incomplete_todos)))
    print("----------------------")
    for i, todo in enumerate(incomplete_todos, start=1):
        print("{}. {}".format(i, todo))

def migrate_tasks(lines: List[str]) -> List[str]:
    migrated_tasks = []
    
    for i in range(len(lines)):
        if lines[i].startswith("- [ ]"):
            migrated_tasks.append(lines[i])
            lines[i] = lines[i].replace("- [ ]", "- [>]")
    
    lines.append(migrated_tasks)
    return lines



def print_section(lines: List[str], start: int, end: int) -> str:
    return ''.join(lines[start:end])


def find_matching_date_indices(date_pattern: str, lines: List[str]) -> List[Tuple[int, int]]:
    pattern: str = re.compile(f'# {date_pattern.replace("*", "[0-9]+")}')
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
    try:
        with open(file_path, mode) as f:
            lines = f.readlines()
            lines = line_processor(lines, *args, **kwargs)
            if lines is not None:
                f.seek(0)
                f.write(''.join(lines))
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")

def py_daily_parser():
    parser = argparse.ArgumentParser(description='py-daily CLI utility')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--print', choices=['todo', 'log'], help='print todo tasks or logs')
    group.add_argument('command', nargs='?', help='add a todo task or a log')
    parser.add_argument('value', nargs='?', help='description of the todo task or log')

    args = parser.parse_args()

    if args.print:
        # user provided -p or --print
        if args.print == 'todo':
            process_file(print_all_tasks)
        elif args.print == 'log':
            pass

    elif args.command:
        text_value = args.value

        # user provided command
        if args.command == 'todo':
            todo_item: str = f'- [ ] {text_value}\n'
            print("Adding to-do item:", todo_item)
            process_file(append_text_today, text=todo_item)
        elif args.command == 'log':
            log_item = f'- {text_value}\n'
            print("Logging entry:", log_item)
            process_file(append_text_today, text=log_item)
        elif args.command == 'migrate':
            process_file(migrate_tasks)
        else:
            print(process_file(print_date_sections, date_pattern=args.command))
    else:
        process_file(print_date_sections, date_pattern=today)

if __name__ == "__main__":
    py_daily_parser()