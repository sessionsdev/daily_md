#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime
import re

config = configparser.ConfigParser()
config.read('config.ini')

file_path = config['DEFAULT']['file_path']
date_format = config['DEFAULT']['date_format']
date_format = "%Y-%m-%d %A"
today = datetime.now().strftime(date_format)

def create_today_header(lines=None):
    lines = lines or []
    header = f'# {today}\n'
    if not any(line.startswith(header) for line in lines):
        lines.append(header + "\n")
    return lines

def get_or_create_today_header_index(lines=None):
    lines = lines or []
    header = f'# {today}\n'
    for index, line in enumerate(lines):
        if line.startswith(header):
            return index
    lines = create_today_header(lines)
    return len(lines) - 1


def get_section_indices(lines, header_index):
    next_header_index = 0
    
    for i, line in enumerate(lines[header_index+1:], start=header_index+1):
        if line.startswith("#"):
            next_header_index = i
            break
    
    return (header_index, next_header_index-1 if next_header_index else len(lines)-1) 

def append_todo(lines, text):
    indexs = get_section_indices(lines, get_or_create_today_header_index(lines))
    todo_item = f'- [ ] {text}\n'
    if indexs[0] == indexs[1]:
        lines.insert(indexs[1]+1, todo_item)
    else:
        lines.insert(indexs[1], todo_item)

def print_section(lines, start, end):
    return ''.join(lines[start:end])


def find_matching_date_indices(date_pattern, lines):
    pattern = re.compile(f'# {date_pattern.replace("*", "[0-9]+")}')
    return tuple(i for i, line in enumerate(lines) if pattern.match(line))


def print_date_sections(lines, date_pattern):
    indices = find_matching_date_indices(date_pattern, lines)
    section_indices = []
    for index in indices:
        section_indices.append(get_section_indices(lines, index))
    
    print("-----------------------------------------")
    for section in section_indices:
        print(print_section(lines, section[0], section[1]))
        print("-----------------------------------------")

def append_log(lines, text):
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
    print("Printing argument:", args.print)


parser = argparse.ArgumentParser(description="display_help")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-l", "--log", help="Log an entry")
group.add_argument("-t", "--todo", help="Add a to-do item")
group.add_argument("-m", "--migrate", action="store_true", help="Migrate past uncompleted todo items to today's section")
group.add_argument("-c", "--complete", help="Mark an item as complete")
group.add_argument("-p", "--print", help="Print an argument")


args = parser.parse_args()

commands = {
    'log': log_entry,
    'todo': add_todo,
    'migrate': migrate,
    'complete': mark_complete,
    'print': print_argument,
}

for key in commands.keys():
    if getattr(args, key):
        commands[key](args)
        break

# with open(file_path, 'r+') as f:
#     lines = f.readlines()
#     if args.todo:
#         append_todo(lines, args.todo)
#     elif args.log:
#         append_log(lines, args.log)
#     elif args.day:
#         print_date_sections(lines, today)
#     f.seek(0)
#     f.write(''.join(lines))

