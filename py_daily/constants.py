import os

TODO = "- [ ]"
COMPLETED_TODO = "- [x]"
MIGRATED_TODO = "- [>]"
DATE_INDEXES_KEY = "date_indexes"
TASK_INDEXES_KEY = "incomplete_task_indexes"
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.ini")
BACKUPS_DIR = os.path.join(os.path.dirname(__file__), "backups")
INDEXES_FILENAME = os.path.join(os.path.dirname(__file__), "indexes.pickle")
