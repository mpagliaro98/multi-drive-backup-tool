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


def display_drive_space(path, precision):
    """
    Display and format the total, used, and free space of a given drive path.
    :param path: The path to the disk location to get this information for, in this case
                 a drive such as "C:".
    :param precision: The number of values after the decimal when displaying space values.
    """
    total, used, free = shutil.disk_usage(path)
    format_str = "{:." + str(precision) + "f} GiB"
    print("DRIVE: {}\\".format(path))
    print("\tTotal: " + format_str.format(total / (2 ** 30)), end="")
    print(", Used: " + format_str.format(used / (2 ** 30)), end="")
    print(", Free: " + format_str.format(free / (2 ** 30)))


def log(log_str):
    """
    Logging function, this will take in any given string and write it to a log file in
    the running directory.
    :param log_str: The string to append to the log file.
    """
    print("stub")
