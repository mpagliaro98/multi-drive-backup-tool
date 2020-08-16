"""
backup.py
Author: Michael Pagliaro
Functionality to copy multiple files from one location to another efficiently.
"""

import os
import shutil
import time
from datetime import datetime
import sys
import traceback
import util
import configuration


# Constant for the backup confirmation filename
CONFIRMATION_FILENAME = "_BACKUP-CONFIRMATION.txt"

# Variables to track how many files have been processed during the backup process
NUM_FILES_PROCESSED = 0
NUM_FILES_MODIFIED = 0
NUM_FILES_NEW = 0
NUM_FILES_ERROR = 0
NUM_FILES_DELETED = 0
TOTAL_SIZE_PROCESSED = 0


def run_backup(config):
    """
    The primary entry function that starts and runs the backup process.
    :param config: A configuration containing paths to folders to backup.
    """
    print("Initializing...", end="\r", flush=True)
    util.begin_log()
    util.log("\n" + configuration.config_display_string(config, show_exclusions=True))
    for input_number in range(1, config.num_entries()+1):
        input_path = config.get_entry(input_number).input
        outputs = config.get_entry(input_number).outputs
        print("Initializing...", end="\r", flush=True)
        total_size, total_files = util.directory_size_with_exclusions(input_path, config, input_number)
        for output_path in outputs:
            # Get the name of the folder to make the backup in
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " BACKUP")

            # Start the log messages
            util.log("\n" + '/'*60)
            util.log("///// INPUT: " + input_path)
            util.log("///// OUTPUT: " + backup_folder)
            util.log('/'*60 + "\n")

            # Run the backup process and time it
            print(' '*20 + "\nBacking up {} to {}...".format(input_path, backup_folder))
            reset_globals()
            start_time = time.time()
            recursive_backup(input_path, backup_folder, total_size, total_files, config, input_number)
            end_time = time.time()
            print("\nBackup from {} to {} is complete. ({})".format(input_path, backup_folder,
                                                                    util.time_string(end_time-start_time)))

            # Report on any errors and finalize the backup
            final_report_str = "Backup complete: {} files processed, {} new files, {} existing files modified, " + \
                               "{} files removed ({:.2f} GiB)"
            util.log(final_report_str.format(NUM_FILES_PROCESSED, NUM_FILES_NEW, NUM_FILES_MODIFIED,
                                             NUM_FILES_DELETED, TOTAL_SIZE_PROCESSED / (2 ** 30)))
            if NUM_FILES_ERROR > 0:
                print("There were {} error(s) reported during this backup. Check the log for more info."
                      .format(NUM_FILES_ERROR))
                util.log("There were {} error(s) reported during this backup.".format(NUM_FILES_ERROR))
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
    global NUM_FILES_ERROR
    # Exclude this file or folder if it should be left out
    if config.get_entry(input_number).should_exclude(input_path):
        util.log("EXCLUDED - " + input_path)
        return False
    # If this path is to a file
    if os.path.isfile(input_path):
        try:
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
        except PermissionError:
            # Write the full error to the log file and record that an error occurred
            log_exception(output_path, "CREATING OR UPDATING")
            mark_file_processed(os.path.getsize(input_path), error=True)
    # Otherwise, it's a directory
    else:
        # If this directory doesn't exist in the output, make it
        if not os.path.exists(output_path):
            try:
                os.mkdir(output_path)
                shutil.copymode(input_path, output_path)
            except PermissionError:
                # Log the exception and indicate that an error occurred
                log_exception(output_path, "CREATING DIRECTORY")
                NUM_FILES_ERROR += 1
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
                try:
                    if os.path.isdir(delete_file_path):
                        deleted_size, deleted_file_count = util.directory_size(delete_file_path)
                        for _ in range(deleted_file_count):
                            mark_file_processed(deleted=True)
                        util.rmtree(delete_file_path)
                    else:
                        os.remove(delete_file_path)
                        # Don't increment the deleted count if this is the old confirmation file
                        if not output_file == CONFIRMATION_FILENAME and \
                                not output_path == config.get_entry(input_number).input:
                            mark_file_processed(deleted=True)
                    util.log("DELETED - " + delete_file_path)
                except PermissionError:
                    # Log the exception and indicate that an error occurred
                    log_exception(delete_file_path, "DELETING")
                    NUM_FILES_ERROR += 1
    print("{}/{} files processed, {} new files, {} existing files modified, {} files removed ({:.2f}/{:.2f} GiB)"
          .format(NUM_FILES_PROCESSED, total_files, NUM_FILES_NEW, NUM_FILES_MODIFIED, NUM_FILES_DELETED,
                  TOTAL_SIZE_PROCESSED / (2 ** 30), total_size / (2 ** 30)), end="\r", flush=True)
    return True


def reset_globals():
    """
    Reset the variables that track how many files are being processed.
    """
    global NUM_FILES_PROCESSED
    global NUM_FILES_MODIFIED
    global NUM_FILES_NEW
    global NUM_FILES_ERROR
    global NUM_FILES_DELETED
    global TOTAL_SIZE_PROCESSED
    NUM_FILES_PROCESSED = 0
    NUM_FILES_MODIFIED = 0
    NUM_FILES_NEW = 0
    NUM_FILES_ERROR = 0
    NUM_FILES_DELETED = 0
    TOTAL_SIZE_PROCESSED = 0


def mark_file_processed(file_size=0, modified=False, is_new=False, error=False, deleted=False):
    """
    Should be called when a file has been processed and backed up. This will increment the relevant
    variables that track how many files have been processed. If deleted is set to true, the size and number
    of files processed will not be incremented.
    :param file_size: The size of the file that was processed. 0 by default.
    :param modified: True if the file was already in the backup, and has just been changed. False by default.
    :param is_new: True if the file was not in the backup previously and was just copied over. False by default.
    :param error: True if there was an error processing the file. False by default.
    :param deleted: True to process a deleted file. False by default. This will not touch other fields.
    """
    global NUM_FILES_PROCESSED
    global NUM_FILES_MODIFIED
    global NUM_FILES_NEW
    global NUM_FILES_ERROR
    global NUM_FILES_DELETED
    global TOTAL_SIZE_PROCESSED
    if not deleted:
        NUM_FILES_PROCESSED += 1
        TOTAL_SIZE_PROCESSED += file_size
    if modified:
        NUM_FILES_MODIFIED += 1
    if is_new:
        NUM_FILES_NEW += 1
    if error:
        NUM_FILES_ERROR += 1
    if deleted:
        NUM_FILES_DELETED += 1


def create_backup_text_file(backup_base_folder):
    """
    Creates a file containing the current time into the given folder. This is meant to signify
    when the most recent backup has been completed.
    :param backup_base_folder: The folder to write the file to.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(backup_base_folder, CONFIRMATION_FILENAME)
    text_file = open(file_path, "w")
    text_file.write("This backup was completed on " + current_time)
    text_file.close()


def log_exception(error_file_path, action="ACCESSING"):
    """
    Writes the most recent exception to the log file. This includes the full traceback.
    :param error_file_path: The file or folder that caused the error.
    :param action: What was happening to that file to cause the error, such as "creating" or "deleting".
    """
    util.log("\n" + '=' * 60 + "\nERROR {} {}".format(action, error_file_path))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exception_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_error_str = ""
    for item in exception_list:
        full_error_str += item
    util.log(full_error_str + '=' * 60 + "\n")
