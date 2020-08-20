"""
util.py
Author: Michael Pagliaro
Additional utility functions used by the backup tool.
"""

import os
import string
import shutil
import filecmp
from datetime import datetime
import stat


# The log file to be written to whenever log() is called
LOG_FILE = None
LOGS_DIRECTORY = "logs"


def get_drive_list():
    """
    Searches the local machine and gets a list of the drive letters for each available
    drive on this system.
    :return: A list of drive letters for drives that can be accessed.
    """
    return ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]


def drive_space_display_string(path, precision):
    """
    Create a string that formats the total, used, and free space of a given drive path.
    :param path: The path to the disk location to get this information for, in this case
                 a drive such as "C:".
    :param precision: The number of values after the decimal when displaying space values.
    :return: A string containing formatted information about the given drives.
    """
    total, used, free = shutil.disk_usage(path)
    format_str = "{:." + str(precision) + "f} GiB"
    return_str = "DRIVE: {}\\ ----- ".format(path)
    return_str += "Total: " + format_str.format(total / (2 ** 30))
    return_str += ", Used: " + format_str.format(used / (2 ** 30))
    return_str += ", Free: " + format_str.format(free / (2 ** 30)) + "\n"
    return return_str


def directory_size(path):
    """
    Calculates the amount of space taken up by files within a given directory, as well as how many files
    are in that directory.
    :param path: A directory path.
    :return: The number of bytes of storage files in that directory take up, followed by the total number
             of files in that directory.
    """
    total_size = 0
    total_files = 0
    start_path = path
    for path, dirs, files in os.walk(start_path):
        for file in files:
            next_file = os.path.join(path, file)
            total_size += os.path.getsize(next_file)
            total_files += 1
    return total_size, total_files


def directory_size_with_exclusions(path, config, input_number):
    """
    Calculates the size of a directory and how many files it contains while taking into account any
    exclusions specified in the configuration. Files marked to be excluded will not be factored into
    size and total files calculations.
    :param path: A directory path.
    :param config: The current backup configuration.
    :param input_number: The number of the index of the entry, starting at 1.
    :return: The number of bytes of storage files in that directory take up, followed by the total number
             of files in that directory, taking exclusions into account.
    """
    # Don't continue down this path if it should be excluded
    if config.get_entry(input_number).should_exclude(path):
        return 0, 0
    # If this is a file, add 1 to total files and its file size to the total file size
    if os.path.isfile(path):
        return os.path.getsize(path), 1
    # Otherwise, it's a directory, so recurse on each child of the directory
    else:
        total_size, total_files = 0, 0
        try:
            for filename in os.listdir(path):
                size, files = directory_size_with_exclusions(os.path.join(path, filename), config, input_number)
                total_size += size
                total_files += files
        except FileNotFoundError as error:
            # Display a warning if long paths need to be enabled on Windows
            if len(path) >= 260:
                print("FileNotFoundError: Unable to access " + path)
                print("This is likely because the file path is longer than 260 characters.")
                print("If you are running this on Windows, set LongPathsEnabled to 1 in your registry.")
            else:
                print(error)
            exit(1)
        return total_size, total_files


def time_string(time_seconds):
    """
    Creates a formatted string to express a length of time. Given a value in seconds, the value will
    be split into hours, minutes, and seconds based on how long that time period is.
    :param time_seconds: A value of time in seconds.
    :return: A formatted string expressing the time.
    """
    if time_seconds / 60 >= 1:
        if time_seconds / 3600 >= 1:
            # At least one hour
            time_minutes = time_seconds - (3600 * (time_seconds // 3600))
            num_hours = int(time_seconds // 3600)
            if num_hours == 1:
                hours_string = "hour"
            else:
                hours_string = "hours"
            num_minutes = int(time_minutes // 60)
            if num_minutes == 1:
                minutes_string = "minute"
            else:
                minutes_string = "minutes"
            return "{} {}, {} {}, {:.3f} seconds".format(num_hours, hours_string, num_minutes,
                                                         minutes_string, time_minutes % 60)
        else:
            # At least one minute
            num_minutes = int(time_seconds // 60)
            if num_minutes == 1:
                minutes_string = "minute"
            else:
                minutes_string = "minutes"
            return "{} {}, {:.3f} seconds".format(num_minutes, minutes_string, time_seconds % 60)
    else:
        # Less than one minute
        return "{:.3f} seconds".format(time_seconds)


def file_compare(path1, path2, byte_limit=(100 * (2 ** 20)), mtime_delta=2):
    """
    A modified version of filecmp.cmp() which will do much simpler checks to see if two files are equal if
    the files are over a certain size, in order to avoid doing slow byte-by-byte comparisons for files
    that are gigabytes large. If two files are the exact same size and have the same last modified time (within
    a given range), they are treated equal as long as they are more than byte_limit bytes large. Otherwise,
    filecmp.cmp() is run on both files.
    :param path1: The path of the first file. This is the one checked for the byte_limit.
    :param path2: The path of the second file.
    :param byte_limit: The maximum size in bytes for which we should do byte-by-byte comparisons on the two
                       files. By default, this is set to 100*2^20, or 104,857,600, which is 100MB.
    :param mtime_delta: How much variation the last modified time can have to still be considered equal.
                        This is taken into account because rounding differences when copying a file from an
                        NTFS device to a FAT device sometimes cause the last modified time of a file to change
                        by 1 or 2 seconds. This is by default set to 2, so as long as the last modified time
                        of the two files are within 2 seconds of each other, they will be considered equal.
    :return: True if the two files should be considered equal, false otherwise.
    """
    stats1 = os.stat(path1)
    stats2 = os.stat(path2)
    # If the first file is larger than the byte limit, only compare file size and modified time
    if stats1.st_size > byte_limit:
        if stats1.st_size == stats2.st_size and abs(stats1.st_mtime - stats2.st_mtime) <= mtime_delta:
            return True
        else:
            return False
    # Otherwise, use the built in file compare
    else:
        return filecmp.cmp(path1, path2)


def rmtree(start_path):
    """
    A function for removing a directory and all its sub-directories. This deletes all files in a
    given directory, then recursively walks through all sub-directories. This is meant as a substitute
    to using shutil.rmtree() as I encountered issues using that to delete certain types of files.
    :param start_path: The directory to delete.
    """
    for path, dirs, files in os.walk(start_path):
        # Delete all files, give write permissions if necessary
        for filename in files:
            full_filename = os.path.join(path, filename)
            os.chmod(full_filename, stat.S_IWRITE)
            os.remove(full_filename)
        # Recursively delete all sub-folders
        for folder_name in dirs:
            rmtree(os.path.join(path, folder_name))
    # Delete this folder now that it's empty
    os.rmdir(start_path)


def path_is_in_directory(path_to_check, directory_path):
    """
    Checks if a given path to a directory or file is directly in a given directory and not
    within any of its sub-directories.
    :param path_to_check: The file or directory to check if it's in the directory.
    :param directory_path: The directory to see if the other path is in it.
    :return: True if the file or directory is immediately in the directory, false otherwise.
    """
    return os.path.split(path_to_check)[0] == directory_path


def logger(func):
    """
    Creates a decorator function that when applied to a function, enables logging during the runtime
    of that function. When the function ends, the logfile is closed.
    :param func: The function to decorate.
    :return: A decorator function that wraps another function, controlling logging before and after it runs.
    """
    def wrapper_logger(*args, **kwargs):
        begin_log()
        return_value = func(*args, **kwargs)
        end_log()
        return return_value
    return wrapper_logger


def begin_log():
    """
    Open the log file to prepare for it to be written to. This will also write the first line
    of the log file. This should be called before using log() or end_log().
    """
    global LOG_FILE
    if not os.path.exists(os.path.join(os.getcwd(), LOGS_DIRECTORY)):
        os.mkdir(os.path.join(os.getcwd(), LOGS_DIRECTORY))
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = "log_backup_" + current_time + ".txt"
    file_path = os.path.join(os.getcwd(), LOGS_DIRECTORY, file_name)
    LOG_FILE = open(file_path, "w")
    LOG_FILE.write("Beginning backup log: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")


def end_log():
    """
    Close the log file after writing an ending message to the file. This should only be called
    after begin_log(). To write more log messages after this is called, begin_log() must be
    called again, which will start a new file.
    """
    global LOG_FILE
    LOG_FILE.write("Ending backup log: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    LOG_FILE.close()


def log(log_str=""):
    """
    Logging function, this will take in any given string and write it to a log file in
    the running directory. This will automatically print a newline in the log file after
    every time this function is called. The begin_log() function must be called before this
    can be used.
    :param log_str: The string to append to the log file.
    """
    global LOG_FILE
    LOG_FILE.write(log_str + "\n")
