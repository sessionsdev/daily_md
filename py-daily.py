#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime
import re
from typing import List, Tuple

config = configparser.ConfigParser()
config.read('config.ini')

file_path = config['DEFAULT']['file_path']
# date_format = config['DEFAULT']['date_format']
date_format: str = "%Y-%m-%d %A"
today: datetime = datetime.now().strftime(date_format)


def wildcard_to_date_regex(pattern: str) -> str:
    pattern = pattern.replace("*", ".*")
    pattern = pattern.replace("-", "-")
    pattern = pattern.replace(" ", "\\ ")
    pattern = re.escape(pattern)
    validate_pattern(pattern)
    return f"^{pattern}$"

def validate_pattern(pattern):
    date_format = "2023-01-01 Monday"
    compiled_pattern = re.compile(pattern.replace("*", "[\w-]+"))
    match = compiled_pattern.search(date_format)
    if match:
        print("MATCH")
        return True
    else:
        print("NO MATCH")
        return False




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


def append_todo(lines: List[str], text: str) -> None:
    indexs: Tuple(int, int) = get_section_indices(
        lines, get_or_create_today_header_index(lines))
    todo_item: str = f'- [ ] {text}\n'
    if indexs[0] == indexs[1]:
        lines.insert(indexs[1]+1, todo_item)
    else:
        lines.insert(indexs[1], todo_item)


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


def append_log(lines: List[str], text: str) -> None:
    header = get_or_create_today_header_index(lines)
    log_item = f'- {text}\n'
    index = lines.index(header)
    lines.insert(index + 1, log_item)


def log_entry(args):
    print("Logging entry:", args.log)


def add_todo(args):
    print("Adding to-do item:", args.todo)


def migrate(args):
    print("Migrating past uncompleted to-do items to today's section")


def mark_complete(args):
    print("Marking item as complete:", args.complete)


def print_argument(args):
    print("PRINTING ---------------------")
    if args.print is None:
        print("No argument was passed")
    else:
        print("Printing argument:", args.print)

def process_file(file_path = None, line_processor = None, *args, **kwargs):
    if file_path is None or line_processor is None:
        raise ValueError("Filepath and line processor function required.")

    with open(file_path, 'r+') as f:
        lines = f.readlines()
        lines = line_processor(lines, *args, **kwargs)
        if lines is not None:
            f.seek(0)
            f.write(''.join(lines))


parser = argparse.ArgumentParser(description='py-daily CLI utility')

group = parser.add_mutually_exclusive_group()
group.add_argument('-p', '--print', choices=['todo', 'log'], help='print todo tasks or logs')
group.add_argument('command', nargs='?', help='add a todo task or a log')
parser.add_argument('value', nargs='?', help='description of the todo task or log')

args = parser.parse_args()

if args.print:
    # user provided -p or --print
    print("Printing {}".format(args.print))
elif args.command:
    # user provided command
    if args.command == 'todo':
        # add a todo task with description args.value
        print("Adding todo task: {}".format(args.value))
    elif args.command == 'log':
        # add a log with description args.value
        print("Adding log: {}".format(args.value))
    else:
        print("IN ARGS COMMAND")
        print(args.command)
        print(process_file(file_path, print_date_sections, date_pattern=args.command))
else:
    # no command or flag provided, default action
    print(wildcard_to_date_regex(today))
    print("No command or flag provided, performing default action")







# parser = argparse.ArgumentParser(description="display_help")

# group = parser.add_mutually_exclusive_group()
# group.add_argument("-l", "--log", help="Log an entry")
# group.add_argument("-t", "--todo", help="Add a to-do item")
# group.add_argument("-m", "--migrate", action="store_true",
#                    help="Migrate past uncompleted todo items to today's section")
# group.add_argument("-c", "--complete", help="Mark an item as complete")

# parser.add_argument("-p", "--print", help="Print an argument", nargs="?", required=False)


# args = parser.parse_args()

# commands = {
#     'log': log_entry,
#     'todo': add_todo,
#     'migrate': migrate,
#     'complete': mark_complete,
#     'print': print_argument,
# }

# for key in commands.keys():
#     print(key)
#     print(args)

#     if getattr(args, key):
#         commands[key](args)
#         break

# with open(file_path, 'r+') as f:
#     lines = f.readlines()
#     if args.date_pattern:
#         print_date_sections(lines, args.date_pattern)
#     else:
#         print_date_sections(lines, today)
#     f.seek(0)
#     f.write(''.join(lines))

