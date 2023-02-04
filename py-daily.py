#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime

config = configparser.ConfigParser()
config.read('config.ini')

file_path = config['DEFAULT']['file_path']
date_format = config['DEFAULT']['date_format']

def create_header(content):
    today = datetime.now().strftime(date_format)
    header = f'# {today}\n'
    if content:
        content.append('\n' + header)
    else:
        content.append(header)
    return header

def find_header(content):
    header = f'# {datetime.now().strftime("%Y-%m-%d")}'
    for line in content:
        if line.startswith(header):
            return line
    return create_header(content)

def append_todo(content, text):
    header = find_header(content)
    todo_item = f'- [ ] {text}\n'
    index = content.index(header)
    content.insert(index + 1, todo_item)

def append_log(content, text):
    header = find_header(content)
    log_item = f'- {text}\n'
    index = content.index(header)
    content.insert(index + 1, log_item)

parser = argparse.ArgumentParser(description='Add a todo item to a file')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-t', '--todo', help='Add a todo item with a checkbox')
group.add_argument('-l', '--log', help='Add a log item with a dash')


args = parser.parse_args()

with open(file_path, 'r+') as f:
    content = f.readlines()
    if args.todo:
        append_todo(content, args.todo)
    elif args.log:
        append_log(content, args.log)
    f.seek(0)
    f.write(''.join(content))
