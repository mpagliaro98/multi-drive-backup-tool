"""
log.py
Author: Michael Pagliaro
Utility functions specific to writing log files.
"""


from datetime import datetime
import sys
import traceback
import os


# The log file to be written to whenever log() is called
LOG_FILE = None
LOGS_DIRECTORY = "logs"


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


def log_print(log_str=""):
    """
    Logging function, this takes any string and writes it to the current log file as well as prints it
    to standard output. This automatically puts a newline after the string in the file and in the console
    output. The log file must be opened before using this function.
    :param log_str:
    :return:
    """
    global LOG_FILE
    LOG_FILE.write(log_str + "\n")
    print(log_str)


def log_exception(error_file_path, action="ACCESSING"):
    """
    Writes the most recent exception to the log file. This includes the full traceback.
    :param error_file_path: The file or folder that caused the error.
    :param action: What was happening to that file to cause the error, such as "creating" or "deleting".
    """
    log("\n" + '=' * 60 + "\nERROR {} {}".format(action, error_file_path))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exception_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_error_str = ""
    for item in exception_list:
        full_error_str += item
    log(full_error_str + '=' * 60 + "\n")