import os

TODO = "- [ ]"
COMPLETED_TODO = "- [x]"
MIGRATED_TODO = "- [>]"
DATE_INDEXES_KEY = "date_indexes"
TASK_INDEXES_KEY = "incomplete_task_indexes"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE_PATH = os.path.join(DATA_DIR, "config.ini")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
INDEXES_FILENAME = os.path.join(DATA_DIR, "indexes.pickle")
