"""
util.py
Author: Michael Pagliaro
Additional utility functions used by the backup tool.
"""

import os
import string
import shutil
from datetime import datetime


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
    return_str = "DRIVE: {}\\\n".format(path)
    return_str += "\tTotal: " + format_str.format(total / (2 ** 30))
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
