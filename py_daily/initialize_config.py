import os
import configparser
import readline


def initialize_config():
    # Initialize the configuration parser
    config = configparser.ConfigParser()

    # Define a function for tab completion of file paths
    def complete_file_path(text, state):
        # Get the list of completions for the current input
        options = [f for f in os.listdir('.') if f.startswith(text)]
        try:
            return options[state]
        except IndexError:
            return None

    # Prompt the user for the file path
    readline.set_completer_delims('\t')
    readline.parse_and_bind('tab: complete')
    readline.set_completer(complete_file_path)
    while True:
        file_path = input('Enter file path (default=daily.md): ').strip() or 'daily.md'
        if os.path.isfile(file_path):
            break
        else:
            print(f'{file_path} is not a file.')

    # Define a function for tab completion of backup directory paths
    def complete_backup_dir(text, state):
        # Get the list of completions for the current input
        options = [f for f in os.listdir('.') if f.startswith(text)]
        try:
            return options[state]
        except IndexError:
            return None

    # Prompt the user for the backup directory
    readline.set_completer(complete_backup_dir)
    while True:
        backup_dir = input('Enter backup directory (default=./backups): ').strip() or './backups'
        if os.path.isdir(backup_dir):
            break
        else:
            print(f'{backup_dir} is not a directory.')

    # Prompt the user for the number of backups to keep
    num_backups_to_keep = input('Enter number of backups to keep (default=5): ').strip() or '5'

    # Prompt the user to choose whether to save backups
    save_backups = input('Save backups (y/n, default=y): ').strip().lower() in {'y', 'yes'}

    # Prompt the user to choose whether to save indexes
    save_indexes = input('Save indexes (y/n, default=y): ').strip().lower() in {'y', 'yes'}

    # Store the configuration values in the config file
    config['options'] = {
        'file_path': os.path.abspath(file_path),
        'backup_dir': os.path.abspath(backup_dir),
        'save_backups': str(save_backups),
        'num_backups': num_backups_to_keep,
        'save_indexes': str(save_indexes)
    }

    config_file_path = os.path.join(os.path.dirname(__file__), 'config.ini')

    print(f"Saving config to: {config_file_path}")

    with open(config_file_path, 'w') as f:
        config.write(f)
