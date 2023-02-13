from datetime import datetime

from file_processor import FileProcessor


class LineProcessor:
    def __init__(self):
        self.file_processor = FileProcessor()

    def append_text_today(self, text: str) -> list[str] or None:
        lines = self.file_processor.lines
        if not lines:
            return False

        date_indexes = self.file_processor.date_indexes
        today: str = datetime.now().strftime("%Y-%m-%d")
        section_today = date_indexes.get(today)
        end_index = section_today[1]


        # index_today_end = self.file_processor._indexes._indexes.get(constants.DATE_INDEXES_KEY).get(today)[1]
        if end_index:
            lines.insert(end_index + 1, text)
            return lines
        else:
            return None
