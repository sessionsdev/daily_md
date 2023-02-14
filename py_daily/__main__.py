import argparse

from py_daily import core
from py_daily import *


def py_daily_parser():
    parser = argparse.ArgumentParser(description="Process some options.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--log", dest="log", help="Log an entry")
    group.add_argument("-t", "--todo", dest="todo", help="Add a to-do item")
    group.add_argument(
        "-m",
        "--migrate",
        dest="migrate",
        action="store_true",
        help="Migrate past uncompleted todo items to today's section",
    )
    group.add_argument(
        "-c", "--complete", dest="complete", help="Mark an item as complete"
    )
    parser.add_argument(
        "-p",
        "--print",
        type=str,
        dest="print",
        help="Print an argument",
        nargs="?",
        const="default",
    )

    args = parser.parse_args()

    if args.log:
        # Handle the -l option
        core.handle_log_args(args.log)
    elif args.todo:
        # Handle the -t option
        core.handle_todo_args(args.todo)
    elif args.migrate:
        # Handle the -m or --migrate option
        core.handle_migrate(args.migrate)
        print("Migrating past uncompleted to-do items to today's section.")
    elif args.complete:
        # Handle the -c or --complete option with argument "some text"
        print(f"Marking item as complete: {args.complete}")
    elif args.print:
        core.handle_print_args(args.print)
    else:
        # Handle the -h or --help option
        print("Displaying help message.")


if __name__ == "__main__":
    py_daily_parser()
