from datetime import datetime

import re

from py_daily import file_handler
from py_daily import constants
from py_daily.exceptions import DateHeaderNotFoundError


class LineHandler:
    def __init__(self):
        self._file_handler = None

    def get_file_handler(self):
        if self._file_handler is None:
            self._file_handler = file_handler.FileHandler()
        return self._file_handler

    def create_header_today(self):
        now = datetime.now()
        today_full = now.strftime("%Y-%m-%d %A")
        header = f"# {today_full}\n"

        lines = self.get_file_handler().lines

        if not self.get_file_handler().date_indexes.get(now.strftime("%Y-%m-%d")):
            if not lines or lines[-1] != "\n":
                lines.append("\n")
            lines.append(header)

        if lines:
            self.get_file_handler().write_to_file(lines)
            print(f"Header for {today_full} successfully created!")

    def append_text_today(self, text: str) -> list[str] or None:
        today: str = datetime.now().strftime("%Y-%m-%d")
        lines = self.get_file_handler().lines
        if not lines:
            raise DateHeaderNotFoundError(today)

        date_indexes = self.get_file_handler().date_indexes
        section_today = date_indexes.get(today)
        if not section_today:
            raise DateHeaderNotFoundError(today)

        end_index = section_today[1]

        if end_index:
            lines.insert(end_index + 1, text)
            self.get_file_handler().write_to_file(lines)
            return True
        else:
            return None

    def get_lines_by_dates(self, dates: list[str]) -> dict[str, list[str]]:
        result = {}
        for date in dates:
            section_indexes: tuple[int, int] = self.get_file_handler().date_indexes.get(
                date, (None, None)
            )
            start, end = section_indexes
            print(section_indexes)
            if start is None or end is None:
                continue
            result[date] = self.get_file_handler().lines[start:end]
        return result

    def get_lines_by_date_pattern(self, pattern: str) -> dict[str, list[str]]:
        result = {}
        for date, (start, end) in self.get_file_handler().date_indexes.items():
            if re.match(pattern, date):
                result[date] = self.get_file_handler().lines[start:end]
        return result

    def get_lines_for_date(self, date: str) -> list[str]:
        lines_by_date = self.get_lines_by_dates([date])
        return lines_by_date.get(date, [])

    def get_todo_lines(self):
        return [self.get_file_handler().lines[i] for i in self.get_file_handler().todo_indexes]

    def migrate_tasks_to_date(self, date: str):
        start, end = self.get_file_handler().date_indexes.get(date, (None, None))
        if start is None or end is None:
            raise DateHeaderNotFoundError(date)

        todo_indexes = self.get_file_handler().todo_indexes
        if not todo_indexes:
            print("No incomplete tasks to migrate.")
            return

        lines = self.get_file_handler().lines

        for i in reversed(todo_indexes):
            if i < start or i > end:
                line = lines[i]
                if line.startswith(constants.TODO):
                    lines[i] = line.replace(constants.TODO, constants.MIGRATED_TODO, 1)
                    lines.insert(end + 1, line)

        self.get_file_handler().write_to_file(lines)
