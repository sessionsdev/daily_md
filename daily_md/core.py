from datetime import datetime

from daily_md import line_handlers
from daily_md.config import config
from daily_md.constants import TODO

today_full_date: str = datetime.now().strftime("%Y-%m-%d %A")
today: str = datetime.now().strftime("%Y-%m-%d")
line_handler = line_handlers.LineHandler()


def print_header(header_text):
    header_length = len(header_text) + 8
    print("+" + "-" * header_length + "+")
    print("|    " + header_text + "    |")
    print("+" + "-" * header_length + "+")


def print_section(lines: list[str]) -> None:
    separator = "\n-----------------------------------------\n"
    print(separator, end="")
    for line in lines:
        print(line, end="")
    print(separator)


def handle_todo_args(todo_args):
    todo = f"{TODO} {todo_args}\n"
    line_handler.append_text_today(todo)


def handle_log_args(log_args):
    log = f"- {log_args}\n"
    line_handler.append_text_today(log)


def handle_migrate(migrate_args):
    line_handler.migrate_tasks_to_date(today)


def handle_print_args(print_args):
    if print_args == "default":
        lines = line_handler.get_lines_for_date(today)
        if lines:
            print_section(lines)
        else:
            prompt_header_creation()
    elif print_args == "todo":
        print_header("TODO LIST")
        lines = line_handler.get_todo_lines()
        print("".join(lines))
    elif print_args == "config":
        print_header("CONFIG VALUES")
        print()
        values = config.get_all_values()
        for name, value in values.items():
            print(f"{name}: {value}")
        print()
    else:
        date_pattern = expand_date_pattern(print_args) or None
        if date_pattern is None:
            return

        lines_by_date = line_handler.get_lines_by_date_pattern(date_pattern)
        for date, lines in lines_by_date.items():
            print_section(lines)


def prompt_header_creation():
    create_header = input("Today's header not found.  Create it now? (y/n) ")
    if create_header.lower() == "y":
        line_handler.create_header_today()
        return
    else:
        return


def expand_date_pattern(pattern: str) -> str:
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
