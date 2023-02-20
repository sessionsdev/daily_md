import argparse

from daily_md import *
from daily_md import core
from daily_md.initialize_config import initialize_config


def cli():
    parser = argparse.ArgumentParser(description="Process some options.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--config",
        dest="config",
        action="store_true",
        help="Configure the daily script.",
    )
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
        "-c", "--complete", dest="complete", action="store_true", help="Mark an item as complete"
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
        core.handle_log_args(args.log)
    elif args.todo:
        core.handle_todo_args(args.todo)
    elif args.migrate:
        core.handle_migrate()
    elif args.complete:
        core.complete_todos()
    elif args.print:
        core.handle_print_args(args.print)
    elif args.config:
        initialize_config()
    else:
        core.handle_print_args("default")


if __name__ == "__main__":
    cli()
