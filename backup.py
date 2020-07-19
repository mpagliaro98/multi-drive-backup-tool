"""
backup.py
Author: Michael Pagliaro
Functionality to copy multiple files from one location to another efficiently.
"""

import os
import filecmp
import shutil
import time
import util


NUM_FILES_PROCESSED = 0
NUM_FILES_MODIFIED = 0
NUM_FILES_NEW = 0
TOTAL_SIZE_PROCESSED = 0


def run_backup(config):
    """
    The primary entry function that starts and runs the backup process.
    :param config: A configuration containing paths to folders to backup.
    """
    for input_path, outputs in config.get_entries():
        for output_path in outputs:
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " BACKUP")
            print("\nBacking up {} to {}...".format(input_path, backup_folder))
            reset_globals()
            start_time = time.time()
            recursive_backup(input_path, backup_folder)
            end_time = time.time()
            print("\nBackup from {} to {} is complete. ({})".format(input_path, backup_folder,
                                                                    util.time_string(end_time-start_time)))


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
                mark_file_processed(os.path.getsize(input_path), modified=True, is_new=False)
            else:
                mark_file_processed(os.path.getsize(input_path), modified=False, is_new=False)
        else:
            shutil.copy2(input_path, output_path)
            mark_file_processed(os.path.getsize(input_path), modified=False, is_new=True)
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
    print("{} files processed, {} new files, {} existing files modified ({:.2f} GiB)"
          .format(NUM_FILES_PROCESSED, NUM_FILES_NEW, NUM_FILES_MODIFIED, TOTAL_SIZE_PROCESSED / (2 ** 30)),
          end="\r", flush=True)


def reset_globals():
    """
    Reset the variables that track how many files are being processed.
    """
    global NUM_FILES_PROCESSED
    global NUM_FILES_MODIFIED
    global NUM_FILES_NEW
    global TOTAL_SIZE_PROCESSED
    NUM_FILES_PROCESSED = 0
    NUM_FILES_MODIFIED = 0
    NUM_FILES_NEW = 0
    TOTAL_SIZE_PROCESSED = 0


def mark_file_processed(file_size, modified, is_new):
    """
    Should be called when a file has been processed and backed up. This will increment the relevant
    variables that track how many files have been processed.
    :param file_size: The size of the file that was processed.
    :param modified: True if the file was already in the backup, and has just been changed.
    :param is_new: True if the file was not in the backup previously and was just copied over.
    """
    global NUM_FILES_PROCESSED
    global NUM_FILES_MODIFIED
    global NUM_FILES_NEW
    global TOTAL_SIZE_PROCESSED
    NUM_FILES_PROCESSED += 1
    if modified:
        NUM_FILES_MODIFIED += 1
    if is_new:
        NUM_FILES_NEW += 1
    TOTAL_SIZE_PROCESSED += file_size
