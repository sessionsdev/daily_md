import configparser
import os
import readline

from daily_md.constants import CONFIG_FILE_PATH


def initialize_config():
    # Initialize the configuration parser
    config = configparser.ConfigParser()

    # Define a function for tab completion of file paths
    def complete_file_path(text, state):
        # Get the list of completions for the current input
        text = os.path.expanduser(text)  # Expand user home directory (~)
        dirname, basename = os.path.split(text)
        if dirname == "":
            dirname = "."
        options = [
            os.path.join(dirname, f)
            for f in os.listdir(dirname)
            if f.startswith(basename)
        ]
        try:
            return options[state]
        except IndexError:
            return None

    # Prompt the user for the file path
    readline.set_completer_delims("\t")
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete_file_path)
    while True:
        file_path = input("Enter file path (default=daily.md): ").strip() or "daily.md"
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in [".md", ".txt"]:
            print(
                f"{file_ext} files are not supported. Please enter a .md or .txt file."
            )
            continue
        if os.path.isfile(file_path):
            break
        else:
            create_file = (
                input(f"{file_path} does not exist. Do you want to create it? (Y/N): ")
                .strip()
                .lower()
            )
            if create_file == "y":
                with open(file_path, "w") as f:
                    f.write("")
                break
            else:
                print("Exiting program.")
                exit()

    # Prompt the user for the number of backups to keep
    num_backups_to_keep = (
        input("Enter number of backups to keep (default=5): ").strip() or "5"
    )

    # Prompt the user to choose whether to save backups
    save_backups_str = input("Save backups (y/n, default=y): ").strip().lower()
    save_backups = save_backups_str in {"y", "yes"} if save_backups_str else True

    # Prompt the user to choose whether to save indexes
    save_indexes_str = input("Save indexes (y/n, default=y): ").strip().lower()
    save_indexes = save_indexes_str in {"y", "yes"} if save_indexes_str else True

    # Store the configuration values in the config file
    config["options"] = {
        "file_path": os.path.abspath(file_path),
        "save_backups": str(save_backups),
        "num_backups": num_backups_to_keep,
        "save_indexes": str(save_indexes),
    }

    print(f"Saving config to: {CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, "w") as f:
        config.write(f)
