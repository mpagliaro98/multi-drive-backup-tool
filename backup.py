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
import log
from observer import observable


# Constant for the backup confirmation filename
CONFIRMATION_FILENAME = "_BACKUP-CONFIRMATION.txt"

# The string on the end of the final backup folders
BACKUP_FOLDER_SUFFIX = "BACKUP"

# Variables to track how many files have been processed during the backup process, all are observable
BACKUP_NUMBER = 0
NUM_FILES_PROCESSED = 0
NUM_FILES_MARKED = 0
NUM_FILES_MODIFIED = 0
NUM_FILES_NEW = 0
NUM_FILES_ERROR = 0
NUM_FILES_DELETED = 0
TOTAL_SIZE_PROCESSED = 0
BACKUP_PROGRESS = 0
CURRENT_STATUS = ""
ERROR = ""


@log.logger
def run_backup(config):
    """
    The primary entry function that starts and runs the backup process. This algorithm will go through each
    input-output pair in the configuration individually and run on each. It begins on each pair by marking which
    files will be new, modified, or deleted, then it uses those to check space requirements on the disk, then it
    does the file operations on each file in each list.
    :param config: A configuration containing paths to folders to backup.
    """
    print("Initializing...", end="\r", flush=True)
    set_status("Initializing...")
    reset_backup_number()
    log.log("\n" + configuration.config_display_string(config, show_exclusions=True))

    # Loop through every entry in the configuration
    for input_number in range(1, config.num_entries()+1):
        input_path = config.get_entry(input_number).input
        outputs = config.get_entry(input_number).outputs
        for output_path in outputs:
            # Get the name of the folder to make the backup in
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " " + BACKUP_FOLDER_SUFFIX)

            # Start the log messages
            log.log("\n" + '/' * 60 +
                    "\n///// INPUT: " + input_path +
                    "\n///// OUTPUT: " + backup_folder +
                    "\n" + '/' * 60 + "\n")

            # Mark all the files needed for the backup process
            print(' ' * 40 + "\nPreparing files for backup from {} to {}...".format(input_path, backup_folder))
            reset_globals()
            start_time = time.time()
            new_files, changed_files, remove_files = mark_files(input_path, backup_folder, config, input_number)
            set_num_marked(len(new_files) + len(changed_files) + len(remove_files))
            print("\nFile preparation complete.")
            if NUM_FILES_ERROR > 0:
                log.log_print("There were {} error(s) reported during file preparation.".format(NUM_FILES_ERROR))
                print("Please check the log file for more info on the individual errors.")

            # Check that doing this backup won't over-fill the disk, if it will then return
            has_space, remaining_space, space_difference =\
                check_space_requirements(new_files, changed_files, remove_files, backup_folder)
            if not has_space:
                drive_letter, tail = os.path.splitdrive(backup_folder)
                error_str = "Copying {} to {} may not fit on the {} drive.".format(
                    input_path, backup_folder, drive_letter)
                error_str += "\nPlease clear up space on the drive you want to copy to and try again."
                error_str += "\nTry clearing at least {} on the {} drive and trying again.".format(
                    util.bytes_to_string(-1 * remaining_space, 3), drive_letter)
                log.log_print("\n" + error_str)
                set_error(error_str)
                set_status("ERROR: The backup will not fit. Backup process has stopped.")
                return

            # Make changes to the files found in file preparation
            print("Backing up files from {} to {}...".format(input_path, backup_folder))
            num_errors = backup_files(new_files, changed_files, remove_files)
            end_time = time.time()

            # Backup is complete, report the time taken, space difference, and if any errors occurred
            complete_str = "Backup complete in {}. ".format(util.time_string(end_time-start_time))
            complete_str += "(No changes)" if space_difference == 0 else "({}{})".format(
                util.sign_string(space_difference), util.bytes_to_string(abs(space_difference), precision=2))
            print("\n" + complete_str)
            set_status(complete_str)
            if num_errors > 0:
                log.log_print("There were {} error(s) reported during the backup.".format(num_errors))
                print("Please check the log file for more info on the individual errors.")

            # Report on any errors and finalize the backup
            final_report_str = "Backup complete: {} files processed, {} new files, {} existing files modified, " + \
                               "{} files removed ({}, {}{})"
            log.log(final_report_str.format(NUM_FILES_PROCESSED, NUM_FILES_NEW, NUM_FILES_MODIFIED,
                                            NUM_FILES_DELETED, util.bytes_to_string(TOTAL_SIZE_PROCESSED, 2),
                                            util.sign_string(space_difference),
                                            util.bytes_to_string(abs(space_difference), precision=2)))
            if NUM_FILES_ERROR > 0:
                log.log_print("There were {} error(s) reported during this backup.".format(NUM_FILES_ERROR))
                print("Please check the log file for more info on the individual errors.")
            create_backup_text_file(backup_folder)
            increment_backup_number()


def mark_files(input_path, output_path, config, input_number):
    """
    This is the file preparation stage of the backup process. The directory to be backed up is walked through, and
    all new files, changed files, and files that should be deleted are compiled into their respective lists,
    essentially "marking" those files for later. While the directory is walked, a directory skeleton structure
    is created in the output, so any directories that will have files sent to them later will exist in the output.
    :param input_path: The file or directory to backup.
    :param output_path: The file or directory in the drive to backup to.
    :param config: The current configuration.
    :param input_number: The index of the entry currently being worked with, starting from 1.
    :return: A tuple of three lists is returned.
             First is a list of new files. Each element of this list is a tuple of three values: first the absolute
             file path, second that file's size in bytes, and third the absolute file path from the output.
             Second is a list of changed files. Each element of this list is a tuple of four values: first the
             absolute file path from the input, second the size of the file from the input, third the absolute
             file path from the output, and fourth the size of the file from the output.
             Third is a list of files to delete. Each element of this list is a tuple of two values: first the absolute
             file path from the output, and second that file's size in bytes.
    """
    # Don't continue down this path if it should be excluded
    if config.get_entry(input_number).should_exclude(input_path, output_path):
        log.log("EXCLUDED - " + input_path)
        return [], [], []

    # If this is a file, check what to do with it and increment counters as necessary
    if os.path.isfile(input_path):
        file_size = os.path.getsize(input_path)
        if os.path.exists(output_path):
            if not util.file_compare(input_path, output_path):
                # The file has changed and will be added to the update list
                mark_file_processed(file_size, modified=True)
                return [], [(input_path, file_size, output_path, os.path.getsize(output_path))], []
            else:
                # The file needs no attention
                mark_file_processed(file_size)
                return [], [], []
        else:
            # The file is new and will be added to the new list
            mark_file_processed(file_size, is_new=True)
            return [(input_path, file_size, output_path)], [], []

    # Otherwise, it's a directory, so recurse on each child of the directory
    else:
        new_files = []
        changed_files = []
        remove_files = []

        # If this directory doesn't exist in the output, make it
        if not os.path.exists(output_path):
            try:
                os.mkdir(output_path)
                shutil.copymode(input_path, output_path)
            except PermissionError:
                # Log the exception and return so we don't process any of this directory's children
                log.log_exception(output_path, "CREATING DIRECTORY")
                increment_error()
                return [], [], []

        # Initialize values that will help in efficiently gathering names of files to remove
        input_dir_files = os.listdir(input_path)
        output_dir_files = os.listdir(output_path)
        output_dir_idx = 0
        len_output_dir = len(output_dir_files)

        # Start by sorting the file lists so we can index them and compare them side by side
        input_dir_files.sort()
        output_dir_files.sort()

        try:
            # Check every file in the input
            for input_dir_idx in range(len(input_dir_files)):
                filename = input_dir_files[input_dir_idx]
                new_input = os.path.join(input_path, filename)
                new_output = os.path.join(output_path, filename)

                # Loop to check if this file exists in the output as well by looping through output files
                while output_dir_idx < len_output_dir:
                    # If it does, index over it and leave the loop, leaving the file in the output alone
                    if filename == output_dir_files[output_dir_idx]:
                        output_dir_idx += 1
                        break
                    # If this output file isn't the current input file, add it to the remove list
                    else:
                        # Stop checking if we are beyond where this file would alphabetically be
                        if filename < output_dir_files[output_dir_idx]:
                            break
                        else:
                            output_filename = os.path.join(output_path, output_dir_files[output_dir_idx])
                            # Only add this to the list if it's not the old confirmation file
                            if not output_dir_files[output_dir_idx] == CONFIRMATION_FILENAME or \
                                    not input_path == config.get_entry(input_number).input:
                                if os.path.isdir(output_filename):
                                    delete_size, delete_files = util.directory_size(output_filename)
                                    for _ in range(delete_files):
                                        mark_file_processed(deleted=True)
                                else:
                                    mark_file_processed(deleted=True)
                                remove_files.append((output_filename, os.path.getsize(output_filename)))
                            output_dir_idx += 1

                # Recurse and add the returned lists and values to our current counters
                temp_new, temp_changed, temp_remove = mark_files(new_input, new_output, config, input_number)
                new_files.extend(temp_new)
                changed_files.extend(temp_changed)
                remove_files.extend(temp_remove)

            # If there's still more files in the output that weren't looped over, add them all to the remove list
            if output_dir_idx < len_output_dir:
                for end_output_idx in range(output_dir_idx, len(output_dir_files)):
                    output_filename = os.path.join(output_path, output_dir_files[end_output_idx])
                    # Only add this to the list if it's not the old confirmation file
                    if not output_dir_files[end_output_idx] == CONFIRMATION_FILENAME or \
                            not input_path == config.get_entry(input_number).input:
                        if os.path.isdir(output_filename):
                            delete_size, delete_files = util.directory_size(output_filename)
                            for _ in range(delete_files):
                                mark_file_processed(deleted=True)
                        else:
                            mark_file_processed(deleted=True)
                        remove_files.append((output_filename, os.path.getsize(output_filename)))

        except FileNotFoundError as error:
            # Display a warning if long paths need to be enabled on Windows
            if len(input_path) >= 260:
                print("FileNotFoundError: Unable to access " + input_path)
                print("This is likely because the file path is longer than 260 characters.")
                print("If you are running this on Windows, set LongPathsEnabled to 1 in your registry.")
            else:
                print(error)
            exit(1)

        # Show the current progress and return
        progress_str = "{} files found, {} ({} new, {} changed, {} to remove)".format(
            NUM_FILES_PROCESSED, util.bytes_to_string(TOTAL_SIZE_PROCESSED, 2), NUM_FILES_NEW,
            NUM_FILES_MODIFIED, NUM_FILES_DELETED)
        print(progress_str + ' '*10, end="\r", flush=True)
        return new_files, changed_files, remove_files


def check_space_requirements(new_files, changed_files, remove_files, output_path):
    """
    Given lists of new files, changed files, and files to delete, this checks that the drive these file changes
    will be made on will be able to hold all the new files.
    :param new_files: A list of new files to backup generated by mark_files().
    :param changed_files: A list of changed files to backup generated by mark_files().
    :param remove_files: A list of files to delete from the backup generated by mark_files().
    :param output_path: The path where the backup will be made.
    :return: A tuple of three values. First, true if the backup will fit on the drive, false otherwise. Second, the
             remaining free space on the target drive in bytes. This will be negative if the backup won't fit.
             Third, the difference in bytes this backup will take. This will be positive if the new backup will
             be bigger than what's already backed up, or negative if it's smaller.
    """
    total, used, free = shutil.disk_usage(output_path)
    original_free = free
    # Increase the free space on the drive for every file deleted
    for file_tuple in remove_files:
        free += file_tuple[1]
    # Decrease the free space on the drive for every new file added
    for file_tuple in new_files:
        free -= file_tuple[1]
    # Increase free space when the old changed file is deleted, then decrease for the space of the new version
    for file_tuple in changed_files:
        free = free - file_tuple[1] + file_tuple[3]
        # If free space ever dips below 0 during this, return
        if free <= 0:
            return free > 0, free, original_free - free
    return free > 0, free, original_free - free


def backup_files(new_files, changed_files, remove_files):
    """
    The files provided in the given lists will be backed up. This will first delete all the files in the
    remove_files list, then copy over all the files in the new_files list, then modify each file in the
    changed_files list.
    :param new_files: A list of new files to backup generated by mark_files().
    :param changed_files: A list of changed files to backup generated by mark_files().
    :param remove_files: A list of files to delete from the backup generated by mark_files().
    :return: The number of errors that occurred.
    """
    # If there's no changes to make, display a message
    if len(new_files) == 0 and len(changed_files) == 0 and len(remove_files) == 0:
        print("No changes are needed.", end="\r", flush=True)

    # Prepare values that will track the progress of each section of the backup
    num_errors = 0
    count = 0
    limit = len(remove_files)

    # Delete every file in the remove list
    for file_tuple in remove_files:
        delete_file_path = file_tuple[0]
        # Use the correct delete function based on if it's a file or folder
        try:
            if os.path.isdir(delete_file_path):
                deleted_file_count = util.rmtree(delete_file_path)
                for _ in range(deleted_file_count):
                    count += 1
                    increment_backup_progress()
                    print("Deleting old files: {}/{}".format(count, limit) + ' '*20, end="\r", flush=True)
            else:
                os.remove(delete_file_path)
            set_status("Deleting {}".format(os.path.split(delete_file_path)[1]))
            log.log("DELETED - " + delete_file_path)
        except PermissionError:
            # Log the exception and indicate that an error occurred
            log.log_exception(delete_file_path, "DELETING")
            num_errors += 1

    # Reset the counter values and copy over every file in the new list
    count = 0
    limit = len(new_files)
    for file_tuple in new_files:
        new_file = file_tuple[0]
        output_path = file_tuple[2]
        try:
            set_status("Copying over {} ({})".format(os.path.split(new_file)[1],
                                                     util.bytes_to_string(os.path.getsize(new_file), 2)))
            shutil.copy2(new_file, output_path)
            log.log("NEW - " + output_path)
        except PermissionError:
            # Write the full error to the log file and record that an error occurred
            log.log_exception(output_path, "CREATING")
            num_errors += 1
        count += 1
        increment_backup_progress()
        print("Copying over new files: {}/{}".format(count, limit) + ' '*20, end="\r", flush=True)

    # Reset the counter values and overwrite every file in the changed list
    count = 0
    limit = len(changed_files)
    for file_tuple in changed_files:
        new_file = file_tuple[0]
        output_path = file_tuple[2]
        try:
            set_status("Updating {}, ({})".format(os.path.split(new_file)[1],
                                                  util.bytes_to_string(os.path.getsize(new_file), 2)))
            shutil.copy2(new_file, output_path)
            log.log("UPDATED - " + output_path)
        except PermissionError:
            # Write the full error to the log file and record that an error occurred
            log.log_exception(output_path, "UPDATING")
            num_errors += 1
        count += 1
        increment_backup_progress()
        print("Updating existing files: {}/{}".format(count, limit) + ' '*20, end="\r", flush=True)
    return num_errors


@observable
def reset_globals():
    """
    Reset the variables that track how many files are being processed during the file preparation stage.
    """
    global NUM_FILES_PROCESSED
    global NUM_FILES_MARKED
    global NUM_FILES_MODIFIED
    global NUM_FILES_NEW
    global NUM_FILES_ERROR
    global NUM_FILES_DELETED
    global TOTAL_SIZE_PROCESSED
    global BACKUP_PROGRESS
    global ERROR
    NUM_FILES_PROCESSED = 0
    NUM_FILES_MARKED = 0
    NUM_FILES_MODIFIED = 0
    NUM_FILES_NEW = 0
    NUM_FILES_ERROR = 0
    NUM_FILES_DELETED = 0
    TOTAL_SIZE_PROCESSED = 0
    BACKUP_PROGRESS = 0
    ERROR = ""


@observable
def increment_processed():
    """
    Increment the global variable for tracking the number of files processed.
    """
    global NUM_FILES_PROCESSED
    NUM_FILES_PROCESSED += 1


@observable
def set_num_marked(num_marked):
    """
    Increment the global variable for tracking the number of files marked.
    """
    global NUM_FILES_MARKED
    NUM_FILES_MARKED = num_marked


@observable
def increment_modified():
    """
    Increment the global variable for tracking the number of files modified.
    """
    global NUM_FILES_MODIFIED
    NUM_FILES_MODIFIED += 1


@observable
def increment_new():
    """
    Increment the global variable for tracking the number of new files copied.
    """
    global NUM_FILES_NEW
    NUM_FILES_NEW += 1


@observable
def increment_deleted():
    """
    Increment the global variable for tracking the number of files deleted.
    """
    global NUM_FILES_DELETED
    NUM_FILES_DELETED += 1


@observable
def increment_error():
    """
    Increment the global variable for tracking the number of errors that occurred during the backup.
    """
    global NUM_FILES_ERROR
    NUM_FILES_ERROR += 1


@observable
def increment_size(size):
    """
    Increment the global variable for tracking the total size of files processed.
    :param size: The number of bytes to increment by.
    """
    global TOTAL_SIZE_PROCESSED
    TOTAL_SIZE_PROCESSED += size


@observable
def reset_backup_number():
    """
    Reset the global variable for tracking the backup number to 0, which tracks which backup is currently being
    done, starting from 0.
    """
    global BACKUP_NUMBER
    BACKUP_NUMBER = 0


@observable
def increment_backup_number():
    """
    Increment the global variable for tracking the backup number, which tracks which backup is currently being
    done, starting from 0.
    """
    global BACKUP_NUMBER
    BACKUP_NUMBER += 1


@observable
def increment_backup_progress():
    """
    Increment the global variable for tracking the number of files that have been copied, deleted, or modified so far.
    """
    global BACKUP_PROGRESS
    BACKUP_PROGRESS += 1


@observable
def set_status(status):
    """
    Set the status global variable. This will usually hold the name of what file is being worked on currently and
    the action being taken, or the total time taken when the backup is complete.
    :param status: The string to set the status to.
    """
    global CURRENT_STATUS
    CURRENT_STATUS = status


@observable
def set_error(error):
    """
    Set a major error message to be sent to the GUI. This message will display in a pop-up window.
    :param error: The string to set the error message to.
    """
    global ERROR
    ERROR = error


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
    if not deleted:
        increment_processed()
        increment_size(file_size)
    if modified:
        increment_modified()
    if is_new:
        increment_new()
    if error:
        increment_error()
    if deleted:
        increment_deleted()


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
