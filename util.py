"""
util.py
Author: Michael Pagliaro
Additional utility functions used by the backup tool.
"""


def get_drive_list():
    """
    Searches the local machine and gets a list of the drive letters for each available
    drive on this system.
    :return: A list of drive letters for drives that can be accessed.
    """
    return []


def log(log_str):
    """
    Logging function, this will take in any given string and write it to a log file in
    the running directory.
    :param log_str: The string to append to the log file.
    """
    print("stub")
