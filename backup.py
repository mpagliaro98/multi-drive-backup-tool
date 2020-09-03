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

# The string on the end of the final backup folders
BACKUP_FOLDER_SUFFIX = "BACKUP"

# Variables to track how many files have been processed during the backup process
NUM_FILES_PROCESSED = 0
NUM_FILES_MODIFIED = 0
NUM_FILES_NEW = 0
NUM_FILES_ERROR = 0
NUM_FILES_DELETED = 0
TOTAL_SIZE_PROCESSED = 0


@util.logger
def run_backup(config):
    """
    The primary entry function that starts and runs the backup process.
    :param config: A configuration containing paths to folders to backup.
    """
    print("Initializing...", end="\r", flush=True)
    util.log("\n" + configuration.config_display_string(config, show_exclusions=True))

    # Loop through every entry in the configuration
    for input_number in range(1, config.num_entries()+1):
        input_path = config.get_entry(input_number).input
        outputs = config.get_entry(input_number).outputs
        for output_path in outputs:
            # Get the name of the folder to make the backup in
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " " + BACKUP_FOLDER_SUFFIX)

            # Start the log messages
            util.log("\n" + '/'*60)
            util.log("///// INPUT: " + input_path)
            util.log("///// OUTPUT: " + backup_folder)
            util.log('/'*60 + "\n")

            # Mark all the files needed for the backup process
            print(' ' * 40 + "\nPreparing files for backup from {} to {}...".format(input_path, backup_folder))
            reset_globals()
            start_time = time.time()
            new_files, changed_files, remove_files = mark_files(input_path, backup_folder, config, input_number)
            print("\nFile preparation complete.")
            if NUM_FILES_ERROR > 0:
                util.log_print("There were {} error(s) reported during file preparation.".format(NUM_FILES_ERROR))
                print("Please check the log file for more info on the individual errors.")

            # Check that doing this backup won't over-fill the disk, if it will then return
            has_space, remaining_space = check_space_requirements(new_files, changed_files, remove_files, backup_folder)
            if not has_space:
                drive_letter, tail = os.path.splitdrive(backup_folder)
                util.log_print("\nCopying {} to {} may not fit on the {} drive.".format(input_path, backup_folder,
                                                                                        drive_letter))
                util.log_print("Please clear up space on the drive you want to copy to and try again.")
                util.log_print("Try clearing at least {} on the {} drive and trying again.".format(
                    util.bytes_to_string(-1 * remaining_space, 3), drive_letter))
                return

            # Make changes to the files found in file preparation
            print("Backing up files from {} to {}...".format(input_path, backup_folder))
            num_errors = backup_files(new_files, changed_files, remove_files)
            end_time = time.time()
            print("\nBackup complete. ({})".format(util.time_string(end_time-start_time)))
            if num_errors > 0:
                util.log_print("There were {} error(s) reported during the backup.".format(num_errors))
                print("Please check the log file for more info on the individual errors.")

            # Report on any errors and finalize the backup
            final_report_str = "Backup complete: {} files processed, {} new files, {} existing files modified, " + \
                               "{} files removed ({})"
            util.log(final_report_str.format(NUM_FILES_PROCESSED, NUM_FILES_NEW, NUM_FILES_MODIFIED,
                                             NUM_FILES_DELETED, util.bytes_to_string(TOTAL_SIZE_PROCESSED, 2)))
            if NUM_FILES_ERROR > 0:
                util.log_print("There were {} error(s) reported during this backup.".format(NUM_FILES_ERROR))
                print("Please check the log file for more info on the individual errors.")
            create_backup_text_file(backup_folder)


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
             First is a list of new files. Each element of this list is a tuple of two values: first the absolute
             file path, and second that file's size in bytes.
             Second is a list of changed files. Each element of this list is a tuple of four values: first the
             absolute file path from the input, second the size of the file from the input, third the absolute
             file path from the output, and fourth the size of the file from the output.
             Third is a list of files to delete. Each element of this list is a tuple of two values: first the absolute
             file path from the output, and second that file's size in bytes.
    """
    global NUM_FILES_ERROR

    # Don't continue down this path if it should be excluded
    if config.get_entry(input_number).should_exclude(input_path):
        util.log("EXCLUDED - " + input_path)
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
            return [(input_path, file_size)], [], []

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
                log_exception(output_path, "CREATING DIRECTORY")
                NUM_FILES_ERROR += 1
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
                            if not output_dir_files[output_dir_idx] == CONFIRMATION_FILENAME or \
                                    not input_path == config.get_entry(input_number).input:
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
                    if not output_dir_files[end_output_idx] == CONFIRMATION_FILENAME or \
                            not input_path == config.get_entry(input_number).input:
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
        print(progress_str, end="\r", flush=True)
        return new_files, changed_files, remove_files


def check_space_requirements(new_files, changed_files, remove_files, output_path):
    """
    Given lists of new files, changed files, and files to delete, this checks that the drive these file changes
    will be made on will be able to hold all the new files.
    :param new_files: A list of new files to backup generated by mark_files().
    :param changed_files: A list of changed files to backup generated by mark_files().
    :param remove_files: A list of files to delete from the backup generated by mark_files().
    :param output_path: The path where the backup will be made.
    :return: A tuple of two values. First, true if the backup will fit on the drive, false otherwise. Second, the
             remaining free space on the target drive in bytes. This will be negative if the backup won't fit.
    """
    total, used, free = shutil.disk_usage(output_path)
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
            return free > 0, free
    return free > 0, free


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
    num_errors = 0
    return num_errors


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
    print("{}/{} files processed, {} new files, {} existing files modified, {} files removed ({} / {})  "
          .format(NUM_FILES_PROCESSED, total_files, NUM_FILES_NEW, NUM_FILES_MODIFIED, NUM_FILES_DELETED,
                  util.bytes_to_string(TOTAL_SIZE_PROCESSED, 2), util.bytes_to_string(total_size, 2)),
          end="\r", flush=True)
    return True


def reset_globals():
    """
    Reset the variables that track how many files are being processed during the file preparation stage.
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


def backup_has_space(config):
    """
    Loops through every input-output pair in the configuration, and checks to see if all input paths
    can fit in all outputs if they were all to be copied over. If a backup already exists for one of
    the input-output pairs, it will only compute the worst-case size difference when new files would
    be copied over and old files removed. This keeps a running total of how the space on each affected
    drive would change to ensure that all backups can fit.
    :param config: The current configuration.
    :return: True if all backups will fit, false otherwise.
    """
    rolling_totals = dict()
    for input_number in range(1, config.num_entries() + 1):
        for dest_number in range(1, config.get_entry(input_number).num_destinations()+1):
            input_path = config.get_entry(input_number).input
            output_path = config.get_entry(input_number).get_destination(dest_number)

            # Make an entry for this drive in the dictionary if it doesn't exist
            drive_letter, tail = os.path.splitdrive(output_path)
            if drive_letter not in rolling_totals:
                rolling_totals[drive_letter] = 0

            # If the backup folder exists, run a diff, otherwise just use the size of the input
            folder_name = os.path.split(input_path)[1]
            backup_folder = os.path.join(output_path, folder_name + " " + BACKUP_FOLDER_SUFFIX)
            if os.path.isdir(backup_folder):
                diff_size = util.folder_diff_size(input_path, backup_folder, config, input_number)
                output_size, output_files = util.directory_size(backup_folder)
            else:
                diff_size, total_files = util.directory_size_with_exclusions(input_path, config, input_number)
                output_size = 0
            rolling_totals[drive_letter] = rolling_totals[drive_letter] + diff_size

            # Check if the worst case size of copying new files will fill the drive
            total, used, free = shutil.disk_usage(output_path)
            if rolling_totals[drive_letter] >= free:
                util.log_print(" "*40)
                util.log_print("Copying {} to {} may not fit on the {} drive.".format(input_path, output_path,
                                                                                      drive_letter))
                util.log_print("Please clear up space on the drive you want to copy to and try again.")
                util.log_print("Try clearing at least {} on the {} drive and trying again.".format(
                    util.bytes_to_string(rolling_totals[drive_letter] - free, 3), drive_letter))
                return False
            else:
                # The worst case will fit, so increment the rolling total by the actual difference and not worst case
                rolling_totals[drive_letter] = rolling_totals[drive_letter] - diff_size
                input_size, input_files = util.directory_size_with_exclusions(input_path, config, input_number)
                true_diff_size = input_size - output_size
                rolling_totals[drive_letter] = rolling_totals[drive_letter] + true_diff_size
        return True
