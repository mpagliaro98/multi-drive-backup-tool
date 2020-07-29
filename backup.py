"""
backup.py
Author: Michael Pagliaro
Functionality to copy multiple files from one location to another efficiently.
"""

import os
import shutil
import time
from datetime import datetime
import util
import configuration


# Variables to track how many files have been processed during the backup process
NUM_FILES_PROCESSED = 0
NUM_FILES_MODIFIED = 0
NUM_FILES_NEW = 0
TOTAL_SIZE_PROCESSED = 0


def run_backup(config):
    """
    The primary entry function that starts and runs the backup process.
    :param config: A configuration containing paths to folders to backup.
    """
    util.begin_log()
    util.log("\n" + configuration.config_display_string(config, show_exclusions=True))
    for input_number in range(1, config.num_entries()+1):
        input_path = config.get_input(input_number)
        outputs = config.get_destinations(input_number)
        total_size, total_files = util.directory_size_with_exclusions(input_path, config, input_number)
        for output_path in outputs:
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " BACKUP")
            util.log("\n//////////////////////////////////////////////////////")
            util.log("///// INPUT: " + input_path)
            util.log("///// OUTPUT: " + backup_folder)
            util.log("//////////////////////////////////////////////////////\n")
            print("\nBacking up {} to {}...".format(input_path, backup_folder))
            reset_globals()
            start_time = time.time()
            recursive_backup(input_path, backup_folder, total_size, total_files, config, input_number)
            end_time = time.time()
            print("\nBackup from {} to {} is complete. ({})".format(input_path, backup_folder,
                                                                    util.time_string(end_time-start_time)))
            util.log("Backup complete: {} files processed, {} new files, {} existing files modified ({:.2f} GiB)"
                     .format(NUM_FILES_PROCESSED, NUM_FILES_NEW, NUM_FILES_MODIFIED, TOTAL_SIZE_PROCESSED / (2 ** 30)))
            create_backup_text_file(backup_folder)
    util.end_log()


def recursive_backup(input_path, output_path, total_size, total_files, config, input_number):
    """
    The main backup algorithm. This recursively walks through the files specified by the
    input and copies them to their respective spot in the destination. If a backup has already
    been made previously, this will only update files that have been changed, added, or removed,
    causing subsequent backups to run much faster.
    :param input_path: The path to a file or folder to backup.
    :param output_path: The path to the inputs spot in the destination to back it up to.
    :param total_size: The total size in bytes of the full input backup. This shouldn't decrease during recursion.
    :param total_files: The total number of files in the full input backup. This shouldn't decrease during recursion.
    :param config: The current backup configuration.
    :param input_number: The number of the index of the entry, starting at 1.
    :return: True if the current file/directory was processed, false if it was excluded.
    """
    # Exclude this file or folder if it should be left out
    if config.should_exclude(input_number, input_path):
        util.log("EXCLUDED - " + input_path)
        return False
    # If this path is to a file
    if os.path.isfile(input_path):
        # Check if the file exists in output, then check if it's changed and copy it if it has been
        if os.path.exists(output_path):
            if not util.file_compare(input_path, output_path):
                shutil.copy2(input_path, output_path)
                mark_file_processed(os.path.getsize(input_path), modified=True, is_new=False)
                util.log("UPDATED - " + output_path)
            else:
                mark_file_processed(os.path.getsize(input_path), modified=False, is_new=False)
        else:
            shutil.copy2(input_path, output_path)
            mark_file_processed(os.path.getsize(input_path), modified=False, is_new=True)
            util.log("NEW - " + output_path)
    # Otherwise, it's a directory
    else:
        # If this directory doesn't exist in the output, make it
        if not os.path.exists(output_path):
            os.mkdir(output_path)
            shutil.copymode(input_path, output_path)
        files_processed = []
        for filename in os.listdir(input_path):
            result = recursive_backup(os.path.join(input_path, filename), os.path.join(output_path, filename),
                                      total_size, total_files, config, input_number)
            if result:
                files_processed.append(filename)

        # If any files/folders remain in the output that weren't in the input, delete them
        for output_file in os.listdir(output_path):
            if output_file not in files_processed:
                delete_file_path = os.path.join(output_path, output_file)
                # Use the correct delete function based on if it's a file or folder
                if os.path.isdir(delete_file_path):
                    util.rmtree(delete_file_path)
                else:
                    os.remove(delete_file_path)
                util.log("DELETED - " + delete_file_path)
    print("{}/{} files processed, {} new files, {} existing files modified ({:.2f}/{:.2f} GiB)"
          .format(NUM_FILES_PROCESSED, total_files, NUM_FILES_NEW, NUM_FILES_MODIFIED,
                  TOTAL_SIZE_PROCESSED / (2 ** 30), total_size / (2 ** 30)), end="\r", flush=True)
    return True


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


def create_backup_text_file(backup_base_folder):
    """
    Creates a file containing the current time into the given folder. This is meant to signify
    when the most recent backup has been completed.
    :param backup_base_folder: The folder to write the file to.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = "_BACKUP-CONFIRMATION.txt"
    file_path = os.path.join(backup_base_folder, file_name)
    text_file = open(file_path, "w")
    text_file.write("This backup was completed on " + current_time)
    text_file.close()
