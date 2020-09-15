"""
mdbt.py
Author: Michael Pagliaro
The command line argument interface. This is one possible entry-point to the application which allows users
to interface with it by passing command line arguments in order to run different functions of the program.
"""


import sys
import getopt
import configuration
import backup


class ArgumentException(Exception):
    """
    An exception raised when an argument type is created with illegal data. This should not come up
    during normal execution of the program.
    """
    pass


class ArgumentDoesNotExistException(Exception):
    """
    An exception raised when an argument is given to the application that does not have a type. Most
    errors like these will be caught by getopt, so this will rarely appear.
    """
    pass


########################################################################################
# Argument Types #######################################################################
########################################################################################


class Argument:
    """
    A basic class representing a type of command line argument. Arguments of this type will have an
    identifying flag, data that goes with that argument, text to help with usage, and a function that is
    called when this argument is used.
    """

    def __init__(self, flag, data, usage, function):
        """
        Creates an argument type.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        :param function: A function that will be called when this argument is invoked.
        """
        self._flag = flag
        self._data = data
        self._usage = usage
        self._function = function

    @property
    def flag(self):
        """
        The flag that denotes this argument. This should be unique across all arguments.
        :return: The argument flag as a string.
        """
        return self._flag

    @property
    def data(self):
        """
        What data is expected from this argument. This is mainly used in usage text.
        :return: The argument data description as a string.
        """
        return self._data

    @property
    def usage(self):
        """
        Some text to describe this argument in the usage text.
        :return: The usage text for this argument as a string.
        """
        return self._usage

    @property
    def function(self):
        """
        A function that will be called when this argument is invoked.
        :return: The function object for this argument's function.
        """
        return self._function


class ArgumentEmpty(Argument):
    """
    A special type of argument that takes no data.
    """

    def __init__(self, flag, usage, function):
        """
        Creates the empty argument type. This will call the constructor of Argument, but set the
        data text to None. When this argument is processed, it will not expect data after it on the
        command line.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param usage: Some text to describe this argument in the usage text.
        :param function: A function that will be called when this argument is invoked.
        """
        super().__init__(flag, None, usage, function)


class ArgumentData(Argument):
    """
    A special type of argument that only takes data, and does not invoke a function when it
    is processed.
    """

    def __init__(self, flag, data, usage):
        """
        Creates the data argument type. This will call the constructor of Argument, but set the
        function to None. When this argument is processed, it won't try to make a function call.
        For a better visual indication of data arguments, they will only be allowed to have long
        flag names (2 or more characters in the flag), so if one is created with a one character
        name, an ArgumentException will be raised.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        """
        super().__init__(flag, data, usage, None)
        if len(flag) <= 1:
            raise ArgumentException


class ArgumentWrapper(Argument):
    """
    A special type of argument that executes a function before every other type of argument, then
    executes another function after every other argument.
    """

    def __init__(self, flag, data, usage, begin_function, end_function):
        """
        Creates the wrapper argument type. This will call the constructor of argument, but set its
        function field to None. Instead, this type has a begin_function and end_function property.
        When this argument is processed, the begin_function will run before any other arguments, and
        the end_function will run after any other arguments.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        :param begin_function: A function that will be called when this argument is invoked before the
                               main argument loop.
        :param end_function: A function that will be called when this argument is invoked after the
                             main argument loop.
        """
        super().__init__(flag, data, usage, None)
        self._begin_function = begin_function
        self._end_function = end_function

    @property
    def begin_function(self):
        """
        A function that will be called when this argument is invoked before the main argument loop.
        :return: The function object for this argument's begin function.
        """
        return self._begin_function

    @property
    def end_function(self):
        """
        A function that will be called when this argument is invoked after the main argument loop.
        :return: The function object for this argument's end function.
        """
        return self._end_function


########################################################################################
# Argument Functions ###################################################################
# All argument functions should take **kwargs as their only defined parameter, and #####
# return a configuration object and an index into the current options list. ############
########################################################################################


def option_save(**kwargs):
    """
    The code run when the save argument is given. This expects a configuration, a list of options from
    getopt, and the index of the current option being used. This will save the given configuration
    to a file with the name given with this argument.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'opt_idx' as the index into that list where
                   the current argument is.
    :return: A tuple of the current configuration and the current opt_idx.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    opt_idx = kwargs["opt_idx"]
    config_name = opts[opt_idx][1]
    config.name = config_name
    configuration.save_config(config, config_name)
    return config, opt_idx


def option_load(**kwargs):
    """
    The code run when the load argument is given. This expects a list of options from getopt and the index
    of the current option being used. This will load the configuration of the name that was provided with
    the argument and return it.
    :param kwargs: A dictionary of arguments. This expects 'opts' as a list of options created by getopt and
                   'opt_idx' as the index into that list where the current argument is.
    :return: A tuple of the loaded configuration and the current opt_idx.
    """
    opts = kwargs["opts"]
    opt_idx = kwargs["opt_idx"]
    config_name = opts[opt_idx][1]
    return configuration.load_config(config_name), opt_idx


def option_backup(**kwargs):
    """
    The code run when the backup argument is given. This expects a configuration and the index of the
    current option being used. This will pass the configuration to the backup module to run the backup
    process.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration and 'opt_idx'
                   as the index into that list where the current argument is.
    :return: A tuple of the current configuration and the current opt_idx.
    """
    config = kwargs["config"]
    backup.run_backup(config)
    return config, kwargs["opt_idx"]


########################################################################################
# Arguments ############################################################################
# All arguments used by this application are defined here. #############################
########################################################################################


ARGUMENT_FLAGS = [Argument("s", "config_name", "A name to save this configuration as.", option_save),
                  Argument("l", "config_name", "The name of a saved configuration to load.", option_load),
                  ArgumentWrapper("c", "config_name", "Load this config at the start and save it at the end.",
                                  option_load, option_save),
                  ArgumentEmpty("b", "Run a backup on the current configuration.", option_backup),
                  ArgumentData("ii", "input_index", "Input index"),
                  ArgumentData("di", "destination_index", "Destination index"),
                  ArgumentData("ei", "exclusion_index", "Exclusion index"),
                  ArgumentData("li", "limitation_index", "Limitation index")]


########################################################################################
# Utility Functions and Main ###########################################################
# Below are any utility functions for the main program and the main function itself. ###
########################################################################################


def display_usage():
    """
    Displays the usage text of this application.
    """
    print("Usage: mdbt.py [combination of flags below]")
    for arg in ARGUMENT_FLAGS:
        prefix = "--" if len(arg.flag) > 1 else "-"
        print(' '*4 + ("{}{}: {}".format(prefix, arg.flag, arg.usage) if arg.data is None
              else "{}{} <{}>: {}".format(prefix, arg.flag, arg.data, arg.usage)))


def get_argument(flag):
    """
    Given an argument flag from the command line, this finds the argument object that contains all data
    about that argument. The flag passed in is expected to be prefaced with a hyphen, for example '-b'
    or '--di'. If no argument exists with the given flag, it will raise an ArgumentDoesNotExistException.
    :param flag: A flag to find its corresponding argument as a string.
    :return: The argument object with a matching flag property.
    """
    flag_value = flag[1:] if len(flag) <= 2 else flag[2:]
    for arg in ARGUMENT_FLAGS:
        if flag_value == arg.flag:
            return arg
    raise ArgumentDoesNotExistException


def main(argv):
    """
    The main entry-point for this command line argument interface. This will check which arguments were entered
    and run the appropriate functions for each.
    """
    # Display usage text if no arguments are given
    if len(argv) == 0:
        display_usage()
        sys.exit(2)

    # Prepare the configuration and things for getopt
    config = configuration.Configuration()
    getopt_options = ""
    getopt_long_options = []

    # Build the option string and list for getopt
    for arg in ARGUMENT_FLAGS:
        if len(arg.flag) > 1:
            getopt_long_options.append(arg.flag + "=")
        else:
            getopt_options += arg.flag + ("" if isinstance(arg, ArgumentEmpty) else ":")

    # Read in the arguments with getopt
    try:
        opts, args = getopt.getopt(argv, getopt_options, getopt_long_options)
    except getopt.GetoptError as ge:
        print("There was an error in the arguments you entered.")
        print(ge.msg)
        display_usage()
        sys.exit(2)

    # Loop through opts, collect a list of wrapper arguments and remove those from the main argument list
    wrapper_opts = []
    wrapper_opt_idxs = []
    for opt_idx in range(len(opts)):
        argument = get_argument(opts[opt_idx][0])
        if isinstance(argument, ArgumentWrapper):
            wrapper_opts.append(opts[opt_idx])
            wrapper_opt_idxs.append(opt_idx)
    for opt_idx in reversed(wrapper_opt_idxs):
        del opts[opt_idx]

    # Run the begin function of every wrapper argument
    for opt_idx in range(len(wrapper_opts)):
        opt = wrapper_opts[opt_idx][0]
        argument = get_argument(opt)
        config, opt_idx = argument.begin_function(config=config, opts=wrapper_opts, opt_idx=opt_idx)

    # Loop through the main argument list
    for opt_idx in range(len(opts)):
        opt = opts[opt_idx][0]
        argument = get_argument(opt)
        if isinstance(argument, ArgumentData):
            continue
        else:
            config, opt_idx = argument.function(config=config, opts=opts, opt_idx=opt_idx)

    # Run the end function of every wrapper argument
    for opt_idx in range(len(wrapper_opts)):
        opt = wrapper_opts[opt_idx][0]
        argument = get_argument(opt)
        config, opt_idx = argument.end_function(config=config, opts=wrapper_opts, opt_idx=opt_idx)


if __name__ == "__main__":
    main(sys.argv[1:])
