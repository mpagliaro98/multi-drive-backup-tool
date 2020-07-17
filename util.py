"""
util.py
Author: Michael Pagliaro
Additional utility functions used by the backup tool.
"""

import os
import string
import shutil


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


def log(log_str):
    """
    Logging function, this will take in any given string and write it to a log file in
    the running directory.
    :param log_str: The string to append to the log file.
    """
    print("stub")
