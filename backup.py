"""
backup.py
Author: Michael Pagliaro
Functionality to copy multiple files from one location to another efficiently.
"""

import os
import filecmp
import shutil


def run_backup(config):
    """
    The primary entry function that starts and runs the backup process.
    :param config: A configuration containing paths to folders to backup.
    """
    for input_path, outputs in config.get_entries():
        for output_path in outputs:
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " BACKUP")
            recursive_backup(input_path, backup_folder)


def recursive_backup(input_path, output_path):
    """
    The main backup algorithm. This recursively walks through the files specified by the
    input and copies them to their respective spot in the destination. If a backup has already
    been made previously, this will only update files that have been changed, added, or removed,
    causing subsequent backups to run much faster.
    :param input_path: The path to a file or folder to backup.
    :param output_path: The path to the inputs spot in the destination to back it up to.
    """
    if os.path.isfile(input_path):
        # Check if the file exists in output, then check if it's changed and copy it if it has been
        if os.path.exists(output_path):
            if not filecmp.cmp(input_path, output_path):
                shutil.copy2(input_path, output_path)
        else:
            shutil.copy2(input_path, output_path)
    else:
        # If this directory doesn't exist in the output, make it
        if not os.path.exists(output_path):
            os.mkdir(output_path)
            shutil.copymode(input_path, output_path)
        for filename in os.listdir(input_path):
            recursive_backup(os.path.join(input_path, filename), os.path.join(output_path, filename))
        # If any files/folders remain in the output that weren't in the input, delete them
        input_dir_files = os.listdir(input_path)
        output_dir_files = os.listdir(output_path)
        for output_file in output_dir_files:
            if output_file not in input_dir_files:
                os.remove(os.path.join(output_path, output_file))
