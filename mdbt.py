"""
mdbt.py
Author: Michael Pagliaro
The command line argument interface. This is one possible entry-point to the application which allows users
to interface with it by passing command line arguments in order to run different functions of the program.
"""

import sys
import getopt
import itertools
import collections
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


class BadDataException(Exception):
    """
    An exception raised when an argument comes in with improperly formatted or invalid data.
    """
    pass


class BadArgumentsException(Exception):
    """
    An exception raised when improper arguments are given. This is usually raised when data arguments
    are required and aren't found.
    """
    pass


class WrapperArgumentException(Exception):
    """
    An exception raised when a wrapper argument is invoked more than once during a single execution.
    """
    pass


class Iterator:
    """
    A wrapper class for an iterator that allows access of the current value.
    """

    def __init__(self, iterator, starting_value):
        """
        Create this iterator wrapper. A starting value is required since we cannot view the current value
        of the iterator before calling next.
        :param iterator: The iterator to use.
        :param starting_value: The starting value of this iterator.
        """
        self._iterator = iterator
        self._current = starting_value

    def __next__(self):
        """
        Increment to the next value. This stores the value to be accessed later.
        :return: The new current value.
        """
        self._current = next(self._iterator)
        return self._current

    def __iter__(self):
        """
        Allows this object to be iterable.
        :return: This object.
        """
        return self

    @property
    def current(self):
        """
        The current value being viewed by the iterator.
        :return: The iterator's current value.
        """
        return self._current


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
        Creates the wrapper argument type. This will call the constructor of argument, but also creates two
        unique fields: a begin_function and an end_function. The function field will be changed as this
        argument gets used throughout the application.
        :param flag: The flag that denotes this argument. This should be unique across all arguments.
        :param data: What data is expected from this argument. This is mainly used in usage text.
        :param usage: Some text to describe this argument in the usage text.
        :param begin_function: A function that will be called the first time this argument is invoked.
        :param end_function: A function that will be called the second time this argument is invoked.
        """
        super().__init__(flag, data, usage, begin_function)
        self._begin_function = begin_function
        self._end_function = end_function

    @property
    def function(self):
        """
        Overrides the function property of its parent class. When this wrapper argument is first created, the
        function field is set to begin_function. When this method is called, begin_function will be returned, and
        the function field will now be set to the end_function. If this field is called again, end_function will
        be returned, and the function field will be set to None. Any time it is called after that, it will raise
        a WrapperArgumentException.
        :return: The proper function object depending on how many times this argument was invoked.
        """
        if self._function == self._begin_function:
            self._function = self._end_function
            return self._begin_function
        elif self._function == self._end_function:
            self._function = None
            return self._end_function
        else:
            raise WrapperArgumentException("Argument \"" + self._flag + "\" cannot be invoked more than once.")


########################################################################################
# Argument Functions ###################################################################
# All argument functions should take **kwargs as their only defined parameter, and #####
# return a dictionary of specific values or None.                                  #####
########################################################################################
# Supported inputs: "config": A configuration, "opts": A list of options, ##############
#     "iterator": An iterator with a 'current' field                      ##############
# Supported return values: "config": A configuration, "advance": The number of values ##
#     to increment the iterator by                                                    ##
########################################################################################


def option_input(**kwargs):
    """
    The code run when the input argument is given. This will create a new input path in the configuration
    to a folder or file specified.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    input_data = opts[iterator.current][1]
    configuration.append_input_to_config(config, input_data)


def option_destination(**kwargs):
    """
    The code run when the destination argument is given. This will create a new destination path in the
    configuration for the specified entry.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    output_data = opts[iterator.current][1]
    next_opt = opts[iterator.current+1]
    next_opt_type = get_argument(next_opt[0])

    # Make sure this is followed by a data argument and extract its data
    if not isinstance(next_opt_type, ArgumentData):
        raise BadArgumentsException("Destination argument should be followed by a data argument for input_index.")
    input_index = next_opt[1]

    # Validate the data from the data argument
    if input_index.isnumeric():
        input_index = int(input_index)
    else:
        raise BadDataException("The input index should be a valid number.")
    if input_index > config.num_entries() or input_index <= 0:
        raise BadDataException("The input index should correspond to a valid entry.")

    # Create the new destination
    configuration.append_output_to_config(config, input_index, output_data)
    return {"advance": 1}


def option_save(**kwargs):
    """
    The code run when the save argument is given. This will save the given configuration to a file with the
    name given with this argument.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration, 'opts' as
                   a list of options created by getopt, and 'iterator' as the current iterator being used.
    """
    config = kwargs["config"]
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    config_name = opts[iterator.current][1]
    config.name = config_name
    configuration.save_config(config, config_name)


def option_load(**kwargs):
    """
    The code run when the load argument is given. This will load the configuration of a given name and return it.
    :param kwargs: A dictionary of arguments. This expects 'opts' as a list of options created by getopt and
                   'iterator' as the current iterator being used.
    :return: The new configuration object returned in a dictionary with the key 'config'.
    """
    opts = kwargs["opts"]
    iterator = kwargs["iterator"]
    config_name = opts[iterator.current][1]
    print("Loading {}.dat...".format(config_name))
    return {"config": configuration.load_config(config_name)}


def option_backup(**kwargs):
    """
    The code run when the backup argument is given. This will pass the configuration to the backup module
    to run the backup process.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration.
    """
    backup.run_backup(kwargs["config"])


def option_print(**kwargs):
    """
    The code run when the print argument is given. This will display the given configuration.
    :param kwargs: A dictionary of arguments. This expects 'config' as a valid configuration.
    """
    print("\nCalculating file sizes...", end="\r", flush=True)
    print(configuration.config_display_string(kwargs["config"], show_exclusions=True))


########################################################################################
# Arguments ############################################################################
# All arguments used by this application are defined here. #############################
########################################################################################


ARGUMENT_FLAGS = [Argument("i", "input_path", "A path that will be a source for a backup.", option_input),
                  Argument("d", "destination_path", "A path that will be a destination for an input. Should be " +
                           "followed by --ii <input_index>.", option_destination),
                  Argument("s", "config_name", "A name to save this configuration as.", option_save),
                  Argument("l", "config_name", "The name of a saved configuration to load.", option_load),
                  ArgumentWrapper("c", "config_name", "Load this config at the start and save it at the end.",
                                  option_load, option_save),
                  ArgumentEmpty("b", "Run a backup on the current configuration.", option_backup),
                  ArgumentEmpty("p", "Print the current configuration.", option_print),
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
        print(' ' * 4 + ("{}{}: {}".format(prefix, arg.flag, arg.usage) if arg.data is None
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


def process_return_vals(return_vals, **kwargs):
    """
    Given a dictionary of return values from one of the menu option functions, this will process each of
    them and update necessary values. To support additional return values, this function needs to be updated
    along with every time it is called.
    :param return_vals: A dictionary of return values given by one of the menu option functions. This can
                        be None.
    :param kwargs: Additional arguments, which in this case are objects that could possibly be updated by an
                   incoming return value. This expects 'config' and 'iterator'.
    :return: A tuple of a configuration object and an Iterator. If these are not changed by this function, the
             ones passed in will just be returned.
    """
    return_config = kwargs["config"]
    return_iterator = kwargs["iterator"]
    if return_vals is not None:
        for key, value in return_vals.items():
            if key == "config":
                return_config = value
            elif key == "advance":
                collections.deque(itertools.islice(return_iterator, value))
    return return_config, return_iterator


def extract_opt_type(opts, arg_type):
    """
    Loop through a list of options and take any options of a given argument type and put them into a
    separate list. These options in the new list will be removed from the original list.
    :param opts: A list of options created by getopt.
    :param arg_type: An argument class to extract from the list.
    :return: A list of arg_type options that used to be in the original list. The opts list will be
             modified by reference.
    """
    opts_type = []
    wrapper_opt_idxs = []
    for opt_idx in range(len(opts)):
        argument = get_argument(opts[opt_idx][0])
        if isinstance(argument, arg_type):
            opts_type.append(opts[opt_idx])
            wrapper_opt_idxs.append(opt_idx)
    for opt_idx in reversed(wrapper_opt_idxs):
        del opts[opt_idx]
    return opts_type


def argument_loop(config, opts):
    """
    Loops through a list of command line arguments parsed by getopt and processes the function and data
    associated with each one.
    :param config: The current configuration.
    :param opts: A list of options created by getopt.
    :return: The configuration, which can be modified.
    """
    iterator = Iterator(iter(range(len(opts))), starting_value=0)
    for opt_idx in iterator:
        opt = opts[opt_idx][0]
        argument = get_argument(opt)
        if isinstance(argument, ArgumentData):
            raise BadArgumentsException("Data argument \"" + argument.flag + "\" found when not required.")
        else:
            return_vals = argument.function(config=config, opts=opts, iterator=iterator)
            config, iterator = process_return_vals(return_vals, config=config, iterator=iterator)
    return config


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

    # Collect a list of wrapper arguments and remove those from the main argument list
    wrapper_opts = extract_opt_type(opts, ArgumentWrapper)

    # Run the begin function of every wrapper argument
    config = argument_loop(config, wrapper_opts)

    # Loop through the main argument list
    config = argument_loop(config, opts)

    # Run the end function of every wrapper argument
    argument_loop(config, wrapper_opts)


if __name__ == "__main__":
    main(sys.argv[1:])
